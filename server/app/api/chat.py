from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import uuid
from datetime import datetime
import httpx

from ..models import (
    ChatSession, ChatMessage, ChatRole, ChatConfig,
    ApiResponse, PaginatedResponse
)
from ..database import db
from ..config import get_settings

settings = get_settings()

router = APIRouter(prefix="/chat", tags=["chat"])


def paginate_sessions(items: list, page: int = 1, page_size: int = 20) -> PaginatedResponse:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse(
        items=items[start:end],
        total=total,
        page=page,
        pageSize=page_size,
        hasMore=end < total
    )


@router.get("/sessions", response_model=ApiResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all chat sessions"""
    sessions = list(db.chat_sessions.values())
    sessions.sort(key=lambda s: s.updatedAt, reverse=True)

    return ApiResponse(success=True, data=paginate_sessions(sessions, page, page_size).model_dump())


@router.get("/sessions/{session_id}", response_model=ApiResponse)
async def get_session(session_id: str):
    """Get a specific chat session"""
    session = db.chat_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ApiResponse(success=True, data=session.model_dump())


@router.post("/sessions", response_model=ApiResponse)
async def create_session(request: Optional[dict] = None):
    """Create a new chat session"""
    if request is None:
        request = {}

    session = ChatSession(
        id=str(uuid.uuid4()),
        title=request.get("title", "新对话"),
        messages=request.get("messages", []),
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    db.chat_sessions[session.id] = session

    return ApiResponse(success=True, data=session.model_dump())


@router.patch("/sessions/{session_id}", response_model=ApiResponse)
async def update_session(session_id: str, updates: dict):
    """Update a chat session"""
    session = db.chat_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    for key, value in updates.items():
        if hasattr(session, key) and value is not None:
            setattr(session, key, value)

    session.updatedAt = datetime.now()

    return ApiResponse(success=True, data=session.model_dump())


@router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def delete_session(session_id: str):
    """Delete a chat session"""
    if session_id not in db.chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del db.chat_sessions[session_id]
    return ApiResponse(success=True, data={"message": "Session deleted"})


@router.post("/sessions/{session_id}/messages", response_model=ApiResponse)
async def send_message(session_id: str, request: dict):
    """Send a message in a chat session"""
    session = db.chat_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = request.get("content", "")
    config = request.get("config")

    # Create user message
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=ChatRole.USER,
        content=content,
        createdAt=datetime.now()
    )
    session.messages.append(user_message)

    # Call DeepSeek API
    assistant_content = await call_deepseek_api(session.messages, config)

    # Create assistant message
    assistant_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=ChatRole.ASSISTANT,
        content=assistant_content,
        createdAt=datetime.now()
    )
    session.messages.append(assistant_message)

    session.updatedAt = datetime.now()
    session.memoryCount += 1

    return ApiResponse(success=True, data={
        "userMessage": user_message.model_dump(),
        "assistantMessage": assistant_message.model_dump()
    })


async def call_deepseek_api(messages: list[ChatMessage], config: Optional[dict] = None) -> str:
    """Call DeepSeek API to get assistant response"""
    if not settings.deepseek_api_key:
        return "DeepSeek API key is not configured. Please set DEEPSEEK_API_KEY in your .env file."

    # Convert messages to OpenAI format
    openai_messages = []
    for msg in messages:
        openai_messages.append({
            "role": msg.role.value,
            "content": msg.content
        })

    # Add system prompt for memory context
    system_prompt = """你是 Mnemosyne，一个智能记忆助手。你能帮助用户管理记忆、回答问题、进行对话。
请基于用户的记忆和上下文来回答问题，保持友好和帮助的态度。"""
    openai_messages.insert(0, {"role": "system", "content": system_prompt})

    # Prepare request
    temperature = config.get("temperature", 0.7) if config else 0.7
    max_tokens = config.get("maxTokens", 2000) if config else 2000

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.deepseek_model,
        "messages": openai_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if result.get("choices") and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "抱歉，我没有收到有效的回复。"
    except httpx.HTTPStatusError as e:
        return f"API 请求失败: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"调用 DeepSeek API 时发生错误: {str(e)}"


@router.get("/config", response_model=ApiResponse)
async def get_config():
    """Get chat configuration"""
    return ApiResponse(success=True, data=db.chat_config.model_dump())


@router.patch("/config", response_model=ApiResponse)
async def update_config(config: ChatConfig):
    """Update chat configuration"""
    for key, value in config.model_dump().items():
        if value is not None:
            setattr(db.chat_config, key, value)

    return ApiResponse(success=True, data=db.chat_config.model_dump())


@router.get("/presets", response_model=ApiResponse)
async def get_presets():
    """Get chat presets"""
    presets = [
        {
            "id": "balanced",
            "name": "平衡",
            "description": "平衡创造性 和准确性",
            "icon": "⚖️",
            "config": {"temperature": 0.7, "topP": 1.0, "repeatPenalty": 1.1}
        },
        {
            "id": "creative",
            "name": "创造性",
            "description": "更有创造性的回答",
            "icon": "🎨",
            "config": {"temperature": 0.9, "topP": 0.95, "repeatPenalty": 1.2}
        },
        {
            "id": "precise",
            "name": "精确",
            "description": "更精确和详细的回答",
            "icon": "🎯",
            "config": {"temperature": 0.3, "topP": 1.0, "repeatPenalty": 1.05}
        }
    ]
    return ApiResponse(success=True, data=presets)
