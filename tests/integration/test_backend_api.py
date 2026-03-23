import pytest
from starlette.testclient import TestClient
import sys
sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')
from mnemosyne.adapter.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_list_backends(client):
    response = client.get("/api/v1/backends/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_connect_backend(client):
    response = client.post("/api/v1/backends/connect", json={
        "provider": "milvus",
        "host": "localhost",
        "port": 19530,
        "database": "default"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True