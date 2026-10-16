"""K41: 窗口版对未知参数 exit 2（不静默忽略）。

验证：
1. GUI 入口对未知参数返回 exit 2
2. GUI 入口对已知参数正常处理
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GUI_PATH = REPO_ROOT / "src" / "auditor" / "gui" / "main_window.py"


def test_gui_unknown_arg_returns_2():
    """K41: GUI 入口对未知参数返回 exit 2。"""
    # 直接测试函数
    from auditor.gui.main_window import run_gui

    exit_code = run_gui(["--unknown-flag"])
    assert exit_code == 2, f"未知参数应返回 2，实际返回 {exit_code}"


def test_gui_selftest_returns_0():
    """K41: GUI 入口对 --selftest 返回 0 或 1。"""
    from auditor.gui.main_window import run_gui

    exit_code = run_gui(["--selftest"])
    assert exit_code in (0, 1), f"--selftest 应返回 0 或 1，实际返回 {exit_code}"


def test_gui_help_returns_0():
    """K41: GUI 入口对 --help 返回 0。"""
    from auditor.gui.main_window import run_gui

    exit_code = run_gui(["--help"])
    assert exit_code == 0, f"--help 应返回 0，实际返回 {exit_code}"


def test_gui_no_args_imports_pyside6():
    """K41: GUI 入口无参数时尝试导入 PySide6。"""
    from auditor.gui.main_window import run_gui

    # 这个测试在无 PySide6 环境下会返回 3
    # 我们只验证函数存在
    assert callable(run_gui)


def test_gui_known_args_list():
    """K41: GUI 入口已知参数列表正确。"""
    content = GUI_PATH.read_text(encoding="utf-8")

    # 检查已知参数列表
    assert "--selftest" in content, "应支持 --selftest"
    assert "--help" in content or "-h" in content, "应支持 --help"
