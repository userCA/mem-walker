# 🌌 Project Mnemosyne: 全息认知记忆架构 (Holographic Cognitive Architecture)

> "真正的记忆不是对过去的存储，而是对自我的动态重构。"

本设计代表了 AI 记忆系统的巅峰——**全息认知架构 (Holographic Cognitive Architecture)**。它超越了简单的 RAG，模拟了人类大脑在瞬时感知、情景落地和晶体智慧之间流动的能力，创造了一个不仅仅是“记录”，而且会“进化”的 AI。

---

## 1. 核心哲学：活体印记 (The Living Engram)

我们拒绝静态的“数据库”隐喻。记忆是一个有机体。
*   **流动性 (Fluidity)**：信息不是静止的；它从 **热 (感知)** 流向 **温 (情景)**，再流向 **冷 (语义)**，最后成为 **冰 (直觉)**。
*   **全息性 (Holography)**：每一个记忆碎片都与整体相连。提取一个节点会牵动整个相关的上下文图谱 (GraphRAG)。
*   **熵 (Entropy)**：遗忘与记忆同等重要。系统主动“修剪”噪音以防止认知过载，将庞大的经历压缩为高效的启发式规则。

---

## 2. 四层认知栈 (The 4-Layer Cognitive Stack)

### ⚡️ Layer 1: 感知缓冲区 (Sensory Buffer / Working Memory)
*   **类比**: 前额叶皮层 (Prefrontal Cortex)。
*   **功能**: 容纳即时的“意识流”。处理用户当前思维链的原始、混乱输入。
*   **技术**: **Redis Streams** (时间窗口，例如最近 5 分钟或 20 轮)。
*   **特性**: **瞬时性**。如果不被关注，这里的数据会瞬间消失。这是唯一用户可直接写入的层级。

### 🎬 Layer 2: 情景流 (Episodic Stream / Hippocampus)
*   **类比**: 海马体 (Hippocampus)。
*   **功能**: "我记得当时..."。将原始经历存储为时间序列事件。
*   **技术**: **Milvus** (Partition: `episodic_stream`) + **MongoDB** (Raw Logs)。
*   **特性**: **时序性**。高度依赖时间索引。它是“发生了什么”的**事实源头 (Source of Truth)**，但不一定是“真理”（因为用户可能撒谎或变卦）。

### 🕸️ Layer 3: 语义网 (Semantic Web / Neocortex)
*   **类比**: 新皮层 (Neocortex)。
*   **功能**: "我知道..."。提炼后的事实、关系和用户模型。
*   **技术**: **LlamaIndex PropertyGraphIndex** (后端可接 **Neo4j** 或 **NetworkX**)。
*   **特性**: **关系性**。它将“我吃了一个苹果”和“我吃了一个梨”去重为 `User -> Likes -> Fruit`。它通过“真理维护系统”解决冲突（认知失调）。

### 🔮 Layer 4: 直觉层 (Intuition / Procedural)
*   **类比**: 基底核 (Basal Ganglia)。
*   **功能**: "我感觉..." 或 "我知道怎么做..."。高维向量代表的“直觉”、风格迁移和隐性偏见。
*   **技术**: **LlamaIndex PostProcessors** (动态注入 System Prompt) 或 **Fine-tuned LoRA**。
*   **特性**: **反射性**。这一层不返回文本；它修改*权重*或*系统提示词*，隐式地改变 AI 的性格和语气。

---

## 3. "做梦" 过程 (System 2 Consolidation)

奇迹发生在用户*不*说话的时候。系统进入 **默认模式网络 (DMN)** 状态。我们将使用 **LlamaIndex Workflows (Event-Driven)** 来实现这一轻量级编排。

### Phase A: 固化流水线 (Consolidation Pipeline)
1.  **提取 (Extraction)**: 一个 LlamaIndex Agent 扫描 L1 (感知) 和 L2 (情景) 中的新实体和断言。
2.  **图谱嫁接 (Graph Grafting)**: 新节点尝试挂载到 L3 图谱上。
    *   *冲突*: 用户昨天说“我爱猫”，今天说“我讨厌猫”。
    *   *解决*: 系统将其标记为 **认知失调 (Cognitive Dissonance)**。创建一个“冲突节点”，在下次对话中解决（“等等，我以为你讨厌猫？”）。
3.  **压缩 (Compression)**: 重复的情景被压缩为一个带有权重计数器的语义节点。
4.  **修剪 (Pruning)**: 低权重、无情感的记忆被标记为“归档”（移至冷存储，从活跃索引中移除）。

### Phase B: 生成式回放 (The "Dream")
*   系统基于新记忆生成 *假设性* 问题来测试自己的检索能力。
*   如果无法检索到正确的记忆，它会重新索引或提升权重。这是 **自监督学习 (Self-Supervised Learning)**。

---

## 4. 检索算法："全息搜索" (Holographic Search)

我们不仅仅是“搜索向量”。我们执行由向量相似度引导的 **多跳图游走 (Multi-Hop Graph Walk)**。

1.  **锚点识别**: 识别用户查询中的关键实体（如 "Alice", "Project X"）。
2.  **图谱扩展 (BFS)**: 在 L3 (Graph) 中从这些锚点出发，游走 1-2 跳以发现相关概念。
3.  **向量重排序**: 使用查询向量对这些扩展节点的相关性进行评分。
4.  **时间增强**: 提升那些在时间上聚集在检索到的 L3 节点周围的 L2 (情景) 节点（例如，“当我们讨论 Project X 时，我们还说了什么？”）。
5.  **合成**: 上下文窗口被填充为一个结构化的叙事：“我们从 [Episode T1] 知道 [Fact A] 和 [Fact B]，但在 [Episode T2] 中存在冲突。”

---

## 5. 记忆保留数学模型

$$ R(m) = \frac{1}{1 + e^{-(\alpha \cdot I + \beta \cdot C + \gamma \cdot S - \delta \cdot T)}} $$

*   $R(m)$: 保留概率 (0-1)。
*   $I$ (Importance): 信息的内在价值（例如，“我的密码是...” vs “嗨”）。
*   $C$ (Connectivity): 知识图谱中的度中心性。孤立的事实会消亡；连接的事实会存活。
*   $S$ (Sentiment): 情感效价的绝对值。创伤和极乐具有极高的粘性。
*   $T$ (Time): 自上次*有意义*访问以来的时间（不仅仅是读取，而是*有用*的检索）。

---

## 6. 技术栈推荐 (Lightweight & Powerful)

*   **Orchestration**: **LlamaIndex Workflows** (轻量级、事件驱动的 Agent 编排)。
*   **Vector Store**: **Milvus** (海马体 - 高性能向量检索)。
*   **Graph Store**: **Neo4j** (新皮层 - 复杂关系) 或 **SimpleGraphStore** (轻量级)。
*   **Fast Cache**: **Redis** (前额叶 - 工作记忆)。
*   **Embedding**: OpenAI text-embedding-3-small 或 BGE-M3。