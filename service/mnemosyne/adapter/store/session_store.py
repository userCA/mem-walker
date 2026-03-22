import aiosqlite
from datetime import datetime
from typing import Optional
import uuid

class SessionStore:
    """SQLite-based session store for ChatSession metadata."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False

    async def _ensure_init(self):
        """Lazy initialization - create table if not exists."""
        if self._initialized:
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    is_expanded BOOLEAN DEFAULT TRUE,
                    memory_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    user_id TEXT NOT NULL
                )
            """)
            await db.commit()
        self._initialized = True

    async def create_session(self, title: str, user_id: str) -> dict:
        await self._ensure_init()
        session_id = str(uuid.uuid4())
        now = datetime.now()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO chat_sessions (id, title, is_pinned, is_expanded, memory_count, created_at, updated_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, title, False, True, 0, now, now, user_id))
            await db.commit()
        return {
            "id": session_id,
            "title": title,
            "is_pinned": False,
            "is_expanded": True,
            "memory_count": 0,
            "created_at": now,
            "updated_at": now,
            "user_id": user_id
        }

    async def get_session(self, session_id: str) -> Optional[dict]:
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM chat_sessions WHERE id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
        return None

    async def list_sessions(self, user_id: str) -> list[dict]:
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]

    async def update_session(self, session_id: str, updates: dict) -> Optional[dict]:
        await self._ensure_init()
        updates["updated_at"] = datetime.now()
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [session_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE chat_sessions SET {set_clause} WHERE id = ?",
                values
            )
            await db.commit()
        return await self.get_session(session_id)

    async def delete_session(self, session_id: str) -> bool:
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            await db.commit()
        return True

    async def increment_memory_count(self, session_id: str) -> None:
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE chat_sessions
                SET memory_count = memory_count + 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), session_id))
            await db.commit()

    def _row_to_dict(self, row: tuple) -> dict:
        return {
            "id": row[0],
            "title": row[1],
            "is_pinned": bool(row[2]),
            "is_expanded": bool(row[3]),
            "memory_count": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "user_id": row[7]
        }