from fastapi import APIRouter, Depends, Query
from typing import Optional
from ..dto.common import ApiResponse, PaginatedResponse
from ..dto.memory_dto import Memory, CreateMemoryRequest, UpdateMemoryRequest, MemoryStats
from ..service.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])

# Global service reference - populated by main.py lifespan
_memory_service_ref: MemoryService = None

def set_memory_service_ref(service: MemoryService):
    global _memory_service_ref
    _memory_service_ref = service

def get_memory_service() -> MemoryService:
    return _memory_service_ref

@router.get("/", response_model=ApiResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MemoryService = Depends(get_memory_service)
):
    items, total = await service.list("default_user", page, page_size)
    return ApiResponse(success=True, data=PaginatedResponse(
        items=[m.model_dump() for m in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    ).model_dump())

@router.get("/stats", response_model=ApiResponse)
async def get_stats(service: MemoryService = Depends(get_memory_service)):
    stats = await service.get_stats("default_user")
    return ApiResponse(success=True, data=stats.model_dump())

@router.get("/search", response_model=ApiResponse)
async def search_memories(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, le=50),
    service: MemoryService = Depends(get_memory_service)
):
    results = await service.search(q, "default_user", limit)
    return ApiResponse(success=True, data=[r.model_dump() for r in results])

@router.get("/{memory_id}", response_model=ApiResponse)
async def get_memory(memory_id: str, service: MemoryService = Depends(get_memory_service)):
    memory = await service.get(memory_id)
    return ApiResponse(success=True, data=memory.model_dump())

@router.post("/", response_model=ApiResponse)
async def create_memory(
    request: CreateMemoryRequest,
    service: MemoryService = Depends(get_memory_service)
):
    dto = Memory(
        id="",  # Will be generated
        title=request.title,
        content=request.content,
        priority=request.priority,
        importance=request.importance,
        tags=[],
        layer=request.layer
    )
    created = await service.create(dto, "default_user")
    return ApiResponse(success=True, data=created.model_dump())

@router.patch("/{memory_id}", response_model=ApiResponse)
async def update_memory(
    memory_id: str,
    request: UpdateMemoryRequest,
    service: MemoryService = Depends(get_memory_service)
):
    updates = request.model_dump(exclude_unset=True)
    updated = await service.update(memory_id, updates)
    return ApiResponse(success=True, data=updated.model_dump())

@router.delete("/{memory_id}", response_model=ApiResponse)
async def delete_memory(memory_id: str, service: MemoryService = Depends(get_memory_service)):
    await service.delete(memory_id)
    return ApiResponse(success=True, data={"message": "Memory deleted"})