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

class MemoryAccess(BaseModel):
    """Access statistics for a memory."""
    lastAccessedAt: datetime = Field(default_factory=datetime.now)
    accessCount: int = 0
    lastModifiedAt: datetime = Field(default_factory=datetime.now)

class MemoryReference(BaseModel):
    """Reference to another memory or external resource."""
    id: str
    title: str
    snippet: Optional[str] = None
    similarity: Optional[float] = None

class ForgettingStrategy(str, Enum):
    """Strategy for memory forgetting/decay."""
    NONE = "none"                    # No forgetting
    TIME_DECAY = "time_decay"        # Pure time-based decay
    ACCESS_DECAY = "access_decay"    # Decay based on access patterns
    HYBRID = "hybrid"                # Combined time + access decay


class MemoryDecayConfig(BaseModel):
    """Configuration for memory confidence decay."""
    strategy: ForgettingStrategy = ForgettingStrategy.HYBRID
    half_life_days: float = 30.0     # Days for confidence to halve
    min_confidence: float = 0.1      # Minimum confidence threshold
    access_boost: float = 0.05       # Confidence boost per access
    decay_interval_hours: int = 24   # How often to run decay


class Memory(BaseModel):
    id: str
    title: str
    content: str
    status: MemoryStatus = MemoryStatus.ACTIVE
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    tags: list[MemoryTag] = Field(default_factory=list)
    layer: Optional[MemoryLayer] = None
    access: MemoryAccess = Field(default_factory=MemoryAccess)
    references: list[MemoryReference] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)

class MemoryStats(BaseModel):
    total: int = 0
    byStatus: dict[str, int] = {}
    byPriority: dict[str, int] = {}
    byLayer: dict[str, int] = {}
    averageImportance: float = 0.0
    averageConfidence: float = 0.0
    byConfidence: dict[str, int] = Field(default_factory=lambda: {"high": 0, "medium": 0, "low": 0})

class CreateMemoryRequest(BaseModel):
    title: str
    content: str
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    tags: list[str] = Field(default_factory=list)
    layer: Optional[MemoryLayer] = None

class UpdateMemoryRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[MemoryStatus] = None
    priority: Optional[MemoryPriority] = None
    importance: Optional[int] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tags: Optional[list[str]] = None