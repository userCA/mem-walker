"""Base abstract class for embedding models."""

from abc import ABC, abstractmethod
from typing import List, Literal, Optional, Union


class EmbeddingBase(ABC):
    """
    Abstract base class for embedding models.
    
    All embedding implementations should inherit from this class
    and implement the embed method.
    """
    
    @abstractmethod
    def embed(
        self, 
        text: Union[str, List[str]], 
        memory_action: Optional[Literal["add", "search", "update"]] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for the given text(s).
        
        Args:
            text: Single text string or list of text strings to embed
            memory_action: Optional action type for optimization
                - "add": Optimized for adding new memories
                - "search": Optimized for search queries
                - "update": Optimized for updating existing memories
                
        Returns:
            Single embedding vector or list of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per batch
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If batch embedding generation fails
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embedding vectors."""
        pass
