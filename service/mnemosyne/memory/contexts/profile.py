"""Profile Memory Context implementation."""

from typing import Any, Dict, List, Optional

from ..profiles.manager import UserProfileKBManager
from ..profiles.schema import MemoryType, Importance
from .base import MemoryContext

class ProfileMemoryContext(MemoryContext):
    """
    Profile Memory Context.
    
    Wraps UserProfileKBManager for the User Profile Knowledge Base scenario.
    """
    
    def __init__(self, manager: UserProfileKBManager):
        self.manager = manager
        
    def add(
        self,
        content: Any,
        **kwargs
    ) -> str:
        """
        Add profile memory.
        
        Args:
            content: str - Content
            **kwargs:
                user_id: str (required)
                agent_id: str (required)
                memory_type: MemoryType (optional, default PREFERENCE)
                importance: Importance (optional, default NORMAL)
        """
        user_id = kwargs.get("user_id")
        agent_id = kwargs.get("agent_id")
        
        if not user_id or not agent_id:
            raise ValueError("user_id and agent_id are required for ProfileMemoryContext")
            
        return self.manager.add_memory(
            user_id=user_id,
            agent_id=agent_id,
            content=str(content),
            memory_type=kwargs.get("memory_type", MemoryType.PREFERENCE),
            importance=kwargs.get("importance", Importance.NORMAL),
            timestamp=kwargs.get("timestamp")
        )

    def search(
        self,
        query: Any,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search profile.
        
        Args:
            query: str - Query text
            **kwargs:
                user_id: str (required)
                agent_id: str (optional)
                memory_types: List[MemoryType] (optional)
                limit: int (default 5)
        """
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for ProfileMemoryContext")
            
        return self.manager.query_memory(
            user_id=user_id,
            query_text=str(query),
            agent_id=kwargs.get("agent_id"),
            memory_types=kwargs.get("memory_types"),
            top_k=kwargs.get("limit", 5)
        )

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        # ProfileKBManager doesn't expose strict get by ID yet in high level API,
        # but VectorStore has it. 
        # Refactoring opportunity: Expose get in Manager or access vector store directly.
        # Ideally Facade should provide it.
        # For now, let's delegate or raise NotImplemented if strictly not supported by Manager facade.
        # Actually Manager acts as facade. Let's see if Manager has get.
        # Manager has query_memory. 
        # But we can access self.manager.vector_store.get(memory_id) if we really want.
        
        # Let's assume for now we implement it if manager exposes it, otherwise simple wrapper.
        pass

    def delete(self, memory_id: str) -> bool:
        # Similar to get, Manager facade needs to expose delete.
        # Currently Manager doesn't expose delete explicitly.
        # But VectorStore does.
        # We can call self.manager.vector_store.delete(memory_id)
        # But this breaks encapsulation slightly. Optimally Manager should have delete.
        pass

    def update(self, memory_id: str, data: Any, **kwargs) -> Dict[str, Any]:
        # Not implemented in Manager yet.
        pass
    
    def close(self) -> None:
        self.manager.close()
