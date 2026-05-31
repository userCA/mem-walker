from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BackendProvider(str, Enum):
    MILVUS = "milvus"
    SQLITE = "sqlite"
    CHROMA = "chroma"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"

class BackendStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"

class BackendHealth(BaseModel):
    """Health status of a backend connection."""
    status: BackendStatus = BackendStatus.DISCONNECTED
    latency: Optional[float] = None
    lastChecked: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None

class CollectionStats(BaseModel):
    """Statistics for a collection."""
    name: str
    memoryCount: int = 0
    vectorDimension: int = 768
    indexType: str = "HNSW"
    createdAt: datetime = Field(default_factory=datetime.now)

class StorageMetrics(BaseModel):
    """Storage metrics for a backend."""
    totalMemory: int = 0
    usedMemory: int = 0
    vectorCount: int = 0
    indexSize: int = 0
    diskUsage: int = 0
    connectionPoolSize: int = 10
    activeConnections: int = 0

class BackendConnection(BaseModel):
    provider: BackendProvider
    status: BackendStatus = BackendStatus.DISCONNECTED
    host: str = "localhost"
    port: int = 19530
    database: str = "default"
    health: BackendHealth = Field(default_factory=BackendHealth)
    metrics: Optional[StorageMetrics] = None
    collections: List[CollectionStats] = Field(default_factory=list)

class BackendConfig(BaseModel):
    provider: BackendProvider
    host: str = "localhost"
    port: int = 19530
    database: str = "default"
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    timeout: int = 30
    vectorDimension: int = 768
    batchSize: int = 100

class BackendTestResult(BaseModel):
    success: bool
    latency: Optional[float] = None
    error: Optional[str] = None
    collections: List[str] = Field(default_factory=list)