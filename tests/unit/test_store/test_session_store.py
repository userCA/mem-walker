import pytest
import tempfile
import os
from mnemosyne.adapter.store.session_store import SessionStore

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def store(temp_db):
    return SessionStore(temp_db)

@pytest.mark.asyncio
async def test_create_session(store):
    session = await store.create_session(
        title="Test Session",
        user_id="user_123"
    )
    assert session["title"] == "Test Session"
    assert session["user_id"] == "user_123"
    assert "id" in session

@pytest.mark.asyncio
async def test_get_session(store):
    created = await store.create_session(title="Test", user_id="user_123")
    fetched = await store.get_session(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]

@pytest.mark.asyncio
async def test_list_sessions(store):
    await store.create_session(title="S1", user_id="user_123")
    await store.create_session(title="S2", user_id="user_123")
    sessions = await store.list_sessions(user_id="user_123")
    assert len(sessions) == 2