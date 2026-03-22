# Mnemosyne Adapter API 设计文档

**版本**: 1.1
**日期**: 2026-03-22
**状态**: 已修订（修复 review 发现的问题）

## 1. 概述

### 1.1 目标

在 mnemosyne 子目录下新增独立的 API 适配层（`mnemosyne-adapter`），将前端 React 应用通过 REST API 连接到 mnemosyne 核心记忆系统，实现：

- 前端接口签名完全兼容（100% 覆盖现有 `/chat/*`, `/memories/*`, `/backends/*` 端点）
- mnemosyne 核心业务逻辑零侵入、零修改
- Chat 消息作为 episodic memory 存储，真正验证记忆效果
- 可独立部署、可观测、可回退

### 1.2 架构原则

| 原则 | 说明 |
|------|------|
| 非侵入 | 不修改 mnemosyne 核心代码 |
| 完整封装 | 通过 Python API 调用 mnemosyne，不暴露内部实现 |
| 接口兼容 | 前端无需修改即可切换到新 API |
| 可观测 | 统一日志、异常处理、性能监控 |
| 可回退 | 支持环境变量切换新旧 API |

---

## 2. 目录结构

```
service/mnemosyne/
├── __init__.py
├── memory/                    # [现有] 核心记忆模块
├── vector_stores/             # [现有] 向量存储
├── embeddings/                # [现有] 嵌入模型
├── llms/                      # [现有] LLM 集成
├── reranker/                  # [现有] 重排序
├── graphs/                    # [现有] 图存储
├── adapter/                   # [新增] API 适配层
│   ├── __init__.py
│   ├── main.py                # FastAPI 应用入口
│   ├── config.py              # 适配器配置
│   ├── router/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat 路由
│   │   ├── memory.py          # Memory 路由
│   │   └── backend.py         # Backend 路由
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── chat_controller.py
│   │   ├── memory_controller.py
│   │   └── backend_controller.py
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── chat_dto.py        # Chat 请求/响应 DTO
│   │   ├── memory_dto.py      # Memory 请求/响应 DTO
│   │   ├── backend_dto.py     # Backend 请求/响应 DTO
│   │   └── common.py          # 通用 DTO (ApiResponse, PaginatedResponse)
│   ├── service/
│   │   ├── __init__.py
│   │   ├── memory_service.py  # mnemosyne Memory 服务适配
│   │   ├── chat_service.py    # Chat 业务逻辑 (调用 memory_service)
│   │   └── backend_service.py # Backend 业务逻辑
│   ├── mapper/
│   │   ├── __init__.py
│   │   ├── chat_mapper.py     # Frontend DTO ↔ mnemosyne 模型映射
│   │   └── memory_mapper.py   # Frontend DTO ↔ mnemosyne 模型映射
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py         # 请求日志中间件
│   │   ├── error_handler.py   # 统一异常处理
│   │   └── performance.py     # 性能监控中间件
│   └── exception/
│       ├── __init__.py
│       └── adapters.py        # 适配器专用异常
└── pyproject.toml             # [更新] 添加 fastapi 等依赖
```

---

## 3. API 设计

### 3.1 端点一览

#### Chat API (`/api/v1/chat`)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/sessions` | 列出对话会话 | ✅ |
| GET | `/sessions/{session_id}` | 获取会话详情 | ✅ |
| POST | `/sessions` | 创建新会话 | ✅ |
| PATCH | `/sessions/{session_id}` | 更新会话 | ✅ |
| DELETE | `/sessions/{session_id}` | 删除会话 | ✅ |
| POST | `/sessions/{session_id}/messages` | 发送消息 | ✅ |
| GET | `/config` | 获取配置 | ✅ |
| PATCH | `/config` | 更新配置 | ✅ |
| GET | `/presets` | 获取预设列表 | ✅ |

#### Memory API (`/api/v1/memories`)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/` | 列出记忆 | ✅ |
| GET | `/stats` | 获取统计 | ✅ |
| GET | `/tags` | 获取标签 | ✅ |
| GET | `/layers` | 获取层级分布 | ✅ |
| GET | `/search` | 搜索记忆 | ✅ |
| GET | `/{memory_id}` | 获取单条记忆 | ✅ |
| POST | `/` | 创建记忆 | ✅ |
| PATCH | `/{memory_id}` | 更新记忆 | ✅ |
| DELETE | `/{memory_id}` | 删除记忆 | ✅ |
| POST | `/batch` | 批量操作 | ✅ |

#### Backend API (`/api/v1/backends`)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/` | 列出后端连接 | ✅ |
| GET | `/{provider}` | 获取后端详情 | ✅ |
| POST | `/connect` | 连接后端 | ✅ |
| POST | `/{provider}/disconnect` | 断开后端 | ✅ |
| POST | `/test` | 测试连接 | ✅ |
| PATCH | `/{provider}` | 更新配置 | ✅ |
| GET | `/{provider}/metrics` | 获取指标 | ✅ |
| GET | `/{provider}/collections` | 获取集合列表 | ✅ |
| POST | `/{provider}/collections` | 创建集合 | ✅ |
| DELETE | `/{provider}/collections/{name}` | 删除集合 | ✅ |

### 3.2 响应格式

所有接口统一响应格式：

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

分页响应：
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "hasMore": true
  },
  "error": null
}
```

### 3.3 请求/响应示例

#### POST /api/v1/chat/sessions/{id}/messages

**请求**：
```json
{
  "content": "我今天学了什么？",
  "config": {
    "temperature": 0.7,
    "maxTokens": 2000
  }
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "userMessage": {
      "id": "msg-uuid-1",
      "role": "user",
      "content": "我今天学了什么？",
      "createdAt": "2026-03-22T10:00:00Z"
    },
    "assistantMessage": {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "根据您的记忆，您今天学习了 Rust 编程语言...",
      "createdAt": "2026-03-22T10:00:01Z"
    }
  },
  "error": null
}
```

#### GET /api/v1/memories/

**响应**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "mem-uuid-1",
        "title": "Rust 编程基础",
        "content": "今天学习了 Rust 的所有权系统...",
        "status": "active",
        "priority": "high",
        "importance": 4,
        "tags": [{"id": "tag-1", "name": "编程", "color": "#007bff"}],
        "layer": "semantic",
        "createdAt": "2026-03-22T09:00:00Z",
        "updatedAt": "2026-03-22T09:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20,
    "hasMore": false
  },
  "error": null
}
```

---

## 4. 数据模型映射

### 4.1 Chat 模型映射

**前端 ChatSession** → **mnemosyne episodic memory**

| 前端字段 | mnemosyne 存储方式 | 说明 |
|----------|-------------------|------|
| `id` | `memory_id` | 自动生成 UUID |
| `title` | `content` (第一句摘要) | 记忆内容 |
| `messages` | 关联的 episodic memories | 每条消息单独存储 |
| `createdAt` | `created_at` | 创建时间 |
| `updatedAt` | `updated_at` | 更新时间 |

**ChatMessage** 作为 episodic memory 存储，包含：
```python
{
    "content": "用户/助手消息内容",
    "metadata": {
        "session_id": "会话ID",
        "role": "user/assistant",
        "message_id": "消息ID"
    }
}
```

### 4.2 Memory 模型映射

**前端 Memory** → **mnemosyne generic memory**

| 前端字段 | mnemosyne 字段 | 说明 |
|----------|---------------|------|
| `id` | `memory_id` | - |
| `title` | `content` (截取前100字) | - |
| `content` | `content` | 完整内容 |
| `status` | `metadata.status` | active/archived/frozen |
| `priority` | `metadata.priority` | low/medium/high/urgent |
| `importance` | `metadata.importance` | 1-5 分，存储在 metadata 中 |
| `tags` | `metadata.tags` | 标签列表 |
| `layer` | `metadata.layer` | semantic/episodic/procedural/working |

**注意**：`score` 字段是向量相似度（0-1），不要与 `importance` 混淆。

### 4.3 Chat 会话存储设计

由于向量存储不支持 metadata 字段过滤，Chat 会话采用**混合存储策略**：

| 数据 | 存储位置 | 说明 |
|------|----------|------|
| ChatSession 元信息 | `SessionStore` (SQLite) | id, title, isPinned, isExpanded, memoryCount, createdAt, updatedAt |
| ChatMessage 内容 | mnemosyne episodic memory | content, metadata.role, metadata.message_id |

**SessionStore 表结构**：
```sql
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_expanded BOOLEAN DEFAULT TRUE,
    memory_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    user_id TEXT NOT NULL
);
```

**检索会话消息时**：
1. 先从 SessionStore 获取会话列表
2. 通过 `user_id` + 时间范围查询 episodic memories
3. 按 `created_at` 排序组合返回

### 4.4 Backend 模型映射

Backend 配置存储在 mnemosyne 的 `metadata` 中：

```python
{
    "provider": "milvus",
    "host": "localhost",
    "port": 19530,
    "database": "default",
    "status": "connected"
}
```

---

## 5. Chat 与 Memory 整合设计

### 5.1 消息存储流程

```
POST /api/v1/chat/sessions/{id}/messages
         │
         ▼
┌─────────────────────────────────┐
│  ChatController.send_message()  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  ChatService.process_message() │
│                                 │
│  1. 存储用户消息为 episodic     │
│     memory.add(msg, user_id,    │
│        metadata={role:user})   │
│                                 │
│  2. 检索相关记忆                │
│     memory.search(query,       │
│        user_id, limit=5)       │
│                                 │
│  3. 组装上下文调用 LLM          │
│                                 │
│  4. 存储助手回复为 episodic    │
│     memory.add(reply, user_id, │
│        metadata={role:assistant})│
└─────────────────────────────────┘
         │
         ▼
    返回给前端
```

### 5.2 LLM 配置

支持可插拔 LLM：

```python
# 环境变量配置
LLM_PROVIDER=deepseek|openai|local

# DeepSeek 配置
DEEPSEEK_API_KEY=xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# OpenAI 配置 (mnemosyne 内部)
OPENAI_API_KEY=xxx
OPENAI_MODEL=gpt-4
```

默认使用 DeepSeek（保持现有行为），可通过 `LLM_PROVIDER` 切换。

### 5.3 记忆上下文组装

检索到的记忆格式化为 LLM 上下文：

```python
def format_memory_context(memories: List[Dict]) -> str:
    """将记忆搜索结果格式化为 LLM 上下文"""
    if not memories:
        return ""

    context_parts = ["相关记忆："]
    for i, mem in enumerate(memories, 1):
        context_parts.append(f"{i}. {mem['content']}")
    return "\n".join(context_parts)

# LLM 调用示例
memory_context = format_memory_context(relevant_memories)
prompt = f"""基于以下记忆回答用户问题：
{memory_context}

用户问题：{user_message}
回答："""
```

### 5.4 Mnemosyne 客户端接口（可测试性）

定义 `MnemosyneClient` 接口，便于单元测试时 mock：

```python
from abc import ABC, abstractmethod

class MnemosyneClient(ABC):
    """mnemosyne 核心接口抽象，用于可测试性"""

    @abstractmethod
    def add(self, content: str, user_id: str, metadata: dict) -> str:
        """添加记忆，返回 memory_id"""
        pass

    @abstractmethod
    def search(self, query: str, user_id: str, limit: int) -> List[Dict]:
        """搜索记忆"""
        pass

    @abstractmethod
    def get(self, memory_id: str) -> Optional[Dict]:
        """获取单条记忆"""
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass

    @abstractmethod
    def update(self, memory_id: str, content: str) -> Dict:
        """更新记忆"""
        pass

# 实际实现
class MnemosyneClientImpl(MnemosyneClient):
    def __init__(self, memory: Memory):
        self._memory = memory

    def add(self, content: str, user_id: str, metadata: dict) -> str:
        return self._memory.add(content, user_id=user_id, metadata=metadata)

    # ... 其他方法实现

# 测试 Mock 实现
class MockMnemosyneClient(MnemosyneClient):
    def __init__(self):
        self._memories = {}

    # ... 返回预设数据
```

---

## 6. 中间件设计

### 6.1 日志中间件

```python
class LoggingMiddleware:
    async def __call__(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host
        )

        response = await call_next(request)

        logger.info(
            "request_end",
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=elapsed_ms
        )
        return response
```

### 6.2 异常处理中间件

```python
@router.exception_handler(AdapterError)
async def adapter_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request.state.request_id
            }
        }
    )
```

### 6.3 性能监控中间件

记录每个请求的：
- 耗时 (duration_ms)
- 数据库查询次数
- 向量检索耗时
- LLM 调用耗时

---

## 7. 配置管理

### 7.1 环境变量

```bash
# 适配器配置
ADAPTER_HOST=0.0.0.0
ADAPTER_PORT=8000
API_PREFIX=/api/v1

# mnemosyne 核心配置 (透传)
STORAGE_BACKEND=local|milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
LOCAL_DB_PATH=./data/mnemosyne.db

# LLM 配置
LLM_PROVIDER=deepseek|openai|local
DEEPSEEK_API_KEY=xxx
OPENAI_API_KEY=xxx

# 可观测性
LOG_LEVEL=INFO
ENABLE_TRACING=true
```

### 7.2 配置文件 (pyproject.toml)

```toml
[project]
name = "mnemosyne-adapter"
version = "0.1.0"

dependencies = [
    # mnemosyne 核心包，通过相对路径引用（本地开发）
    # 容器部署时通过私有 PyPI 或 git URL 安装
    "mnemosyne @ file:///${PROJECT_ROOT}/service",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.5.0",
    "httpx>=0.26.0",
    "structlog>=24.1.0",
    "aiosqlite>=0.19.0",
]
```

### 7.3 回退配置

```bash
# API 回退控制
USE_LEGACY_API=false      # true: 使用旧 server/app/api
USE_ADAPTER_API=true      # false: 停用适配器 API
API_BASE_URL=/api/v1      # 前端 API 基础路径
```

---

## 8. 测试策略

### 8.1 测试覆盖目标

| 层级 | 覆盖内容 | 目标覆盖率 |
|------|----------|-----------|
| 单元测试 | DTO 验证、Mapper 转换、服务逻辑 | 80%+ |
| 集成测试 | API 端点、mnemosyne 交互 | 70%+ |
| E2E 测试 | 前端完整流程 | 100% 关键路径 |

### 8.2 测试用例清单

#### 单元测试

```
tests/
├── unit/
│   ├── test_dto/
│   │   ├── test_chat_dto.py
│   │   └── test_memory_dto.py
│   ├── test_mapper/
│   │   ├── test_chat_mapper.py
│   │   └── test_memory_mapper.py
│   ├── test_service/
│   │   ├── test_chat_service.py
│   │   └── test_memory_service.py
│   └── test_middleware/
│       └── test_error_handler.py
```

#### 集成测试

```
tests/
└── integration/
    ├── test_chat_api.py
    ├── test_memory_api.py
    ├── test_backend_api.py
    └── test_mnemosyne_integration.py
```

#### E2E 测试

```
tests/
└── e2e/
    ├── test_chat_flow.spec.ts
    ├── test_memory_crud.spec.ts
    └── test_regression.spec.ts
```

### 8.3 回归测试场景

| 场景 | 预期结果 |
|------|----------|
| 创建 ChatSession | 返回会话ID，可查询 |
| 发送消息 | 消息存储为 episodic memory |
| 检索记忆 | 返回相关记忆列表 |
| CRUD 记忆 | 数据正确持久化 |
| 切换 LLM | 使用配置的 LLM 生成回复 |

---

## 9. 部署方案

### 9.1 独立部署

```bash
# 启动适配器服务
cd service/mnemosyne/adapter
uvicorn mnemosyne.adapter.main:app --host 0.0.0.0 --port 8000

# 或使用 Docker
docker build -t mnemosyne-adapter .
docker run -p 8000:8000 mnemosyne-adapter
```

### 9.2 挂载到现有 FastAPI 应用

```python
from mnemosyne.adapter.main import create_adapter_app

app = FastAPI()
adapter_app = create_adapter_app()
app.mount("/api/v1", adapter_app)
```

### 9.3 回退机制

详见章节 7.3 回退配置。

前端通过环境变量切换 API：

```bash
# 生产环境使用适配器 API
USE_LEGACY_API=false
USE_ADAPTER_API=true
API_BASE_URL=/api/v1

# 回退到旧 API
USE_LEGACY_API=true
USE_ADAPTER_API=false
API_BASE_URL=/api  # 旧 API 无版本前缀
```

nginx 配置：
```nginx
location /api {
    if ($use_legacy = true) {
        proxy_pass http://legacy-server:8000;
    }
    proxy_pass http://adapter-server:8000;
}
```

---

## 10. 接口对照表

详见附录 A。

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Chat 消息大量存储影响检索性能 | 中 | 设置消息过期策略，定期归档 |
| LLM 调用超时 | 高 | 配置超时重试，优雅降级 |
| 向量存储连接失败 | 高 | 连接池 + 重试机制 |
| 数据模型映射丢失精度 | 中 | 严格 DTO 验证 + 单元测试 |

---

## 12. 下一步计划

1. 创建 `service/mnemosyne/adapter/` 目录结构
2. 实现 DTO 和 Mapper 层
3. 实现 Service 层与 mnemosyne 集成
4. 实现 Controller 和 Router 层
5. 实现中间件（日志、异常、监控）
6. 编写单元测试
7. 编写集成测试
8. 编写 E2E 测试
9. 更新前端 API base URL
10. 执行回归测试

---

## 附录 A：接口对照表

| 原接口 | 新接口 | 变更说明 |
|--------|--------|----------|
| GET /chat/sessions | GET /api/v1/chat/sessions | 添加 v1 前缀 |
| POST /chat/sessions/{id}/messages | POST /api/v1/chat/sessions/{id}/messages | 添加 v1 前缀 |
| GET /memories/ | GET /api/v1/memories/ | 添加 v1 前缀 |
| POST /memories/ | POST /api/v1/memories/ | 添加 v1 前缀 |
| GET /backends/ | GET /api/v1/backends/ | 添加 v1 前缀 |
| POST /backends/connect | POST /api/v1/backends/connect | 添加 v1 前缀 |

**注意**：接口签名（请求/响应格式）保持完全兼容。
