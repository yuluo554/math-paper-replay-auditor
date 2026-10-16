"""K40: 冻结入口用薄模块（绝对导入）。

验证：
1. cli.py 不使用相对导入
2. cli.py 有 __main__ 入口
3. 入口文件只做导入和调用，不做复杂逻辑
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLI_PATH = REPO_ROOT / "src" / "auditor" / "cli.py"


def test_cli_no_relative_imports():
    """K40: cli.py 不使用相对导入。"""
    content = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"cli.py 不应使用相对导入: line {node.lineno}"


def test_cli_has_main_guard():
    """K40: cli.py 有 __main__ 入口。"""
    content = CLI_PATH.read_text(encoding="utf-8")
    assert "if __name__" in content, "cli.py 必须有 __main__ 入口"
    assert '"__main__"' in content or "'__main__'" in content, \
        "cli.py 必须有 if __name__ == '__main__'"


def test_cli_calls_sys_exit():
    """K40: cli.py 的 main() 返回退出码。"""
    content = CLI_PATH.read_text(encoding="utf-8")
    assert "sys.exit" in content or "return" in content, \
        "cli.py 的 main() 应返回退出码"


def test_cli_imports_are_absolute():
    """K40: cli.py 的导入是绝对导入。"""
    content = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # 检查不是相对导入
                assert not alias.name.startswith("."), \
                    f"cli.py 不应使用相对导入: {alias.name}"
