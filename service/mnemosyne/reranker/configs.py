"""Configuration for reranker models."""

from dataclasses import dataclass


@dataclass
class RerankerConfig:
    """Base configuration for reranker models."""
    
    # BM25 parameters
    k1: float = 1.5  # Term frequency saturation parameter
    b: float = 0.75  # Length normalization parameter
    
    # CrossEncoder parameters
    model_name: str = "BAAI/bge-reranker-base"
    device: str = "cpu"
    batch_size: int = 32
    
    # Performance settings
    top_k: int = 10
