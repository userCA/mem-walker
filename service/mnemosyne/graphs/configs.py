"""Configuration for graph stores."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class GraphStoreConfig:
    """Base configuration for graph stores."""

    # Performance settings (common across all stores)
    batch_size: int = 100
    max_depth: int = 3


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j graph store."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: Optional[str] = None
    database: str = "neo4j"

    # Connection pool settings
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60

    # Performance settings
    batch_size: int = 100
    max_depth: int = 3


@dataclass
class DuckDBConfig:
    """Configuration for DuckDB graph store."""

    db_path: str = ":memory:"  # Use ":memory:" for RAM-only, or file path
    read_only: bool = False
    config: Optional[Dict[str, Any]] = None  # DuckDB configuration options

    # Performance settings
    batch_size: int = 100
    max_depth: int = 3
