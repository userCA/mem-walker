from fastapi import APIRouter, HTTPException
import time
from datetime import datetime

from ..models import (
    BackendConnection, BackendConfig, BackendTestResult,
    BackendProvider, BackendStatus, BackendHealth, StorageMetrics,
    ApiResponse
)
from ..database import db

router = APIRouter(prefix="/backends", tags=["backends"])


@router.get("/", response_model=ApiResponse)
async def list_backends():
    """List all backend connections"""
    backends = list(db.backends.values())
    return ApiResponse(success=True, data=[b.model_dump() for b in backends])


@router.get("/{provider}", response_model=ApiResponse)
async def get_backend(provider: BackendProvider):
    """Get a specific backend connection"""
    backend = db.backends.get(provider)
    if not backend:
        raise HTTPException(status_code=404, detail="Backend not found")

    return ApiResponse(success=True, data=backend.model_dump())


@router.post("/connect", response_model=ApiResponse)
async def connect_backend(config: BackendConfig):
    """Connect to a backend"""
    # Simulate connection
    start_time = time.time()

    # Check if already connected
    if config.provider in db.backends:
        backend = db.backends[config.provider]
        if backend.status == BackendStatus.CONNECTED:
            return ApiResponse(success=True, data=backend.model_dump())

    # Simulate connection delay
    time.sleep(0.5)

    latency = (time.time() - start_time) * 1000

    backend = BackendConnection(
        provider=config.provider,
        status=BackendStatus.CONNECTED,
        host=config.host,
        port=config.port,
        database=config.database,
        health=BackendHealth(
            status=BackendStatus.CONNECTED,
            latency=latency,
            lastChecked=datetime.now()
        ),
        metrics=StorageMetrics(
            totalMemory=10 * 1024 * 1024 * 1024,
            usedMemory=2 * 1024 * 1024 * 1024,
            vectorCount=0,
            diskUsage=50 * 1024 * 1024 * 1024
        ),
        collections=[]
    )

    db.backends[config.provider] = backend

    return ApiResponse(success=True, data=backend.model_dump())


@router.post("/{provider}/disconnect", response_model=ApiResponse)
async def disconnect_backend(provider: BackendProvider):
    """Disconnect from a backend"""
    if provider not in db.backends:
        raise HTTPException(status_code=404, detail="Backend not found")

    db.backends[provider].status = BackendStatus.DISCONNECTED
    db.backends[provider].health.status = BackendStatus.DISCONNECTED

    return ApiResponse(success=True, data={"message": "Disconnected"})


@router.post("/test", response_model=ApiResponse)
async def test_connection(config: BackendConfig):
    """Test backend connection"""
    start_time = time.time()

    # Simulate connection test
    time.sleep(0.3)

    latency = (time.time() - start_time) * 1000

    # For demo, simulate success for all providers
    result = BackendTestResult(
        success=True,
        latency=latency,
        collections=["test_collection"]
    )

    return ApiResponse(success=True, data=result.model_dump())


@router.patch("/{provider}", response_model=ApiResponse)
async def update_backend_config(provider: BackendProvider, config: dict):
    """Update backend configuration"""
    if provider not in db.backends:
        raise HTTPException(status_code=404, detail="Backend not found")

    backend = db.backends[provider]

    if "host" in config:
        backend.host = config["host"]
    if "port" in config:
        backend.port = config["port"]
    if "database" in config:
        backend.database = config["database"]

    backend.health.lastChecked = datetime.now()

    return ApiResponse(success=True, data=backend.model_dump())


@router.get("/{provider}/metrics", response_model=ApiResponse)
async def get_metrics(provider: BackendProvider):
    """Get backend storage metrics"""
    if provider not in db.backends:
        raise HTTPException(status_code=404, detail="Backend not found")

    backend = db.backends[provider]
    if not backend.metrics:
        raise HTTPException(status_code=404, detail="Metrics not available")

    return ApiResponse(success=True, data=backend.metrics.model_dump())


@router.get("/{provider}/collections", response_model=ApiResponse)
async def get_collections(provider: BackendProvider):
    """Get backend collections"""
    if provider not in db.backends:
        raise HTTPException(status_code=404, detail="Backend not found")

    backend = db.backends[provider]
    return ApiResponse(success=True, data=[c.model_dump() for c in backend.collections])


@router.post("/{provider}/collections", response_model=ApiResponse)
async def create_collection(provider: BackendProvider, name: str, dimension: int = 768):
    """Create a new collection"""
    if provider not in db.backends:
        raise HTTPException(status_code=404, detail="Backend not found")

    from ..models import CollectionStats

    collection = CollectionStats(
        name=name,
        memoryCount=0,
        vectorDimension=dimension,
        createdAt=datetime.now()
    )

    db.backends[provider].collections.append(collection)

    return ApiResponse(success=True, data=collection.model_dump())


@router.delete("/{provider}/collections/{name}", response_model=ApiResponse)
async def delete_collection(provider: BackendProvider, name: str):
    """Delete a collection"""
    if provider not in db.backends:
        raise HTTPException(status_code=404, detail="Backend not found")

    backend = db.backends[provider]
    backend.collections = [c for c in backend.collections if c.name != name]

    return ApiResponse(success=True, data={"message": "Collection deleted"})
