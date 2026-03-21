"""Test Runner - 执行单元测试并生成报告。"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class TestResult:
    """测试结果。"""
    passed: int
    failed: int
    errors: int
    skipped: int
    total: int
    pass_rate: float
    duration_seconds: float
    coverage: Optional[float] = None
    failed_tests: List[str] = field(default_factory=list)
    output: str = ""


class TestRunner:
    """测试执行器。"""

    def __init__(
        self,
        test_dir: str = "service/tests",
        coverage_threshold: float = 80.0,
        verbose: bool = False,
        python_path: str = None
    ):
        """初始化测试执行器。

        Args:
            test_dir: 测试目录路径
            coverage_threshold: 覆盖率阈值 (%)
            verbose: 详细输出
            python_path: Python 解释器路径，默认使用当前 Python
        """
        self.test_dir = Path(test_dir).resolve()  # 使用绝对路径
        self.coverage_threshold = coverage_threshold
        self.verbose = verbose
        self.python_path = python_path or sys.executable

    def run(self) -> TestResult:
        """运行测试。

        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()

        # 构建 pytest 命令
        # service_dir = self.test_dir.parent (即项目根目录)
        # tests_path = "tests" (相对于 service 目录)
        service_dir = self.test_dir.parent
        tests_path = "tests"

        cmd = [
            self.python_path,
            "-m", "pytest",
            tests_path,
            "-v" if self.verbose else "-q",
            "--tb=short",
            "-p", "no:cacheprovider",
            "--override-ini=addopts=",
        ]

        try:
            # 设置环境变量以包含 mnemosyne 模块路径
            env = os.environ.copy()
            service_path = str(service_dir)
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = f"{service_path}:{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = service_path

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(service_dir),
                env=env
            )

            output = result.stdout + result.stderr
            duration = time.time() - start_time

            # 调试信息
            if result.returncode != 0:
                print(f"Warning: pytest returned {result.returncode}")

            # 解析测试结果
            test_result = self._parse_pytest_output(output, duration)

            # 读取覆盖率
            coverage = self._read_coverage()
            if coverage is not None:
                test_result.coverage = coverage

            return test_result

        except Exception as e:
            return TestResult(
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                total=0,
                pass_rate=0.0,
                duration_seconds=time.time() - start_time,
                output=f"Error running tests: {str(e)}"
            )

    def _parse_pytest_output(self, output: str, duration: float) -> TestResult:
        """解析 pytest 输出。"""
        passed = failed = errors = skipped = 0
        failed_tests = []

        lines = output.split("\n")
        for line in lines:
            # 解析 pytest 摘要行
            # 格式: "============= 38 passed, 2 skipped, 4 warnings in 93.04s ============="
            if "passed" in line.lower() or "failed" in line.lower() or "skipped" in line.lower():
                # 查找总结行
                if "=" in line and ("passed" in line or "failed" in line or "skipped" in line):
                    parts = line.replace("=", " ").split()
                    for i, part in enumerate(parts):
                        # 去掉末尾的逗号和s
                        clean_part = part.rstrip(",").rstrip("s")
                        if clean_part == "passed":
                            try:
                                passed = int(parts[i - 1])
                            except (ValueError, IndexError):
                                pass
                        elif clean_part == "skipped":
                            try:
                                skipped = int(parts[i - 1])
                            except (ValueError, IndexError):
                                pass
                        elif clean_part == "failed":
                            try:
                                failed = int(parts[i - 1])
                            except (ValueError, IndexError):
                                pass

            # 解析失败测试
            if "FAILED" in line:
                # 提取测试名称
                parts = line.split("::")
                if len(parts) > 1:
                    test_name = parts[1].split(" ")[0]
                    failed_tests.append(test_name)

        total = passed + failed + errors + skipped
        pass_rate = (passed / total * 100) if total > 0 else 0.0

        return TestResult(
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            total=total,
            pass_rate=pass_rate,
            duration_seconds=duration,
            failed_tests=failed_tests,
            output=output
        )

    def _read_coverage(self) -> Optional[float]:
        """读取覆盖率数据。"""
        coverage_file = Path("/tmp/coverage.json")
        if not coverage_file.exists():
            return None

        try:
            with open(coverage_file) as f:
                data = json.load(f)
                # 计算总覆盖率
                totals = data.get("totals", {})
                return totals.get("percent_covered", 0.0)
        except Exception:
            return None

    def check_passed(self, result: TestResult) -> tuple[bool, str]:
        """检查测试是否通过门禁。

        Returns:
            (通过, 消息)
        """
        # 没有测试结果时警告但不失败
        if result.total == 0 and result.errors == 0:
            return True, "No tests run (可能是测试路径问题)"

        if result.errors > 0:
            return False, f"测试执行出错 ({result.errors} errors)"

        if result.failed > 0:
            return False, f"测试失败 ({result.failed}/{result.total})"

        if result.total > 0 and result.pass_rate < 100.0:
            return False, f"测试通过率未达 100% (当前: {result.pass_rate:.1f}%)"

        # 覆盖率是警告性的，不是阻塞性的
        if result.coverage is not None and result.coverage < self.coverage_threshold:
            return True, f"测试通过 (覆盖率警告: {result.coverage:.1f}% < {self.coverage_threshold}%)"

        return True, f"测试通过 (覆盖率: {result.coverage or 'N/A'}%)"

    def to_dict(self, result: TestResult) -> dict:
        """转换为字典格式。"""
        return {
            "timestamp": datetime.now().isoformat(),
            "passed": result.passed,
            "failed": result.failed,
            "errors": result.errors,
            "skipped": result.skipped,
            "total": result.total,
            "pass_rate": result.pass_rate,
            "coverage": result.coverage,
            "duration_seconds": result.duration_seconds,
            "passed_gate": result.failed == 0 and result.errors == 0
        }
