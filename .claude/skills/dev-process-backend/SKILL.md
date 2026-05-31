---
name: dev-process-backend
description: "mnemosyne 后端开发流程规范（Python/FastAPI）—— dev-process-optimizer 的子 skill。预防：BM25 状态重复、向量存储静默丢参、FAISS 内存泄漏、配置断裂、LLM 接口膨胀、Milvus 破坏性迁移。覆盖：adapter/ memory/ vector_stores/ embeddings/ graphs/ llms/ reranker/。"
---

# 后端开发流程规范（mnemosyne）

> 子 skill，架构/跨层问题先看 `dev-process-optimizer`。

防止重复犯错。每条规则源于 mnemosyne 项目真实 git 历史和代码审查发现。

---

## 修改前快速检查

```
□ 改动涉及 vector_stores/？检查基类 VectorStoreBase 的所有子类是否同步
□ 新增 DTO 字段？确认 mapper 也处理了该字段，且前端 types/ 有对应类型
□ 改动涉及 Memory facade？确认 Generic/Profile/File 三个 context 都兼容
□ 新增配置项？追踪：AdapterConfig → Memory.__init__ → 实际使用点
□ 改动涉及 chat 消息？确认 SessionStore（UI）和 Memory（AI）双写路径
```

---

## 规则 1：BM25 状态不重复 —— Reader/Writer 共享一个 BM25Calculator

**模式：** `_MemoryReader` 和 `_MemoryWriter` 各自实例化 `BM25Calculator`，维护分离的语料库统计。IDF 数据在读写之间不共享，查询向量质量下降。

**真实案例：** `storage.py` 第 92 行和第 384 行各自创建 `BM25Calculator()` 实例。Reader 的 IDF 统计基于写入时的数据快照，Writer 新增文档后 Reader 的 IDF 不会更新。

**检查清单：**
- BM25Calculator 应该由 `_MemoryLifecycle` 或 `Memory` facade 持有，传入 Reader 和 Writer
- grep `BM25Calculator()` 在 `memory/storage.py` 中 —— 应该只有一处实例化
- 如果必须保留两个实例，Writer 更新后必须同步 IDF 到 Reader

---

## 规则 2：向量存储方法不可静默忽略参数

**模式：** 基类或接口定义了方法签名，子类接受了参数但静默忽略，不抛异常也不警告。调用者以为功能生效，实际上数据被丢弃。

**真实案例：** `SQLiteVectorStore.insert()` 接受 `bm25_vectors: Optional[List] = None` 参数但完全忽略（`sqlite.py` 第 121 行注释 `# BM25 vectors not supported in SQLite`）。调用者传入 BM25 向量但被静默丢弃。

**检查清单：**
- 实现 `VectorStoreBase` 子类时，不支持的方法应显式 `raise NotImplementedError` 并说明原因
- 或者提供默认实现而非静默吞参
- grep 每个 `VectorStoreBase` 子类的 `insert()` / `search()` —— 参数列表中每个参数都在方法体中出现了吗？

---

## 规则 3：FAISS 伪删除会泄漏内存 —— 定期重建索引

**模式：** `FAISSIndexManager.delete_vector()` 使用伪删除（ID 加 `_DELETED_` 前缀），SQLite 搜索过滤掉这些条目，但 FAISS 索引本身持续增长。

**真实案例：** `faiss_manager.py` 第 124-147 行的 `delete_vector()` 只标记删除不实际移除向量。大量增删后 FAISS 索引膨胀，搜索变慢。

**检查清单：**
- 涉及 FAISS 删除逻辑时，确认是否有重建索引的机制（如达到删除阈值后全量重建）
- 长期运行场景测试：增删 1000 次后搜索延迟是否退化
- 新增向量存储后端时：删除必须是真删除，或至少有后台压缩机制

---

## 规则 4：配置链路端到端追踪

**模式：** 两个配置系统并存 —— `GlobalSettings`（核心库 dataclass，`from_env()`）和 `AdapterConfig`（FastAPI Pydantic Settings）。Memory 构造函数接受可选参数覆盖默认值，但也会调用 `GlobalSettings.from_env()`。配置可能在多个环节被覆盖或忽略。

**真实案例：** `adapter/main.py` 第 37-54 行通过构造函数参数传入自定义 embedding/vector_store，覆盖 `GlobalSettings` 中的对应配置。但 `Memory.__init__` 第 71-72 行仍调用 `GlobalSettings.from_env()`，加载了不会被使用的值。

**检查清单：**
- 新增配置项时，端到端追踪：
  ```
  环境变量 → AdapterConfig 字段 → Memory.__init__ 参数 → GlobalSettings 字段 → 实际使用点
  ```
- 确认配置只在**一处**读取，避免 AdapterConfig 和 GlobalSettings 各读一遍
- grep 新增配置字段名 —— 如果两处都出现，确认语义一致

---

## 规则 5：LLM 接口不违反接口隔离原则（ISP）

**模式：** `LLMBase` 接口包含 `generate`、`extract_facts`、`extract_entities`、`detect_conflicts` 四个方法。并非每个 LLM 实现都需要知道如何检测冲突或提取实体。强制实现会催生 stub 或 `NotImplementedError`。

**真实案例：** `llms/base.py` 定义了 `detect_conflicts` 抽象方法。`storage.py` 第 239-241 行用 try/except 兜底 `NotImplementedError`。这说明接口本身就是设计问题 —— 调用者预期方法可能不存在。

**检查清单：**
- 给 `LLMBase` 新增方法前问：每个 LLM 子类都需要这个方法吗？
- 如果只有部分子类需要 → 用 mixin 或独立的 strategy 类，不加到基类
- grep `NotImplementedError` 在 `llms/` 中 —— 这些都是接口膨胀的信号

---

## 规则 6：Milvus 集合迁移必须是显式操作而非静默重建

**模式：** `_init_collection` 检测到 schema 不匹配时静默删除旧集合并重建。所有已持久化数据丢失，无警告。

**真实案例：** `vector_stores/milvus.py` 的 `_init_collection()` 在 partition key 变化时触发 `utility.drop_collection()` + `create_collection()`。这发生在服务启动时，对用户完全透明。

**检查清单：**
- 修改 Milvus collection schema 前，必须有数据迁移脚本（导出 → 重建 → 导入）
- `_init_collection()` 中删除集合前必须记录 warning 级别日志
- 生产环境部署 schema 变更前先在 staging 验证迁移脚本

---

## 规则 7：DTO/Mapper 一致性 —— 每个后端字段前端必须可达

**模式：** 后端 DTO 新增字段，mapper 也处理了，但前端 types/ 没同步。前端 TypeScript 编译通过（类型可选），但字段在 UI 上永远不显示。

**真实案例：** `memory_dto.py` 的 `MemoryDTO` 使用 `model_config = {"populate_by_name": True}` 和 `alias` 做 camelCase 转换。mapper 中新增的字段如果没加 alias，前端收到的 JSON key 是 snake_case，与 TypeScript 接口的 camelCase 不匹配。

**检查清单：**
- 后端 DTO 新增字段 → 检查 mapper 是否映射了该字段（grep 字段名在 `adapter/mapper/`）
- 检查前端 `web/src/types/memory.ts`（或对应的类型文件）是否有对应字段
- 如果字段使用 alias，确认 alias 与前端类型 key 一致
- 涉及 datetime 字段时，确认 mapper 中的格式化和前端的解析一致

---

## 规则 8：错误处理 —— 先日志再传播，不静默回退

**模式：** try/except 捕获异常后执行静默回退路径，不记录日志。原始错误被完全隐藏，排查无从下手。

**真实案例：** `storage.py` `_MemoryLifecycle._update_memory_payload()` 在更新失败时捕获裸异常走回退路径，没有日志。Milvus 写入失败时用户看到的是一条"成功"的更新，底层错误无从追踪。

**检查清单：**
- `memory/storage.py` 中每个 `except Exception` 必须有 `_log.exception()` 或至少 `_log.warning()`
- 回退路径必须记录原因："Update via primary path failed, falling back to X"
- grep `except Exception` 在 `memory/` 和 `adapter/service/` —— 每个都要有日志

---

## 规则 9：Chat 消息双重存储 —— 写 SessionStore 和 Memory 必须同步

**模式：** Chat 消息需要同时写入 SessionStore（SQLite，UI 展示用）和 Memory（向量检索用）。只写一边会导致消息在 UI 不可见或 AI 检索不到。

**检查清单：**
- 新增 chat 消息写入路径时，确认 `chat_service.py` 中两处写入都发生
- `SessionStore.add_message()` 失败时不应该阻塞 Memory 写入，反之亦然（独立失败）
- 但需要记录不一致状态用于后台修复

---

## 规则 10：模块级 Logger —— 文件顶部定义一次

**模式：** `logging.getLogger(__name__)` 在函数体内重复调用。每次创建相同 logger 对象，暗示 "logger 是局部资源"。

**修复：**
```python
# 文件顶部，所有 import 之后
_log = logging.getLogger(__name__)
```

**检查：** grep `logging.getLogger(__name__)` 在 `memory/` 和 `adapter/` 中。每个文件只应出现一次（模块级别）。

---

## 规则 11：新增 API 端点必须三端对齐

**模式：** 前端 `api/` 目录定义了 API 函数，但后端 `router/` 没有对应端点。前端调用 404，错误被 catch 后静默吞掉。

**真实案例：** 前端 `chatApi.deleteMessage`、`chatApi.clearSession` 已定义，但后端 `chat_controller.py` 没有对应路由。**状态：✅ 已修复 (2026-05-31)。** 扩展检查发现共 8 个缺失端点（chat 6、backend 1、memory 1），全部补齐。SessionStore 新增 `delete_message`、`clear_messages`、`get_message` 方法。

**检查清单：**
- 新增 API 端点：路由器（`adapter/router/`）→ 控制器（`adapter/controller/`）→ 服务（`adapter/service/`）→ DTO（`adapter/dto/`）全部到位
- 前端 `web/src/api/` 中定义的每个端点函数必须能在后端找到对应路由
- 用 `grep -r "router\." adapter/router/` 核对路由表是否完整

---

## 修改后验证

```
□ pytest service/tests/ —— 全量测试
□ 如果改了 vector_stores 基类 → 确认所有子类（SQLite、Milvus）的对应方法已更新
□ 如果改了 DTO → git diff adapter/dto/ adapter/mapper/ 确认映射一致
□ 如果改了 API 端点 → 核对前端 web/src/api/ 的对应函数
□ 如果改了配置 → 追踪 AdapterConfig → Memory.__init__ → 实际使用点
□ grep 新增字段名 —— 确认有写入点 AND 读取点，不是死代码
□ 如果涉及 Milvus schema 变更 → 确认不是静默 drop collection
```
