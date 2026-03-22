from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

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

class MemoryTag(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    count: Optional[int] = None

class Memory(BaseModel):
    id: str
    title: str
    content: str
    status: MemoryStatus = MemoryStatus.ACTIVE
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    tags: list[MemoryTag] = Field(default_factory=list)
    layer: Optional[MemoryLayer] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)

class MemoryStats(BaseModel):
    total: int = 0
    byStatus: dict[str, int] = {}
    byPriority: dict[str, int] = {}
    byLayer: dict[str, int] = {}
    averageImportance: float = 0.0

class CreateMemoryRequest(BaseModel):
    title: str
    content: str
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    tags: list[str] = Field(default_factory=list)
    layer: Optional[MemoryLayer] = None

class UpdateMemoryRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[MemoryStatus] = None
    priority: Optional[MemoryPriority] = None
    importance: Optional[int] = None
    tags: Optional[list[str]] = None