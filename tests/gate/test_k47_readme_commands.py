"""K47: README 命令逐字可跑。

M5 遗留教训：原版只做 `assert "pip install" in content` 这类字面断言，
于是 README 里指向 `data/benchmark/samples/C001-clean/paper.tex`（不存在的路径）
的命令、以及 `python -m auditor`（缺 __main__.py）的命令，
在 128 个测试全绿的情况下没人发现。

本守门要求：README 里出现的**每一条 python -m auditor 命令**，
其引用的路径必须在仓库中真实存在。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_exists():
    """K47: README.md 存在。"""
    assert README_PATH.exists(), "README.md 必须存在"


def test_readme_has_install_command():
    """K47: README 包含安装命令。"""
    assert "pip install" in _readme_text(), "README 应包含 pip install 命令"


def test_readme_install_extras_exist_in_pyproject():
    """K47: README 用到的 extras 必须在 pyproject 中声明（安装面对账）。"""
    text = _readme_text()
    extras_used = set()
    for m in re.finditer(r'pip install -e "\.\[([^\]]+)\]"', text):
        extras_used.update(x.strip() for x in m.group(1).split(","))

    assert extras_used, "README 未见 `pip install -e \".[...]\"` 形式"

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = set(re.findall(r"^(\w+)\s*=\s*\[", pyproject, re.MULTILINE))

    missing = extras_used - declared
    assert not missing, f"K47: README 用了未声明的 extras: {missing}"


def test_readme_auditor_commands_reference_existing_paths():
    """K47: README 中每条 python -m auditor 命令引用的路径必须真实存在。

    这是把"逐字可跑"从口号变成断言的关键一条——
    对不存在的路径，`audit` 会 exit 2、`bench` 会 exit 2，
    旧版测试却因为只查子串而全绿。
    """
    text = _readme_text()
    missing = []

    for line in text.splitlines():
        if "python -m auditor" not in line and "auditor.exe" not in line:
            continue
        # 逐条抽 --input / --output 形态的路径参数
        for m in re.finditer(r"--(?:input|output)\s+(\S+)", line):
            path_str = m.group(1).strip()
            if not path_str or path_str.startswith(("<", "$")):
                continue
            candidate = REPO_ROOT / path_str
            if not candidate.exists():
                missing.append(f"{path_str}（来自: {line.strip()}）")

    assert not missing, (
        "K47 违规: README 命令引用了不存在的路径:\n" + "\n".join(missing)
    )


def test_readme_quoted_module_invocations_are_importable():
    """K47: README 里 `python -m <mod>` 的模块必须真的可执行（含 __main__）。"""
    text = _readme_text()
    modules = set(re.findall(r"python -m (auditor(?:\.\w+)*)", text))

    assert modules, "README 未见 `python -m auditor...` 形式"

    for mod in modules:
        if mod == "auditor":
            # 包级调用需要 __main__.py，否则报 "No module named auditor.__main__"
            assert (REPO_ROOT / "src" / "auditor" / "__main__.py").exists(), (
                "K47 违规: README 用 `python -m auditor`，但缺 src/auditor/__main__.py"
            )


def test_readme_has_quick_start():
    """K47: README 有快速开始章节。"""
    content = _readme_text()
    assert "安装" in content or "Install" in content, "README 应有安装章节"
    assert "使用" in content or "Usage" in content or "快速开始" in content, \
        "README 应有使用章节"


def test_readme_documents_exit_codes():
    """K47: README 应说明退出码语义（用户据以判断"跑通"）。"""
    content = _readme_text()
    assert "退出码" in content or "exit" in content.lower(), (
        "README 应说明退出码语义（0=无问题 / 1=检出问题 / 2=用法错误 / 3=缺依赖）"
    )
