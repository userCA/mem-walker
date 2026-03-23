from fastapi import FastAPI
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
from mnemosyne.embeddings import FastEmbedEmbedding
from mnemosyne.embeddings.configs import FastEmbedConfig
from .controller.chat_controller import set_chat_service_ref
from .controller.memory_controller import set_memory_service_ref
from .controller.backend_controller import set_backend_service_ref

# Global app state
_app_state = {"initialized": False}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - initialize services
    config = get_config()

    # Initialize embedding with FastEmbed (local, no API key needed)
    embedding_config = FastEmbedConfig(
        model="BAAI/bge-small-en-v1.5",
        dimension=384
    )
    base_embedding = FastEmbedEmbedding(embedding_config)

    # Initialize mnemosyne with FastEmbed embedding
    memory = Memory(embedding=base_embedding)

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

    # Populate controller global references
    set_memory_service_ref(memory_service)
    set_chat_service_ref(chat_service)
    set_backend_service_ref(backend_service)

    # Store memory for cleanup
    app.state.memory = memory

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