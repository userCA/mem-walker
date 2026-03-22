from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import uuid
from datetime import datetime

from ..models import (
    Memory, MemoryStatus, MemoryPriority, MemoryTag, MemoryStats,
    MemoryFilter, MemoryBatchAction, ApiResponse, PaginatedResponse
)
from ..database import db

router = APIRouter(prefix="/memories", tags=["memories"])


def paginate(items: list, page: int = 1, page_size: int = 20) -> PaginatedResponse:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse(
        items=items[start:end],
        total=total,
        page=page,
        pageSize=page_size,
        hasMore=end < total
    )


@router.get("/", response_model=ApiResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("updatedAt:desc"),
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """List all memories with pagination and filtering"""
    items = list(db.memories.values())

    # Apply filters
    if status:
        statuses = [MemoryStatus(s) for s in status.split(",")]
        items = [m for m in items if m.status in statuses]

    if priority:
        priorities = [MemoryPriority(p) for p in priority.split(",")]
        items = [m for m in items if m.priority in priorities]

    if search:
        search = search.lower()
        items = [
            m for m in items
            if search in m.title.lower() or search in m.content.lower()
        ]

    # Apply sorting
    field, order = sort.split(":")
    items.sort(
        key=lambda m: getattr(m, field, m.updatedAt),
        reverse=(order == "desc")
    )

    return ApiResponse(success=True, data=paginate(items, page, page_size).model_dump())


@router.get("/stats", response_model=ApiResponse)
async def get_stats():
    """Get memory statistics"""
    memories = list(db.memories.values())

    stats = MemoryStats(
        total=len(memories),
        byStatus={s: sum(1 for m in memories if m.status == s) for s in MemoryStatus},
        byPriority={p: sum(1 for m in memories if m.priority == p) for p in MemoryPriority},
        byLayer={l: sum(1 for m in memories if m.layer == l) for l in ["semantic", "episodic", "procedural", "working"]},
        averageImportance=sum(m.importance for m in memories) / len(memories) if memories else 0
    )

    return ApiResponse(success=True, data=stats.model_dump())


@router.get("/tags", response_model=ApiResponse)
async def get_tags():
    """Get all tags with counts"""
    tag_counts: dict[str, dict] = {}

    for memory in db.memories.values():
        for tag in memory.tags:
            if tag.id not in tag_counts:
                tag_counts[tag.id] = {"id": tag.id, "name": tag.name, "color": tag.color, "count": 0}
            tag_counts[tag.id]["count"] += 1

    return ApiResponse(success=True, data=list(tag_counts.values()))


@router.get("/layers", response_model=ApiResponse)
async def get_layers():
    """Get memory distribution across layers"""
    memories = list(db.memories.values())
    layer_counts: dict[str, int] = {
        "semantic": 0,
        "episodic": 0,
        "procedural": 0,
        "working": 0,
    }

    for memory in memories:
        if memory.layer:
            layer_counts[memory.layer] = layer_counts.get(memory.layer, 0) + 1

    total = len(memories) if memories else 1
    layers = [
        {"layer": layer, "count": count, "percentage": round(count / total * 100, 1)}
        for layer, count in layer_counts.items()
    ]

    return ApiResponse(success=True, data=layers)


@router.get("/search", response_model=ApiResponse)
async def search_memories(q: str = Query(...), limit: int = Query(10, le=50)):
    """Search memories by query"""
    q = q.lower()
    results = [
        m for m in db.memories.values()
        if q in m.title.lower() or q in m.content.lower()
    ][:limit]

    return ApiResponse(success=True, data=[m.model_dump() for m in results])


@router.get("/{memory_id}", response_model=ApiResponse)
async def get_memory(memory_id: str):
    """Get a specific memory by ID"""
    memory = db.memories.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Update access stats
    memory.access.lastAccessedAt = datetime.now()
    memory.access.accessCount += 1

    return ApiResponse(success=True, data=memory.model_dump())


@router.post("/", response_model=ApiResponse)
async def create_memory(memory: Memory):
    """Create a new memory"""
    memory.id = str(uuid.uuid4())
    memory.createdAt = datetime.now()
    memory.updatedAt = datetime.now()
    db.memories[memory.id] = memory

    return ApiResponse(success=True, data=memory.model_dump())


@router.patch("/{memory_id}", response_model=ApiResponse)
async def update_memory(memory_id: str, updates: dict):
    """Update a memory"""
    memory = db.memories.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    for key, value in updates.items():
        if hasattr(memory, key) and value is not None:
            setattr(memory, key, value)

    memory.updatedAt = datetime.now()

    return ApiResponse(success=True, data=memory.model_dump())


@router.delete("/{memory_id}", response_model=ApiResponse)
async def delete_memory(memory_id: str):
    """Delete a memory"""
    if memory_id not in db.memories:
        raise HTTPException(status_code=404, detail="Memory not found")

    del db.memories[memory_id]
    return ApiResponse(success=True, data={"message": "Memory deleted"})


@router.post("/batch", response_model=ApiResponse)
async def batch_action(action: MemoryBatchAction):
    """Execute batch action on memories"""
    if action.type == "delete":
        for memory_id in action.ids:
            if memory_id in db.memories:
                del db.memories[memory_id]
    elif action.type == "archive":
        for memory_id in action.ids:
            if memory_id in db.memories:
                db.memories[memory_id].status = MemoryStatus.ARCHIVED
    elif action.type == "freeze":
        for memory_id in action.ids:
            if memory_id in db.memories:
                db.memories[memory_id].status = MemoryStatus.FROZEN

    return ApiResponse(success=True, data={"affected": len(action.ids)})
