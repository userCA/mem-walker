"""Milvus vector store implementation."""

import uuid
from typing import Any, Dict, List, Optional

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
        
        logger.info(f"Created collection: {name} with vector size: {vector_size}")
    
    def insert(
        self,
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
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
            
            data.append({
                "id": vec_id,
                "embedding": vector,
                "user_id": payload.get("user_id", "default"),
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
                "created_at": timestamp
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
