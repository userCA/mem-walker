from typing import List, Optional
from mnemosyne import Memory
from ..mapper.memory_mapper import MemoryMapper
from ..dto.memory_dto import Memory as MemoryDTO, MemoryStats
from ..exception.adapters import NotFoundError

class MemoryService:
    """Service layer for memory operations."""

    def __init__(self, memory: Memory):
        self._memory = memory
        self._mapper = MemoryMapper()

    async def search(self, query: str, user_id: str, limit: int = 10) -> List[MemoryDTO]:
        results = self._memory.search(query, user_id=user_id, limit=limit)
        # Boost confidence for accessed memories
        for r in results:
            memory_id = r.get("id")
            if memory_id:
                try:
                    self._memory.default_context.boost_confidence(memory_id, boost=0.01)
                except Exception:
                    pass
        return [self._mapper.from_mnemosyne(r) for r in results]

    async def get(self, memory_id: str) -> MemoryDTO:
        result = self._memory.get(memory_id)
        if not result:
            raise NotFoundError("Memory", memory_id)
        return self._mapper.from_mnemosyne(result)

    async def create(self, dto: MemoryDTO, user_id: str = "default_user") -> MemoryDTO:
        mnem_mem = self._mapper.to_mnemosyne(dto, user_id)
        memory_id = self._memory.add(
            messages=mnem_mem["content"],
            user_id=user_id,
            metadata=mnem_mem["metadata"],
            infer=True  # 启用 LLM 提取事实
        )
        return await self.get(memory_id)

    async def create_episodic_memory(self, content: str, user_id: str, metadata: dict) -> str:
        """Store a chat message as episodic memory."""
        return self._memory.add(
            messages=content,
            user_id=user_id,
            metadata={**metadata, "memory_type": "episodic"}
        )

    def search_sync(self, query: str, user_id: str, limit: int = 10) -> List[dict]:
        """Synchronous search for memories (used by ChatService for context building)."""
        return self._memory.search(query, user_id=user_id, limit=limit)

    async def update(self, memory_id: str, updates: dict) -> MemoryDTO:
        if updates.get("content"):
            self._memory.update(memory_id, updates["content"])
        return await self.get(memory_id)

    async def delete(self, memory_id: str) -> bool:
        return self._memory.delete(memory_id)

    async def list(self, user_id: str, page: int = 1, page_size: int = 20) -> tuple[List[MemoryDTO], int]:
        all_memories = self._memory.get_all(user_id)
        total = len(all_memories)
        start = (page - 1) * page_size
        end = start + page_size
        items = [self._mapper.from_mnemosyne(m) for m in all_memories[start:end]]
        return items, total

    async def get_stats(self, user_id: str) -> MemoryStats:
        all_memories = self._memory.get_all(user_id)
        total = len(all_memories)
        by_status = {}
        by_priority = {}
        by_layer = {}
        total_importance = 0
        total_confidence = 0.0
        by_confidence_range = {"high": 0, "medium": 0, "low": 0}

        for m in all_memories:
            metadata = m.get("metadata", {})
            status = metadata.get("status", "active")
            priority = metadata.get("priority", "medium")
            layer = metadata.get("layer", "semantic")
            confidence = metadata.get("confidence", 0.8)

            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_layer[layer] = by_layer.get(layer, 0) + 1
            total_importance += metadata.get("importance", 3)
            total_confidence += confidence

            if confidence >= 0.7:
                by_confidence_range["high"] += 1
            elif confidence >= 0.3:
                by_confidence_range["medium"] += 1
            else:
                by_confidence_range["low"] += 1

        return MemoryStats(
            total=total,
            byStatus=by_status,
            byPriority=by_priority,
            byLayer=by_layer,
            averageImportance=total_importance / total if total > 0 else 0.0,
            averageConfidence=total_confidence / total if total > 0 else 0.0,
            byConfidence=by_confidence_range
        )

    async def apply_decay(self, user_id: str) -> dict:
        """Apply confidence decay to all memories for a user."""
        return self._memory.default_context.apply_decay(user_id)

    async def cleanup_forgotten(self, user_id: str, dry_run: bool = False) -> dict:
        """Clean up long-forgotten memories."""
        return self._memory.default_context.cleanup_forgotten(user_id, dry_run)

    async def boost_confidence(self, memory_id: str, boost: float = 0.05) -> bool:
        """Boost confidence when memory is accessed."""
        return self._memory.default_context.boost_confidence(memory_id, boost)

    async def get_tags(self, user_id: str) -> List[dict]:
        """Get all unique tags with their counts."""
        all_memories = self._memory.get_all(user_id)
        tag_counts: dict[str, dict] = {}

        for m in all_memories:
            metadata = m.get("metadata", {})
            for tag in metadata.get("tags", []):
                tag_name = tag.get("name", "unknown")
                if tag_name not in tag_counts:
                    tag_counts[tag_name] = {
                        "id": tag.get("id", tag_name),
                        "name": tag_name,
                        "color": tag.get("color"),
                        "count": 0
                    }
                tag_counts[tag_name]["count"] += 1

        return list(tag_counts.values())

    async def get_layers(self, user_id: str) -> List[dict]:
        """Get all layers with their counts and percentages."""
        all_memories = self._memory.get_all(user_id)
        total = len(all_memories)
        layer_counts: dict[str, int] = {}

        for m in all_memories:
            metadata = m.get("metadata", {})
            layer = metadata.get("layer", "semantic")
            layer_counts[layer] = layer_counts.get(layer, 0) + 1

        return [
            {
                "layer": layer,
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0
            }
            for layer, count in layer_counts.items()
        ]