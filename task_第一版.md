# Mnemosyne 低延迟优化任务

## 目标
将 Search 延迟从当前的 1.5s-2.5s (P95) 降低至 < 300ms

## Phase 1: 快速见效优化 ⏱️ 1周
- [ ] 1.1 实现本地小模型 (LocalSLM)
  - [ ] 创建 `llms/local_slm.py`
  - [ ] 使用 llama-cpp-python + Qwen2.5-0.5B
  - [ ] 实现 `extract_entities()` 方法
- [ ] 1.2 实现 Embedding 缓存
  - [ ] 创建 `embeddings/cached.py`
  - [ ] 实现 LRU Cache 包装器
- [ ] 1.3 调整向量搜索参数
  - [ ] 修改 `storage.py` 中的 `limit * 2` → `limit * 1.2`
- [ ] 1.4 更新配置系统
  - [ ] 在 `configs/settings.py` 添加 LocalSLMConfig
- [ ] 1.5 集成到 Memory 组件
  - [ ] 修改 `memory/main.py` 集成 LocalSLM 和 CachedEmbedding
- [ ] 1.6 验证与测试
  - [ ] 编写单元测试
  - [ ] 运行性能基准测试

**预期收益**: P95 从 1.5s → 500ms (降低 66%)

## Phase 2: 架构优化 ⏱️ 2-3周
- [ ] 2.1 全链路异步化 (async/await)
- [ ] 2.2 并行执行 Vector + Graph Search
- [ ] 2.3 添加 Graph Search 超时控制
- [ ] 2.4 引入 Redis 分布式缓存

**预期收益**: P95 从 500ms → 200ms (再降低 60%)

## Phase 3: 极致优化 ⏱️ 持续迭代
- [ ] 3.1 Milvus 索引优化 (IVF_FLAT)
- [ ] 3.2 两阶段检索引擎 (Fast Path + Slow Path)
- [ ] 3.3 预加载和 Warm-up
- [ ] 3.4 批处理端到端优化

**预期收益**: P95 < 100ms

## 关键决策
- ✅ Search 路径使用本地小模型（速度优先）
- ✅ Write 路径保持使用 OpenAI LLM（精度优先）
- ✅ 引入模型文件依赖（~500MB GGUF 文件）

## 性能指标跟踪
| 阶段 | P95 延迟 | P50 延迟 | 改善幅度 |
|------|---------|---------|---------|
| 当前 | 1.5-2.5s | 1.0-1.5s | - |
| Phase 1 目标 | < 500ms | < 300ms | -66% |
| Phase 2 目标 | < 200ms | < 100ms | -86% |
| Phase 3 目标 | < 100ms | < 50ms | -93% |
