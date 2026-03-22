# Mnemosyne Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 mnemosyne-adapter API 层，为前端 React 提供兼容的 REST 接口，连接 mnemosyne 核心记忆系统。

**Architecture:** 在 `service/mnemosyne/adapter/` 下构建 FastAPI 应用，分层为 router → controller → service → mapper → mnemosyne 核心。Chat 会话使用混合存储策略（SQLite SessionStore + mnemosyne episodic memory）。

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, aiosqlite, structlog, httpx, mnemosyne-core

---

## File Structure

```
service/mnemosyne/adapter/
├── __init__.py
├── main.py                      # FastAPI 应用入口
├── config.py                    # 适配器配置
├── router/
│   ├── __init__.py
│   ├── chat.py                  # /api/v1/chat 路由
│   ├── memory.py                # /api/v1/memories 路由
│   └── backend.py               # /api/v1/backends 路由
├── controller/
│   ├── __init__.py
│   ├── chat_controller.py
│   ├── memory_controller.py
│   └── backend_controller.py
├── dto/
│   ├── __init__.py
│   ├── common.py                # ApiResponse, PaginatedResponse
│   ├── chat_dto.py              # ChatSession, ChatMessage, ChatConfig DTOs
│   ├── memory_dto.py            # Memory, MemoryStats, MemoryFilter DTOs
│   └── backend_dto.py           # BackendConnection, BackendConfig DTOs
├── service/
│   ├── __init__.py
│   ├── memory_service.py        # mnemosyne 核心适配
│   ├── chat_service.py          # Chat 业务逻辑
│   └── backend_service.py       # Backend 配置管理
├── mapper/
│   ├── __init__.py
│   ├── chat_mapper.py           # Frontend DTO ↔ mnemosyne 模型映射
│   └── memory_mapper.py         # Frontend DTO ↔ mnemosyne 模型映射
├── store/
│   ├── __init__.py
│   └── session_store.py         # SQLite SessionStore
├── middleware/
│   ├── __init__.py
│   ├── logging.py               # 请求日志
│   ├── error_handler.py         # 统一异常处理
│   └── performance.py           # 性能监控
├── exception/
│   ├── __init__.py
│   └── adapters.py              # AdapterError 等异常类
└── llm/
    ├── __init__.py
    ├── base.py                  # LLMProvider 接口
    ├── deepseek.py              # DeepSeek 实现
    └── openai.py                # OpenAI 实现

tests/
├── unit/
│   ├── test_dto/
│   ├── test_mapper/
│   ├── test_service/
│   └── test_store/
└── integration/
    ├── test_chat_api.py
    ├── test_memory_api.py
    └── test_backend_api.py

web/src/lib/
└── api-client.ts                # 更新 API_BASE_URL
```

---

## Task 1: 项目骨架与依赖

**Files:**
- Create: `service/mnemosyne/adapter/__init__.py`
- Create: `service/mnemosyne/adapter/router/__init__.py`
- Create: `service/mnemosyne/adapter/controller/__init__.py`
- Create: `service/mnemosyne/adapter/dto/__init__.py`
- Create: `service/mnemosyne/adapter/service/__init__.py`
- Create: `service/mnemosyne/adapter/mapper/__init__.py`
- Create: `service/mnemosyne/adapter/store/__init__.py`
- Create: `service/mnemosyne/adapter/middleware/__init__.py`
- Create: `service/mnemosyne/adapter/exception/__init__.py`
- Create: `service/mnemosyne/adapter/llm/__init__.py`
- Create: `service/pyproject.toml` (更新)

- [ ] **Step 1: 更新 pyproject.toml 添加依赖**

```toml
[project]
name = "mnemosyne"
version = "0.1.0"
requires-python = ">=3.11"

[project.optional-dependencies]
adapter = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.26.0",
    "structlog>=24.1.0",
    "aiosqlite>=0.19.0",
]
```

- [ ] **Step 2: 创建所有 __init__.py 文件** (空文件)

```bash
touch service/mnemosyne/adapter/__init__.py
touch service/mnemosyne/adapter/router/__init__.py
# ... 其他目录同理
```

- [ ] **Step 3: Commit**

```bash
git add service/mnemosyne/adapter/ service/pyproject.toml
git commit -m "feat(adapter): create project skeleton"
```

---

## Task 2: DTO 层 - 通用与 Chat

**Files:**
- Create: `service/mnemosyne/adapter/dto/common.py`
- Create: `service/mnemosyne/adapter/dto/chat_dto.py`

- [ ] **Step 1: 编写 common.py 测试**

```python
# tests/unit/test_dto/test_common.py
import pytest
from mnemosyne.adapter.dto.common import ApiResponse, PaginatedResponse

def test_api_response_success():
    response = ApiResponse(success=True, data={"key": "value"})
    assert response.success is True
    assert response.data == {"key": "value"}
    assert response.error is None

def test_api_response_error():
    response = ApiResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Not found"})
    assert response.success is False
    assert response.error["code"] == "NOT_FOUND"

def test_paginated_response():
    response = PaginatedResponse(
        items=[{"id": "1"}, {"id": "2"}],
        total=10,
        page=1,
        page_size=2,
        has_more=True
    )
    assert len(response.items) == 2
    assert response.total == 10
    assert response.has_more is True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_dto/test_common.py -v
# Expected: ERROR - module not found
```

- [ ] **Step 3: 编写 common.py 实现**

```python
# service/mnemosyne/adapter/dto/common.py
from pydantic import BaseModel, Field
from typing import Any, Optional, Generic, TypeVar

T = TypeVar("T")

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[dict] = None

class PaginatedResponse(BaseModel):
    items: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = Field(alias="pageSize", default=20)
    has_more: bool = Field(alias="hasMore", default=False)

    class Config:
        populate_by_name = True
```

- [ ] **Step 4: 编写 chat_dto.py**

```python
# service/mnemosyne/adapter/dto/chat_dto.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    status: str = "sent"
    createdAt: datetime = Field(default_factory=datetime.now)

class ChatSession(BaseModel):
    id: str
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    memoryCount: int = 0
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    isPinned: bool = False
    isExpanded: bool = True

class ChatConfig(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    maxTokens: int = 2000
    topP: float = 1.0
    repeatPenalty: float = 1.1

class SendMessageRequest(BaseModel):
    content: str
    config: Optional[dict] = None
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/unit/test_dto/ -v
# Expected: 3 tests PASS
```

- [ ] **Step 6: Commit**

```bash
git add tests/unit/test_dto/test_common.py service/mnemosyne/adapter/dto/common.py service/mnemosyne/adapter/dto/chat_dto.py
git commit -m "feat(adapter): add DTOs for common and chat"
```

---

## Task 3: DTO 层 - Memory 与 Backend

**Files:**
- Create: `service/mnemosyne/adapter/dto/memory_dto.py`
- Create: `service/mnemosyne/adapter/dto/backend_dto.py`
- Create: `tests/unit/test_dto/test_memory_dto.py`
- Create: `tests/unit/test_dto/test_backend_dto.py`

- [ ] **Step 1: 编写 memory_dto.py 测试**

```python
# tests/unit/test_dto/test_memory_dto.py
import pytest
from mnemosyne.adapter.dto.memory_dto import Memory, MemoryStatus, MemoryPriority, CreateMemoryRequest

def test_memory_dto_creation():
    memory = Memory(
        id="test-123",
        title="Test Memory",
        content="This is test content",
        status=MemoryStatus.ACTIVE,
        priority=MemoryPriority.HIGH
    )
    assert memory.id == "test-123"
    assert memory.title == "Test Memory"
    assert memory.status == MemoryStatus.ACTIVE
    assert memory.priority == MemoryPriority.HIGH

def test_create_memory_request():
    request = CreateMemoryRequest(
        title="New Memory",
        content="Memory content"
    )
    assert request.title == "New Memory"
    assert request.priority == MemoryPriority.MEDIUM  # default
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_dto/test_memory_dto.py -v
# Expected: ERROR - module not found
```

- [ ] **Step 3: 编写 memory_dto.py 实现**

```python
# service/mnemosyne/adapter/dto/memory_dto.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FROZEN = "frozen"
    DELETED = "deleted"

class MemoryPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class MemoryLayer(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    WORKING = "working"

class MemoryTag(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    count: Optional[int] = None

class Memory(BaseModel):
    id: str
    title: str
    content: str
    status: MemoryStatus = MemoryStatus.ACTIVE
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    tags: list[MemoryTag] = Field(default_factory=list)
    layer: Optional[MemoryLayer] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)

class MemoryStats(BaseModel):
    total: int = 0
    byStatus: dict[str, int] = {}
    byPriority: dict[str, int] = {}
    byLayer: dict[str, int] = {}
    averageImportance: float = 0.0

class CreateMemoryRequest(BaseModel):
    title: str
    content: str
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: int = Field(ge=1, le=5, default=3)
    tags: list[str] = Field(default_factory=list)
    layer: Optional[MemoryLayer] = None

class UpdateMemoryRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[MemoryStatus] = None
    priority: Optional[MemoryPriority] = None
    importance: Optional[int] = None
    tags: Optional[list[str]] = None
```

- [ ] **Step 4: 编写 backend_dto.py 测试**

```python
# tests/unit/test_dto/test_backend_dto.py
import pytest
from mnemosyne.adapter.dto.backend_dto import BackendConnection, BackendProvider, BackendStatus

def test_backend_connection_defaults():
    conn = BackendConnection(provider=BackendProvider.MILVUS)
    assert conn.provider == BackendProvider.MILVUS
    assert conn.status == BackendStatus.DISCONNECTED
    assert conn.host == "localhost"
```

- [ ] **Step 5: 编写 backend_dto.py 实现**

```python
# service/mnemosyne/adapter/dto/backend_dto.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class BackendProvider(str, Enum):
    MILVUS = "milvus"
    SQLITE = "sqlite"
    CHROMA = "chroma"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"

class BackendStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class BackendConnection(BaseModel):
    provider: BackendProvider
    status: BackendStatus = BackendStatus.DISCONNECTED
    host: str = "localhost"
    port: int = 19530
    database: str = "default"

class BackendConfig(BaseModel):
    provider: BackendProvider
    host: str = "localhost"
    port: int = 19530
    database: str = "default"
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    timeout: int = 30
    vectorDimension: int = 768
```

- [ ] **Step 6: 运行测试验证通过**

```bash
pytest tests/unit/test_dto/test_memory_dto.py tests/unit/test_dto/test_backend_dto.py -v
# Expected: 3 tests PASS
```

- [ ] **Step 7: Commit**

```bash
git add service/mnemosyne/adapter/dto/memory_dto.py service/mnemosyne/adapter/dto/backend_dto.py tests/unit/test_dto/test_memory_dto.py tests/unit/test_dto/test_backend_dto.py
git commit -m "feat(adapter): add Memory and Backend DTOs"
---

## Task 4: 异常与配置层

**Files:**
- Create: `service/mnemosyne/adapter/exception/adapters.py`
- Create: `service/mnemosyne/adapter/config.py`
- Create: `tests/unit/test_exception/test_adapters.py`

- [ ] **Step 1: 编写 adapters.py 测试**

```python
# tests/unit/test_exception/test_adapters.py
import pytest
from mnemosyne.adapter.exception.adapters import AdapterError, NotFoundError, ValidationError, LLMError

def test_adapter_error():
    err = AdapterError(code="TEST", message="test error", status_code=500)
    assert err.code == "TEST"
    assert err.message == "test error"
    assert err.status_code == 500

def test_not_found_error():
    err = NotFoundError("Memory", "mem-123")
    assert err.code == "NOT_FOUND"
    assert err.status_code == 404
    assert "mem-123" in err.message

def test_llm_error():
    err = LLMError("API failed")
    assert err.code == "LLM_ERROR"
    assert err.status_code == 502
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_exception/test_adapters.py -v
# Expected: ERROR - module not found
```

- [ ] **Step 3: 编写 adapters.py 实现**

```python
# service/mnemosyne/adapter/exception/adapters.py
from fastapi import HTTPException

class AdapterError(Exception):
    """Base exception for adapter errors."""
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AdapterError):
    """Resource not found."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404
        )

class ValidationError(AdapterError):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=400)

class LLMError(AdapterError):
    """LLM call failed."""
    def __init__(self, message: str):
        super().__init__(code="LLM_ERROR", message=message, status_code=502)
```

- [ ] **Step 4 (continued): 编写 config.py**

```python
# service/mnemosyne/adapter/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class AdapterConfig(BaseSettings):
    # API 配置
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM 配置
    llm_provider: str = "deepseek"  # deepseek | openai | local
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # mnemosyne 配置
    storage_backend: str = "local"
    local_db_path: str = "./data/mnemosyne.db"

    # 可观测性
    log_level: str = "INFO"
    enable_tracing: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "ADAPTER_"

@lru_cache()
def get_config() -> AdapterConfig:
    return AdapterConfig()
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/unit/test_exception/ -v
# Expected: tests PASS
```

- [ ] **Step 6: Commit**

```bash
git add service/mnemosyne/adapter/exception/adapters.py service/mnemosyne/adapter/config.py tests/unit/test_exception/
git commit -m "feat(adapter): add exception classes and config"
```

---

## Task 5: SessionStore (SQLite)

**Files:**
- Create: `service/mnemosyne/adapter/store/session_store.py`

- [ ] **Step 1: 编写 session_store.py 测试**

```python
# tests/unit/test_store/test_session_store.py
import pytest
import tempfile
import os
from mnemosyne.adapter.store.session_store import SessionStore

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def store(temp_db):
    return SessionStore(temp_db)

def test_create_session(store):
    session = store.create_session(
        title="Test Session",
        user_id="user_123"
    )
    assert session["title"] == "Test Session"
    assert session["user_id"] == "user_123"
    assert "id" in session

def test_get_session(store):
    created = store.create_session(title="Test", user_id="user_123")
    fetched = store.get_session(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]

def test_list_sessions(store):
    store.create_session(title="S1", user_id="user_123")
    store.create_session(title="S2", user_id="user_123")
    sessions = store.list_sessions(user_id="user_123")
    assert len(sessions) == 2
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_store/test_session_store.py -v
# Expected: ERROR - module not found
```

- [ ] **Step 3: 编写 session_store.py 实现**

```python
# service/mnemosyne/adapter/store/session_store.py
import aiosqlite
from datetime import datetime
from typing import Optional
import uuid

class SessionStore:
    """SQLite-based session store for ChatSession metadata."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    async def _init_db(self):
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

    async def create_session(self, title: str, user_id: str) -> dict:
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
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM chat_sessions WHERE id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
        return None

    async def list_sessions(self, user_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]

    async def update_session(self, session_id: str, updates: dict) -> Optional[dict]:
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
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            await db.commit()
        return True

    async def increment_memory_count(self, session_id: str) -> None:
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_store/test_session_store.py -v
# Expected: 3 tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/adapter/store/session_store.py tests/unit/test_store/test_session_store.py
git commit -m "feat(adapter): implement SessionStore with SQLite"
```

---

## Task 6: Mapper 层

**Files:**
- Create: `service/mnemosyne/adapter/mapper/chat_mapper.py`
- Create: `service/mnemosyne/adapter/mapper/memory_mapper.py`

- [ ] **Step 1: 编写 chat_mapper.py 测试**

```python
# tests/unit/test_mapper/test_chat_mapper.py
import pytest
from datetime import datetime
from mnemosyne.adapter.mapper.chat_mapper import ChatMapper
from mnemosyne.adapter.dto.chat_dto import ChatSession, ChatMessage, ChatRole

def test_session_to_mnemosyne():
    mapper = ChatMapper()
    session = ChatSession(
        id="sess-123",
        title="Test Session",
        messages=[],
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    result = mapper.session_to_episodic(session)
    assert result["metadata"]["session_id"] == "sess-123"
    assert "Test Session" in result["content"]

def test_episodic_to_session():
    mapper = ChatMapper()
    episodic = {
        "content": "Test Session",
        "metadata": {
            "session_id": "sess-123",
            "title": "Test Session",
            "is_pinned": False,
            "is_expanded": True,
            "memory_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_id": "user_123"
        },
        "created_at": datetime.now()
    }
    session = mapper.episodic_to_session(episodic)
    assert session.id == "sess-123"
    assert session.title == "Test Session"
```

- [ ] **Step 2: 编写 chat_mapper.py 实现**

```python
# service/mnemosyne/adapter/mapper/chat_mapper.py
from datetime import datetime
from typing import Optional
from mnemosyne.adapter.dto.chat_dto import ChatSession, ChatMessage, ChatRole

class ChatMapper:
    """Maps between Frontend DTOs and mnemosyne episodic memory format."""

    def session_to_episodic(self, session: ChatSession) -> dict:
        """Convert ChatSession to mnemosyne episodic memory format."""
        return {
            "content": session.title,
            "metadata": {
                "session_id": session.id,
                "title": session.title,
                "is_pinned": session.isPinned,
                "is_expanded": session.isExpanded,
                "memory_count": session.memoryCount,
                "created_at": session.createdAt.isoformat() if isinstance(session.createdAt, datetime) else session.createdAt,
                "updated_at": session.updatedAt.isoformat() if isinstance(session.updatedAt, datetime) else session.updatedAt,
                "user_id": "default_user"  # TODO: get from context
            }
        }

    def episodic_to_session(self, episodic: dict) -> ChatSession:
        """Convert mnemosyne episodic memory to ChatSession."""
        metadata = episodic.get("metadata", {})
        return ChatSession(
            id=metadata.get("session_id", ""),
            title=episodic.get("content", metadata.get("title", "")),
            messages=[],
            memoryCount=metadata.get("memory_count", 0),
            isPinned=metadata.get("is_pinned", False),
            isExpanded=metadata.get("is_expanded", True),
            createdAt=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updatedAt=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat()))
        )

    def message_to_episodic(self, message: ChatMessage, session_id: str) -> dict:
        """Convert ChatMessage to mnemosyne episodic memory format."""
        return {
            "content": message.content,
            "metadata": {
                "session_id": session_id,
                "role": message.role.value,
                "message_id": message.id,
                "created_at": message.createdAt.isoformat() if isinstance(message.createdAt, datetime) else message.createdAt
            }
        }

    def episodic_to_message(self, episodic: dict) -> ChatMessage:
        """Convert mnemosyne episodic memory to ChatMessage."""
        metadata = episodic.get("metadata", {})
        return ChatMessage(
            id=metadata.get("message_id", ""),
            role=ChatRole(metadata.get("role", "user")),
            content=episodic.get("content", ""),
            createdAt=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
        )
```

- [ ] **Step 3: 编写 memory_mapper.py**

```python
# service/mnemosyne/adapter/mapper/memory_mapper.py
from typing import Dict, Any
from mnemosyne.adapter.dto.memory_dto import Memory, MemoryStatus, MemoryPriority, MemoryLayer, MemoryTag

class MemoryMapper:
    """Maps between Frontend Memory DTO and mnemosyne memory format."""

    def to_mnemosyne(self, memory: Memory, user_id: str = "default_user") -> dict:
        """Convert frontend Memory DTO to mnemosyne memory format."""
        return {
            "content": memory.content,
            "metadata": {
                "title": memory.title,
                "status": memory.status.value,
                "priority": memory.priority.value,
                "importance": memory.importance,
                "tags": [tag.dict() for tag in memory.tags],
                "layer": memory.layer.value if memory.layer else None,
                "user_id": user_id
            }
        }

    def from_mnemosyne(self, mnem_mem: dict) -> Memory:
        """Convert mnemosyne memory to frontend Memory DTO."""
        metadata = mnem_mem.get("metadata", {})
        tags = [
            MemoryTag(id=t.get("id", ""), name=t.get("name", ""), color=t.get("color"))
            for t in metadata.get("tags", [])
        ]
        return Memory(
            id=mnem_mem.get("memory_id", mnem_mem.get("id", "")),
            title=metadata.get("title", mnem_mem.get("content", "")[:100]),
            content=mnem_mem.get("content", ""),
            status=MemoryStatus(metadata.get("status", "active")),
            priority=MemoryPriority(metadata.get("priority", "medium")),
            importance=metadata.get("importance", 3),
            tags=tags,
            layer=MemoryLayer(metadata.get("layer")) if metadata.get("layer") else None,
            createdAt=mnem_mem.get("created_at", mnem_mem.get("createdAt")),
            updatedAt=mnem_mem.get("updated_at", mnem_mem.get("updatedAt"))
        )

    def to_mnemosyne_search_result(self, memory: Memory, score: float = 0.0) -> dict:
        """Convert search result with score."""
        result = self.to_mnemosyne(memory)
        result["score"] = score
        return result
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_mapper/ -v
# Expected: tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add service/mnemosyne/adapter/mapper/ tests/unit/test_mapper/
git commit -m "feat(adapter): implement DTO mappers"
```

---

## Task 7: LLM 接口与实现

**Files:**
- Create: `service/mnemosyne/adapter/llm/base.py`
- Create: `service/mnemosyne/adapter/llm/deepseek.py`
- Create: `service/mnemosyne/adapter/llm/openai.py`

- [ ] **Step 1: 编写 base.py (LLMProvider 接口)**

```python
# service/mnemosyne/adapter/llm/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class LLMMessage(BaseModel):
    role: str
    content: str

class LLMProvider(ABC):
    """Interface for LLM providers."""

    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> str:
        """Send chat request and return assistant response."""
        pass

    @abstractmethod
    async def close(self):
        """Close the LLM connection."""
        pass
```

- [ ] **Step 2: 编写 deepseek.py**

```python
# service/mnemosyne/adapter/llm/deepseek.py
import httpx
from typing import List
from .base import LLMProvider, LLMMessage
from ..exception.adapters import LLMError

class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def chat(self, messages: List[LLMMessage], **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                raise LLMError("No response content from DeepSeek")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"DeepSeek API error: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"DeepSeek call failed: {str(e)}")

    async def close(self):
        pass
```

- [ ] **Step 3: 编写 openai.py (类似结构)**

```python
# service/mnemosyne/adapter/llm/openai.py
import httpx
from typing import List
from .base import LLMProvider, LLMMessage
from ..exception.adapters import LLMError

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: List[LLMMessage], **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                raise LLMError("No response content from OpenAI")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"OpenAI call failed: {str(e)}")

    async def close(self):
        pass
```

- [ ] **Step 4: Commit**

```bash
git add service/mnemosyne/adapter/llm/
git commit -m "feat(adapter): implement LLM provider interface"
```

---

## Task 8: Service 层

**Files:**
- Create: `service/mnemosyne/adapter/service/memory_service.py`
- Create: `service/mnemosyne/adapter/service/chat_service.py`
- Create: `service/mnemosyne/adapter/service/backend_service.py`

- [ ] **Step 1: 编写 memory_service.py**

```python
# service/mnemosyne/adapter/service/memory_service.py
from typing import List, Optional
from mnemosyne import Memory
from ..mapper.memory_mapper import MemoryMapper
from ..dto.memory_dto import Memory as MemoryDTO, MemoryStats
from ..exception.adapters import NotFoundError

class MemoryService:
    """Service layer for memory operations."""

    def __init__(self, memory: Memory):
        self._memory = memory
        self._mapper = MemoryMapper()

    async def search(self, query: str, user_id: str, limit: int = 10) -> List[MemoryDTO]:
        results = self._memory.search(query, user_id=user_id, limit=limit)
        return [self._mapper.from_mnemosyne(r) for r in results]

    async def get(self, memory_id: str) -> MemoryDTO:
        result = self._memory.get(memory_id)
        if not result:
            raise NotFoundError("Memory", memory_id)
        return self._mapper.from_mnemosyne(result)

    async def create(self, dto: MemoryDTO, user_id: str = "default_user") -> MemoryDTO:
        mnem_mem = self._mapper.to_mnemosyne(dto, user_id)
        memory_id = self._memory.add(
            messages=mnem_mem["content"],
            user_id=user_id,
            metadata=mnem_mem["metadata"]
        )
        return await self.get(memory_id)

    async def create_episodic_memory(self, content: str, user_id: str, metadata: dict) -> str:
        """Store a chat message as episodic memory."""
        return self._memory.add(
            messages=content,
            user_id=user_id,
            metadata={**metadata, "memory_type": "episodic"}
        )

    def search_sync(self, query: str, user_id: str, limit: int = 10) -> List[dict]:
        """Synchronous search for memories (used by ChatService for context building)."""
        return self._memory.search(query, user_id=user_id, limit=limit)

    async def update(self, memory_id: str, updates: dict) -> MemoryDTO:
        if updates.get("content"):
            self._memory.update(memory_id, updates["content"])
        return await self.get(memory_id)

    async def delete(self, memory_id: str) -> bool:
        return self._memory.delete(memory_id)

    async def list(self, user_id: str, page: int = 1, page_size: int = 20) -> tuple[List[MemoryDTO], int]:
        all_memories = self._memory.get_all(user_id)
        total = len(all_memories)
        start = (page - 1) * page_size
        end = start + page_size
        items = [self._mapper.from_mnemosyne(m) for m in all_memories[start:end]]
        return items, total

    async def get_stats(self, user_id: str) -> MemoryStats:
        all_memories = self._memory.get_all(user_id)
        total = len(all_memories)
        by_status = {}
        by_priority = {}
        by_layer = {}
        total_importance = 0

        for m in all_memories:
            metadata = m.get("metadata", {})
            status = metadata.get("status", "active")
            priority = metadata.get("priority", "medium")
            layer = metadata.get("layer", "semantic")

            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_layer[layer] = by_layer.get(layer, 0) + 1
            total_importance += metadata.get("importance", 3)

        return MemoryStats(
            total=total,
            byStatus=by_status,
            byPriority=by_priority,
            byLayer=by_layer,
            averageImportance=total_importance / total if total > 0 else 0.0
        )
```

- [ ] **Step 2: 编写 chat_service.py**

```python
# service/mnemosyne/adapter/service/chat_service.py
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
```

- [ ] **Step 3: 编写 backend_service.py**

```python
# service/mnemosyne/adapter/service/backend_service.py
from typing import Dict, Optional
from ..dto.backend_dto import BackendConnection, BackendConfig, BackendStatus

class BackendService:
    """Service layer for backend operations."""

    def __init__(self):
        self._backends: Dict[str, BackendConnection] = {}

    async def list_backends(self) -> list[BackendConnection]:
        return list(self._backends.values())

    async def get_backend(self, provider: str) -> Optional[BackendConnection]:
        return self._backends.get(provider)

    async def connect(self, config: BackendConfig) -> BackendConnection:
        backend = BackendConnection(
            provider=config.provider,
            status=BackendStatus.CONNECTED,
            host=config.host,
            port=config.port,
            database=config.database
        )
        self._backends[config.provider.value] = backend
        return backend

    async def disconnect(self, provider: str) -> bool:
        if provider in self._backends:
            self._backends[provider].status = BackendStatus.DISCONNECTED
            return True
        return False
```

- [ ] **Step 4: Commit**

```bash
git add service/mnemosyne/adapter/service/
git commit -m "feat(adapter): implement service layer"
```

---

## Task 9: Controller 层

**Files:**
- Create: `service/mnemosyne/adapter/controller/chat_controller.py`
- Create: `service/mnemosyne/adapter/controller/memory_controller.py`
- Create: `service/mnemosyne/adapter/controller/backend_controller.py`

- [ ] **Step 1: 编写 chat_controller.py**

```python
# service/mnemosyne/adapter/controller/chat_controller.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from ..dto.common import ApiResponse, PaginatedResponse
from ..dto.chat_dto import ChatSession, ChatConfig, SendMessageRequest
from ..service.chat_service import ChatService
from ..exception.adapters import AdapterError
from main import get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

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
```

- [ ] **Step 2: 编写 memory_controller.py**

```python
# service/mnemosyne/adapter/controller/memory_controller.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from ..dto.common import ApiResponse, PaginatedResponse
from ..dto.memory_dto import Memory, CreateMemoryRequest, UpdateMemoryRequest, MemoryStats
from ..service.memory_service import MemoryService
from main import get_memory_service

router = APIRouter(prefix="/memories", tags=["memories"])

@router.get("/", response_model=ApiResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MemoryService = Depends(get_memory_service)
):
    items, total = await service.list("default_user", page, page_size)
    return ApiResponse(success=True, data=PaginatedResponse(
        items=[m.model_dump() for m in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    ).model_dump())

@router.get("/stats", response_model=ApiResponse)
async def get_stats(service: MemoryService = Depends(get_memory_service)):
    stats = await service.get_stats("default_user")
    return ApiResponse(success=True, data=stats.model_dump())

@router.get("/search", response_model=ApiResponse)
async def search_memories(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, le=50),
    service: MemoryService = Depends(get_memory_service)
):
    results = await service.search(q, "default_user", limit)
    return ApiResponse(success=True, data=[r.model_dump() for r in results])

@router.get("/{memory_id}", response_model=ApiResponse)
async def get_memory(memory_id: str, service: MemoryService = Depends(get_memory_service)):
    memory = await service.get(memory_id)
    return ApiResponse(success=True, data=memory.model_dump())

@router.post("/", response_model=ApiResponse)
async def create_memory(
    request: CreateMemoryRequest,
    service: MemoryService = Depends(get_memory_service)
):
    dto = Memory(
        id="",  # Will be generated
        title=request.title,
        content=request.content,
        priority=request.priority,
        importance=request.importance,
        tags=[],
        layer=request.layer
    )
    created = await service.create(dto, "default_user")
    return ApiResponse(success=True, data=created.model_dump())

@router.patch("/{memory_id}", response_model=ApiResponse)
async def update_memory(
    memory_id: str,
    request: UpdateMemoryRequest,
    service: MemoryService = Depends(get_memory_service)
):
    updates = request.model_dump(exclude_unset=True)
    updated = await service.update(memory_id, updates)
    return ApiResponse(success=True, data=updated.model_dump())

@router.delete("/{memory_id}", response_model=ApiResponse)
async def delete_memory(memory_id: str, service: MemoryService = Depends(get_memory_service)):
    await service.delete(memory_id)
    return ApiResponse(success=True, data={"message": "Memory deleted"})
```

- [ ] **Step 3: 编写 backend_controller.py**

```python
# service/mnemosyne/adapter/controller/backend_controller.py
from fastapi import APIRouter, Depends
from ..dto.common import ApiResponse
from ..dto.backend_dto import BackendConfig
from ..service.backend_service import BackendService
from main import get_backend_service

router = APIRouter(prefix="/backends", tags=["backends"])

@router.get("/", response_model=ApiResponse)
async def list_backends(service: BackendService = Depends(get_backend_service)):
    backends = await service.list_backends()
    return ApiResponse(success=True, data=[b.model_dump() for b in backends])

@router.get("/{provider}", response_model=ApiResponse)
async def get_backend(provider: str, service: BackendService = Depends(get_backend_service)):
    backend = await service.get_backend(provider)
    if not backend:
        from ..exception.adapters import NotFoundError
        raise NotFoundError("Backend", provider)
    return ApiResponse(success=True, data=backend.model_dump())

@router.post("/connect", response_model=ApiResponse)
async def connect_backend(config: BackendConfig, service: BackendService = Depends(get_backend_service)):
    backend = await service.connect(config)
    return ApiResponse(success=True, data=backend.model_dump())

@router.post("/{provider}/disconnect", response_model=ApiResponse)
async def disconnect_backend(provider: str, service: BackendService = Depends(get_backend_service)):
    success = await service.disconnect(provider)
    return ApiResponse(success=True, data={"success": success})

@router.post("/test", response_model=ApiResponse)
async def test_connection(config: BackendConfig, service: BackendService = Depends(get_backend_service)):
    # Test logic would connect and verify
    return ApiResponse(success=True, data={"success": True})
```

- [ ] **Step 4: Commit**

```bash
git add service/mnemosyne/adapter/controller/
git commit -m "feat(adapter): implement controller layer"
```

---

## Task 10: 中间件层

**Files:**
- Create: `service/mnemosyne/adapter/middleware/logging.py`
- Create: `service/mnemosyne/adapter/middleware/error_handler.py`
- Create: `service/mnemosyne/adapter/middleware/performance.py`

- [ ] **Step 1: 编写 logging.py**

```python
# service/mnemosyne/adapter/middleware/logging.py
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown"
        )

        response = await call_next(request)

        logger.info(
            "request_end",
            request_id=request_id,
            status_code=response.status_code
        )

        return response
```

- [ ] **Step 2: 编写 error_handler.py**

```python
# service/mnemosyne/adapter/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from ..exception.adapters import AdapterError

async def adapter_exception_handler(request: Request, exc: AdapterError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )
```

- [ ] **Step 3: 编写 performance.py**

```python
# service/mnemosyne/adapter/middleware/performance.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response
```

- [ ] **Step 4: Commit**

```bash
git add service/mnemosyne/adapter/middleware/
git commit -m "feat(adapter): implement middleware layer"
```

---

## Task 11: Router 层与主应用入口

**Files:**
- Create: `service/mnemosyne/adapter/router/chat.py`
- Create: `service/mnemosyne/adapter/router/memory.py`
- Create: `service/mnemosyne/adapter/router/backend.py`
- Create: `service/mnemosyne/adapter/main.py`

- [ ] **Step 1: 创建路由文件**

```python
# service/mnemosyne/adapter/router/chat.py
from ..controller.chat_controller import router as chat_router
```

```python
# service/mnemosyne/adapter/router/memory.py
from ..controller.memory_controller import router as memory_router
```

```python
# service/mnemosyne/adapter/router/backend.py
from ..controller.backend_controller import router as backend_router
```

- [ ] **Step 2: 创建路由聚合文件 (router/__init__.py)**

```python
# service/mnemosyne/adapter/router/__init__.py
from fastapi import APIRouter
from .chat import router as chat_router
from .memory import router as memory_router
from .backend import router as backend_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(backend_router)
```

- [ ] **Step 3: 编写 main.py**

```python
# service/mnemosyne/adapter/main.py
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
```

- [ ] **Step 4: Commit**

```bash
git add service/mnemosyne/adapter/router/ service/mnemosyne/adapter/main.py
git commit -m "feat(adapter): implement router and main app entry"
```

---

## Task 12: 前端 API URL 更新

**Files:**
- Modify: `web/src/lib/api-client.ts` (或相关配置)

- [ ] **Step 1: 更新 API base URL**

```typescript
// web/src/lib/api-client.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api = {
  get: async <T>(path: string, params?: Record<string, any>): Promise<T> => {
    const url = new URL(path, API_BASE_URL);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    }
    const response = await fetch(url.toString(), {
      headers: { 'Content-Type': 'application/json' },
    });
    return response.json();
  },
  // ... post, patch, delete similar
};
```

- [ ] **Step 2: Commit**

```bash
git add web/src/lib/api-client.ts
git commit -m "feat(web): update API base URL to /api/v1"
```

---

## Task 13: 单元测试

**Files:**
- Create: `tests/unit/test_dto/test_common.py`
- Create: `tests/unit/test_dto/test_chat_dto.py`
- Create: `tests/unit/test_mapper/test_chat_mapper.py`
- Create: `tests/unit/test_mapper/test_memory_mapper.py`
- Create: `tests/unit/test_store/test_session_store.py`
- Create: `tests/unit/test_service/test_memory_service.py`

- [ ] **Step 1: 编写并运行所有单元测试**

```bash
# 创建测试目录结构
mkdir -p tests/unit/test_dto tests/unit/test_mapper tests/unit/test_store tests/unit/test_service

# 运行测试
cd service
pytest ../tests/unit/ -v --tb=short
```

- [ ] **Step 2: Commit**

```bash
git add tests/unit/
git commit -m "test(adapter): add unit tests"
```

---

## Task 14: 集成测试

**Files:**
- Create: `tests/integration/test_chat_api.py`
- Create: `tests/integration/test_memory_api.py`
- Create: `tests/integration/test_backend_api.py`

- [ ] **Step 1: 编写 test_chat_api.py**

```python
# tests/integration/test_chat_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from mnemosyne.adapter.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/v1/chat/sessions", json={"title": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]

@pytest.mark.asyncio
async def test_list_sessions(client):
    response = await client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
```

- [ ] **Step 2: 运行集成测试**

```bash
cd service
pytest ../tests/integration/ -v --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test(adapter): add integration tests"
```

---

## Task 15: 最终验证与报告

- [ ] **Step 1: 运行完整测试套件**

```bash
cd service
pytest ../tests/ -v --tb=short --cov=mnemosyne/adapter --cov-report=term-missing
```

- [ ] **Step 2: 验证 API 端点**

```bash
# 启动服务并测试
uvicorn mnemosyne.adapter.main:app --host 0.0.0.0 --port 8000 &

# 测试端点
curl http://localhost:8000/api/v1/chat/sessions
curl http://localhost:8000/api/v1/memories/
curl http://localhost:8000/api/v1/backends/
```

- [ ] **Step 3: 生成接口对照表**

```bash
# 输出接口对照表到文档
cat > docs/superpowers/specs/2026-03-22-api-mapping.md << 'EOF'
# API 接口对照表

| 原接口 | 新接口 | 状态 |
|--------|--------|------|
... (complete based on actual endpoints)
EOF
```

- [ ] **Step 4: Commit 最终状态**

```bash
git add -A
git commit -m "feat(adapter): complete mnemosyne-adapter implementation"
```

---

## 总结

| Task | 组件 | 依赖 |
|------|------|------|
| 1 | 项目骨架 | - |
| 2 | DTO common & chat | 1 |
| 3 | DTO memory & backend | 1 |
| 4 | 异常 & 配置 | 1 |
| 5 | SessionStore | 4 |
| 6 | Mapper | 2, 3 |
| 7 | LLM 接口 | 4 |
| 8 | Service | 5, 6, 7 |
| 9 | Controller | 8 |
| 10 | Middleware | 4 |
| 11 | Router & Main | 9, 10 |
| 12 | 前端更新 | 11 |
| 13 | 单元测试 | 2-11 |
| 14 | 集成测试 | 11, 13 |
| 15 | 验证报告 | 14 |
