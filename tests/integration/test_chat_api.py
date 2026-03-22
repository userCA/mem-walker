import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')
from mnemosyne.adapter.main import app

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/v1/chat/sessions", json={"title": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]

@pytest.mark.asyncio
async def test_list_sessions(client):
    response = await client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]

@pytest.mark.asyncio
async def test_get_chat_config(client):
    response = await client.get("/api/v1/chat/config")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_get_chat_presets(client):
    response = await client.get("/api/v1/chat/presets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3