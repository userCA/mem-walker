# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述 / Project Overview

Mnemosyne 是一个用于 AI 应用的全息认知记忆系统，采用双层记忆架构：情景记忆（向量）+ 语义记忆（图）。系统由 Python 后端（FastAPI 适配器 + 核心记忆库）和 React 前端组成。

Mnemosyne is a holographic cognitive memory system for AI applications with a two-layer memory architecture: Episodic (vector) + Semantic (graph). The system consists of a Python backend (FastAPI adapter + core memory library) and a React frontend.

### 项目阶段 / Project Phases

- [x] Phase 1: 本地文件记忆能力扩展 / Local file memory capability
- [x] Phase 2: 后端 API 修复与前端对接 / Backend API fixes and frontend integration
- [ ] Phase 3: 性能优化与回归检测 / Performance optimization and regression detection

### 最近进度 / Recent Progress

- **2026-04-15**: 实现 DuckDBGraphStore - 轻量级图存储，无需额外部署数据库
- **2026-04-05**: 实现记忆矛盾检测功能 (Knowledge Conflict Detection)
- **2026-03-24**: Playwright MCP 配置完成，Chromium 浏览器已安装
- **2026-03-23**: 重构后端架构，移除旧 FastAPI 服务，改用 mnemosyne-adapter
- **2026-03-22**: 完成记忆对话功能 + DeepSeek AI 集成
- **2026-03-21**: 完成 AI 工程评估工作流
- **2026-03-20**: 完成 SQLiteVectorStore + FAISSIndexManager
- **2026-03-20**: 完成 FileMemoryContext
- **2026-03-20**: 完成单元测试 (38 tests passing)

---

## 常用命令 / Common Commands

### Backend (service/)

```bash
cd service

# Install dependencies
poetry install

# Run the FastAPI server
poetry run uvicorn mnemosyne.adapter.main:app --reload --port 8000

# Run tests
poetry run pytest
poetry run pytest tests/integration/ -v  # Integration tests only

# Code quality
poetry run black mnemosyne/           # Format
poetry run ruff mnemosyne/            # Lint
poetry run mypy mnemosyne/            # Type check
```

### Frontend (web/)

```bash
cd web

# Install dependencies
npm install

# Development
npm run dev          # Start dev server

# Build & quality
npm run build        # Type check + build for production
npm run lint         # ESLint
npm run type-check   # TypeScript only
```

### Evaluation Workflow

```bash
# Install pre-commit hook
python evaluation/install_hook.py

# Initialize session (run at start of each session)
python evaluation/session_init.py
```

---

## 架构 / Architecture

```
┌─────────────────────────────────────────┐
│         React Frontend (web/)           │
│  Components │ Hooks │ Zustand │ React Query │
└──────────────────┬──────────────────────┘
                   │ HTTP (axios)
                   ▼
┌─────────────────────────────────────────┐
│    FastAPI Adapter (mnemosyne/adapter/) │
│  Controllers │ Services │ DTOs │ Mappers │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      Mnemosyne Core (mnemosyne/)        │
│  Memory │ Embeddings │ VectorStores │    │
│  Graphs │ LLMs │ Reranker                 │
└─────────────────────────────────────────┘
```

### 关键目录 / Key Directories

- `service/mnemosyne/adapter/` - FastAPI REST API layer
- `service/mnemosyne/memory/` - Core memory facade and storage
- `service/mnemosyne/vector_stores/` - Vector storage (Milvus, SQLite+FAISS)
- `service/mnemosyne/embeddings/` - Text embedding providers
- `service/mnemosyne/graphs/` - Knowledge graph (Neo4j, DuckDB)
- `service/mnemosyne/reranker/` - Result reranking (BM25, CrossEncoder)
- `web/src/components/` - React UI components by domain
- `evaluation/` - AI engineering evaluation workflow

### 双重存储模式 / Dual Storage Pattern

Chat messages use dual storage:
- **SessionStore (SQLite)** - Messages for UI display
- **Memory (mnemosyne)** - Episodic memories for AI retrieval

### 记忆上下文策略 / Memory Contexts

Different strategies in `memory/contexts/`:
- `GenericMemoryContext` - Default fact/experience memory
- `ProfileMemoryContext` - User profile knowledge base
- `FileMemoryContext` - Local file memory

---

## 入口点 / Entry Points

- Backend API: `service/mnemosyne/adapter/main.py` - `create_app()` factory
- Core Memory: `service/mnemosyne/memory/main.py` - `Memory` facade class
- Frontend App: `web/src/main.tsx` - React entry point

---

## 环境变量 / Environment Variables

Required for backend (see `service/.env.example`):
- `OPENAI_API_KEY` - OpenAI API key
- `MILVUS_HOST`, `MILVUS_PORT` - Milvus (optional, SQLite+FAISS default)
- `NEO4J_URI`, `NEO4J_PASSWORD` - Neo4j graph store
- `DUCKDB_PATH` - DuckDB graph store path (default: `:memory:`)

Frontend connects to `http://localhost:8000` by default.

---

## 虚拟环境 / Virtual Environment

**重要**: 所有依赖安装和运行都在 `.venv-milvus` 虚拟环境中：

```bash
# 激活虚拟环境
source .venv-milvus/bin/activate

# 安装依赖（项目根目录）
pip install -e service/

# 运行后端
cd service && uvicorn mnemosyne.adapter.main:app --reload --port 8000

# 运行测试
pytest service/tests/
```

---

## 关键模式 / Key Patterns

1. **Facade Pattern**: `Memory` class in `memory/main.py` coordinates all components
2. **DTO/Mapper Pattern**: Adapter transforms internal models ↔ API responses
3. **Dependency Injection**: Services receive deps via constructor
4. **Repository Pattern**: Vector/graph stores abstract data persistence

---

## 扩展点 / Extension Points

- Custom embeddings: Extend `EmbeddingBase` class
- Custom vector stores: Extend `VectorStoreBase` class
- Custom rerankers: Implement reranking interface
- Custom memory contexts: Extend `MemoryContext` base class

---

## 已解决问题 / Resolved Issues

| 问题 / Issue | 解决方案 / Solution |
|-------------|-------------------|
| Memory DTO 缺少 access 字段 | 添加 MemoryAccess 类 |
| /memories/tags 404 | 已添加到 memory_controller |
| /memories/layers 404 | 已添加到 memory_controller |
| 向量维度不匹配 | 使用 SQLiteVectorStore(384) |
| Chat messages 不显示 | 双重存储架构 |
| CORS policy 错误 | 配置 localhost:3000/3001 |

---

## 评估门禁规则 / Evaluation Gate Rules

### Blocking (必须通过)
- [ ] 所有单元测试通过
- [ ] 测试覆盖率 >= 80%
- [ ] P95 延迟回归 < 10%

### Non-blocking (建议通过)
- [ ] P99 延迟回归 < 15%
- [ ] 代码覆盖率提升

---

## 性能基线 / Performance Baseline

| 指标 / Metric | 基线 / Baseline | 最后更新 / Last Updated |
|--------------|----------------|------------------------|
| P95 延迟 / P95 Latency | TBD | 待建立 |
| P99 延迟 / P99 Latency | TBD | 待建立 |
| 测试覆盖率 / Test Coverage | TBD | 待建立 |
| 测试通过率 / Test Pass Rate | 100% (38 passed, 2 skipped) | 2026-03-21 |

---

## 会话初始化协议 / Session Init Protocol

新会话开始时：
```bash
# 1. 读取项目状态 / Read project status
cat CLAUDE.md

# 2. 读取当前性能基线 / Read current baseline
cat evaluation/baselines/.baseline.json

# 3. 查看最近提交 / Check recent commits
git log --oneline -10

# 4. 查看错误日志 / Check mistake log
cat docs/mistake-log.md 2>/dev/null || echo "No mistake log yet"

# 5. 查看评估报告 / Check evaluation report
cat evaluation/reports/latest.json 2>/dev/null || echo "No report yet"

# 6. 查看工作日志 / Check worklogs (重要!)
ls -la evaluation/worklogs/
cat evaluation/worklogs/$(ls -t evaluation/worklogs/ | head -1)
```

---

## Integration Safety Checks / 集成安全检查

在进行 API 变更（端点、DTO 或数据库模式）后，始终通过检查以下内容来验证前端集成：
1. 响应中缺失字段
2. datetime 格式不匹配
3. 端点 URL 一致性

如果不确定，在继续之前询问。

---

## Debugging Protocol / 调试协议

在调试问题时，系统地检查：
1. 后端是否实际可访问/已连接？
2. 是前端状态问题还是后端数据问题？
3. 是 CSS/可见性问题（检查对比度、背景色）？

在假设来源之前测试每一层。

---

## Post-Implementation Tasks / 实施后任务

在完成任何功能实现或配置变更后：
1. 立即更新相关文档文件（CLAUDE.md、README.md、docs/）
2. 更新状态/进度标记
3. 然后再认为任务完成

---

## Edit Discipline / 编辑纪律

优先进行有针对性的最小编辑而非大规模重写。如果单个任务需要超过 10 次编辑：
1. 暂停并总结建议的更改
2. 然后再继续

就架构变更请求确认。
