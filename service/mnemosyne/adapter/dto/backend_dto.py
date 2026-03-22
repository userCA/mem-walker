from pydantic import BaseModel
from typing import Optional
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

class BackendConnection(BaseModel):
    provider: BackendProvider
    status: BackendStatus = BackendStatus.DISCONNECTED
    host: str = "localhost"
    port: int = 19530
    database: str = "default"

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