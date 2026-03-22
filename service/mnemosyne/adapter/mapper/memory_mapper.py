from typing import Dict, Any
from mnemosyne.adapter.dto.memory_dto import Memory, MemoryStatus, MemoryPriority, MemoryLayer, MemoryTag

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
                "tags": [tag.dict() for tag in memory.tags],
                "layer": memory.layer.value if memory.layer else None,
                "user_id": user_id
            }
        }

    def from_mnemosyne(self, mnem_mem: dict) -> Memory:
        """Convert mnemosyne memory to frontend Memory DTO."""
        metadata = mnem_mem.get("metadata", {})
        tags = [
            MemoryTag(id=t.get("id", ""), name=t.get("name", ""), color=t.get("color"))
            for t in metadata.get("tags", [])
        ]
        return Memory(
            id=mnem_mem.get("memory_id", mnem_mem.get("id", "")),
            title=metadata.get("title", mnem_mem.get("content", "")[:100]),
            content=mnem_mem.get("content", ""),
            status=MemoryStatus(metadata.get("status", "active")),
            priority=MemoryPriority(metadata.get("priority", "medium")),
            importance=metadata.get("importance", 3),
            tags=tags,
            layer=MemoryLayer(metadata.get("layer")) if metadata.get("layer") else None,
            createdAt=mnem_mem.get("created_at", mnem_mem.get("createdAt")),
            updatedAt=mnem_mem.get("updated_at", mnem_mem.get("updatedAt"))
        )

    def to_mnemosyne_search_result(self, memory: Memory, score: float = 0.0) -> dict:
        """Convert search result with score."""
        result = self.to_mnemosyne(memory)
        result["score"] = score
        return result