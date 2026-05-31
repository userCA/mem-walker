# Development Log

> mnemosyne 开发历史、架构决策和功能缺口记录。
> 格式：**日期** | 类型 | 简述 | 相关 commits

---

## 项目阶段 / Project Phases

| 阶段 | 状态 | 内容 |
|------|------|------|
| Phase 1 | ✅ 完成 2026-03 | 本地文件记忆能力扩展 |
| Phase 2 | ✅ 完成 2026-04 | 后端 API 修复与前端对接 |
| Phase 3 | 🔄 进行中 | 性能优化与回归检测 |

---

## 架构决策记录 / Architecture Decisions

### ADR-001: 双重存储架构 | 2026-03-22

Chat messages 同时写入 SessionStore (SQLite, UI 展示) 和 Memory (mnemosyne 向量+图, AI 检索)。两个写入独立失败，不互相阻塞。不一致状态通过后台修复。

### ADR-002: 适配器层 DTO/Mapper 模式 | 2026-03-22

内部字典 → Mapper → Pydantic DTO (camelCase) → JSON 响应的转换链。Pydantic `populate_by_name=True` + `alias` 处理 snake_case ↔ camelCase。

### ADR-003: 配置双系统 | 2026-03-22

`GlobalSettings` (核心库 dataclass, `from_env()`) 和 `AdapterConfig` (FastAPI Pydantic Settings, `ADAPTER_` 前缀) 分离。Adapter 通过构造函数参数覆盖核心配置。注意：两个系统不同步的风险（见 mistake-log）。

### ADR-004: 上下文策略模式 | 2026-03-20

`MemoryContext` 抽象基类，三种策略：`GenericMemoryContext` (默认)、`ProfileMemoryContext` (用户画像)、`FileMemoryContext` (本地文件)。上层通过 Memory facade 统一调用。

### ADR-005: DuckDB 图存储 | 2026-04-15

新增 `DuckDBGraphStore` 作为轻量级图存储后端，无需部署 Neo4j。支持内存模式和文件持久化。与 Neo4jGraphStore 共享 `GraphStoreBase` 接口。

### ADR-006: BM25 混合搜索 + RRF 融合 | 2026-04-13 ~ 04-14

并行执行向量搜索 + BM25 稀疏向量搜索 + 可选图扩展，通过 Reciprocal Rank Fusion 融合结果。`BM25Calculator` 独立管理语料库 IDF 统计。

### ADR-007: Milvus user_id 分区键 | 2026-04-14

设置 `user_id` 为 Milvus partition key，实现租户隔离，扫描量减少 90%+。风险：partition key 变更触发集合静默重建导致数据丢失（见 mistake-log）。

### ADR-008: 项目结构整合 | 2026-05-31

消除根目录与 service/ 之间的重复：删除 service/.venv (用 .venv-milvus)，合并测试目录到 service/tests/，删除重复的缓存和产物目录。详见 commit `2c9a40e`。

---

## 功能演进 / Feature Evolution

### 2026-03

- **03-20**: SQLiteVectorStore + FAISSIndexManager 完成
- **03-20**: FileMemoryContext 完成
- **03-20**: 单元测试 38 通过，2 跳过
- **03-21**: 记忆对话功能 + DeepSeek AI 集成
- **03-22**: 重构后端架构，移除旧 FastAPI，迁移到 mnemosyne-adapter
- **03-23**: Chat 消息双重存储架构
- **03-24**: Playwright MCP 配置

### 2026-04

- **04-04**: 记忆搜索分析 (`docs/superpowers/2026-04-04-mnemosyne-search-analysis.md`)
- **04-05**: 记忆矛盾检测 (Knowledge Conflict Detection)
- **04-13**: 混合搜索设计规范 (`docs/superpowers/plans/`)
- **04-14**: BM25 预计算计划，Milvus userId 分区计划
- **04-15**: DuckDBGraphStore 实现

### 2026-05

- **05-14**: BM25 确定性哈希修复，去重哈希修复，Milvus flush 修复
- **05-31**: 项目结构整合优化，dev-process skill 创建，mistake-log 和 development-log 初始化
- **05-31**: 前端问题修复：清除 26 处 console.log，CSS 硬编码颜色替换为设计令牌，补全 8 个后端缺失端点（chat 6 + backend 1 + memory 1）

---

## 功能缺口 / Feature Gaps

| 缺口 | 优先级 | 备注 |
|------|--------|------|
| `_MemoryReader`/`_MemoryWriter` BM25Calculator 状态共享 | 高 | 影响 BM25 查询质量 |
| SQLiteVectorStore bm25_vectors 静默丢弃 | 中 | 虚假安全感 |
| FAISSIndexManager 伪删除 → 定期重建索引 | 中 | 长期运行性能退化 |
| LLMBase ISP 拆分（detect_conflicts 独立） | 中 | 接口膨胀 |
| Milvus schema 迁移脚本 | 高 | 生产部署阻塞项 |
| 前端缺失端点（deleteMessage, clearSession 等） | ✅ 已修复 2026-05-31 | 新增 6 个 chat + 1 个 backend + 1 个 memory 路由 |
| 测试覆盖率不足（BM25、去重、Milvus、Mapper） | 高 | 见 mistake-log 高频出错区域 |
| BM25 IDF 持久化加载时机 | 低 | save/load 已实现，启动流程待优化 |

---

## 工作日志 / Worklog Index

`evaluation/worklogs/` 中的工作日志：
- `2026-04-05-conflict-detection.md` — 冲突检测实现
