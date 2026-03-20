"""SQLite Vector Store implementation.

A local vector storage solution using SQLite for metadata and FAISS for vector indexing.
Provides zero-dependency local storage with ACID guarantees.
"""

import json
import os
import shutil
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import numpy as np

from ..utils import get_logger
from .base import VectorStoreBase
from .faiss_manager import FAISSIndexManager

logger = get_logger(__name__)


class SQLiteVectorStore(VectorStoreBase):
    """SQLite-based vector store with FAISS indexing.

    Features:
    - Local storage with no external dependencies
    - ACID transactions via SQLite
    - FAISS vector indexing for fast similarity search
    - WAL mode for improved concurrent performance
    """

    def __init__(
        self,
        db_path: str = "./data/memories.db",
        vector_size: int = 1536,
        use_faiss: bool = True,
        index_dir: str = "./data/vectors"
    ):
        """Initialize SQLite Vector Store.

        Args:
            db_path: Path to SQLite database file
            vector_size: Dimension of vectors
            use_faiss: Whether to use FAISS for vector indexing
            index_dir: Directory for FAISS index files
        """
        self.db_path = db_path
        self.vector_size = vector_size
        self.use_faiss = use_faiss
        self.index_dir = index_dir

        # Ensure directories exist
        db_dir = os.path.dirname(db_path) or "."
        os.makedirs(db_dir, exist_ok=True)

        if use_faiss:
            os.makedirs(index_dir, exist_ok=True)
            self.faiss_manager = FAISSIndexManager(index_dir)

        self._lock = threading.Lock()

        self._init_db()
        logger.info(f"Initialized SQLiteVectorStore at {db_path}")

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")

            # Create memories table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    original_message TEXT,
                    content_hash TEXT,
                    metadata TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER,
                    is_deleted INTEGER DEFAULT 0
                )
            """)

            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON memories(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_is_deleted ON memories(is_deleted)")

            conn.commit()

    def _enable_wal_mode(self, conn: sqlite3.Connection) -> None:
        """Enable WAL mode on a connection."""
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance_metric: str = "cosine"
    ) -> None:
        """Create collection (no-op for SQLite, schema is fixed)."""
        logger.info(f"SQLite collection ready (name={name}, vector_size={vector_size})")

    def insert(
        self,
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Insert vectors with payloads.

        Args:
            vectors: List of embedding vectors
            payloads: Optional metadata for each vector
            ids: Optional custom IDs

        Returns:
            List of inserted vector IDs
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

        if len(ids) != len(vectors):
            raise ValueError("Number of IDs must match number of vectors")

        timestamp = int(time.time())

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                for i, (vec_id, vector) in enumerate(zip(ids, vectors)):
                    payload = payloads[i] if payloads else {}

                    # Extract content_hash from metadata if present
                    content_hash = None
                    if payload.get("metadata") and isinstance(payload["metadata"], dict):
                        content_hash = payload["metadata"].get("content_hash")

                    conn.execute("""
                        INSERT INTO memories
                        (id, user_id, content, original_message, content_hash, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vec_id,
                        payload.get("user_id", "default"),
                        payload.get("content", ""),
                        payload.get("original_message", ""),
                        content_hash,
                        json.dumps(payload.get("metadata", {})),
                        timestamp
                    ))

                    # Add to FAISS index
                    if self.use_faiss:
                        user_id = payload.get("user_id", "default")
                        self.faiss_manager.add_vectors(user_id, [vector], [vec_id])

                conn.commit()

        logger.debug(f"Inserted {len(vectors)} vectors into SQLite")
        return ids

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional metadata filters

        Returns:
            List of search results with scores and payloads
        """
        user_id = filters.get("user_id", "default") if filters else "default"

        # Try FAISS search first
        if self.use_faiss and user_id in self.faiss_manager.indices:
            candidates = self.faiss_manager.search(user_id, query_vector, limit * 3)
            candidate_ids = [c[0] for c in candidates]
            candidate_scores = {c[0]: c[1] for c in candidates}

            # Filter out deleted IDs
            candidate_ids = [cid for cid in candidate_ids if not cid.startswith("_DELETED_")]

            if not candidate_ids:
                return []

            # Fetch from SQLite
            placeholders = ','.join('?' * len(candidate_ids))
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(f"""
                    SELECT * FROM memories
                    WHERE id IN ({placeholders}) AND is_deleted = 0
                """, candidate_ids)
                rows = cursor.fetchall()

            # Build results preserving FAISS score order
            results = []
            for row in rows:
                mem_id = row["id"]
                if mem_id in candidate_scores:
                    results.append({
                        "id": mem_id,
                        "score": candidate_scores[mem_id],
                        "user_id": row["user_id"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "created_at": row["created_at"]
                    })

            # Sort by score descending
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]

        # Fallback: SQLite LIKE search (much slower, less accurate)
        logger.warning("FAISS index not available, using SQLite fallback search")
        return self._sqlite_fallback_search(user_id, limit)

    def _sqlite_fallback_search(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback search using SQLite LIKE (for when FAISS is disabled)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM memories
                WHERE user_id = ? AND is_deleted = 0
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "score": 1.0,  # No similarity score in fallback mode
                "user_id": row["user_id"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    def delete(self, vector_id: str) -> bool:
        """Delete a vector by ID.

        Args:
            vector_id: ID of vector to delete

        Returns:
            True if deleted successfully
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Soft delete in SQLite
                conn.execute("UPDATE memories SET is_deleted = 1 WHERE id = ?", (vector_id,))
                conn.commit()

        # Mark as deleted in FAISS
        if self.use_faiss:
            for user_id in self.faiss_manager.indices:
                self.faiss_manager.delete_vector(user_id, vector_id)

        logger.debug(f"Deleted vector {vector_id}")
        return True

    def update(
        self,
        vector_id: str,
        vector: Optional[List[float]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a vector and/or its payload.

        Args:
            vector_id: ID of vector to update
            vector: New embedding vector (not supported in SQLite)
            payload: New metadata

        Returns:
            True if updated successfully
        """
        if vector is not None:
            logger.warning("Vector update not supported in SQLiteVectorStore")

        if payload is None:
            return False

        timestamp = int(time.time())

        with sqlite3.connect(self.db_path) as conn:
            update_fields = []
            update_values = []

            if "content" in payload:
                update_fields.append("content = ?")
                update_values.append(payload["content"])

            if "metadata" in payload:
                update_fields.append("metadata = ?")
                update_values.append(json.dumps(payload["metadata"]))

            update_fields.append("updated_at = ?")
            update_values.append(timestamp)
            update_values.append(vector_id)

            query = f"UPDATE memories SET {', '.join(update_fields)} WHERE id = ? AND is_deleted = 0"
            cursor = conn.execute(query, update_values)
            conn.commit()

            updated = cursor.rowcount > 0

        if updated:
            logger.debug(f"Updated vector {vector_id}")

        return updated

    def get(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a vector by ID.

        Args:
            vector_id: ID of vector to retrieve

        Returns:
            Vector data with payload or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM memories WHERE id = ? AND is_deleted = 0",
                (vector_id,)
            )
            row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "user_id": row["user_id"],
                "content": row["content"],
                "original_message": row["original_message"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List all vectors matching filters.

        Args:
            filters: Optional metadata filters
            limit: Optional limit on results

        Returns:
            List of vectors with payloads
        """
        query = "SELECT * FROM memories WHERE is_deleted = 0"
        params = []

        if filters:
            if "user_id" in filters:
                query += " AND user_id = ?"
                params.append(filters["user_id"])

            if "content_hash" in filters:
                query += " AND content_hash = ?"
                params.append(filters["content_hash"])

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        with self._lock:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)

            if self.use_faiss and os.path.exists(self.index_dir):
                shutil.rmtree(self.index_dir)

            # Reinitialize empty database
            self._init_db()

            if self.use_faiss:
                self.faiss_manager = FAISSIndexManager(self.index_dir)

        logger.info("Deleted SQLite collection")

    def collection_info(self) -> Dict[str, Any]:
        """Get information about the collection.

        Returns:
            Collection metadata and statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM memories WHERE is_deleted = 0")
            count = cursor.fetchone()[0]

        info = {
            "db_path": self.db_path,
            "num_entities": count,
            "vector_size": self.vector_size,
            "use_faiss": self.use_faiss
        }

        if self.use_faiss:
            info["vector_index_dir"] = self.index_dir
            info["users_with_indices"] = len(self.faiss_manager.indices)

        return info

    def close(self) -> None:
        """Close connections and save indices."""
        if self.use_faiss:
            self.faiss_manager.save_all_indices()
        logger.debug("SQLiteVectorStore closed")

    def get_by_user(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all memories for a specific user.

        Args:
            user_id: User identifier
            limit: Optional limit

        Returns:
            List of memories
        """
        return self.list(filters={"user_id": user_id}, limit=limit)

    def exists(self, content_hash: str, user_id: str) -> bool:
        """Check if a memory with given content hash exists for user.

        Args:
            content_hash: Content hash to check
            user_id: User identifier

        Returns:
            True if exists
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM memories WHERE content_hash = ? AND user_id = ? AND is_deleted = 0",
                (content_hash, user_id)
            )
            return cursor.fetchone() is not None
