# Mistake Log

> 本项目真实 bug 和反模式记录，作为 dev-process skill 的规则来源。
> 格式：**日期** | 反模式 | 位置 | 后果 | 预防规则

---

## 2026-05-31 | sys.path 硬编码 | 5 个测试文件

**位置：** `tests/integration/test_memory_api.py`、`test_backend_api.py`、`test_chat_api.py`、`test_embeddings_integration.py`、`test_reranker_integration.py`

**问题：** 测试文件使用 `sys.path.insert(0, '/Users/yuanbaishu/pythonProject/memory-module/service')` 硬编码本地路径，在其他机器上直接崩溃。

**修复：** 删除所有 sys.path 操作。项目通过 `pip install -e service/` 安装，直接 `from mnemosyne.xxx import` 即可。

**预防：** 编写测试时禁止 `sys.path` 操作。如果包无法正常导入，修复 pyproject.toml 或安装方式，不要靠 path hack 绕过。

---

## 2026-05-31 | BM25 状态重复 | `memory/storage.py`

**位置：** `_MemoryReader` (L92) 和 `_MemoryWriter` (L384) 各自创建 `BM25Calculator` 实例。

**问题：** Reader 和 Writer 维护分离的语料库 IDF 统计。Writer 新增文档后 Reader 的 IDF 不更新，查询稀疏向量质量下降。

**状态：** 待优化。应将 BM25Calculator 提升到 `_MemoryLifecycle` 或 `Memory` facade 统一持有。

**预防规则：** dev-process-backend 规则 1。

---

## 2026-05-31 | SQLiteVectorStore 静默丢弃参数 | `vector_stores/sqlite.py` L121

**位置：** `SQLiteVectorStore.insert()` 方法签名接受 `bm25_vectors: Optional[List] = None`，但方法体内完全忽略，注释 `# BM25 vectors not supported in SQLite`。

**问题：** 调用者传入 BM25 向量后被静默丢弃，产生"功能已生效"的虚假安全感。

**修复思路：** 应 `raise NotImplementedError("SQLiteVectorStore does not support BM25 vectors")`，或记录 warning 日志。

**预防规则：** dev-process-backend 规则 2。

---

## 2026-05-31 | FAISS 伪删除内存泄漏 | `vector_stores/faiss_manager.py` L124-147

**位置：** `FAISSIndexManager.delete_vector()` 使用伪删除（ID 加 `_DELETED_` 前缀），SQLite 搜索过滤这些条目，但 FAISS 索引本身持续增长。

**问题：** 大量增删后搜索性能退化，索引膨胀。

**修复思路：** 当删除比例超过阈值时触发全量索引重建；或新向量存储后端实现真删除。

**预防规则：** dev-process-backend 规则 3。

---

## 2026-05-31 | 配置双系统不一致 | `configs/settings.py` + `adapter/config.py`

**位置：** `GlobalSettings.from_env()` (核心库) 和 `AdapterConfig` (FastAPI) 各读一遍环境变量。

**问题：** Adapter 通过构造函数参数覆盖核心库配置，但 `Memory.__init__` 仍会调用 `GlobalSettings.from_env()` 加载不会被使用的值。两个系统不同步。

**预防规则：** dev-process-backend 规则 4。

---

## 2026-05-31 | LLMBase ISP 违规 | `llms/base.py`

**位置：** `LLMBase` 定义 `generate`、`extract_facts`、`extract_entities`、`detect_conflicts` 四个方法。

**问题：** 不是每个 LLM 都需要冲突检测或实体提取。`storage.py` L239-241 用 try/except 兜底 `NotImplementedError`——说明调用者预期方法可能不存在，这正是接口膨胀的信号。

**修复思路：** 将 `detect_conflicts` 和 `extract_entities` 拆分为独立 strategy/mixin。

**预防规则：** dev-process-backend 规则 5。

---

## 2026-05-14 | Milvus 集合静默重建导致数据丢失 | `vector_stores/milvus.py`

**位置：** `_init_collection()` 检测到 schema 不匹配时（如 partition key 变化），调用 `utility.drop_collection()` + `create_collection()`。

**问题：** 服务启动时静默删除集合并重建，所有已持久化数据丢失。用户毫无感知。

**相关 commits：** `4848884`、`dc17c08`、`6978fba`

**修复：** 添加 `_needs_rebuild()` 方法检测，记录 warning 日志。但生产环境仍需迁移脚本。

**预防规则：** dev-process-backend 规则 6。

---

## 2026-05-14 | Flush 禁用导致数据搜索不到 | `vector_stores/milvus.py`

**Commit:** `cecffde`

**问题：** Milvus 在 insert 后需要 `flush()` 才能使数据在搜索中可见，之前被禁用。

**预防：** 修改向量存储写入逻辑后，必须验证写入后立即可搜索。

---

## 2026-05-14 | Chat 消息双写不同步 | `adapter/service/chat_service.py`

**位置：** Chat 消息需同时写入 SessionStore (SQLite, UI 展示) 和 Memory (向量检索)。

**问题：** 新增写入路径时可能只写一侧，导致消息在 UI 不可见或 AI 检索不到。

**预防规则：** dev-process-backend 规则 9。

---

## 2026-05-14 | BM25 非确定性哈希 | `memory/bm25_calculator.py`

**Commit:** `fe8b8b2`

**问题：** 非确定性哈希导致稀疏向量索引不一致，搜索返回错误结果。

**修复：** 使用确定性 MD5 哈希 + 添加 None 检查和分词验证。

**预防：** 涉及哈希的场景必须确认确定性，尤其是用于索引/去重时。

---

## 2026-05-14 | 去重哈希不一致 | `memory/storage.py`

**Commit:** `f452542`

**问题：** 内容哈希去重因哈希算法不一致而断裂，导致重复记忆写入。

**修复：** 统一使用确定性 MD5 哈希。

---

## 2026-05-14 | 前端 API 端点与后端不对齐 | `web/src/api/chat.ts`

**位置：** 前端 `chatApi` 定义了 `deleteMessage`、`clearSession`、`regenerateMessage` 三个函数，但后端 `chat_controller.py` 没有对应路由。

**问题：** 前端调用返回 404，用户看到模糊的"请求失败"提示。

**状态：** ✅ 已修复 (2026-05-31)。新增 `updateSession`、`deleteSession`、`updateConfig`、`deleteMessage`、`clearMessages`、`regenerateMessage`（reserved）6 个路由。`backend_controller` 新增 `updateConfig` 路由。`memory_controller` 新增 `batch` 路由（reserved）。`SessionStore` 新增 `delete_message`、`clear_messages`、`get_message` 方法。

**预防规则：** dev-process-frontend 规则 1。

---

## 2026-05-14 | 生产代码残留 console.log | `useChat.ts`、`ChatPanel.tsx`

**位置：** `useChat.ts` L25-38 和 `ChatPanel.tsx` 组件中。

**问题：** 调试日志在生产环境控制台输出噪音，且可能泄露敏感数据。

**状态：** ✅ 已修复 (2026-05-31)。清除 26 处 `console.log`/`console.debug`（ChatPanel 11 处、ChatMessage 6 处、useChat 6 处）。`useUI.ts` 中 2 处 `console.warn` 改为 `console.error`（生产保留）。

**预防规则：** dev-process-frontend 规则 4。

---

## 2026-04-15 | 向量维度不匹配 | `vector_stores/sqlite.py`

**问题：** 更换 embedding 模型后向量维度变化，SQLiteVectorStore 未重建索引，搜索返回错误结果。

**修复：** 使用 `SQLiteVectorStore(384)` 明确指定维度，维度不匹配时抛异常。

---

## 2026-04-14 | Milvus 测试 Flaky | tests

**Commit:** `7955af7`

**问题：** 并行测试使用固定集合名称导致竞态条件，测试随机失败。

**修复：** 使用动态集合名称 + 每个测试独立集合。

---

## 2026-04-14 | 抽象方法违约 | `vector_stores/base.py`

**Commit:** `667d4cc`

**问题：** `bm25_search` 作为抽象方法定义在 `VectorStoreBase`，强制所有子类实现，即使不支持 BM25。SQLite 被迫提供 stub。

**修复：** 改为非抽象方法，默认 `raise NotImplementedError`。
