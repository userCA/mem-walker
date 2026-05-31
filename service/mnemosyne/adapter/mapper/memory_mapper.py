from typing import Dict, Any
from datetime import datetime
from mnemosyne.adapter.dto.memory_dto import (
    Memory, MemoryStatus, MemoryPriority, MemoryLayer, MemoryTag,
    MemoryAccess, MemoryReference
)

class MemoryMapper:
    """Maps between Frontend Memory DTO and mnemosyne memory format."""

    def to_mnemosyne(self, memory: Memory, user_id: str = "default_user") -> dict:
        """Convert frontend Memory DTO to mnemosyne memory format."""
        return {
            "content": memory.content,
            "metadata": {
                "title": memory.title,
                "status": memory.status.value,
                "priority": memory.priority.value,
                "importance": memory.importance,
                "confidence": memory.confidence,
                "tags": [tag.model_dump() for tag in memory.tags],
                "layer": memory.layer.value if memory.layer else None,
                "user_id": user_id
            }
        }

    def _parse_datetime(self, value: Any) -> datetime:
        """Parse datetime from various formats."""
        if value is None:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            # Try parsing ISO format
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                pass
            # Try parsing as timestamp
            try:
                return datetime.fromtimestamp(float(value))
            except ValueError:
                pass
        return datetime.now()

    def from_mnemosyne(self, mnem_mem: dict) -> Memory:
        """Convert mnemosyne memory to frontend Memory DTO."""
        metadata = mnem_mem.get("metadata", {})
        tags = [
            MemoryTag(id=t.get("id", ""), name=t.get("name", ""), color=t.get("color"))
            for t in metadata.get("tags", [])
        ]

        # Parse created_at and updated_at
        created_at = self._parse_datetime(mnem_mem.get("created_at"))
        # Preserve temporal semantics: if updated_at is missing, keep created_at.
        updated_raw = mnem_mem.get("updated_at")
        updated_at = self._parse_datetime(updated_raw) if updated_raw is not None else created_at

        # Build access object - core doesn't track access stats, so we use defaults
        access = MemoryAccess(
            lastAccessedAt=updated_at,
            accessCount=0,
            lastModifiedAt=updated_at
        )

        return Memory(
            id=mnem_mem.get("memory_id", mnem_mem.get("id", "")),
            title=metadata.get("title", mnem_mem.get("content", "")[:100]),
            content=mnem_mem.get("content", ""),
            status=MemoryStatus(metadata.get("status", "active")),
            priority=MemoryPriority(metadata.get("priority", "medium")),
            importance=metadata.get("importance", 3),
            confidence=metadata.get("confidence", 0.8),
            tags=tags,
            layer=MemoryLayer(metadata.get("layer")) if metadata.get("layer") else None,
            access=access,
            references=[],
            createdAt=created_at,
            updatedAt=updated_at
        )

    def to_mnemosyne_search_result(self, memory: Memory, score: float = 0.0) -> dict:
        """Convert search result with score."""
        result = self.to_mnemosyne(memory)
        result["score"] = score
        return result