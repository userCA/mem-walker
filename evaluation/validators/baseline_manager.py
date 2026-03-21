"""Baseline Manager - 管理性能基线数据。"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Baseline:
    """性能基线数据。"""
    version: str = "1.0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 性能指标
    p95_latency_ms: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    mean_latency_ms: Optional[float] = None
    median_latency_ms: Optional[float] = None
    min_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None

    # 测试指标
    test_coverage: Optional[float] = None
    test_pass_rate: Optional[float] = None
    total_tests: Optional[int] = None
    passed_tests: Optional[int] = None
    failed_tests: Optional[int] = None

    # 元数据
    commit_hash: Optional[str] = None
    branch: Optional[str] = None


class BaselineManager:
    """基线管理器。"""

    def __init__(self, baseline_path: str = "evaluation/baselines/.baseline.json"):
        """初始化基线管理器。

        Args:
            baseline_path: 基线文件路径
        """
        self.baseline_path = Path(baseline_path)
        self._ensure_baseline_exists()

    def _ensure_baseline_exists(self):
        """确保基线文件存在。"""
        if not self.baseline_path.exists():
            self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
            self._save(Baseline())

    def load(self) -> Baseline:
        """加载基线数据。

        Returns:
            Baseline: 基线数据
        """
        try:
            with open(self.baseline_path) as f:
                data = json.load(f)
                return Baseline(**data)
        except (json.JSONDecodeError, TypeError):
            return Baseline()

    def save(self, baseline: Baseline):
        """保存基线数据。

        Args:
            baseline: 基线数据
        """
        baseline.updated_at = datetime.now().isoformat()
        if baseline.created_at is None:
            baseline.created_at = baseline.updated_at
        self._save(baseline)

    def _save(self, baseline: Baseline):
        """保存到文件。"""
        with open(self.baseline_path, "w") as f:
            json.dump(self._to_dict(baseline), f, indent=2)

    def _to_dict(self, baseline: Baseline) -> dict:
        """转换为字典。"""
        return {
            "version": baseline.version,
            "created_at": baseline.created_at,
            "updated_at": baseline.updated_at,
            "p95_latency_ms": baseline.p95_latency_ms,
            "p99_latency_ms": baseline.p99_latency_ms,
            "mean_latency_ms": baseline.mean_latency_ms,
            "median_latency_ms": baseline.median_latency_ms,
            "min_latency_ms": baseline.min_latency_ms,
            "max_latency_ms": baseline.max_latency_ms,
            "test_coverage": baseline.test_coverage,
            "test_pass_rate": baseline.test_pass_rate,
            "total_tests": baseline.total_tests,
            "passed_tests": baseline.passed_tests,
            "failed_tests": baseline.failed_tests,
            "commit_hash": baseline.commit_hash,
            "branch": baseline.branch,
        }

    def update_from_results(
        self,
        benchmark_result: "BenchmarkResult" = None,
        test_result: "TestResult" = None,
        commit_hash: str = None,
        branch: str = None
    ):
        """从测试/基准结果更新基线。

        Args:
            benchmark_result: 基准测试结果
            test_result: 测试结果
            commit_hash: 提交哈希
            branch: 分支名
        """
        baseline = self.load()

        if benchmark_result is not None:
            baseline.p95_latency_ms = benchmark_result.p95_latency_ms
            baseline.p99_latency_ms = benchmark_result.p99_latency_ms
            baseline.mean_latency_ms = benchmark_result.mean_latency_ms
            baseline.median_latency_ms = benchmark_result.median_latency_ms
            baseline.min_latency_ms = benchmark_result.min_latency_ms
            baseline.max_latency_ms = benchmark_result.max_latency_ms

        if test_result is not None:
            baseline.test_coverage = test_result.coverage
            baseline.test_pass_rate = test_result.pass_rate
            baseline.total_tests = test_result.total
            baseline.passed_tests = test_result.passed
            baseline.failed_tests = test_result.failed

        if commit_hash:
            baseline.commit_hash = commit_hash
        if branch:
            baseline.branch = branch

        self.save(baseline)

    def check_regression(
        self,
        current: "BenchmarkResult",
        threshold_percent: float = 10.0
    ) -> tuple[bool, str]:
        """检查性能是否回归。

        Args:
            current: 当前基准测试结果
            threshold_percent: 回归阈值 (%)

        Returns:
            (通过, 消息)
        """
        baseline = self.load()

        if baseline.p95_latency_ms is None:
            return True, "No baseline available, skipping regression check"

        delta_percent = (
            (current.p95_latency_ms - baseline.p95_latency_ms)
            / baseline.p95_latency_ms * 100
        )

        if delta_percent > threshold_percent:
            return False, (
                f"Performance regression detected: "
                f"P95 {baseline.p95_latency_ms:.2f}ms -> {current.p95_latency_ms:.2f}ms "
                f"(+{delta_percent:.1f}%)"
            )

        return True, f"No regression (delta: {delta_percent:+.1f}%)"

    def check_coverage_regression(
        self,
        current: float,
        threshold_percent: float = 80.0
    ) -> tuple[bool, str]:
        """检查覆盖率是否回归。

        Args:
            current: 当前覆盖率
            threshold_percent: 最低覆盖率阈值 (%)

        Returns:
            (通过, 消息)
        """
        if current < threshold_percent:
            return False, f"Coverage below threshold ({current:.1f}% < {threshold_percent}%)"

        baseline = self.load()
        if baseline.test_coverage is not None:
            delta = current - baseline.test_coverage
            if delta < -5:  # 下降超过 5%
                return False, f"Coverage regression: {baseline.test_coverage:.1f}% -> {current:.1f}%"

        return True, f"Coverage OK ({current:.1f}%)"

    def to_dict(self) -> dict:
        """转换为字典格式。"""
        baseline = self.load()
        return self._to_dict(baseline)
