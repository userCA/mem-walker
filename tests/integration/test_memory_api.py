import pytest
from starlette.testclient import TestClient
import sys
sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')
from mnemosyne.adapter.main import app

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