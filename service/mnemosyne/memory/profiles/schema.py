from enum import Enum

class MemoryType(str, Enum):
    """Memory classification (Dimension 1)"""
    DIALOGUE = "dialogue"    # Chat history
    PREFERENCE = "preference"# User preferences (likes/dislikes)
    BEHAVIOR = "behavior"    # Behavioral data (clicks, actions)
    KNOWLEDGE = "knowledge"  # Knowledge extracted from interaction

class TimeLayer(str, Enum):
    """Time-based layering (Dimension 2)"""
    SHORT = "short"  # < 7 days (Hot)
    MID = "mid"      # 7-30 days (Warm)
    LONG = "long"    # > 30 days (Cold)

class Importance(str, Enum):
    """Importance level (Dimension 3)"""
    CORE = "core"    # Core traits/facts
    NORMAL = "normal"# Standard memories
    TEMP = "temp"    # Temporary/transient

# Field Names for Milvus Schema
FIELD_ID = "memory_id"
FIELD_USER_ID = "user_id"
FIELD_AGENT_ID = "agent_id"
FIELD_TYPE = "memory_type"
FIELD_TIME_LAYER = "time_layer"
FIELD_IMPORTANCE = "importance"
FIELD_CONTENT = "content"
FIELD_VECTOR = "content_vector"
FIELD_TIMESTAMP = "timestamp"
