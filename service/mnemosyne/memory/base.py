"""Base abstract class for memory interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryBase(ABC):
    """
    Abstract base class for memory system.
    
    Defines the core interface for memory operations.
    """
    
    @abstractmethod
    def add(
        self,
        messages: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        infer: bool = True
    ) -> str:
        """
        Add a memory.
        
        Args:
            messages: Content to remember
            user_id: User ID for multi-tenancy
            metadata: Optional metadata
            infer: Whether to extract facts using LLM
            
        Returns:
            Memory ID
        """
        pass
    
    @abstractmethod
    def add_batch(
        self,
        messages: List[str],
        user_id: str
    ) -> List[str]:
        """
        Add multiple memories in batch.
        
        Args:
            messages: List of content to remember
            user_id: User ID for multi-tenancy
            
        Returns:
            List of memory IDs
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories.
        
        Args:
            query: Search query
            user_id: User ID for multi-tenancy
            limit: Maximum number of results
            
        Returns:
            List of memories with scores
        """
        pass
    
    @abstractmethod
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory data or None if not found
        """
        pass
    
    @abstractmethod
    def get_all(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of all memories
        """
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: Memory ID to delete
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def update(
        self,
        memory_id: str,
        data: str
    ) -> Dict[str, Any]:
        """
        Update a memory.
        
        Args:
            memory_id: Memory ID to update
            data: New content
            
        Returns:
            Updated memory data
        """
        pass
