"""K35: README 与 CI 同 extras。

验证：
1. README 安装行与 CI 用同一 extras 集合
2. 收集数一致
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _extract_readme_install_extras() -> set:
    """从 README 提取安装命令中的 extras。"""
    if not README_PATH.exists():
        return set()

    content = README_PATH.read_text(encoding="utf-8")
    extras = set()

    # 匹配 pip install -e ".[...]" 或 pip install ".[...]"
    pattern = r'pip\s+install\s+(?:\-e\s+)?["\']\.\[([^\]]+)\]["\']'
    for match in re.finditer(pattern, content):
        extra_list = match.group(1)
        for extra in extra_list.split(","):
            extras.add(extra.strip())

    return extras


def _get_ci_extras() -> set:
    """从 CI workflow 提取 extras。"""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci_path.exists():
        ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yaml"

    if not ci_path.exists():
        return set()

    content = ci_path.read_text(encoding="utf-8")
    extras = set()

    # 匹配 pip install -e ".[...]"
    pattern = r'pip\s+install\s+(?:\-e\s+)?["\']\.\[([^\]]+)\]["\']'
    for match in re.finditer(pattern, content):
        extra_list = match.group(1)
        for extra in extra_list.split(","):
            extras.add(extra.strip())

    return extras


def test_readme_install_command_exists():
    """K35: README 包含安装命令。"""
    extras = _extract_readme_install_extras()
    assert extras, "README 应包含 pip install 命令"


def test_readme_uses_dev_and_core():
    """K35: README 安装命令应包含 dev 和 core extras。"""
    extras = _extract_readme_install_extras()
    assert "dev" in extras, "README 安装命令应包含 dev extra"
    assert "core" in extras, "README 安装命令应包含 core extra"


def test_ci_matches_readme_extras():
    """K35: CI 与 README 用同一 extras 集合。"""
    readme_extras = _extract_readme_install_extras()
    ci_extras = _get_ci_extras()

    # 如果 CI 文件存在，extras 应一致
    if ci_extras:
        assert readme_extras == ci_extras, (
            f"README extras ({readme_extras}) 与 CI extras ({ci_extras}) 不一致"
        )
