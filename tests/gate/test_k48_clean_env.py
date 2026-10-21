"""K48: 干净环境验证逐条留档。

验证：
1. plan/verify/ 目录与留档 README 存在
2. 留档包含逐条命令和退出码
3. 退出码语义符合 README 声明

D7 修复：本文件此前**每一项都是条件式断言**（`if VERIFY_README.exists():` 才检查），
第 1 项更是纯 `pass`——留档整个删掉，门仍然全绿。
现在改为**无条件断言**（留档是本仓的硬交付物，不是"有则检查"）：
留档缺失/为空/不含命令与退出码，直接变红。
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_DIR = REPO_ROOT / "plan" / "verify"
VERIFY_README = VERIFY_DIR / "README.md"

# 留档必须逐条记录的退出码语义（对照 README「退出码语义」表）
REQUIRED_EXIT_CODES = ("0", "1", "2")


def test_verify_directory_exists():
    """K48: plan/verify/ 目录存在（留档是本仓的硬交付物）。"""
    assert VERIFY_DIR.is_dir(), f"留档目录不存在: {VERIFY_DIR}"


def test_verify_readme_exists_and_not_empty():
    """K48: 留档 README 存在且非空。"""
    assert VERIFY_README.is_file(), f"留档 README 不存在: {VERIFY_README}"
    content = VERIFY_README.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "留档 README 不应为空"


def test_verify_documents_commands():
    """K48: 留档文档必须记录关键命令（selftest / bench / audit）。"""
    content = VERIFY_README.read_text(encoding="utf-8")
    for cmd in ("selftest", "bench", "audit"):
        assert cmd in content, f"留档未记录关键命令 {cmd!r}"


def test_verify_records_exit_codes():
    """K48: 留档必须记录退出码（0 / 1 / 2 三种语义都要出现）。"""
    content = VERIFY_README.read_text(encoding="utf-8")
    # 逐条留档是表格形态：`| ... | <退出码> | ... |`
    table_codes = set(re.findall(r"\|\s*([0-9])\s*\|", content))
    for code in REQUIRED_EXIT_CODES:
        assert code in table_codes, (
            f"留档表格中未记录退出码 {code}（当前表格里出现的: "
            f"{sorted(table_codes) or '无'}）"
        )


def test_verify_records_this_round():
    """K48: 留档必须含本轮（M8）记录——防止"留档只写一次就再也不更新"。"""
    content = VERIFY_README.read_text(encoding="utf-8")
    assert "M8" in content, (
        "留档没有本轮（M8）记录：留档必须**追加**每一轮的逐条命令与退出码，"
        "不覆盖历史轮次"
    )
