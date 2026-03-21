#!/usr/bin/env python3
"""Session Initialization Protocol.

每次新会话开始时运行此脚本以了解项目状态。

Usage:
    python session_init.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def read_file(path: Path) -> str:
    """读取文件内容。"""
    if path.exists():
        return path.read_text().strip()
    return ""


def run_git_log(count: int = 10) -> str:
    """运行 git log。"""
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{count}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Not a git repository or no commits"


def run_git_status() -> str:
    """运行 git status。"""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() or "Working tree clean"
    except subprocess.CalledProcessError:
        return "Not a git repository"


def check_pytest() -> str:
    """检查 pytest 是否可用。"""
    try:
        result = subprocess.run(
            ["pytest", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("\n")[0]
    except subprocess.CalledProcessError:
        return "pytest not installed"


def main():
    project_root = Path(__file__).parent.parent

    print("=" * 70)
    print(" Mnemosyne Session Initialization")
    print("=" * 70)
    print()
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # 1. Read AGENT.md
    print("📋 Project Status (AGENT.md):")
    print("-" * 40)
    agent_md = project_root / "AGENT.md"
    if agent_md.exists():
        content = read_file(agent_md)
        # Print first 30 lines
        lines = content.split("\n")[:30]
        for line in lines:
            print(f"  {line}")
        if len(content.split("\n")) > 30:
            print("  ... (truncated, see AGENT.md for full content)")
    else:
        print("  ⚠️  AGENT.md not found")
    print()

    # 2. Read baseline
    print("📊 Performance Baseline:")
    print("-" * 40)
    baseline_file = project_root / "evaluation" / "baselines" / ".baseline.json"
    if baseline_file.exists():
        try:
            baseline = json.loads(read_file(baseline_file))
            print(f"  P95 Latency: {baseline.get('p95_latency_ms', 'N/A')} ms")
            print(f"  P99 Latency: {baseline.get('p99_latency_ms', 'N/A')} ms")
            print(f"  Coverage:    {baseline.get('test_coverage', 'N/A')}%")
            print(f"  Test Pass:   {baseline.get('test_pass_rate', 'N/A')}%")
            print(f"  Updated:     {baseline.get('updated_at', 'N/A')}")
        except json.JSONDecodeError:
            print("  ⚠️  Invalid baseline file")
    else:
        print("  ⚠️  No baseline established")
    print()

    # 3. Read latest report
    print("📝 Latest Evaluation Report:")
    print("-" * 40)
    report_file = project_root / "evaluation" / "reports" / "latest.json"
    if report_file.exists():
        try:
            report = json.loads(read_file(report_file))
            status = "✅ PASSED" if report.get("passed") else "❌ FAILED"
            print(f"  Status:  {status}")
            print(f"  Date:    {report.get('timestamp', 'N/A')}")
            checks = report.get("blocking_checks", [])
            print(f"  Checks:  {len(checks)} blocking")
        except json.JSONDecodeError:
            print("  ⚠️  Invalid report file")
    else:
        print("  ℹ️  No evaluation report yet")
    print()

    # 4. Git log
    print("🔄 Recent Commits:")
    print("-" * 40)
    git_log = run_git_log(5)
    for line in git_log.split("\n"):
        print(f"  {line}")
    print()

    # 5. Git status
    print("📁 Working Tree Status:")
    print("-" * 40)
    git_status = run_git_status()
    for line in git_status.split("\n"):
        print(f"  {line}")
    print()

    # 6. Environment check
    print("🔧 Environment:")
    print("-" * 40)
    print(f"  pytest: {check_pytest()}")
    print(f"  Python: {sys.version.split()[0]}")
    print()

    print("=" * 70)
    print("Ready to continue development")
    print("=" * 70)


if __name__ == "__main__":
    main()
