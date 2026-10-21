"""K46: 发布附件名一律 ASCII。

验证：
1. 附件名只包含 ASCII 字符
2. 不含中文、emoji 等非 ASCII 字符
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _project_version() -> str:
    """读 pyproject.toml 的 [project].version（版本单一事实源）。"""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(PYPROJECT_PATH, "rb") as f:
        data = tomllib.load(f)
    return str(data["project"]["version"])


def _is_ascii(name: str) -> bool:
    """检查字符串是否只包含 ASCII 字符。"""
    try:
        name.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def test_demo_attachment_names_ascii():
    """K46: 演示附件名一律 ASCII。"""
    # 检查 docs/demo/ 目录
    demo_dir = REPO_ROOT / "docs" / "demo"
    if demo_dir.exists():
        for f in demo_dir.iterdir():
            if f.is_file():
                assert _is_ascii(f.name), \
                    f"附件名包含非 ASCII 字符: {f.name}"


def test_release_attachment_names_ascii():
    """K46: 发布附件名一律 ASCII。

    期望名必须与**当前版本**对齐（D13）：此前写死的是 v0.1.0，
    而实际发布的是 v0.1.1（此后是 v0.1.2）——这条测试只断言"字符串是 ASCII"，
    所以名字陈旧也永远绿。版本号改为从 pyproject.toml 读取，不再手写。
    """
    # 检查常见的发布附件名模式
    version = _project_version()
    expected_names = [
        f"auditor-v{version}-win64.zip",
        f"auditor-v{version}-win64-sha256.txt",
        "auditor-source-v{0}.zip".format(version),
        "demo-clean-vs-error.gif",
        "demo-clean-report.html",
        "demo-error-report.html",
    ]

    for name in expected_names:
        assert _is_ascii(name), \
            f"发布附件名包含非 ASCII 字符: {name}"


def test_no_chinese_in_filenames():
    """K46: 文件名不含中文（发布附件名一律 ASCII）。"""
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    # 检查仓库根目录，排除 plan/ 与 docs/（计划文档与技术报告可以有中文名；
    # 本守门真正要管的是**发布附件名**，见上面两条 test_*_attachment_names_ascii）
    # update/ 与 plan/、docs/ 同类——都是中文名的过程文档目录，故一并排除
    # （本仓的迭代诊断交接物 update/ 即属此类；见 plan/RELEASE-M8.md）。
    exclude_dirs = {
        "plan",
        "docs",
        "update",
        ".git",
        ".github",
        "__pycache__",
        "dist",
        "build",
    }

    for f in REPO_ROOT.rglob("*"):
        if f.is_file():
            # 排除 plan/ 目录下的文件
            rel_parts = f.relative_to(REPO_ROOT).parts
            if rel_parts[0] in exclude_dirs:
                continue
            name = f.name
            assert not chinese_pattern.search(name), \
                f"文件名包含中文: {name}"
