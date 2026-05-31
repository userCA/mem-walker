import pytest
from starlette.testclient import TestClient
import sys
sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')
from mnemosyne.adapter.main import app
from mnemosyne.adapter.controller.memory_controller import get_memory_service
from mnemosyne.adapter.controller.backend_controller import get_backend_service

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_list_memories(client):
    response = client.get("/api/v1/memories/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]

def test_get_memory_stats(client):
    response = client.get("/api/v1/memories/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_search_memories(client):
    response = client.get("/api/v1/memories/search", params={"q": "test", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_get_memory_tags(client):
    response = client.get("/api/v1/memories/tags")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)

def test_get_memory_layers(client):
    response = client.get("/api/v1/memories/layers")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    # Each layer should have layer, count, percentage fields
    if len(data["data"]) > 0:
        layer = data["data"][0]
        assert "layer" in layer
        assert "count" in layer
        assert "percentage" in layer


def test_create_memory_passes_confidence(client):
    captured = {}

    class FakeMemoryService:
        async def create(self, dto, user_id):
            captured["confidence"] = dto.confidence
            return dto

    app.dependency_overrides[get_memory_service] = lambda: FakeMemoryService()
    try:
        response = client.post("/api/v1/memories/", json={
            "title": "t",
            "content": "c",
            "confidence": 0.42
        })
        assert response.status_code == 200
        assert captured["confidence"] == 0.42
    finally:
        app.dependency_overrides.pop(get_memory_service, None)


def test_export_returns_not_implemented(client):
    response = client.post("/api/v1/memories/export", params={"format": "json"})
    assert response.status_code == 501
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_IMPLEMENTED"


def test_import_returns_not_implemented(client):
    response = client.post("/api/v1/memories/import")
    assert response.status_code == 501
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_IMPLEMENTED"


def test_backend_collection_management_returns_not_implemented(client):
    class FakeBackendService:
        pass

    app.dependency_overrides[get_backend_service] = lambda: FakeBackendService()
    try:
        create_resp = client.post("/api/v1/backends/sqlite/collections", params={"name": "x", "dimension": 384})
        delete_resp = client.delete("/api/v1/backends/sqlite/collections/x")
        assert create_resp.status_code == 501
        assert delete_resp.status_code == 501
        assert create_resp.json()["error"]["code"] == "NOT_IMPLEMENTED"
        assert delete_resp.json()["error"]["code"] == "NOT_IMPLEMENTED"
    finally:
        app.dependency_overrides.pop(get_backend_service, None)