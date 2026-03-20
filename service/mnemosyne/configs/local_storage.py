"""Local storage configuration for SQLite-based vector store."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LocalStorageConfig:
    """Configuration for local SQLite-based storage.

    This allows switching from external services (Milvus/Neo4j) to
    zero-dependency local storage using SQLite + FAISS.
    """

    # Enable/disable local storage mode
    enabled: bool = False

    # Storage type selection
    storage_type: Literal["sqlite", "file", "hybrid"] = "sqlite"

    # SQLite database path
    db_path: str = "./data/memories.db"

    # FAISS index directory
    vector_index_dir: str = "./data/vectors"

    # Vector configuration
    vector_size: int = 1536
    use_faiss: bool = True
    index_type: Literal["flat", "ivf", "hnsw"] = "flat"

    # Performance tuning
    batch_size: int = 100
    flush_interval: float = 5.0  # seconds
    cache_size: int = 1000

    # WAL mode for better concurrency
    enable_wal_mode: bool = True

    class Config:
        env_prefix = "LOCAL_STORAGE_"


@dataclass
class StorageBackendConfig:
    """Configuration for storage backend selection.

    Controls which storage backend to use:
    - "milvus": Use Milvus (default, requires external service)
    - "local": Use SQLite + FAISS (zero dependency)
    - "auto": Automatically select based on availability
    """

    backend: Literal["milvus", "local", "auto"] = "auto"

    # Priority order when auto-selecting
    priority: list = field(default_factory=lambda: ["local", "milvus"])
