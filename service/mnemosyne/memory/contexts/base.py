"""Abstract Base Class for Memory Contexts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class MemoryContext(ABC):
    """
    Abstract Base Class for Memory Contexts.
    
    A Memory Context represents a specific strategy or scenario for memory management,
    such as 'Generic Facts', 'User Profile', 'Episodic Memory', etc.
    """
    
    @abstractmethod
    def add(
        self,
        content: Any,
        **kwargs
    ) -> str:
        """
        Add content to memory.
        
        Args:
            content: The content to store (str, dict, etc.)
            **kwargs: Context-specific arguments (user_id, agent_id, etc.)
            
        Returns:
            Memory ID
        """
        pass

    @abstractmethod
    def search(
        self,
        query: Any,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search memories.
        
        Args:
            query: The search query
            **kwargs: Context-specific filters and params
            
        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID."""
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        pass
        
    @abstractmethod
    def update(self, memory_id: str, data: Any, **kwargs) -> Dict[str, Any]:
        """Update a memory."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Release resources."""
        pass
