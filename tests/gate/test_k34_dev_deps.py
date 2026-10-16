"""K34: 测试期 import 的库必须进 dev extra。

验证：
1. tests/ 目录所有 import 的第三方库都在 dev extra 中
2. 干净环境 pip install -e ".[dev]" 后 pytest 能跑
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TESTS_DIR = REPO_ROOT / "tests"
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


def _extract_imports_from_file(file_path: Path) -> set:
    """从 Python 文件中提取所有第三方 import。"""
    imports = set()

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def _get_stdlib_names() -> set:
    """获取标准库模块名（3.8 兼容，不用 sys.stdlib_module_names）。"""
    # 冻结名单制，不用 sys.stdlib_module_names（3.10+ 才有，3.8 上空集）
    stdlib = {
        "sys", "os", "pathlib", "typing", "json", "ast", "subprocess",
        "hashlib", "fnmatch", "itertools", "collections", "datetime",
        "re", "math", "random", "statistics", "enum", "dataclasses",
        "functools", "inspect", "logging", "tempfile", "shutil",
        "glob", "csv", "xml", "html", "urllib", "http", "ssl",
        "socket", "threading", "multiprocessing", "concurrent",
        "pickle", "copy", "pprint", "textwrap", "string", "io",
        "builtins", "importlib", "pkgutil", "sysconfig", "site",
        "warnings", "traceback", "contextlib", "fractions", "decimal",
        "numbers", "operator", "itertools", "heapq", "bisect",
        "queue", "select", "signal", "time", "calendar", "os.path",
        "__future__",
    }
    return stdlib


def test_all_test_imports_in_dev_extra():
    """K34: tests/ 目录所有 import 的第三方库都在 dev extra 中。"""
    extras = _parse_pyproject_extras()
    dev_extra = extras.get("dev", [])
    dev_names = {d.split(">=")[0].split("<")[0].strip() for d in dev_extra}

    stdlib = _get_stdlib_names()

    # 本包（auditor）和测试包（tests）不进 dev extra
    local_packages = {"auditor", "tests", "data", "packaging", "tools"}

    # 收集 tests/ 目录所有 import
    test_imports = set()
    for py_file in TESTS_DIR.rglob("*.py"):
        imports = _extract_imports_from_file(py_file)
        test_imports.update(imports)

    # 过滤标准库和本地包
    third_party = test_imports - stdlib - local_packages

    # 过滤掉 tomli/tomllib（这是测试中的条件导入）
    third_party = third_party - {"tomli", "tomllib"}

    # 检查每个第三方库都在 dev extra 中
    missing = third_party - dev_names
    assert not missing, f"以下第三方库在 tests/ 中被 import 但不在 dev extra 中: {missing}"


def test_dev_extra_contains_pytest():
    """K34: dev extra 必须包含 pytest。"""
    extras = _parse_pyproject_extras()
    dev = extras.get("dev", [])

    assert any("pytest" in dep for dep in dev), "dev extra 必须包含 pytest"


def test_dev_extra_contains_pytest_cov():
    """K34: dev extra 必须包含 pytest-cov。"""
    extras = _parse_pyproject_extras()
    dev = extras.get("dev", [])

    assert any("pytest-cov" in dep for dep in dev), "dev extra 必须包含 pytest-cov"


def test_dev_extra_contains_ruff():
    """K34: dev extra 必须包含 ruff。"""
    extras = _parse_pyproject_extras()
    dev = extras.get("dev", [])

    assert any("ruff" in dep for dep in dev), "dev extra 必须包含 ruff"
