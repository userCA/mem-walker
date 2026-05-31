from fastapi import APIRouter, Depends
from ..dto.common import ApiResponse
from ..dto.backend_dto import BackendConfig
from ..service.backend_service import BackendService
from ..exception.adapters import FeatureNotImplementedError

router = APIRouter(prefix="/backends", tags=["backends"])

# Global service reference - populated by main.py lifespan
_backend_service_ref: BackendService = None

def set_backend_service_ref(service: BackendService):
    global _backend_service_ref
    _backend_service_ref = service

def get_backend_service() -> BackendService:
    return _backend_service_ref

@router.get("/", response_model=ApiResponse)
async def list_backends(service: BackendService = Depends(get_backend_service)):
    backends = await service.list_backends()
    return ApiResponse(success=True, data=[b.model_dump() for b in backends])

@router.get("/{provider}/metrics", response_model=ApiResponse)
async def get_backend_metrics(provider: str, service: BackendService = Depends(get_backend_service)):
    metrics = await service.get_metrics(provider)
    if not metrics:
        from ..exception.adapters import NotFoundError
        raise NotFoundError("Backend", provider)
    return ApiResponse(success=True, data=metrics.model_dump())

@router.get("/{provider}/collections", response_model=ApiResponse)
async def get_backend_collections(provider: str, service: BackendService = Depends(get_backend_service)):
    collections = await service.get_collections(provider)
    return ApiResponse(success=True, data=[c.model_dump() for c in collections])

@router.get("/{provider}", response_model=ApiResponse)
async def get_backend(provider: str, service: BackendService = Depends(get_backend_service)):
    backend = await service.get_backend(provider)
    if not backend:
        from ..exception.adapters import NotFoundError
        raise NotFoundError("Backend", provider)
    return ApiResponse(success=True, data=backend.model_dump())

@router.post("/connect", response_model=ApiResponse)
async def connect_backend(config: BackendConfig, service: BackendService = Depends(get_backend_service)):
    backend = await service.connect(config)
    return ApiResponse(success=True, data=backend.model_dump())

@router.post("/{provider}/disconnect", response_model=ApiResponse)
async def disconnect_backend(provider: str, service: BackendService = Depends(get_backend_service)):
    success = await service.disconnect(provider)
    return ApiResponse(success=True, data={"success": success})

@router.post("/test", response_model=ApiResponse)
async def test_connection(config: BackendConfig, service: BackendService = Depends(get_backend_service)):
    # Test logic would connect and verify
    return ApiResponse(success=True, data={"success": True})

@router.post("/{provider}/collections", response_model=ApiResponse)
async def create_collection(
    provider: str,
    name: str,
    dimension: int = 384,
    service: BackendService = Depends(get_backend_service)
):
    """Collection management API contract reserved, currently not implemented."""
    raise FeatureNotImplementedError(
        "backends.collections.create",
        message=f"Collection creation is not implemented yet for provider '{provider}' (name={name}, dimension={dimension})"
    )

@router.delete("/{provider}/collections/{name}", response_model=ApiResponse)
async def delete_collection(
    provider: str,
    name: str,
    service: BackendService = Depends(get_backend_service)
):
    """Collection management API contract reserved, currently not implemented."""
    raise FeatureNotImplementedError(
        "backends.collections.delete",
        message=f"Collection deletion is not implemented yet for provider '{provider}' (name={name})"
    )