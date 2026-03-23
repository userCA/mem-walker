import pytest
from starlette.testclient import TestClient
import sys
sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')
from mnemosyne.adapter.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_create_session(client):
    response = client.post("/api/v1/chat/sessions", json={"title": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]

def test_list_sessions(client):
    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]

def test_get_chat_config(client):
    response = client.get("/api/v1/chat/config")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_get_chat_presets(client):
    response = client.get("/api/v1/chat/presets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3