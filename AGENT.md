# Mnemosyne Memory System - 开发手册

## 项目状态

### 当前阶段
- [x] Phase 1: 本地文件记忆能力扩展 ✓
- [x] Phase 2: AI工程评估工作流 ✓ (当前)
- [ ] Phase 3: 性能优化与回归检测

### 最近进度
- 2026-03-22: 完成记忆对话功能 + DeepSeek AI 集成
  - server/app/api/chat.py - 对话 API 端点
  - web/src/components/chat/ - 聊天 UI 组件
  - web/src/hooks/useChat.ts - 聊天状态管理
  - 集成 DeepSeek API 实现 AI 对话
  - 修复消息显示样式问题
- 2026-03-21: 完成 AI 工程评估工作流
  - evaluation/validators/test_runner.py - 测试执行器
  - evaluation/validators/benchmark_runner.py - 性能基准
  - evaluation/validators/gate_checker.py - 门禁判定
  - evaluation/validators/baseline_manager.py - 基线管理
  - evaluation/hooks/pre-commit - Git pre-commit hook
  - evaluation/session_init.py - 会话初始化协议
- 2026-03-20: 完成 SQLiteVectorStore + FAISSIndexManager
- 2026-03-20: 完成 FileMemoryContext
- 2026-03-20: 完成单元测试 (38 tests passing)

## 会话初始化协议

每次新会话开始时，必须执行以下步骤：

```bash
# 1. 读取项目状态
cat AGENT.md

# 2. 读取当前性能基线
cat evaluation/baselines/.baseline.json

# 3. 查看最近提交
git log --oneline -10

# 4. 查看上次评估报告
cat evaluation/reports/latest.json 2>/dev/null || echo "No report yet"

# 5. 从断点继续工作
```

## 待办事项 (优先级排序)

### P0 - 门禁系统核心 ✅
1. [x] test_runner.py - 测试执行器
2. [x] benchmark_runner.py - 性能基准
3. [x] gate_checker.py - 门禁判定
4. [x] pre-commit hook - 本地门禁

### P1 - 基线管理
1. [ ] 建立初始性能基线（需在真实环境中运行）
2. [ ] 实现基线更新机制
3. [ ] 评估报告生成

### P2 - CI/CD 集成
1. [ ] GitHub Actions 配置
2. [ ] 自动化报告

## 已知问题

- BM25Reranker 测试在无相关文档时 score 可能为负（需确认是否为预期行为）
- SQLiteVectorStore 在高并发写入时可能需要连接池优化

## 性能基线

| 指标 | 基线值 | 最后更新 |
|------|--------|----------|
| P95 延迟 | TBD | 待建立 |
| P99 延迟 | TBD | 待建立 |
| 单元测试覆盖率 | TBD | 待建立 |
| 测试通过率 | 100% (38 passed, 2 skipped) | 2026-03-21 |

> 注意：基线数据需要在有 OpenAI API 环境下运行 benchmark_search.py 后建立

## 技术决策

| 决策 | 方案 | 原因 |
|------|------|------|
| 存储后端 | SQLite + FAISS (本地模式) | 零依赖，易部署 |
| 验证框架 | pytest + pytest-cov | 成熟生态 |
| 门禁策略 | 强制门禁 | 质量保证 |
| 延迟阈值 | P95 回归 > 10% | 感知明显 |

## 评估门禁规则

### 必须通过 (Blocking)
- [ ] 所有单元测试通过
- [ ] 测试覆盖率 >= baseline (默认 80%)
- [ ] P95 延迟回归 < 10%

### 建议通过 (Non-blocking)
- [ ] P99 延迟回归 < 15%
- [ ] 代码覆盖率提升

### 门禁失败处理
```
1. 生成详细报告 (JSON + Markdown)
2. Block commit
3. 输出失败原因和修复建议
```

## 项目结构

```
memory-module/
├── server/                  # FastAPI 后端
│   └── app/
│       ├── api/            # API 端点 (chat, memory, backend)
│       ├── models.py       # Pydantic 模型
│       ├── database.py     # 内存数据库
│       └── config.py       # 配置管理
├── web/                     # React 前端
│   └── src/
│       ├── api/            # API 客户端
│       ├── components/     # UI 组件
│       ├── hooks/          # React Hooks
│       ├── stores/         # Zustand 状态管理
│       └── types/          # TypeScript 类型
├── service/
│   ├── mnemosyne/           # 核心代码
│   │   ├── memory/          # 记忆系统
│   │   ├── vector_stores/   # 向量存储
│   │   ├── embeddings/      # 嵌入模型
│   │   └── reranker/        # 重排序
│   └── tests/               # 测试
├── evaluation/              # 评估工作流
│   ├── validators/          # 验证器
│   ├── hooks/               # Git hooks
│   ├── baselines/           # 基线数据
│   └── reports/             # 评估报告
├── AGENT.md                  # 本文件
└── .gitignore
```

## 下一步行动

### 已完成
- [x] 完成 evaluation validators 实现
- [x] 配置 pre-commit hook (evaluation/install_hook.py)
- [x] 测试完整门禁流程

### 进行中
- [ ] 建立初始性能基线（在有 OpenAI API 环境下运行）
- [ ] 安装 pre-commit hook: `python evaluation/install_hook.py`

### 待完成
- [ ] 后端替换：使用 mnemosyne 系统作为后端
- [ ] GitHub Actions CI/CD 集成
- [ ] 性能基线数据采集
- [ ] 评估报告自动化生成
