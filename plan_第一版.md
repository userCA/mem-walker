# 📅 Project Mnemosyne: 实施计划 (全息版)

> "我们是在构建大脑，而不是数据库。"

## 阶段一：脊髓 (基础设施 & 摄入)
**目标**: 建立双存储基础 (Milvus + Neo4j/Graph) 和基本的摄入流水线。
- [ ] **基础设施**: 配置 Docker Compose 运行 Milvus (Standalone) 和 Neo4j (Community)。
- [ ] **数据层**:
    - 实现 `MilvusHandler`: 负责情景流 (L2) 的读写。
    - 实现 `GraphHandler`: 基于 LlamaIndex `PropertyGraphIndex`，适配 Neo4j 或 SimpleGraphStore。
- [ ] **摄入流水线**:
    - 创建 `MemoryIngestor`: 一个服务，接收原始聊天日志并立即写入 L2 (Milvus)。
    - *验证*: 编写脚本模拟 100 条聊天消息，验证它们是否正确出现在 Milvus 中。

## 阶段二：海马体 (全息检索)
**目标**: 实现查询两个存储并融合结果的“全息搜索”算法。
- [ ] **图谱游走 (Graph Walker)**: 在 `GraphHandler` 中实现 BFS 扩展逻辑。
    - 输入: `["实体 A", "实体 B"]` -> 输出: `[2跳内的相关节点]`。
- [ ] **向量重排序 (Vector Rescoring)**: 实现融合逻辑。
    - 获取图节点 -> 获取其 Embedding -> 计算与查询的余弦相似度 -> 重排序。
- [ ] **统一检索器 (Unified Retriever)**: 暴露一个 `retrieve(query, user_id)` 函数来编排上述过程。
- *验证*: 测试查询“用户对猫的感觉如何？”，确保它能拉取到“讨厌”这一事实 (L3) 和具体的“我讨厌猫”的情景 (L2)。

## 阶段三：默认模式网络 (做梦 & 固化)
**目标**: 使用 **LlamaIndex Workflows** 构建异步的“做梦” Agent。
- [ ] **Dream Weaver (Workflows)**:
    - 定义事件驱动的工作流: `Idle -> Extract -> Graft -> Compress -> Prune -> Idle`。
- [ ] **提取节点 (Extraction Step)**: 编写 Prompt 从最近的 L2 情景中提取实体/断言。
- [ ] **嫁接节点 (Grafting Step)**: 将提取出的信息插入图谱。
    - **关键**: 实现 `ConflictDetector`。如果新事实与旧事实矛盾，创建 `ConflictNode`。
- *验证*: 手动运行“做梦”流程处理一组相互冲突的日志，验证图谱中是否创建了 `ConflictNode`。

## 阶段四：元认知 (自省)
**目标**: 系统自我测试。
- [ ] **生成式回放**: 在做梦循环中实现“自测”步骤。
    - 系统基于新记忆生成一个问题。
    - 系统尝试检索答案。
    - 如果失败，提升权重 (更新 Milvus 中的 `importance` 标量)。

## 依赖库
- `llama-index-core`
- `llama-index-vector-stores-milvus`
- `llama-index-graph-stores-neo4j`
- `pymilvus`
- `neo4j`