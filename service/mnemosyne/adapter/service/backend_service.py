from typing import Dict, Optional, List
import os
import time
from datetime import datetime
from ..dto.backend_dto import (
    BackendConnection, BackendConfig, BackendStatus,
    BackendHealth, StorageMetrics, CollectionStats
)
from ...vector_stores.sqlite import SQLiteVectorStore

class BackendService:
    """Service layer for backend operations."""

    def __init__(self):
        self._backends: Dict[str, BackendConnection] = {}
        self._connections: Dict[str, SQLiteVectorStore] = {}

    async def list_backends(self) -> list[BackendConnection]:
        return list(self._backends.values())

    async def get_backend(self, provider: str) -> Optional[BackendConnection]:
        backend = self._backends.get(provider)
        if backend:
            # Update health info if connected
            if backend.status == BackendStatus.CONNECTED:
                backend.health = BackendHealth(
                    status=BackendStatus.CONNECTED,
                    latency=await self._measure_latency(provider),
                    lastChecked=datetime.now()
                )
        return backend

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

        # Measure latency and get initial stats
        latency = await self._measure_latency(provider)

        # Get collections for the backend
        collections = await self.get_collections(provider)

        backend = BackendConnection(
            provider=config.provider,
            status=BackendStatus.CONNECTED,
            host=config.host,
            port=config.port,
            database=config.database,
            health=BackendHealth(
                status=BackendStatus.CONNECTED,
                latency=latency,
                lastChecked=datetime.now()
            ),
            collections=collections
        )
        self._backends[provider] = backend
        return backend

    async def _measure_latency(self, provider: str) -> Optional[float]:
        """Measure connection latency to the backend."""
        if provider not in self._connections:
            return None
        try:
            start = time.time()
            store = self._connections[provider]
            # Simple ping by getting vector count
            self._get_vector_count(provider)
            return round((time.time() - start) * 1000, 2)  # ms
        except:
            return None

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

    async def get_metrics(self, provider: str) -> Optional[StorageMetrics]:
        """Get storage metrics for a backend."""
        if provider not in self._connections:
            return None
        try:
            vector_count = self._get_vector_count(provider)
            store = self._connections[provider]

            # Get database size
            db_size = os.path.getsize(store.db_path) if os.path.exists(store.db_path) else 0

            # Estimate index size from FAISS index directory
            index_size = 0
            if hasattr(store, 'index_dir') and os.path.exists(store.index_dir):
                for f in os.listdir(store.index_dir):
                    index_size += os.path.getsize(os.path.join(store.index_dir, f))

            return StorageMetrics(
                totalMemory=db_size * 2,  # Rough estimate
                usedMemory=db_size,
                vectorCount=vector_count,
                indexSize=index_size,
                diskUsage=db_size + index_size,
                connectionPoolSize=10,
                activeConnections=1
            )
        except Exception as e:
            return None

    async def get_collections(self, provider: str) -> List[CollectionStats]:
        """Get collections for a backend."""
        if provider not in self._connections:
            return []
        try:
            store = self._connections[provider]
            with store._lock:
                import sqlite3
                with sqlite3.connect(store.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM memories WHERE is_deleted = 0"
                    )
                    row = cursor.fetchone()
                    count = row[0] if row else 0

                    # Return default collection with count
                    return [
                        CollectionStats(
                            name="default",
                            memoryCount=count,
                            vectorDimension=store.vector_size if hasattr(store, 'vector_size') else 384,
                            indexType="HNSW" if hasattr(store, 'use_faiss') and store.use_faiss else "FLAT",
                            createdAt=datetime.now()
                        )
                    ]
        except:
            return []

    async def disconnect(self, provider: str) -> bool:
        if provider in self._backends:
            self._backends[provider].status = BackendStatus.DISCONNECTED
            if provider in self._connections:
                del self._connections[provider]
            return True
        return False