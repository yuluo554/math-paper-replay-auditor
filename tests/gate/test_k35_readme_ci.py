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


def test_ci_workflow_exists():
    """K35: CI workflow 必须存在（原版在 CI 缺失时静默通过，是空转门）。"""
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        ci = REPO_ROOT / ".github" / "workflows" / "ci.yaml"
    assert ci.exists(), (
        "K35 违规: 缺 .github/workflows/ci.yml——"
        "原版守门在 CI 不存在时静默通过（空转门）"
    )


def _declared_floor() -> str:
    """读 pyproject.toml 声明的最低 Python 版本（requires-python）。"""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    spec = data["project"]["requires-python"]
    # 形如 ">=3.12"
    return spec.replace(">=", "").strip()


def test_ci_covers_declared_floor():
    """K35: CI 矩阵必须覆盖**声明的最低 Python 版本**与当前主版本。

    D11/DEC1=B：此前本门硬断言 `"3.8" in ci.yml`，
    floor 抬到 3.12 后它会变红——但那不是"CI 配置错了"，
    而是"门禁写死了旧口径"。现在改为跟随 pyproject 的 requires-python：
    门禁仍要求「最低版本必须在矩阵里」（这才是它的本意），
    但不再写死某个具体版本号。
    """
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        ci = REPO_ROOT / ".github" / "workflows" / "ci.yaml"
    content = ci.read_text(encoding="utf-8")

    floor = _declared_floor()
    assert f'"{floor}"' in content or f"'{floor}'" in content, (
        f"K35: CI 矩阵缺声明的最低版本 {floor}（requires-python）"
    )
    assert '"3.12"' in content or "'3.12'" in content, "K35: CI 矩阵缺 3.12"


def test_ci_does_not_test_eol_interpreters():
    """K35: CI 矩阵不得再测已 EOL 的 Python 版本（3.8/3.10/3.11）。

    与上一条互为对照：上一条要求"floor 必须在矩阵里"，
    这一条要求"矩阵里不得有比 floor 更老的版本"。
    """
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        ci = REPO_ROOT / ".github" / "workflows" / "ci.yaml"
    content = ci.read_text(encoding="utf-8")

    floor = _declared_floor()
    for eol in ("3.8", "3.9", "3.10", "3.11"):
        if eol == floor:
            continue
        assert f'python: "{eol}"' not in content, (
            f"K35 违规: CI 矩阵仍测已 EOL 的 Python {eol}（floor={floor}）"
        )


def test_ci_sets_utf8_env():
    """K35: CI 必须设 PYTHONUTF8（否则测试打印中文在 cp1252 管道上崩）。"""
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        ci = REPO_ROOT / ".github" / "workflows" / "ci.yaml"
    content = ci.read_text(encoding="utf-8")

    assert "PYTHONUTF8" in content, (
        "K35: CI 未设 PYTHONUTF8——本机 `py -X utf8` 掩盖的编码缺口会在 CI 暴露"
    )


def test_ci_smokes_bare_console_script():
    """K35: CI 必须跑裸 console script（安装面第四面，python -m 过不等于它过）。"""
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        ci = REPO_ROOT / ".github" / "workflows" / "ci.yaml"
    content = ci.read_text(encoding="utf-8")

    assert re.search(r"^\s*run:\s*auditor\s", content, re.MULTILINE), (
        "K35: CI 未跑裸 `auditor ...`——只跑 `python -m` 会漏掉"
        "「包没进安装面」类缺陷"
    )


def test_ci_matches_readme_extras():
    """K35: CI 与 README 用同一 extras 集合。"""
    readme_extras = _extract_readme_install_extras()
    ci_extras = _get_ci_extras()

    assert readme_extras, "README 未提取到 extras"
    assert ci_extras, "K35: CI 未提取到 extras（CI 缺失或未装 extras）"

    assert readme_extras == ci_extras, (
        f"README extras ({readme_extras}) 与 CI extras ({ci_extras}) 不一致"
    )
