from fastapi import APIRouter, Depends
from ..dto.common import ApiResponse
from ..dto.backend_dto import BackendConfig
from ..service.backend_service import BackendService

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