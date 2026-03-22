from fastapi import APIRouter
from .chat import chat_router
from .memory import memory_router
from .backend import backend_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(backend_router)
