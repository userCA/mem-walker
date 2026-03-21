"""Gate Checker - 门禁判定核心逻辑。"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .baseline_manager import BaselineManager, Baseline
from .benchmark_runner import BenchmarkRunner, BenchmarkResult
from .test_runner import TestRunner, TestResult


@dataclass
class GateResult:
    """门禁检查结果。"""
    passed: bool
    blocking_checks: List["CheckResult"] = field(default_factory=list)
    non_blocking_checks: List["CheckResult"] = field(default_factory=list)
    total_duration_seconds: float = 0
    report_path: Optional[str] = None

    @property
    def all_checks(self) -> List["CheckResult"]:
        return self.blocking_checks + self.non_blocking_checks


@dataclass
class CheckResult:
    """检查项结果。"""
    name: str
    passed: bool
    blocking: bool
    message: str
    details: Optional[dict] = None


class GateChecker:
    """门禁判定器。"""

    def __init__(
        self,
        baseline_path: str = "evaluation/baselines/.baseline.json",
        test_dir: str = "service/tests",
        benchmark_script: str = "service/mnemosyne/examples/benchmark_search.py",
        coverage_threshold: float = 80.0,
        p95_threshold_ms: float = 500.0,
        regression_threshold_percent: float = 10.0,
        report_dir: str = "evaluation/reports"
    ):
        """初始化门禁判定器。

        Args:
            baseline_path: 基线文件路径
            test_dir: 测试目录
            benchmark_script: benchmark 脚本路径
            coverage_threshold: 覆盖率阈值 (%)
            p95_threshold_ms: P95 延迟阈值 (ms)
            regression_threshold_percent: 回归阈值 (%)
            report_dir: 报告输出目录
        """
        self.baseline_manager = BaselineManager(baseline_path)
        self.test_runner = TestRunner(
            test_dir=test_dir,
            coverage_threshold=coverage_threshold,
            verbose=False
        )
        self.benchmark_runner = BenchmarkRunner(
            benchmark_script=benchmark_script,
            num_queries=50,  # 快速基准测试
            p95_threshold_ms=p95_threshold_ms,
            verbose=False
        )
        self.coverage_threshold = coverage_threshold
        self.regression_threshold = regression_threshold_percent
        self.report_dir = Path(report_dir)

    def run(self) -> GateResult:
        """运行完整门禁检查。

        Returns:
            GateResult: 门禁结果
        """
        start_time = datetime.now()
        results: List[CheckResult] = []
        blocking_checks: List[CheckResult] = []
        non_blocking_checks: List[CheckResult] = []

        # 1. 运行单元测试
        test_result = self.test_runner.run()
        test_check = self._check_tests(test_result)
        results.append(test_check)
        if test_check.blocking:
            blocking_checks.append(test_check)
        else:
            non_blocking_checks.append(test_check)

        # 2. 运行基准测试
        benchmark_result = self.benchmark_runner.run()
        benchmark_check = self._check_benchmark(benchmark_result)
        results.append(benchmark_check)
        if benchmark_check.blocking:
            blocking_checks.append(benchmark_check)
        else:
            non_blocking_checks.append(benchmark_check)

        # 3. 检查性能回归
        if benchmark_result.passed:
            regression_check = self._check_regression(benchmark_result)
            results.append(regression_check)
            if regression_check.blocking:
                blocking_checks.append(regression_check)
            else:
                non_blocking_checks.append(regression_check)

        # 4. 检查覆盖率回归
        if test_result.coverage is not None:
            coverage_check = self._check_coverage_regression(test_result.coverage)
            results.append(coverage_check)
            if coverage_check.blocking:
                blocking_checks.append(coverage_check)
            else:
                non_blocking_checks.append(coverage_check)

        duration = (datetime.now() - start_time).total_seconds()

        # 判定是否通过
        all_blocking_passed = all(c.passed for c in blocking_checks)
        passed = all_blocking_passed

        # 生成报告
        report = GateResult(
            passed=passed,
            blocking_checks=blocking_checks,
            non_blocking_checks=non_blocking_checks,
            total_duration_seconds=duration
        )

        report_path = self._save_report(report, test_result, benchmark_result)
        report.report_path = report_path

        return report

    def _check_tests(self, result: TestResult) -> CheckResult:
        """检查测试结果。"""
        passed, message = self.test_runner.check_passed(result)

        return CheckResult(
            name="单元测试",
            passed=passed,
            blocking=True,  # 测试失败是阻塞性的
            message=message,
            details=self.test_runner.to_dict(result)
        )

    def _check_benchmark(self, result: BenchmarkResult) -> CheckResult:
        """检查基准测试结果。"""
        passed, message = self.benchmark_runner.check_passed(result)

        return CheckResult(
            name="性能基准",
            passed=passed,
            blocking=True,
            message=message,
            details=self.benchmark_runner.to_dict(result)
        )

    def _check_regression(self, result: BenchmarkResult) -> CheckResult:
        """检查性能回归。"""
        passed, message = self.baseline_manager.check_regression(
            result,
            threshold_percent=self.regression_threshold
        )

        return CheckResult(
            name="性能回归",
            passed=passed,
            blocking=True,  # 回归是阻塞性的
            message=message,
            details={
                "baseline": self.baseline_manager.to_dict(),
                "current": self.benchmark_runner.to_dict(result),
                "threshold_percent": self.regression_threshold
            }
        )

    def _check_coverage_regression(self, coverage: float) -> CheckResult:
        """检查覆盖率回归。"""
        passed, message = self.baseline_manager.check_coverage_regression(
            coverage,
            threshold_percent=self.coverage_threshold
        )

        return CheckResult(
            name="覆盖率",
            passed=passed,
            blocking=False,  # 覆盖率低是警告性的
            message=message,
            details={
                "coverage": coverage,
                "threshold": self.coverage_threshold
            }
        )

    def _save_report(
        self,
        gate_result: GateResult,
        test_result: TestResult,
        benchmark_result: BenchmarkResult
    ) -> Optional[str]:
        """保存评估报告。"""
        self.report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.report_dir / f"{timestamp}_gate_report.json"

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "passed": gate_result.passed,
            "total_duration_seconds": gate_result.total_duration_seconds,
            "blocking_checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "details": c.details
                }
                for c in gate_result.blocking_checks
            ],
            "non_blocking_checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "details": c.details
                }
                for c in gate_result.non_blocking_checks
            ],
            "test_result": self.test_runner.to_dict(test_result),
            "benchmark_result": self.benchmark_runner.to_dict(benchmark_result)
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # 更新 latest 链接
        latest_path = self.report_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump(report_data, f, indent=2)

        return str(report_path)

    def update_baseline(
        self,
        test_result: TestResult = None,
        benchmark_result: BenchmarkResult = None
    ):
        """更新基线数据。

        Args:
            test_result: 测试结果
            benchmark_result: 基准测试结果
        """
        # 获取 git 信息
        commit_hash = None
        branch = None
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                text=True
            ).strip()
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            pass

        self.baseline_manager.update_from_results(
            benchmark_result=benchmark_result,
            test_result=test_result,
            commit_hash=commit_hash,
            branch=branch
        )

    def print_summary(self, result: GateResult):
        """打印结果摘要。"""
        print("\n" + "=" * 60)
        print("Gate Check Result")
        print("=" * 60)

        if result.passed:
            print("✅ GATE PASSED - All checks passed")
        else:
            print("❌ GATE FAILED - Blocking issues found")

        print()

        # Blocking checks
        print("Blocking Checks:")
        for check in result.blocking_checks:
            status = "✅" if check.passed else "❌"
            print(f"  {status} {check.name}: {check.message}")

        if result.non_blocking_checks:
            print()
            print("Warnings:")
            for check in result.non_blocking_checks:
                status = "⚠️" if check.passed else "⚠️"
                print(f"  {status} {check.name}: {check.message}")

        print()
        print(f"Duration: {result.total_duration_seconds:.2f}s")

        if result.report_path:
            print(f"Report: {result.report_path}")

        print("=" * 60)
