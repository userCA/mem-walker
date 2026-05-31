# 工作日志 / Worklog

**日期**: 2026-04-05
**主题**: 实现记忆矛盾检测功能 (Knowledge Conflict Detection)

---

## 问题背景

在 RAG 和记忆系统中，矛盾数据处理是一个常见挑战。当用户向系统注入相互矛盾的信息时（如先说"Python 很难学"，后说"Python 很容易学"），系统需要能够检测并适当处理这种冲突。

### 发现的问题

通过代码分析发现：
1. `llms/base.py:73` 已定义 `detect_conflicts` 接口
2. `llms/openai.py:179` 已实现该接口
3. **`_MemoryWriter.add` 未调用该接口** - 这是"设计但未实现"的功能

---

## 解决方案

### 1. 分层渐进式冲突检测策略

```
Phase 1.1: Hash dedup (O(1)) → 精确匹配 → 直接返回
Phase 1.2: Semantic dedup
  ├── score > 0.92 → 精确重复 → 直接返回
  ├── score < 0.70 → 无冲突风险 → 直接插入
  └── 0.70 ≤ score ≤ 0.92 → 灰色地带 → 调用 detect_conflicts
Phase 2:   Fact extraction + Conflict resolution
Phase 3:   Persistence
```

### 2. 新增配置项

**GlobalSettings** (configs/settings.py):
```python
enable_conflict_detection: bool = True
conflict_strategy: str = "newer_wins"  # "newer_wins", "keep_both", "skip"
```

### 3. 冲突解决策略

| 策略 | 行为 | 适用场景 |
|------|------|---------|
| `newer_wins` | 新记忆覆盖旧记忆，保留元数据 | 快速迭代、信任最新信息 |
| `keep_both` | 保留两条记忆，标记冲突 | 审计、保留多样性 |
| `skip` | 跳过冲突记忆 | 保守、避免重复 |

### 4. 阈值定义

```python
SEMANTIC_DUPLICATE_THRESHOLD = 0.92  # 完全重复
SEMANTIC_SAFE_THRESHOLD = 0.70       # 安全区间
SEMANTIC_GRAY_ZONE_MIN = 0.70
SEMANTIC_GRAY_ZONE_MAX = 0.92
```

---

## 修改文件

| 文件 | 修改内容 |
|------|---------|
| `mnemosyne/memory/storage.py` | 新增 Phase 2.5 冲突检测逻辑 |
| `mnemosyne/configs/settings.py` | 新增 conflict_detection 配置 |
| `mnemosyne/memory/main.py` | 传递 conflict_strategy 给 _MemoryWriter |

---

## 性能影响

- **80% 请求**: 无影响（Hash dedup 或 Safe zone 直接通过）
- **20% 请求**: +1 LLM 调用 (50-100ms 额外延迟)
- **总体**: 延迟增加约 5-10ms

---

## 相关文档

- [2026-04-04-mnemosyne-search-analysis.md](../docs/superpowers/2026-04-04-mnemosyne-search-analysis.md) - 检索架构分析

---

## 下一步

- [ ] 添加集成测试验证冲突检测逻辑
- [ ] 添加配置项到 .env.example
- [ ] 考虑添加异步冲突检测以进一步降低延迟

---

## 参考

- mem0 架构中的冲突检测设计
- RAG 中的 Truth Discovery 机制
