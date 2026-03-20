"""Configuration for embedding models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Base configuration for embedding models."""
    
    model: str = "text-embedding-3-small"
    dimension: int = 1536
    api_key: Optional[str] = None
    batch_size: int = 32
    
    # Performance settings
    max_retries: int = 3
    timeout: int = 30


@dataclass
class OpenAIEmbeddingConfig(EmbeddingConfig):
    """Configuration for OpenAI embedding models."""
    
    model: str = "text-embedding-3-small"
    dimension: int = 1536
    encoding_format: str = "float"


@dataclass
class FastEmbedConfig(EmbeddingConfig):
    """Configuration for FastEmbed embedding models."""
    
    model: str = "BAAI/bge-small-en-v1.5"
    dimension: int = 384
    cache_dir: Optional[str] = None
    threads: Optional[int] = None
    local_files_only: bool = False


@dataclass
class HuggingFaceEmbeddingConfig(EmbeddingConfig):
    """Configuration for HuggingFace embedding models."""
    
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    huggingface_base_url: Optional[str] = None
    cache_dir: Optional[str] = None
    local_files_only: bool = False
    model_kwargs: dict = None
    
    def __post_init__(self):
        if self.model_kwargs is None:
            self.model_kwargs = {}
