import pytest
from datetime import datetime
from mnemosyne.adapter.dto.chat_dto import ChatSession, ChatMessage, ChatRole

def test_chat_message():
    msg = ChatMessage(
        id="msg-123",
        role=ChatRole.USER,
        content="Hello"
    )
    assert msg.id == "msg-123"
    assert msg.role == ChatRole.USER
    assert msg.content == "Hello"

def test_chat_session():
    session = ChatSession(
        id="sess-123",
        title="Test Session",
        messages=[],
        memoryCount=5,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    assert session.id == "sess-123"
    assert session.title == "Test Session"
    assert session.memoryCount == 5
    assert session.isPinned is False