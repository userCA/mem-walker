"""Configuration for vector stores."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VectorStoreConfig:
    """Base configuration for vector stores."""
    
    collection_name: str = "mnemosyne_memories"
    vector_size: int = 1536
    distance_metric: str = "cosine"
    
    # Performance settings
    batch_size: int = 100
    index_type: str = "HNSW"


@dataclass
class MilvusConfig(VectorStoreConfig):
    """Configuration for Milvus vector store."""
    
    host: str = "localhost"
    port: int = 19530
    user: Optional[str] = None
    password: Optional[str] = None
    
    # HNSW index parameters
    index_params: dict = None
    
    def __post_init__(self):
        if self.index_params is None:
            self.index_params = {
                "M": 16,  # Max connections per layer
                "efConstruction": 200,  # Build time ef
            }
        
    @property
    def search_params(self) -> dict:
        """Parameters for search."""
        return {"ef": 200}  # Search time ef
