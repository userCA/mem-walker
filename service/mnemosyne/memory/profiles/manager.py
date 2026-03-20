import time
import uuid
import logging
from typing import List, Dict, Any, Optional

from ...configs import GlobalSettings
from ...embeddings.base import EmbeddingBase
from ...utils import get_logger
from .schema import (
    MemoryType, TimeLayer, Importance,
    FIELD_USER_ID, FIELD_AGENT_ID, FIELD_TYPE,
    FIELD_TIME_LAYER, FIELD_IMPORTANCE, FIELD_CONTENT,
    FIELD_TIMESTAMP
)
from .vector_store import ProfileMilvusVectorStore

logger = get_logger(__name__)

class UserProfileKBManager:
    """
    Manager for User Profile Knowledge Base.
    Acts as a Facade (similar to Memory class) delegating to ProfileMilvusVectorStore.
    """

    def __init__(self, embedding: EmbeddingBase, config: Optional[GlobalSettings] = None):
        """
        Initialize the manager.
        """
        self.embedding = embedding
        self.config = config or GlobalSettings.from_env()
        
        # Initialize specialized Vector Store
        # Reuses MilvusConfig from GlobalSettings
        self.vector_store = ProfileMilvusVectorStore(self.config.vector_store_config)

    def add_memory(
        self,
        user_id: str,
        agent_id: str,
        content: str,
        memory_type: MemoryType,
        importance: Importance = Importance.NORMAL,
        timestamp: Optional[int] = None
    ) -> str:
        """
        Add a memory to the knowledge base.
        """
        if not timestamp:
            timestamp = int(time.time())
            
        # Determine Time Layer based on timestamp
        now = int(time.time())
        diff_days = (now - timestamp) / 86400
        if diff_days < 7:
            time_layer = TimeLayer.SHORT
        elif diff_days < 30:
            time_layer = TimeLayer.MID
        else:
            time_layer = TimeLayer.LONG
            
        # Generate embedding
        vector = self.embedding.embed(content, memory_action="add")
        
        # Prepare payload
        payload = {
            FIELD_USER_ID: user_id,
            FIELD_AGENT_ID: agent_id,
            FIELD_TYPE: memory_type,
            FIELD_TIME_LAYER: time_layer,
            FIELD_IMPORTANCE: importance,
            FIELD_CONTENT: content,
            FIELD_TIMESTAMP: timestamp
        }
        
        # Delegate to Vector Store
        ids = self.vector_store.insert(
            vectors=[vector],
            payloads=[payload]
        )
        
        mid = ids[0]
        logger.debug(f"Added memory {mid} for user {user_id}, agent {agent_id}")
        return mid

    def query_memory(
        self,
        user_id: str,
        query_text: str,
        agent_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query memory with hybrid filtering.
        """
        # Generate query vector
        query_vector = self.embedding.embed(query_text, memory_action="search")
        
        # Prepare filters
        filters = {
            FIELD_USER_ID: user_id
        }
        if agent_id:
            filters[FIELD_AGENT_ID] = agent_id
        if memory_types:
            filters["memory_types"] = memory_types
            
        # Delegate to Vector Store
        results = self.vector_store.search(
            query_vector=query_vector,
            limit=top_k,
            filters=filters
        )
        
        return results

    def close(self):
        """Release resources."""
        # Current MilvusVectorStore doesn't strictly require close, 
        # but if we wanted to release collection explicitly:
        if self.vector_store.collection:
            self.vector_store.collection.release()
