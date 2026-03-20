"""BM25 reranker implementation."""

from typing import Any, Dict, List, Optional

from rank_bm25 import BM25Okapi

from ..utils import get_logger
from .base import RerankerBase
from .configs import RerankerConfig

logger = get_logger(__name__)


class BM25Reranker(RerankerBase):
    """
    BM25 reranker implementation.
    
    Uses BM25 algorithm for reranking search results based on term frequency.
    """
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        """
        Initialize BM25 reranker.
        
        Args:
            config: Configuration for BM25
        """
        if config is None:
            config = RerankerConfig()
        
        self.config = config
        self.bm25 = None
        
        logger.info("Initialized BM25 reranker")
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using BM25.
        
        Args:
            query: Search query
            candidates: List of candidate results
            top_k: Number of top results to return
            
        Returns:
            Reranked candidates with updated scores
        """
        if not candidates:
            return []
        
        # Extract content from candidates
        corpus = [
            candidate.get("content", "")
            for candidate in candidates
        ]
        
        # Tokenize corpus
        tokenized_corpus = [doc.split() for doc in corpus]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(
            tokenized_corpus,
            k1=self.config.k1,
            b=self.config.b
        )
        
        # Tokenize query
        tokenized_query = query.split()
        
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Combine with existing scores if available
        for i, candidate in enumerate(candidates):
            existing_score = candidate.get("score", 0.0)
            bm25_score = float(bm25_scores[i])
            
            # Weighted combination: 70% original score + 30% BM25 score
            # Normalize BM25 score to 0-1 range
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
            normalized_bm25 = bm25_score / max_bm25
            
            combined_score = 0.7 * existing_score + 0.3 * normalized_bm25
            candidate["score"] = combined_score
            candidate["bm25_score"] = bm25_score
        
        # Sort by combined score
        reranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        
        logger.debug(f"Reranked {len(candidates)} candidates, returning top {top_k}")
        
        return reranked[:top_k]
    
    def score(
        self,
        query: str,
        document: str
    ) -> float:
        """
        Calculate BM25 score for a single document.
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            BM25 relevance score
        """
        # Create a single-document corpus
        corpus = [document]
        tokenized_corpus = [doc.split() for doc in corpus]
        
        # Create BM25 index
        bm25 = BM25Okapi(
            tokenized_corpus,
            k1=self.config.k1,
            b=self.config.b
        )
        
        # Tokenize query
        tokenized_query = query.split()
        
        # Get score
        scores = bm25.get_scores(tokenized_query)
        
        return float(scores[0])
