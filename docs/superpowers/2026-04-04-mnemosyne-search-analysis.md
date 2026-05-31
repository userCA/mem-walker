# Mnemosyne 检索架构分析

> 创建时间：2026-04-04
> 分析目的：渐进式理解 mnemosyne 混合检索机制

---

## 1. 核心检索流程

### 1.1 架构概览

```
用户 Query
    │
    ▼
┌─────────────────────────────────────┐
│  1. 并行执行                         │
│     - Embedding 生成                │
│     - Entity 提取 (可选)             │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  2. 向量检索 (FAISS/Milvus)         │
│     limit × 2 (扩大候选范围)        │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  3. 图扩展 (可选, BFS depth=2)     │
│     匹配实体 +0.1 分 boost          │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  4. BM25 重排 (如果启用)            │
│     70% 向量分 + 30% BM25 分       │
└─────────────────────────────────────┘
    │
    ▼
  Top-K 结果
```

### 1.2 关键源码位置

| 组件 | 文件位置 | 说明 |
|------|---------|------|
| Memory Facade | `service/mnemosyne/memory/main.py` | 协调所有组件 |
| 核心检索逻辑 | `service/mnemosyne/memory/storage.py` | `_MemoryReader.search()` |
| 记忆上下文 | `service/mnemosyne/memory/contexts/generic.py` | `GenericMemoryContext` |
| 向量存储 | `service/mnemosyne/vector_stores/` | SQLite / Milvus |
| BM25 重排 | `service/mnemosyne/reranker/bm25.py` | 关键词重排 |

---

## 2. 混合检索策略分析

### 2.1 传统 Hybrid Search vs 级联架构

#### 传统 Hybrid Search（同时执行）

```
Query ──┬──> 向量检索 ──┬──> 分数合并 (RRF/weighted) ──> Top-K
        │              │
        └──> 关键词检索 ──┘
```

- **特点**：向量检索和关键词检索同时执行，最后合并分数
- **代表**：Milvus dense+sparse、Elasticsearch knn+bm41

#### 当前系统：级联架构（先向量后重排）

```python
# service/mnemosyne/memory/storage.py (_MemoryReader.search)
results = self.vector_store.search(
    query_vector=query_vector,
    limit=limit * 2,  # 扩大检索范围
    filters={"user_id": user_id}
)
# ...
if self.config.enable_reranking and results:
    results = self.reranker.rerank(str(query), results, top_k=limit)
```

```python
# service/mnemosyne/reranker/bm25.py (BM25Reranker.rerank)
# Weighted combination: 70% original score + 30% BM25 score
combined_score = 0.7 * existing_score + 0.3 * normalized_bm25
```

---

## 3. 为什么选择级联架构？

| 设计选择 | 原因 |
|---------|------|
| **先向量后重排** | 向量检索 O(log N) 很快，用向量缩小范围再用 BM25 精细化 |
| **避免重复索引** | 不需要维护两套索引（dense + sparse） |
| **基础设施简单** | 不需要特殊的混合检索引擎 |
| **级联更灵活** | 可以独立调优向量检索和重排阶段 |

---

## 4. 两种架构对比

| 指标 | 传统混合搜索 | 级联架构（当前） |
|------|------------|----------------|
| **语义相似度** | ✅ 强 | ✅ 强 |
| **关键词匹配** | ✅ 强 | ⚠️ 辅助（重排阶段） |
| **计算成本** | 较高（同时执行） | 较低（向量过滤后重排） |
| **实现复杂度** | 高（需要混合引擎） | 低（独立组件） |
| **调优灵活性** | 低（需要联合调优） | 高（独立调优） |

---

## 5. 何时考虑切换？

### 当前架构的潜在风险

如果相关文档的**向量相似度不高**，可能在第一轮就被过滤掉，无法进入重排阶段。

当前缓解措施：
```python
limit=limit * 2  # 扩大候选范围
```

### 切换信号

如果出现以下情况，考虑引入传统混合搜索：
- [ ] 关键词搜索结果明显优于向量搜索
- [ ] 重要文档频繁被向量检索遗漏
- [ ] 需要同时优化语义和关键词权重

### 切换方案

使用 Milvus 的 `sparse_vector` 支持实现真正的混合搜索：
```python
# 未来可能的实现
search_params = {
    "metric_type": "COSINE",
    "params": {},
    "level": "dense",  # 或 "sparse" 或 "hybrid"
}
```

---

## 6. 关键代码片段

### 6.1 向量检索阶段

```python
# service/mnemosyne/memory/storage.py
async def search(self, query, user_id, limit=5, use_graph=True, **kwargs):
    # 1. 生成 query embedding
    query_vector = self.embedding.embed(query)

    # 2. 向量搜索
    vector_results = self.vector_store.search(
        query_vector=query_vector,
        limit=limit * 2,
        filters={"user_id": user_id}
    )
```

### 6.2 BM25 重排阶段

```python
# service/mnemosyne/reranker/bm25.py
def rerank(self, query: str, results: List[Memory], top_k: int) -> List[Memory]:
    bm25_scores = [self._calculate_bm25(query, r.content) for r in results]
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0

    for i, (result, bm25_score) in enumerate(zip(results, bm25_scores)):
        normalized_bm25 = bm25_score / max_bm25
        combined_score = 0.7 * result.score + 0.3 * normalized_bm25
        result.score = combined_score
```

---

## 7. 后续学习路径

1. **深入向量存储** → `vector_stores/base.py`, `sqlite.py`, `milvus.py`
2. **理解 Embedding** → `embeddings/base.py`, `openai.py`
3. **探索图存储** → `graphs/neo4j.py`
4. **重排机制** → `reranker/bm25.py`, `cross_encoder.py`

---

---

## 8. 理解检验 Q&A

### Q1: `limit=limit * 2` 的目的

**你的回答**：为了防止漏掉关键信息，因为当前是串行检索

**评估**：✅ 基本正确

**补充**：准确说是为了**扩大候选集**，因为后续 BM25 重排需要更多候选进行精细化排序。注意：当前架构是"级联检索"而非简单的串行——Embedding 生成和 Entity 提取是**并行执行**的。

```python
# service/mnemosyne/memory/storage.py
# 并行执行两个任务
query_vector, entities = await asyncio.gather(
    self.embedding.embed(query),
    self._extract_entities(query) if use_graph else None
)
```

---

### Q2: BM25 权重是否可配置？

**你的回答**：可以配置，要根据场景判断，但不知道怎么判断

**评估**：❌ 错误

**补充**：**权重是硬编码的（70/30）**，不可配置。代码中直接写死：
```python
combined_score = 0.7 * existing_score + 0.3 * normalized_bm25
```

目前没有根据场景自动判断的机制。如果需要调整权重，需要修改代码。

---

### Q3: 图扩展触发条件和 boost 分数

**你的回答**：不知道

**评估**：❌ 不知道

**补充**：
- **触发条件**：`use_graph=True`（默认）且 `self.graph_store` 存在
- **boost 分数**：+0.1
- **原理**：通过 LLM 提取 query 中的实体，用 BFS 在图中扩展相关实体，如果记忆内容包含这些实体，分数 +0.1

```python
# service/mnemosyne/memory/storage.py
if use_graph and self.graph_store and entities:
    expanded = self.graph_store.bfs_expand(entities, depth=2)
    # 如果记忆内容包含扩展实体，score + 0.1
    for mem in results:
        if any(e in mem.content for e in expanded):
            mem.score += 0.1
```

---

### Q4: 当前架构与传统 hybrid search 的本质区别

**你的回答**：速度和维护成本，本质是串行还是并行

**评估**：⚠️ 不准确

**补充**：本质区别在于**是否同时执行两种检索**：
- **传统 hybrid**：向量检索和关键词检索**同时执行**，最后用 RRF 或 weighted 合并
- **当前架构**：**先向量检索过滤候选**，再在候选集上用 BM25 重排

当前架构不是纯串行：Embedding 和 Entity 提取是并行的，但向量检索和 BM25 重排是串行的（必须先有向量结果）。

---

### Q5: 向量排名 100 之外的文档是否有机会返回？

**你的回答**：前半说"没有机会"正确，后半说"调整向量权重"不相关

**评估**：✅ 正确

**补充**：确实**没有机会**。因为向量检索阶段只返回 top (limit×2) 结果，排名 100 的文档根本不会进入 BM25 重排阶段。

**这是当前架构的主要风险**：如果相关文档的向量相似度不高，会被直接过滤掉。

---

### Q6: 向量存储实现

**你的回答**：支持 milvus 和 faiss，faiss 更轻量

**评估**：⚠️ 部分正确

**补充**：
- 系统支持 **SQLiteVectorStore**（默认）和 **MilvusVectorStore**
- **FAISS 是 SQLiteVectorStore 内部使用的索引**，不是独立的向量存储实现
- SQLiteVectorStore 内部使用 FAISS 做向量索引，但对外接口是 SQLite
- Milvus 适合企业级高并发，SQLite+FAISS 适合小数据量本地场景

---

### Q7: `enable_reranking` 控制什么？

**你的回答**：✅ 正确，控制是否使用 BM25 重排

**补充**：关闭后系统变为**纯向量检索**，不会有关键词重排。这适合只需要语义相似度、不需要关键词匹配的场景。

---

### Q8: 查询 "Python asyncio 的用法" 的完整流程

**你的回答**：向量化->检索向量数据库->关键词检索->取结果

**评估**：⚠️ 不完整

**补充完整流程**：
```
1. 并行执行：
   - 生成 query embedding
   - LLM 提取实体（如 "Python", "asyncio"）

2. 向量检索：
   - FAISS/Milvus 搜索 top (limit×2)
   - 返回初始排序结果

3. 图扩展（如果 use_graph=True）：
   - BFS 扩展实体节点
   - 匹配到的记忆 +0.1 boost

4. BM25 重排（如果 enable_reranking=True）：
   - 计算每个结果的 BM25 分数
   - combined_score = 0.7×向量分 + 0.3×BM25分

5. 返回 top-K 结果
```

---

### Q9: 何时切换到传统混合搜索？

**你的回答**：不知道

**评估**：❌ 不知道

**补充**：切换信号：
- [ ] 关键词搜索结果明显优于向量搜索
- [ ] 重要文档频繁在向量阶段被遗漏
- [ ] 需要同时优化语义和关键词权重
- [ ] 搜索延迟不是瓶颈，希望提高召回率

**当前缓解措施**：增大 `limit` 参数可以缓解，但有限。

---

### Q10: 实体识别使用什么算法？

**你的回答**：不知道

**评估**：❌ 不知道

**补充**：
- **实体识别**：使用 **LLM（大型语言模型）** 进行提取
- **实现位置**：`service/mnemosyne/memory/storage.py` 的 `_extract_entities()` 方法
- **过程**：将 query 发送给 LLM，让它从中提取实体/关键词

```python
async def _extract_entities(self, query: str) -> List[str]:
    """使用 LLM 从查询中提取实体"""
    prompt = f"从以下文本中提取关键实体（人名、地名、概念等）：{query}"
    response = await self.llm.generate(prompt)
    return parse_entities(response)  # 解析 LLM 返回的实体列表
```

---

---

## 9. 矛盾数据处理（Knowledge Conflict）

### 9.1 问题场景

当知识库中存在矛盾信息时，系统会发生什么？

例如：
```
记忆1: "Python 很难学"
记忆2: "Python 很容易学"
```

### 9.2 当前系统的处理方式

**结论：系统理论上支持矛盾检测，但实际未启用。**

#### 已有的接口（未使用）

系统已经定义了 `detect_conflicts` 接口，但**并未在 `_MemoryWriter.add` 中调用**：

```python
# service/mnemosyne/llms/base.py:73
@abstractmethod
def detect_conflicts(
    self,
    new_fact: str,
    existing_facts: List[str]
) -> Optional[Dict[str, Any]]:
    """Detect conflicts between new and existing facts."""
    pass

# service/mnemosyne/llms/openai.py:179
def detect_conflicts(self, new_fact: str, existing_facts: List[str]) -> Optional[Dict[str, Any]]:
    """Detect conflicts using LLM."""
    # 使用 LLM 判断新事实是否与已有事实矛盾
    # 返回 {"has_conflict": true/false, "conflicting_fact": "...", "reason": "..."}
```

#### 实际发生的情况

```python
# service/mnemosyne/memory/storage.py (_MemoryWriter.add)
# 新数据直接插入，没有任何矛盾检测机制
self.vector_store.insert(
    vectors=[embedding_vector],
    payloads=[payload],
    ids=[memory_id]
)
```

### 9.3 具体行为

| 阶段 | 结果 |
|------|------|
| 插入 | 两个语义相反的向量被存入数据库 |
| 检索 "Python 学习体验" | 可能同时返回两条记忆 |
| 向量相似度 | 两者相似度都**不高**（因为语义相反） |
| BM25 重排 | 取决于查询是否包含 "Python" |

### 9.4 核心问题

- 向量数据库**存储的是语义向量，无法判断真假**
- 没有**时间戳/版本**机制来区分新旧信息
- 没有**真值发现**（Truth Discovery）机制

### 9.5 主流解决方案

#### 1. LLM-based 矛盾检测（mem0 等采用）

```python
# mem0 方案：使用 LLM 判断矛盾
system_prompt = """You are a conflict detection assistant.
Determine if a new fact conflicts with existing facts.
Return JSON: {"has_conflict": true/false, "conflicting_fact": "...", "reason": "..."}"""

# Mnemosyne 已有此接口但未启用
```

**优点**：利用 LLM 语义理解能力
**缺点**：增加延迟和成本

#### 2. Truth Discovery（真值发现）

通过投票机制或置信度传播判断哪个信息更可信：

```
信息来源 A: "Python 很难" (置信度 0.9)
信息来源 B: "Python 很简单" (置信度 0.6)
→ 倾向保留 A，因为 A 的置信度更高
```

#### 3. 时间衰减 + 版本控制

```python
# 重排时考虑时间因子
time_weight = 1.0 / (1.0 + (current_time - created_at).days * decay_rate)
final_score = vector_score * time_weight
```

#### 4. 多向量表示（保留矛盾）

不删除矛盾信息，而是用多个向量表示，让检索时返回多样视角：

```python
# 矛盾信息分别存储
memory: {"content": "Python 很难学", vector_id: "v1", stance: "negative"}
memory: {"content": "Python 很容易学", vector_id: "v2", stance: "positive"}
```

#### 5. Prompt 层面处理（当前 RAG 常用）

让 LLM 在生成回答时自己判断矛盾：

```python
prompt = """基于以下记忆回答问题（注意信息可能存在更新，请综合判断）：
{conflicting_contexts}

问题：{query}"""
```

---

### 9.6 mnemosyne 的缺失

| 功能 | 状态 | 位置 |
|------|------|------|
| `detect_conflicts` 接口定义 | ✅ 已有 | `llms/base.py:73` |
| `detect_conflicts` 实现 | ✅ 已有 | `llms/openai.py:179` |
| 在 add 时调用 | ❌ **缺失** | `_MemoryWriter.add` 未调用 |

**如果要启用矛盾检测，需要在 `_MemoryWriter.add` 的 Phase 2 (Fact Extraction) 之后添加类似逻辑。**

---

## 10. BM25Reranker vs CrossEncoderReranker

### 10.1 为什么默认使用 BM25？

**答案：BM25 更轻量、无需 GPU，适合当前场景。**

### 10.2 对比表

| 指标 | BM25Reranker | CrossEncoderReranker |
|------|-------------|---------------------|
| **模型** | 无（纯统计 BM25 算法） | BERT-based |
| **依赖** | `rank_bm25` | `sentence-transformers` |
| **硬件要求** | CPU 即可 | GPU 加速（推荐） |
| **初始化** | 毫秒级 | 需要下载模型（首次慢） |
| **延迟** | 低 | 较高 |
| **精度** | 中等 | 高 |
| **适用场景** | 轻量、对延迟敏感 | 高精度场景 |

### 10.3 源码证据

```python
# service/mnemosyne/memory/main.py:96
self.reranker = reranker or BM25Reranker(config.reranker_config)
```

默认使用 BM25Reranker。CrossEncoderReranker 存在但需要**显式传入**：

```python
# 使用 CrossEncoder 的方式
from mnemosyne.reranker import CrossEncoderReranker, RerankerConfig

config = RerankerConfig(model_name="BAAI/bge-reranker-base")
reranker = CrossEncoderReranker(config)
memory = Memory(reranker=reranker)
```

### 10.4 CrossEncoder 的优势

CrossEncoder 会将 query 和 document **一起通过 BERT**，能捕捉更精细的语义关系：

```python
# CrossEncoderReranker 内部
pairs = [[query, candidate.get("content", "")] for candidate in candidates]
scores = self.model.predict(pairs)  # 真正的语义交互
```

BM25 只是词频统计，无法理解语义层面的匹配。

---

## 参考

- [Milvus Hybrid Search](https://milvus.io/docs/multi-vector-search.md)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [RRF (Reciprocal Rank Fusion)](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
