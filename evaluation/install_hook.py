#!/usr/bin/env python3
"""Install pre-commit hook for evaluation gate.

Usage:
    python install_hook.py           # 安装
    python install_hook.py --uninstall  # 卸载
"""

import argparse
import os
import sys
from pathlib import Path


def install_hook():
    """Install the pre-commit hook."""
    project_root = Path(__file__).parent.parent
    hook_source = project_root / "evaluation" / "hooks" / "pre-commit"
    git_hooks_dir = project_root / ".git" / "hooks"
    hook_target = git_hooks_dir / "pre-commit"

    # Check if hook source exists
    if not hook_source.exists():
        print(f"❌ Hook source not found: {hook_source}")
        sys.exit(1)

    # Create hooks directory if needed
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Backup existing hook if any
    if hook_target.exists():
        backup = hook_target.with_suffix(".bak")
        print(f"📦 Backing up existing hook to {backup}")
        hook_target.rename(backup)

    # Create symlink or copy
    try:
        # Try symlink first (works on Unix)
        os.symlink(hook_source.resolve(), hook_target)
        print(f"✅ Symlink created: {hook_target} -> {hook_source}")
    except OSError:
        # Fall back to copy
        import shutil
        shutil.copy(hook_source, hook_target)
        hook_target.chmod(0o755)
        print(f"✅ Copied hook: {hook_target}")

    print()
    print("✅ Pre-commit hook installed successfully!")
    print()
    print("Usage:")
    print("  git add .")
    print("  git commit -m 'Your message'")
    print()
    print("The evaluation gate will run before each commit.")


def uninstall_hook():
    """Uninstall the pre-commit hook."""
    project_root = Path(__file__).parent.parent
    hook_target = project_root / ".git" / "hooks" / "pre-commit"

    if not hook_target.exists():
        print("ℹ️  No pre-commit hook found")
        return

    # Remove hook
    hook_target.unlink()
    print(f"✅ Removed: {hook_target}")

    # Restore backup if exists
    backup = hook_target.with_suffix(".bak")
    if backup.exists():
        backup.rename(hook_target)
        print(f"✅ Restored backup: {hook_target}")

    print()
    print("✅ Pre-commit hook uninstalled")


def main():
    parser = argparse.ArgumentParser(description="Install/uninstall pre-commit hook")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the hook")
    args = parser.parse_args()

    if args.uninstall:
        uninstall_hook()
    else:
        install_hook()


if __name__ == "__main__":
    main()
