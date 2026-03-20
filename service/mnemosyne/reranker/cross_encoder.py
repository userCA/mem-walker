"""Cross-Encoder reranker implementation."""

import os
from typing import Any, Dict, List, Optional

from sentence_transformers import CrossEncoder

from ..utils import get_logger
from .base import RerankerBase
from .configs import RerankerConfig

logger = get_logger(__name__)


class CrossEncoderReranker(RerankerBase):
    """
    Cross-Encoder reranker implementation.
    
    Uses BERT-based Cross-Encoders for high-precision reranking.
    Recommended models:
    - BAAI/bge-reranker-base (Good balance)
    - cross-encoder/ms-marco-MiniLM-L-6-v2 (Fastest)
    """
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        """
        Initialize Cross-Encoder reranker.
        
        Args:
            config: Configuration for CrossEncoder
        """
        if config is None:
            config = RerankerConfig()
        
        self.config = config
        
        # Handle offline mode and cache directory
        hf_home = os.getenv("HF_HOME")
        cache_dir = (
            os.getenv("HUGGINGFACE_HUB_CACHE")
            or (os.path.join(hf_home, "hub") if hf_home else None)
        )
        
        logger.info(f"Initializing CrossEncoder with model: {config.model_name}")
        logger.info(f"Using cache dir: {cache_dir}")
        
        try:
            # Initialize model
            # Note: sentence-transformers handles HF_HUB_OFFLINE env var automatically
            self.model = CrossEncoder(
                config.model_name,
                device=config.device,
                model_kwargs={"cache_dir": cache_dir} if cache_dir else None,
                tokenizer_kwargs={"cache_dir": cache_dir} if cache_dir else None
            )
            logger.info("CrossEncoder initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CrossEncoder: {e}")
            raise e
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using Cross-Encoder.
        
        Args:
            query: Search query
            candidates: List of candidate results
            top_k: Number of top results to return
            
        Returns:
            Reranked candidates with updated scores
        """
        if not candidates:
            return []
        
        # Prepare pairs for scoring: [[query, doc1], [query, doc2], ...]
        pairs = [
            [query, candidate.get("content", "")]
            for candidate in candidates
        ]
        
        # Get scores
        scores = self.model.predict(
            pairs,
            batch_size=self.config.batch_size,
            show_progress_bar=False
        )
        
        # Update scores
        for i, candidate in enumerate(candidates):
            # Cross-Encoder scores are usually logits, not bounded 0-1
            # But for ranking, relative order matters
            candidate["score"] = float(scores[i])
            candidate["cross_encoder_score"] = float(scores[i])
        
        # Sort by score
        reranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        
        logger.debug(f"Reranked {len(candidates)} candidates, returning top {top_k}")
        
        return reranked[:top_k]
    
    def score(
        self,
        query: str,
        document: str
    ) -> float:
        """
        Calculate Cross-Encoder score for a single document.
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Relevance score
        """
        score = self.model.predict([query, document])
        return float(score)
