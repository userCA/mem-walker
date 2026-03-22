from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from functools import lru_cache
from .config import get_config
from .router import api_router
from .middleware.logging import LoggingMiddleware
from .middleware.error_handler import adapter_exception_handler, general_exception_handler
from .middleware.performance import PerformanceMiddleware
from .exception.adapters import AdapterError
from .store.session_store import SessionStore
from .service.chat_service import ChatService
from .service.memory_service import MemoryService
from .service.backend_service import BackendService
from .llm.deepseek import DeepSeekProvider
from mnemosyne import Memory

# Global app state
_app_state = {"initialized": False}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - initialize services in app state
    config = get_config()

    # Initialize mnemosyne
    memory = Memory()

    # Initialize SessionStore
    session_store = SessionStore(f"./data/{config.storage_backend}_sessions.db")

    # Initialize LLM provider
    if config.llm_provider == "deepseek":
        llm = DeepSeekProvider(
            api_key=config.deepseek_api_key,
            base_url=config.deepseek_base_url,
            model=config.deepseek_model
        )
    else:
        llm = DeepSeekProvider(api_key=config.deepseek_api_key)

    # Initialize services
    memory_service = MemoryService(memory)
    chat_service = ChatService(session_store, llm, memory_service)
    backend_service = BackendService()

    # Store in app state
    app.state.memory_service = memory_service
    app.state.chat_service = chat_service
    app.state.backend_service = backend_service
    app.state.memory = memory  # For cleanup

    _app_state["initialized"] = True

    yield

    # Shutdown
    if hasattr(app.state, "memory"):
        app.state.memory.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Mnemosyne Adapter API",
        description="API adapter for mnemosyne memory system",
        version="1.0.0"
    )

    # Add middleware
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Exception handlers
    app.add_exception_handler(AdapterError, adapter_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include routers
    app.include_router(api_router, prefix="/api/v1")

    # Lifespan
    app.router.lifespan_context = lifespan

    return app

app = create_app()

# Dependency injection helpers
def get_chat_service() -> ChatService:
    from fastapi import Request
    return Request.state.chat_service

def get_memory_service() -> MemoryService:
    from fastapi import Request
    return Request.state.memory_service

def get_backend_service() -> BackendService:
    from fastapi import Request
    return Request.state.backend_service