"""Base abstract class for reranking models."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RerankerBase(ABC):
    """
    Abstract base class for reranking models.
    
    All reranker implementations should inherit from this class.
    """
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates based on relevance to query.
        
        Args:
            query: Search query
            candidates: List of candidate results to rerank
            top_k: Number of top results to return
            
        Returns:
            Reranked list of candidates with updated scores
        """
        pass
    
    @abstractmethod
    def score(
        self,
        query: str,
        document: str
    ) -> float:
        """
        Calculate relevance score between query and document.
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Relevance score (higher is more relevant)
        """
        pass
