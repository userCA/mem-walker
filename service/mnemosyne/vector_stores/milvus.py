"""Milvus vector store implementation."""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from ..exceptions import VectorStoreError
from ..utils import get_logger
from .base import VectorStoreBase
from .configs import MilvusConfig

logger = get_logger(__name__)


class MilvusVectorStore(VectorStoreBase):
    """
    Milvus vector store implementation.
    
    Provides vector storage and similarity search using Milvus.
    """
    
    def __init__(self, config: Optional[MilvusConfig] = None):
        """
        Initialize Milvus vector store.
        
        Args:
            config: Configuration for Milvus
        """
        if config is None:
            config = MilvusConfig()
        
        self.config = config
        self.collection: Optional[Collection] = None
        
        try:
            # Connect to Milvus
            connections.connect(
                alias="default",
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password
            )
            logger.info(f"Connected to Milvus at {config.host}:{config.port}")
            
            # Create or load collection
            self._init_collection()
            
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Milvus: {e}")
    
    def _init_collection(self) -> None:
        """Initialize or load collection."""
        collection_name = self.config.collection_name
        
        if utility.has_collection(collection_name):
            logger.info(f"Loading existing collection: {collection_name}")
            self.collection = Collection(collection_name)
            # Create any missing indexes BEFORE loading the collection
            self._ensure_scalar_indexes()
            # Ensure BM25 sparse vector index exists
            self._ensure_bm25_index()
            # Now load the collection
            self.collection.load()
        else:
            logger.info(f"Creating new collection: {collection_name}")
            self.create_collection(
                name=collection_name,
                vector_size=self.config.vector_size,
                distance_metric=self.config.distance_metric
            )
            self.collection.load()
    
    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> None:
        """Create a new collection."""
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=vector_size),
            FieldSchema(name="bm25_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="created_at", dtype=DataType.INT64),
        ]
        
        schema = CollectionSchema(fields=fields, description="Mnemosyne memories")
        
        # Create collection
        self.collection = Collection(name=name, schema=schema)
        
        # Create index
        index_params = {
            "metric_type": "COSINE" if distance_metric == "cosine" else "L2",
            "index_type": self.config.index_type,
            "params": self.config.index_params
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        # Create sparse vector index for BM25
        sparse_index_params = {
            "metric_type": "IP",
            "index_type": "SPARSE_INVERTED_INDEX",
            "params": {"nprobe": 10}
        }
        self.collection.create_index(
            field_name="bm25_embedding",
            index_params=sparse_index_params
        )

        # Create scalar indexes for filtering
        self._create_scalar_indexes()

        logger.info(f"Created collection: {name} with vector size: {vector_size}")

    def _create_scalar_indexes(self) -> None:
        """Create scalar indexes for filterable fields."""
        if self.collection is None:
            return

        scalar_config = self.config.scalar_index_config
        if not scalar_config:
            return

        for field_name, index_params in scalar_config.items():
            try:
                # Check if index already exists
                indexes = self.collection.indexes
                field_has_index = any(
                    idx.field_name == field_name for idx in indexes
                )

                if not field_has_index:
                    self.collection.create_index(
                        field_name=field_name,
                        index_params=index_params
                    )
                    logger.info(f"Created scalar index on field: {field_name}")
                else:
                    logger.debug(f"Scalar index already exists on field: {field_name}")

            except Exception as e:
                logger.warning(f"Failed to create scalar index on {field_name}: {e}")

    def _ensure_scalar_indexes(self) -> None:
        """Ensure scalar indexes exist (for existing collections)."""
        if self.collection is None:
            return

        try:
            # Get all existing indexes
            existing_indexes = {idx.field_name for idx in self.collection.indexes}
            # Get schema fields
            schema_fields = {field.name for field in self.collection.schema.fields}

            scalar_config = self.config.scalar_index_config
            if not scalar_config:
                return

            for field_name, index_params in scalar_config.items():
                # Skip if field doesn't exist in schema
                if field_name not in schema_fields:
                    logger.debug(f"Field {field_name} does not exist in collection schema, skipping index")
                    continue
                if field_name not in existing_indexes:
                    self.collection.create_index(
                        field_name=field_name,
                        index_params=index_params
                    )
                    logger.info(f"Created missing scalar index on field: {field_name}")

        except Exception as e:
            logger.warning(f"Failed to ensure scalar indexes: {e}")

    def _ensure_bm25_index(self) -> None:
        """Ensure BM25 sparse vector index exists (for existing collections)."""
        if self.collection is None:
            return

        try:
            # Check if bm25_embedding field exists in schema
            schema_fields = {field.name for field in self.collection.schema.fields}
            if "bm25_embedding" not in schema_fields:
                logger.debug("bm25_embedding field does not exist in collection schema, skipping index creation")
                return

            existing_indexes = {idx.field_name for idx in self.collection.indexes}

            if "bm25_embedding" not in existing_indexes:
                sparse_index_params = {
                    "metric_type": "IP",
                    "index_type": "SPARSE_INVERTED_INDEX",
                    "params": {"nprobe": 10}
                }
                self.collection.create_index(
                    field_name="bm25_embedding",
                    index_params=sparse_index_params
                )
                logger.info("Created missing BM25 sparse vector index")
            else:
                logger.debug("BM25 sparse vector index already exists")

        except Exception as e:
            logger.warning(f"Failed to ensure BM25 index: {e}")

    def _needs_rebuild(self) -> bool:
        """
        Check if collection needs rebuild (missing partition key).

        Returns True if the existing collection lacks the user_id partition key
        and needs to be rebuilt.
        """
        if self.collection is None:
            return False

        try:
            for field in self.collection.schema.fields:
                if field.name == "user_id" and field.is_partition_key:
                    return False  # Has partition key, no rebuild needed
            return True  # Missing partition key
        except Exception as e:
            logger.warning(f"Failed to check partition key status: {e}")
            return True  # Assume rebuild needed on error

    def insert(
        self,
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        bm25_vectors: Optional[List[List[tuple]]] = None
    ) -> List[str]:
        """Insert vectors into collection."""
        if self.collection is None:
            raise VectorStoreError("Collection not initialized")

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

        # Prepare data
        import time
        timestamp = int(time.time())

        data = []
        for i, (vec_id, vector) in enumerate(zip(ids, vectors)):
            payload = payloads[i] if payloads else {}
            bm25_vec = bm25_vectors[i] if bm25_vectors else []

            data.append({
                "id": vec_id,
                "embedding": vector,
                "user_id": payload.get("user_id", "default"),
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
                "created_at": timestamp,
                "bm25_embedding": bm25_vec
            })

        try:
            self.collection.insert(data)
            # self.collection.flush()  # Removed to improve performance
            logger.debug(f"Inserted {len(vectors)} vectors")
            return ids
        except Exception as e:
            raise VectorStoreError(f"Failed to insert vectors: {e}")
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if self.collection is None:
            raise VectorStoreError("Collection not initialized")
        
        try:
            # Load collection
            self.collection.load()
            
            # Build filter expression
            expr = None
            if filters and "user_id" in filters:
                expr = f'user_id == "{filters["user_id"]}"'
            
            # Search
            search_params = {"metric_type": "COSINE", "params": self.config.search_params}
            
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["id", "user_id", "content", "metadata", "created_at"]
            )
            
            # Format results
            formatted_results = []
            for hit in results[0]:
                formatted_results.append({
                    "id": hit.entity.get("id"),
                    "score": float(hit.distance),
                    "user_id": hit.entity.get("user_id"),
                    "content": hit.entity.get("content"),
                    "metadata": hit.entity.get("metadata"),
                    "created_at": hit.entity.get("created_at")
                })
            
            logger.debug(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            raise VectorStoreError(f"Search failed: {e}")
    
    def delete(self, vector_id: str) -> bool:
        """Delete a vector by ID."""
        if self.collection is None:
            raise VectorStoreError("Collection not initialized")
        
        try:
            expr = f'id == "{vector_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            logger.debug(f"Deleted vector: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector {vector_id}: {e}")
            return False
    
    def update(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a vector."""
        # Milvus doesn't support direct update, so delete and re-insert
        if self.delete(vector_id):
            if vector and payload:
                self.insert([vector], [payload], [vector_id])
                return True
        return False
    
    def get(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a vector by ID."""
        if self.collection is None:
            return None
        
        try:
            expr = f'id == "{vector_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["id", "user_id", "content", "metadata", "created_at"]
            )
            
            if results:
                return results[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get vector {vector_id}: {e}")
            return None
    
    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List all vectors matching filters."""
        if self.collection is None:
            return []
        
        try:
            expr_parts = []
            if filters:
                if "user_id" in filters:
                    expr_parts.append(f'user_id == "{filters["user_id"]}"')
                
                # Handle metadata filters (e.g., content_hash)
                # Schema fields that are not metadata
                schema_fields = ["id", "user_id", "content", "created_at", "embedding"]
                
                for key, value in filters.items():
                    if key not in schema_fields:
                        # Treat as metadata field query: metadata["key"] == value
                        if isinstance(value, str):
                            expr_parts.append(f'metadata["{key}"] == "{value}"')
                        elif isinstance(value, (int, float)):
                            expr_parts.append(f'metadata["{key}"] == {value}')
                        elif isinstance(value, bool):
                            expr_parts.append(f'metadata["{key}"] == {str(value).lower()}')

            expr = " && ".join(expr_parts) if expr_parts else ""
            
            results = self.collection.query(
                expr=expr or "",
                output_fields=["id", "user_id", "content", "metadata", "created_at"],
                limit=limit
            )
            
            return results
        except Exception as e:
            logger.error(f"Failed to list vectors: {e}")
            return []
    
    def delete_collection(self) -> None:
        """Delete the collection."""
        if self.collection:
            utility.drop_collection(self.collection.name)
            logger.info(f"Deleted collection: {self.collection.name}")
            self.collection = None
    
    def collection_info(self) -> Dict[str, Any]:
        """Get collection information."""
        if self.collection is None:
            return {}

        return {
            "name": self.collection.name,
            "num_entities": self.collection.num_entities,
            "schema": str(self.collection.schema)
        }

    def bm25_search(
        self,
        query: str = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        query_vector: Optional[List[Tuple[int, float]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25 keyword matching via Milvus sparse vector.

        Args:
            query: Search query string
            limit: Maximum number of results
            filters: Optional metadata filters (user_id required)
            query_vector: Optional precomputed sparse vector (index, score) tuples

        Returns:
            List of search results with scores and payloads
        """
        if self.collection is None:
            raise VectorStoreError("Collection not initialized")

        try:
            self.collection.load()

            # Build filter expression
            expr = None
            if filters and "user_id" in filters:
                expr = f'user_id == "{filters["user_id"]}"'

            # Determine sparse vector source
            if query_vector is None and query is not None:
                sparse_vector = self._text_to_sparse_vector(query)
            elif query_vector is not None:
                sparse_vector = query_vector
            else:
                raise ValueError("Either query or query_vector must be provided")

            search_params = {
                "metric_type": "IP",  # Inner product for sparse
                "params": {"nprobe": 10}
            }

            results = self.collection.search(
                data=[sparse_vector],
                anns_field="bm25_embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["id", "user_id", "content", "metadata", "created_at"]
            )

            # Format results
            formatted_results = []
            for hit in results[0]:
                formatted_results.append({
                    "id": hit.entity.get("id"),
                    "score": float(hit.distance),
                    "user_id": hit.entity.get("user_id"),
                    "content": hit.entity.get("content"),
                    "metadata": hit.entity.get("metadata"),
                    "created_at": hit.entity.get("created_at")
                })

            logger.debug(f"BM25 found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.warning(f"BM25 search failed: {e}, falling back to empty results")
            return []

    def _text_to_sparse_vector(self, text: str) -> List[float]:
        """
        Convert text to sparse vector using TF-IDF-like approach.
        Returns list of (index, value) pairs for non-zero terms.
        """
        terms = text.lower().split()
        term_freq = {}
        for term in terms:
            term_freq[term] = term_freq.get(term, 0) + 1

        # Simple TF-IDF-like normalization
        max_freq = max(term_freq.values()) if term_freq else 1
        sparse = {}
        for term, freq in term_freq.items():
            # Use hash to map term to index (simplified)
            term_hash = hash(term) % 10000
            tf = freq / max_freq
            sparse[term_hash] = tf

        # Convert to Milvus sparse vector format [(index, value), ...]
        return [(idx, val) for idx, val in sparse.items()]
