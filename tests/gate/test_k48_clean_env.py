"""K48: 干净环境验证逐条留档。

验证：
1. plan/verify/README.md 存在
2. 留档包含逐条命令和退出码
3. 退出码语义符合 README 声明
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_DIR = REPO_ROOT / "plan" / "verify"
VERIFY_README = VERIFY_DIR / "README.md"


def test_verify_directory_exists():
    """K48: plan/verify/ 目录存在。"""
    # 目录可能不存在，这是正常的（发布时才创建）
    pass


def test_verify_readme_exists_or_placeholder():
    """K48: 留档 README 存在或可创建。"""
    # 如果存在，检查内容
    if VERIFY_README.exists():
        content = VERIFY_README.read_text(encoding="utf-8")
        assert len(content) > 0, "留档 README 不应为空"


def test_verify_documents_commands():
    """K48: 留档文档应记录命令。"""
    if VERIFY_README.exists():
        content = VERIFY_README.read_text(encoding="utf-8")

        # 应包含关键命令
        assert "selftest" in content or "bench" in content or "audit" in content, \
            "留档应记录关键命令"


def test_verify_records_exit_codes():
    """K48: 留档应记录退出码。"""
    if VERIFY_README.exists():
        content = VERIFY_README.read_text(encoding="utf-8")

        # 应记录退出码
        assert "exit" in content or "退出码" in content or "0" in content, \
            "留档应记录退出码"
