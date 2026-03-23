from fastapi import APIRouter, Depends, Query
from typing import Optional
from ..dto.common import ApiResponse, PaginatedResponse
from ..dto.chat_dto import ChatSession, ChatConfig, SendMessageRequest
from ..service.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

# Global service reference - populated by main.py lifespan
_chat_service_ref: ChatService = None

def set_chat_service_ref(service: ChatService):
    global _chat_service_ref
    _chat_service_ref = service

def get_chat_service() -> ChatService:
    return _chat_service_ref

@router.get("/sessions", response_model=ApiResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ChatService = Depends(get_chat_service)
):
    sessions = await service.list_sessions()
    total = len(sessions)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = sessions[start:end]

    return ApiResponse(success=True, data=PaginatedResponse(
        items=[s.model_dump() for s in paginated],
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total
    ).model_dump())

@router.get("/sessions/{session_id}", response_model=ApiResponse)
async def get_session(session_id: str, service: ChatService = Depends(get_chat_service)):
    session = await service.get_session(session_id)
    return ApiResponse(success=True, data=session.model_dump())

@router.post("/sessions", response_model=ApiResponse)
async def create_session(
    request: Optional[dict] = None,
    service: ChatService = Depends(get_chat_service)
):
    title = request.get("title", "新对话") if request else "新对话"
    session = await service.create_session(title=title)
    return ApiResponse(success=True, data=session.model_dump())

@router.post("/sessions/{session_id}/messages", response_model=ApiResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    service: ChatService = Depends(get_chat_service)
):
    user_msg, assistant_msg = await service.send_message(
        session_id=session_id,
        content=request.content,
        config=request.config
    )
    return ApiResponse(success=True, data={
        "userMessage": user_msg.model_dump(),
        "assistantMessage": assistant_msg.model_dump()
    })

@router.get("/config", response_model=ApiResponse)
async def get_config():
    config = ChatConfig()
    return ApiResponse(success=True, data=config.model_dump())

@router.get("/presets", response_model=ApiResponse)
async def get_presets():
    presets = [
        {"id": "balanced", "name": "平衡", "description": "平衡创造性 和准确性", "icon": "⚖️", "config": {"temperature": 0.7}},
        {"id": "creative", "name": "创造性", "description": "更有创造性的回答", "icon": "🎨", "config": {"temperature": 0.9}},
        {"id": "precise", "name": "精确", "description": "更精确和详细的回答", "icon": "🎯", "config": {"temperature": 0.3}},
    ]
    return ApiResponse(success=True, data=presets)