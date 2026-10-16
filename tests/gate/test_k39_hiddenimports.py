"""K39: 双 exe hiddenimports/excludes 分档。

验证：
1. CLI 目标排除 Qt 栈
2. GUI 目标包含 PySide6
3. CLI 和 GUI 的 hiddenimports 不同
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_EXE_PATH = REPO_ROOT / "packaging" / "build_exe.py"


def _extract_lists_from_file(file_path: Path, var_names: list) -> dict:
    """从 Python 文件提取列表变量。"""
    result = {}
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in var_names:
                    if isinstance(node.value, ast.List):
                        result[target.id] = [
                            elt.value if isinstance(elt, ast.Constant) else ""
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
    return result


def test_cli_excludes_qt():
    """K39: CLI 目标排除 Qt 栈。"""
    lists = _extract_lists_from_file(BUILD_EXE_PATH, ["CLI_EXCLUDES"])
    cli_excludes = lists.get("CLI_EXCLUDES", [])

    assert "PySide6" in cli_excludes, "CLI 应排除 PySide6"
    assert "shiboken6" in cli_excludes, "CLI 应排除 shiboken6"


def test_gui_does_not_exclude_qt():
    """K39: GUI 目标不排除 Qt 栈。"""
    lists = _extract_lists_from_file(BUILD_EXE_PATH, ["GUI_EXCLUDES"])
    gui_excludes = lists.get("GUI_EXCLUDES", [])

    assert "PySide6" not in gui_excludes, "GUI 不应排除 PySide6"


def test_cli_and_gui_hiddenimports_differ():
    """K39: CLI 和 GUI 的 hiddenimports 不同。"""
    lists = _extract_lists_from_file(BUILD_EXE_PATH, ["CLI_HIDDENIMPORTS", "GUI_HIDDENIMPORTS"])
    cli_hi = set(lists.get("CLI_HIDDENIMPORTS", []))
    gui_hi = set(lists.get("GUI_HIDDENIMPORTS", []))

    # GUI 应包含 GUI 专属模块
    assert "auditor.gui.main_window" in gui_hi, "GUI hiddenimports 应包含 main_window"
    assert "auditor.gui.pipelines" in gui_hi, "GUI hiddenimports 应包含 pipelines"

    # CLI 不应包含 GUI 模块
    assert "auditor.gui.main_window" not in cli_hi, "CLI hiddenimports 不应包含 GUI 模块"


def test_cli_hiddenimports_contains_core():
    """K39: CLI hiddenimports 包含核心引擎模块。"""
    lists = _extract_lists_from_file(BUILD_EXE_PATH, ["CLI_HIDDENIMPORTS"])
    cli_hi = lists.get("CLI_HIDDENIMPORTS", [])

    assert "auditor.core.parser" in cli_hi, "CLI hiddenimports 应包含 parser"
    assert "auditor.core.replay" in cli_hi, "CLI hiddenimports 应包含 replay"
    assert "auditor.core.numerical" in cli_hi, "CLI hiddenimports 应包含 numerical"
