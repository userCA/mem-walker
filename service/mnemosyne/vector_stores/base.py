"""Base abstract class for vector stores."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VectorStoreBase(ABC):
    """
    Abstract base class for vector stores.
    
    All vector store implementations should inherit from this class.
    """
    
    @abstractmethod
    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> None:
        """
        Create a new collection for storing vectors.
        
        Args:
            name: Collection name
            vector_size: Dimension of vectors
            distance_metric: Distance metric (cosine, euclidean, ip)
        """
        pass
    
    @abstractmethod
    def insert(
        self,
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Insert vectors into the collection.
        
        Args:
            vectors: List of embedding vectors
            payloads: Optional metadata for each vector
            ids: Optional custom IDs for vectors
            
        Returns:
            List of inserted vector IDs
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores and payloads
        """
        pass
    
    @abstractmethod
    def delete(self, vector_id: str) -> bool:
        """
        Delete a vector by ID.
        
        Args:
            vector_id: ID of vector to delete
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def update(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a vector and/or its payload.
        
        Args:
            vector_id: ID of vector to update
            vector: New embedding vector
            payload: New metadata
            
        Returns:
            True if updated successfully
        """
        pass
    
    @abstractmethod
    def get(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a vector by ID.
        
        Args:
            vector_id: ID of vector to retrieve
            
        Returns:
            Vector data with payload or None if not found
        """
        pass
    
    @abstractmethod
    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all vectors matching filters.
        
        Args:
            filters: Optional metadata filters
            limit: Optional limit on results
            
        Returns:
            List of vectors with payloads
        """
        pass
    
    @abstractmethod
    def delete_collection(self) -> None:
        """Delete the current collection."""
        pass
    
    @abstractmethod
    def collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.
        
        Returns:
            Collection metadata and statistics
        """
        pass
