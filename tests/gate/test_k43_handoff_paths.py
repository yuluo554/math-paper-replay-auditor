"""K43: HANDOFF 库内写相对路径。

验证：
1. 所有 HANDOFF 文件用法行写相对路径
2. 不含本机绝对路径
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_DIR = REPO_ROOT / "plan"


def test_handoff_files_use_relative_paths():
    """K43: HANDOFF 文件用法行写相对路径。"""
    handoff_files = list(PLAN_DIR.glob("HANDOFF-*.md"))

    for handoff_path in handoff_files:
        content = handoff_path.read_text(encoding="utf-8")

        # 检查用法行
        # 应该写 plan/HANDOFF-Mx.md，不写 D:\...\plan\HANDOFF-Mx.md
        lines = content.split("\n")
        for line in lines:
            if "/goal" in line or "读取" in line:
                # 不应包含 Windows 绝对路径（盘符路径）
                # 但允许 /goal 命令前缀
                # 检查是否包含 D:\ 或 C:\ 这样的盘符路径
                import re
                windows_path_pattern = r'[A-Za-z]:\\'
                if re.search(windows_path_pattern, line):
                    # 如果包含 Windows 路径，检查是否在引号内且是启动命令
                    # 启动命令从用户侧拼绝对路径是允许的
                    if '"' in line or "'" in line:
                        # 路径在引号内，这是启动命令，允许
                        pass
                    else:
                        assert False, f"HANDOFF 文件不应包含 Windows 绝对路径: {line}"


def test_handoff_files_exist():
    """K43: 所有 HANDOFF 文件存在。"""
    expected = ["HANDOFF-M1.md", "HANDOFF-M2.md", "HANDOFF-M3.md", "HANDOFF-M4.md", "HANDOFF-M5.md"]
    for name in expected:
        path = PLAN_DIR / name
        assert path.exists(), f"HANDOFF 文件不存在: {name}"
