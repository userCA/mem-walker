import uuid
from datetime import datetime
from typing import List, Optional
from ..store.session_store import SessionStore
from ..mapper.chat_mapper import ChatMapper
from ..dto.chat_dto import ChatSession, ChatMessage, ChatRole, SendMessageRequest
from ..llm.base import LLMProvider, LLMMessage
from ..exception.adapters import NotFoundError

class ChatService:
    """Service layer for chat operations."""

    def __init__(self, session_store: SessionStore, llm_provider: LLMProvider, memory_service=None):
        self._store = session_store
        self._mapper = ChatMapper()
        self._llm = llm_provider
        self._memory_service = memory_service  # For episodic memory storage

    async def create_session(self, title: str = "新对话", user_id: str = "default_user") -> ChatSession:
        session_data = await self._store.create_session(title=title, user_id=user_id)
        return ChatSession(
            id=session_data["id"],
            title=session_data["title"],
            messages=[],
            memoryCount=session_data["memory_count"],
            createdAt=session_data["created_at"],
            updatedAt=session_data["updated_at"],
            isPinned=session_data["is_pinned"],
            isExpanded=session_data["is_expanded"]
        )

    async def get_session(self, session_id: str) -> ChatSession:
        session_data = await self._store.get_session(session_id)
        if not session_data:
            raise NotFoundError("Session", session_id)
        return ChatSession(
            id=session_data["id"],
            title=session_data["title"],
            messages=[],
            memoryCount=session_data["memory_count"],
            createdAt=session_data["created_at"],
            updatedAt=session_data["updated_at"],
            isPinned=session_data["is_pinned"],
            isExpanded=session_data["is_expanded"]
        )

    async def list_sessions(self, user_id: str = "default_user") -> List[ChatSession]:
        sessions = await self._store.list_sessions(user_id)
        return [
            ChatSession(
                id=s["id"],
                title=s["title"],
                messages=[],
                memoryCount=s["memory_count"],
                createdAt=s["created_at"],
                updatedAt=s["updated_at"],
                isPinned=s["is_pinned"],
                isExpanded=s["is_expanded"]
            )
            for s in sessions
        ]

    async def send_message(
        self,
        session_id: str,
        content: str,
        config: Optional[dict] = None,
        user_id: str = "default_user"
    ) -> tuple[ChatMessage, ChatMessage]:
        session = await self.get_session(session_id)

        # Create user message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role=ChatRole.USER,
            content=content,
            createdAt=datetime.now()
        )

        # Store user message as episodic memory in mnemosyne
        if self._memory_service:
            await self._memory_service.create_episodic_memory(
                content=user_msg.content,
                user_id=user_id,
                metadata={
                    "session_id": session_id,
                    "role": "user",
                    "message_id": user_msg.id
                }
            )

        # Build context with relevant memories (from mnemosyne)
        context = self._build_memory_context(content, user_id)

        # Build prompt with context
        system_prompt = f"你是 Mnemosyne，一个智能记忆助手。\n{context}"
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=content)
        ]

        # Call LLM
        llm_config = config or {}
        assistant_content = await self._llm.chat(
            messages,
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("maxTokens", 2000)
        )

        # Create assistant message
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role=ChatRole.ASSISTANT,
            content=assistant_content,
            createdAt=datetime.now()
        )

        # Store assistant message as episodic memory in mnemosyne
        if self._memory_service:
            await self._memory_service.create_episodic_memory(
                content=assistant_msg.content,
                user_id=user_id,
                metadata={
                    "session_id": session_id,
                    "role": "assistant",
                    "message_id": assistant_msg.id
                }
            )

        # Update session memory count
        await self._store.increment_memory_count(session_id)

        return user_msg, assistant_msg

    def _build_memory_context(self, query: str, user_id: str) -> str:
        """Build memory context by retrieving relevant memories from mnemosyne."""
        if not self._memory_service:
            return "相关记忆：\n（暂无）"

        # Search for relevant memories
        memories = self._memory_service.search_sync(query, user_id, limit=5)
        if not memories:
            return "相关记忆：\n（暂无）"

        context_parts = ["相关记忆："]
        for i, mem in enumerate(memories, 1):
            context_parts.append(f"{i}. {mem.get('content', '')}")
        return "\n".join(context_parts)

    async def delete_session(self, session_id: str) -> bool:
        return await self._store.delete_session(session_id)