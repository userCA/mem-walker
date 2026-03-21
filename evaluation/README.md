# Evaluation Workflow

AI 工程评估工作流 - 基于 Harness Engineering 原则。

## 核心原则

1. **验证优先 (Validation First)** - 功能正确性是底线
2. **强制门禁 (Mandatory Gate)** - 所有检查通过才能提交
3. **性能回归检测** - 持续监控性能指标

## 目录结构

```
evaluation/
├── validators/           # 验证器
│   ├── test_runner.py     # 测试执行器
│   ├── benchmark_runner.py # 性能基准
│   ├── gate_checker.py    # 门禁判定
│   └── baseline_manager.py # 基线管理
├── hooks/
│   └── pre-commit         # Git pre-commit hook
├── baselines/
│   └── .baseline.json     # 性能基线数据
├── reports/               # 评估报告
├── install_hook.py        # Hook 安装脚本
└── session_init.py        # 会话初始化
```

## 快速开始

### 1. 安装 Pre-commit Hook

```bash
python evaluation/install_hook.py
```

### 2. 初始化会话（每次新会话开始）

```bash
python evaluation/session_init.py
```

这将显示：
- 项目当前状态
- 性能基线
- 最近提交
- 工作树状态

### 3. 建立初始基线

```bash
# 先运行测试建立基线
cd service && pytest tests/ -v --cov=mnemosyne --cov-report=term-missing

# 更新基线
python -c "
from evaluation import GateChecker
gate = GateChecker()
# 运行测试和基准
test_result = gate.test_runner.run()
benchmark_result = gate.benchmark_runner.run()
# 更新基线
gate.update_baseline(test_result, benchmark_result)
print('Baseline updated')
"
```

### 4. 提交代码

```bash
git add .
git commit -m "Your changes"
# 将自动运行门禁检查
```

## 门禁规则

### Blocking (必须通过)
- [ ] 所有单元测试通过
- [ ] 测试覆盖率 >= 80%
- [ ] P95 延迟 < 500ms
- [ ] 性能回归 < 10%

### Non-blocking (警告)
- [ ] 覆盖率提升
- [ ] P99 延迟改善

## 评估报告

报告位置: `evaluation/reports/latest.json`

```json
{
  "timestamp": "2026-03-21T10:00:00",
  "passed": true,
  "blocking_checks": [
    {"name": "单元测试", "passed": true, "message": "..."},
    {"name": "性能基准", "passed": true, "message": "..."}
  ],
  "non_blocking_checks": [...]
}
```

## 跳过门禁（不推荐）

```bash
git commit --no-verify -m "Emergency fix"
```

## 更新日志

- 2026-03-21: 初始实现
