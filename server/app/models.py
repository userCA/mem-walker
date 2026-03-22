from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# Enums
class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FROZEN = "frozen"
    DELETED = "deleted"


class MemoryPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MemoryLayer(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    WORKING = "working"


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


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Memory Models
class MemoryTag(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    count: Optional[int] = None


class MemoryAccess(BaseModel):
    lastAccessedAt: datetime = Field(default_factory=datetime.now)
    accessCount: int = 0
    lastModifiedAt: datetime = Field(default_factory=datetime.now)


class MemoryReference(BaseModel):
    id: str
    title: str
    snippet: Optional[str] = None
    similarity: Optional[float] = None


class Memory(BaseModel):
    id: str
    title: str
    content: str
    status: MemoryStatus = MemoryStatus.ACTIVE
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    tags: list[MemoryTag] = []
    layer: Optional[MemoryLayer] = None
    access: MemoryAccess = Field(default_factory=MemoryAccess)
    references: list[MemoryReference] = []
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)


class MemoryStats(BaseModel):
    total: int = 0
    byStatus: dict[MemoryStatus, int] = {}
    byPriority: dict[MemoryPriority, int] = {}
    byLayer: dict[str, int] = {}
    averageImportance: float = 0.0


class MemoryFilter(BaseModel):
    status: Optional[list[MemoryStatus]] = None
    priority: Optional[list[MemoryPriority]] = None
    importance: Optional[list[int]] = None
    tags: Optional[list[str]] = None
    layer: Optional[list[MemoryLayer]] = None
    search: Optional[str] = None


class MemoryBatchAction(BaseModel):
    type: str
    ids: list[str]
    payload: Optional[dict] = None


# Backend Models
class BackendHealth(BaseModel):
    status: BackendStatus = BackendStatus.DISCONNECTED
    latency: Optional[float] = None
    lastChecked: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class StorageMetrics(BaseModel):
    totalMemory: int = 0
    usedMemory: int = 0
    vectorCount: int = 0
    indexSize: int = 0
    diskUsage: int = 0
    connectionPoolSize: int = 10
    activeConnections: int = 0


class CollectionStats(BaseModel):
    name: str
    memoryCount: int = 0
    vectorDimension: int = 0
    indexType: str = "HNSW"
    createdAt: datetime = Field(default_factory=datetime.now)


class BackendConnection(BaseModel):
    provider: BackendProvider
    status: BackendStatus = BackendStatus.DISCONNECTED
    host: str = "localhost"
    port: int = 19530
    database: str = "default"
    health: BackendHealth = Field(default_factory=BackendHealth)
    metrics: Optional[StorageMetrics] = None
    collections: list[CollectionStats] = []


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
    success: bool = False
    latency: Optional[float] = None
    error: Optional[str] = None
    collections: list[str] = []


# Chat Models
class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    status: str = "sent"
    memoryReferences: list[MemoryReference] = []
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = None


class ChatSession(BaseModel):
    id: str
    title: str
    messages: list[ChatMessage] = []
    memoryCount: int = 0
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    isPinned: bool = False
    isExpanded: bool = True


class ChatConfig(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    maxTokens: int = 2000
    topP: float = 1.0
    topK: int = 40
    repeatPenalty: float = 1.1
    includeMemories: bool = True
    memoryThreshold: float = 0.7
    systemPrompt: Optional[str] = None


# API Response Models
class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[dict] = None


class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    pageSize: int = 20
    hasMore: bool = False
