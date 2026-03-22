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
async def test_list_backends(client):
    response = await client.get("/api/v1/backends/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_connect_backend(client):
    response = await client.post("/api/v1/backends/connect", json={
        "provider": "milvus",
        "host": "localhost",
        "port": 19530,
        "database": "default"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True