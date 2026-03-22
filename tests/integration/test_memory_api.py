import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')
from mnemosyne.adapter.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_list_memories(client):
    response = await client.get("/api/v1/memories/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]

@pytest.mark.asyncio
async def test_get_memory_stats(client):
    response = await client.get("/api/v1/memories/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_search_memories(client):
    response = await client.get("/api/v1/memories/search", params={"q": "test", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True