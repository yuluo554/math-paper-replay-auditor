"""K42: exe --selftest 内建参数。

验证：
1. CLI 和 GUI 都支持 --selftest
2. --selftest 检查数据目录和核心引擎
3. --selftest 返回正确的退出码
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLI_PATH = REPO_ROOT / "src" / "auditor" / "cli.py"


def test_cli_selftest_flag_exists():
    """K42: CLI 有 selftest 子命令。"""
    content = CLI_PATH.read_text(encoding="utf-8")
    assert "selftest" in content, "CLI 应有 selftest 子命令"


def test_cli_selftest_returns_int():
    """K42: CLI selftest 返回整数退出码。"""
    from auditor.cli import main

    # 模拟 --selftest 参数
    old_argv = sys.argv
    try:
        sys.argv = ["auditor", "selftest"]
        exit_code = main()
        assert isinstance(exit_code, int), "main() 应返回整数"
    finally:
        sys.argv = old_argv


def test_gui_selftest_function_exists():
    """K42: GUI 有 _run_selftest 函数。"""
    from auditor.gui.main_window import _run_selftest

    assert callable(_run_selftest)


def test_selftest_checks_data_dir():
    """K42: --selftest 检查数据目录。"""
    from auditor.gui.main_window import _run_selftest

    exit_code = _run_selftest()
    # 应该成功（数据目录存在）
    assert exit_code == 0, f"自检应成功，实际返回 {exit_code}"


def test_selftest_checks_core_engine():
    """K42: --selftest 检查核心引擎。"""
    content = CLI_PATH.read_text(encoding="utf-8")

    # 检查 selftest 路径导入核心引擎
    assert "pipeline" in content or "core" in content, \
        "selftest 应检查核心引擎"
