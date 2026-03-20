from typing import Any, Dict, List, Optional
import uuid
import time

from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility

from ...vector_stores.milvus import MilvusVectorStore
from ...vector_stores.configs import MilvusConfig
from ...utils import get_logger
from .schema import (
    FIELD_ID, FIELD_USER_ID, FIELD_AGENT_ID, FIELD_TYPE,
    FIELD_TIME_LAYER, FIELD_IMPORTANCE, FIELD_CONTENT,
    FIELD_VECTOR, FIELD_TIMESTAMP
)

logger = get_logger(__name__)

class ProfileMilvusVectorStore(MilvusVectorStore):
    """
    Specialized Milvus Vector Store for User Profile KB.
    Inherits connection logic from MilvusVectorStore but defines custom Schema.
    """

    def __init__(self, config: Optional[MilvusConfig] = None):
        """Initialize with custom collection name."""
        if config is None:
            config = MilvusConfig()
        
        # Override collection name for Profile KB
        # NOTE: We modify the config object copy or ensure it doesn't affect global if shared.
        # Ideally we should pass collection_name to super, but super uses config.collection_name.
        # We'll set it here before calling super().__init__ if possible, or just re-init collection after.
        
        # Strategy: Let super connect, then we handle collection creation if needed with OUR name.
        # But super calls _init_collection() in __init__.
        # So we should modify config.collection_name BEFORE calling super().__init__
        
        config.collection_name = "user_profile_knowledge_base" 
        super().__init__(config)

    def _init_collection(self) -> None:
        """Override to ensure our specific schema is used."""
        # Use the logic from base class but ensure if we create, we use OUR create method
        super()._init_collection()

    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> None:
        """
        Create the Profile KB specific collection.
        This overrides the base method to define the specific Schema.
        """
        # Define Profile KB Schema
        fields = [
            # Primary Key
            FieldSchema(name=FIELD_ID, dtype=DataType.VARCHAR, max_length=64, is_primary=True, auto_id=False),
            # Partition Key: Route data by user_id
            FieldSchema(name=FIELD_USER_ID, dtype=DataType.VARCHAR, max_length=64, is_partition_key=True),
            # Filtering Fields
            FieldSchema(name=FIELD_AGENT_ID, dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name=FIELD_TYPE, dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name=FIELD_TIME_LAYER, dtype=DataType.VARCHAR, max_length=16),
            FieldSchema(name=FIELD_IMPORTANCE, dtype=DataType.VARCHAR, max_length=16),
            # Content
            FieldSchema(name=FIELD_CONTENT, dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name=FIELD_VECTOR, dtype=DataType.FLOAT_VECTOR, dim=vector_size),
            FieldSchema(name=FIELD_TIMESTAMP, dtype=DataType.INT64),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="User Profile Knowledge Base with Partition Key on user_id"
        )
        
        # Create collection
        # Note: Shards num could be higher for production, hardcoded here or passed via config if extended
        self.collection = Collection(name=name, schema=schema, shards_num=4)
        
        # Create indexes
        # 1. Scalar Indexes
        scalar_index_params = {"index_type": "INVERTED"} 
        for field in [FIELD_AGENT_ID, FIELD_TYPE, FIELD_TIME_LAYER, FIELD_IMPORTANCE]:
             self.collection.create_index(field_name=field, index_params=scalar_index_params)
        
        # 2. Vector Index
        index_params = {
            "metric_type": "COSINE" if distance_metric == "cosine" else "L2",
            "index_type": self.config.index_type,
            "params": self.config.index_params
        }
        self.collection.create_index(field_name=FIELD_VECTOR, index_params=index_params)
        
        logger.info(f"Created Profile KB collection: {name} with vector size: {vector_size}")

    def insert(
        self,
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Override insert to map fields correctly.
        payloads must contain: user_id, agent_id, memory_type, etc.
        """
        if self.collection is None:
            raise Exception("Collection not initialized")
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            
        # Prepare data in Column-Based format for Milvus (List of Lists)
        # Order must match Schema: 
        # ID, UserID, AgentID, Type, TimeLayer, Importance, Content, Vector, Timestamp
        
        data_columns = {
            FIELD_ID: ids,
            FIELD_USER_ID: [],
            FIELD_AGENT_ID: [],
            FIELD_TYPE: [],
            FIELD_TIME_LAYER: [],
            FIELD_IMPORTANCE: [],
            FIELD_CONTENT: [],
            FIELD_VECTOR: vectors,
            FIELD_TIMESTAMP: []
        }
        
        for p in payloads:
            data_columns[FIELD_USER_ID].append(p.get(FIELD_USER_ID))
            data_columns[FIELD_AGENT_ID].append(p.get(FIELD_AGENT_ID))
            data_columns[FIELD_TYPE].append(p.get(FIELD_TYPE, "unknown"))
            data_columns[FIELD_TIME_LAYER].append(p.get(FIELD_TIME_LAYER, "mid"))
            data_columns[FIELD_IMPORTANCE].append(p.get(FIELD_IMPORTANCE, "normal"))
            data_columns[FIELD_CONTENT].append(p.get(FIELD_CONTENT, ""))
            data_columns[FIELD_TIMESTAMP].append(p.get(FIELD_TIMESTAMP, int(time.time())))
            
        # Convert to list of lists in correct order for insert
        data_to_insert = [
            data_columns[FIELD_ID],
            data_columns[FIELD_USER_ID],
            data_columns[FIELD_AGENT_ID],
            data_columns[FIELD_TYPE],
            data_columns[FIELD_TIME_LAYER],
            data_columns[FIELD_IMPORTANCE],
            data_columns[FIELD_CONTENT],
            data_columns[FIELD_VECTOR],
            data_columns[FIELD_TIMESTAMP]
        ]
        
        self.collection.insert(data_to_insert)
        return ids

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Override search to build specific filter expressions.
        """
        if self.collection is None:
            raise Exception("Collection not initialized")
            
        self.collection.load()
        
        # Build Expr
        # filters: {FIELD_USER_ID: "...", FIELD_AGENT_ID: "...", "memory_types": [...]}
        expr_parts = []
        
        if filters:
            if FIELD_USER_ID in filters:
                expr_parts.append(f'{FIELD_USER_ID} == "{filters[FIELD_USER_ID]}"')
            
            if FIELD_AGENT_ID in filters:
                expr_parts.append(f'{FIELD_AGENT_ID} == "{filters[FIELD_AGENT_ID]}"')
                
            if "memory_types" in filters and filters["memory_types"]:
                types = filters["memory_types"]
                types_str = ",".join([f'"{t}"' for t in types])
                expr_parts.append(f'{FIELD_TYPE} in [{types_str}]')

        expr = " && ".join(expr_parts) if expr_parts else ""
        
        search_params = {"metric_type": "COSINE", "params": self.config.search_params}
        
        results = self.collection.search(
            data=[query_vector],
            anns_field=FIELD_VECTOR,
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=[FIELD_CONTENT, FIELD_TYPE, FIELD_IMPORTANCE, FIELD_TIMESTAMP, FIELD_AGENT_ID]
        )
        
        # Adapt output to standard format expected by Manager/Caller if needed, 
        # or just return raw hits. Manager expects Dicts.
        
        formatted_results = []
        for hit in results[0]:
            formatted_results.append({
                "id": hit.entity.get(FIELD_ID), # ID might not be in output_fields if not requested, but it is PK
                "score": float(hit.distance),
                FIELD_CONTENT: hit.entity.get(FIELD_CONTENT),
                FIELD_TYPE: hit.entity.get(FIELD_TYPE),
                FIELD_IMPORTANCE: hit.entity.get(FIELD_IMPORTANCE),
                FIELD_TIMESTAMP: hit.entity.get(FIELD_TIMESTAMP),
                FIELD_AGENT_ID: hit.entity.get(FIELD_AGENT_ID),
                # Add others if needed
            })
            
        return formatted_results
