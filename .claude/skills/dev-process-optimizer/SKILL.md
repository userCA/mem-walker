---
name: dev-process-optimizer
description: "通用架构开发流程优化 — 涉及 mnemosyne 跨层协议/架构决策时加载。后端详情见 dev-process-backend，前端详情见 dev-process-frontend。"
---

# 开发流程优化（mnemosyne 总入口）

对本项目的跨层变更或架构决策，先过这篇。纯后端/纯前端问题直接加载对应子 skill。

---

## 架构速查

### 分层依赖

```
┌─────────────────────────────────────────┐
│    React Frontend (web/src/)            │
│  components/ │ hooks/ │ stores/ │ api/  │
└──────────────────┬──────────────────────┘
                   │ HTTP (axios)
                   ▼
┌─────────────────────────────────────────┐
│  FastAPI Adapter (mnemosyne/adapter/)   │
│  router/ │ controller/ │ service/       │
│  dto/ │ mapper/ │ middleware/           │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   Mnemosyne Core (mnemosyne/)           │
│  memory/ │ embeddings/ │ vector_stores/ │
│  graphs/ │ llms/ │ reranker/ │ configs/ │
└─────────────────────────────────────────┘
```

### 数据流全链路

```
API 请求 → router → controller → service → Memory facade
                                              ├─→ MemoryContext (策略)
                                              ├─→ VectorStore (向量搜索)
                                              ├─→ GraphStore (图遍历)
                                              ├─→ Embedding (文本→向量)
                                              ├─→ LLM (事实提取/冲突检测)
                                              └─→ Reranker (BM25 + RRF 融合)
                                                    ↓
                                              DTO ← mapper ← 内部结果
                                                    ↓
                                              JSON 响应 → 前端
```

前端数据流：
```
API 响应 → React Query (缓存) → hook → 组件
状态管理：Zustand stores (UI 状态) + React Query (服务端状态)
```

### 关键原则

1. **双重存储**：Chat messages 同时写 SessionStore（UI 展示）和 Memory（AI 检索），漏写任一侧会导致数据不可见
2. **配置双系统**：`GlobalSettings`（核心库 dataclass）和 `AdapterConfig`（FastAPI Pydantic Settings），通过构造函数参数传递覆盖，不是环境变量覆盖
3. **上下文策略**：`MemoryContext` 是抽象基类，不同策略（Generic/Profile/File）统一接口，不可绕过 facade 直接操作存储
4. **DTO/映射器边界**：内部字典 → Mapper → Pydantic DTO → JSON。前端类型必须与后端 DTO 字段对齐

---

## 子 Skill 索引

**后端问题** → 加载 `dev-process-backend`
- BM25 状态不重复（Reader/Writer 共享一个 BM25Calculator）
- 向量存储方法不可静默忽略参数
- FAISS 伪删除内存泄漏
- 配置链路端到端追踪
- LLM 接口不违反 ISP
- Milvus 集合迁移安全性
- DTO/Mapper 一致性
- 错误处理先日志再传播

**前端问题** → 加载 `dev-process-frontend`
- API 端点与后端对齐（前端定义的端点后端必须有）
- Zustand store 职责分离（UI 状态 vs 服务端数据）
- React Query 键稳定性
- 生产代码无 debug 日志
- 类型定义与后端 DTO 同步
- 组件条件渲染模式

---

## 使用方式

```
1. 这是跨层/架构问题？→ 读本文 + 对应子 skill
2. 纯后端（adapter/ memory/ vector_stores/ embeddings/ graphs/）？→ dev-process-backend
3. 纯前端（web/src/ components/ hooks/ stores/）？→ dev-process-frontend
4. 不确定？→ 先读本文，再按涉及的文件判断
```

---

## 内容维护规则

### 新增规则的三问

新增一条规则之前，必须三个都是"是"：

1. **真重复过？** — 同一个错误至少出现过两次，或者一次但后果是灾难性的（数据丢失、全线崩溃）
2. **能说清怎么办？** — 规则必须包含具体的检测方法或操作步骤
3. **现在还有用？** — 涉及的代码/模块还存在

### 合并优先

新案例能归入已有规则时，追加案例到已有规则，不新建规则。

### 条数上限

每个子 skill ≤ 12 条规则。超过时合并最相似的、删除最过时的。
