from typing import Dict, Optional
import os
from ..dto.backend_dto import BackendConnection, BackendConfig, BackendStatus
from ...vector_stores.sqlite import SQLiteVectorStore

class BackendService:
    """Service layer for backend operations."""

    def __init__(self):
        self._backends: Dict[str, BackendConnection] = {}
        self._connections: Dict[str, SQLiteVectorStore] = {}

    async def list_backends(self) -> list[BackendConnection]:
        return list(self._backends.values())

    async def get_backend(self, provider: str) -> Optional[BackendConnection]:
        return self._backends.get(provider)

    async def connect(self, config: BackendConfig) -> BackendConnection:
        """Connect to a backend storage provider."""
        provider = config.provider.value

        # If already connected, return existing
        if provider in self._backends:
            return self._backends[provider]

        # Initialize the appropriate vector store
        if provider == "sqlite":
            # SQLite is local, use database path
            db_path = config.database if config.database else "./data/memories.db"
            # Ensure it's an absolute path or proper relative path
            if not db_path.startswith("/"):
                db_path = f"./data/{db_path}"

            vector_size = config.vectorDimension if config.vectorDimension else 384
            index_dir = f"{os.path.dirname(db_path)}/vectors" if os.path.dirname(db_path) else "./data/vectors"

            vector_store = SQLiteVectorStore(
                db_path=db_path,
                vector_size=vector_size,
                use_faiss=True,
                index_dir=index_dir
            )
            self._connections[provider] = vector_store

        # Get vector count if available
        vector_count = 0
        if provider in self._connections:
            try:
                # Count vectors in the store
                vector_count = self._get_vector_count(provider)
            except:
                vector_count = 0

        backend = BackendConnection(
            provider=config.provider,
            status=BackendStatus.CONNECTED,
            host=config.host,
            port=config.port,
            database=config.database
        )
        self._backends[provider] = backend
        return backend

    def _get_vector_count(self, provider: str) -> int:
        """Get vector count from the connection."""
        if provider not in self._connections:
            return 0
        store = self._connections[provider]
        try:
            with store._lock:
                import sqlite3
                with sqlite3.connect(store.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE is_deleted = 0")
                    result = cursor.fetchone()
                    return result[0] if result else 0
        except:
            return 0

    async def disconnect(self, provider: str) -> bool:
        if provider in self._backends:
            self._backends[provider].status = BackendStatus.DISCONNECTED
            if provider in self._connections:
                del self._connections[provider]
            return True
        return False