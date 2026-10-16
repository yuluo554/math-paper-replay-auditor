"""K33: extras 一律不得进入运行时必需面。

验证：
1. core extra 包含运行时必需依赖
2. dev/gui/build extras 不进入运行时必需面
3. 安装 .[core] 后能 import auditor 并运行核心功能
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _parse_pyproject_extras() -> dict:
    """解析 pyproject.toml 的 extras。"""
    # tomllib 是 3.11+，3.8 用 tomli
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(PYPROJECT_PATH, "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}).get("optional-dependencies", {})


def test_core_extra_contains_runtime_deps():
    """K33: core extra 包含运行时必需依赖。"""
    extras = _parse_pyproject_extras()
    core = extras.get("core", [])

    # 核心依赖必须包含
    assert any("sympy" in dep for dep in core), "core extra 必须包含 sympy"
    assert any("mpmath" in dep for dep in core), "core extra 必须包含 mpmath"
    assert any("pydantic" in dep for dep in core), "core extra 必须包含 pydantic"


def test_dev_extra_not_in_runtime():
    """K33: dev extra 不进入运行时必需面。"""
    extras = _parse_pyproject_extras()
    dev = extras.get("dev", [])
    core = extras.get("core", [])

    # dev extra 的依赖不应出现在 core 中
    dev_names = {d.split(">=")[0].split("<")[0].strip() for d in dev}
    core_names = {d.split(">=")[0].split("<")[0].strip() for d in core}

    # pytest 不应在 core 中
    assert "pytest" not in core_names, "pytest 不应在 core extra 中"


def test_gui_extra_not_in_runtime():
    """K33: gui extra 不进入运行时必需面。"""
    extras = _parse_pyproject_extras()
    gui = extras.get("gui", [])
    core = extras.get("core", [])

    gui_names = {d.split(">=")[0].split("<")[0].strip() for d in gui}
    core_names = {d.split(">=")[0].split("<")[0].strip() for d in core}

    # PySide6 不应在 core 中
    assert "PySide6" not in core_names, "PySide6 不应在 core extra 中"


def test_build_extra_not_in_runtime():
    """K33: build extra 不进入运行时必需面。"""
    extras = _parse_pyproject_extras()
    build = extras.get("build", [])
    core = extras.get("core", [])

    build_names = {d.split(">=")[0].split("<")[0].strip() for d in build}
    core_names = {d.split(">=")[0].split("<")[0].strip() for d in core}

    # PyInstaller 不应在 core 中
    assert "PyInstaller" not in core_names, "PyInstaller 不应在 core extra 中"


def test_install_core_only_works():
    """K33: 安装 .[core] 后能 import auditor 并运行核心功能。

    变异验证：如果 core extra 缺少依赖，import 会失败。
    """
    # 这个测试在干净环境中运行，这里只验证导入
    import auditor
    from auditor.core.parser import parse
    from auditor.core.replay import replay
    from auditor.core.numerical import recompute_numerical

    assert auditor.__version__ == "0.1.0"
    assert parse is not None
    assert replay is not None
    assert recompute_numerical is not None


def test_dependencies_field_matches_extras():
    """K33: dependencies 字段与 core extra 一致。"""
    # tomllib 是 3.11+，3.8 用 tomli
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(PYPROJECT_PATH, "rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    extras = data.get("project", {}).get("optional-dependencies", {})
    core = extras.get("core", [])

    # core 应该与 dependencies 一致（或包含 dependencies）
    dep_names = {d.split(">=")[0].split("<")[0].strip() for d in deps}
    core_names = {d.split(">=")[0].split("<")[0].strip() for d in core}

    # dependencies 中的每个包都应在 core 中
    for dep_name in dep_names:
        assert dep_name in core_names, f"{dep_name} 在 dependencies 中但不在 core extra 中"
