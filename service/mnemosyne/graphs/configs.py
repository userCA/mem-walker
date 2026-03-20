"""Configuration for graph stores."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GraphStoreConfig:
    """Base configuration for graph stores."""
    
    # Performance settings
    batch_size: int = 100
    max_depth: int = 3


@dataclass
class Neo4jConfig(GraphStoreConfig):
    """Configuration for Neo4j graph store."""
    
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: Optional[str] = None
    database: str = "neo4j"
    
    # Connection pool settings
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60
