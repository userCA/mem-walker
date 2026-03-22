from datetime import datetime
from typing import Optional
from mnemosyne.adapter.dto.chat_dto import ChatSession, ChatMessage, ChatRole

class ChatMapper:
    """Maps between Frontend DTOs and mnemosyne episodic memory format."""

    def session_to_episodic(self, session: ChatSession) -> dict:
        """Convert ChatSession to mnemosyne episodic memory format."""
        return {
            "content": session.title,
            "metadata": {
                "session_id": session.id,
                "title": session.title,
                "is_pinned": session.isPinned,
                "is_expanded": session.isExpanded,
                "memory_count": session.memoryCount,
                "created_at": session.createdAt.isoformat() if isinstance(session.createdAt, datetime) else session.createdAt,
                "updated_at": session.updatedAt.isoformat() if isinstance(session.updatedAt, datetime) else session.updatedAt,
                "user_id": "default_user"  # TODO: get from context
            }
        }

    def episodic_to_session(self, episodic: dict) -> ChatSession:
        """Convert mnemosyne episodic memory to ChatSession."""
        metadata = episodic.get("metadata", {})
        return ChatSession(
            id=metadata.get("session_id", ""),
            title=episodic.get("content", metadata.get("title", "")),
            messages=[],
            memoryCount=metadata.get("memory_count", 0),
            isPinned=metadata.get("is_pinned", False),
            isExpanded=metadata.get("is_expanded", True),
            createdAt=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updatedAt=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat()))
        )

    def message_to_episodic(self, message: ChatMessage, session_id: str) -> dict:
        """Convert ChatMessage to mnemosyne episodic memory format."""
        return {
            "content": message.content,
            "metadata": {
                "session_id": session_id,
                "role": message.role.value,
                "message_id": message.id,
                "created_at": message.createdAt.isoformat() if isinstance(message.createdAt, datetime) else message.createdAt
            }
        }

    def episodic_to_message(self, episodic: dict) -> ChatMessage:
        """Convert mnemosyne episodic memory to ChatMessage."""
        metadata = episodic.get("metadata", {})
        return ChatMessage(
            id=metadata.get("message_id", ""),
            role=ChatRole(metadata.get("role", "user")),
            content=episodic.get("content", ""),
            createdAt=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
        )