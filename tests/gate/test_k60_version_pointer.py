"""K60: 版本指针守门（SI-048）。

背景（2026-10-25 实测）：`v0.1.2` 的 tag 树里 README `:3` 仍写
「✅ v0.1.1 已发布」并把 Release 链接指向 `releases/tag/v0.1.1`。
用户从 `v0.1.2` 的 tag 树或源码包进去照 README 走，拿到的是上一版。

判据（两条都定位到**声明性那一行**，不做全文存在性判断 —— presence ≠ correctness：
`v0.1.2` 这个词可能只出现在变更日志里，那不证明发布指针是对的）：

  ① README 状态行的「vX.Y.Z 已发布」X.Y.Z == 当前版本；
  ② 同一行 / 全文的 `releases/tag/vX.Y.Z` 链接里，**至少有一条**指向当前版本
     （「至少一条」而非「全部」：README 允许同时列出历史 Release，
     但通往当前版本的通路必须存在，否则用户没有下载到新版的入口）。

③ 是**门本身的负控**：喂合成的旧版本 README，两条必须报错。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _version(text: str) -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m, "pyproject.toml 里找不到 project.version"
    return m.group(1)


# ---------------------------------------------------------------- 审计函数

def audit_status_line(readme: str, version: str) -> list[str]:
    """① README 状态行的「vX.Y.Z 已发布」。"""
    found = re.findall(r"v(\d+\.\d+\.\d+)\s*已发布", readme)
    if not found:
        return ["README 找不到「vX.Y.Z 已发布」状态声明 —— 该指针被删或改写了措辞"]
    return [f"README 状态行 = v{v} 已发布，期望 v{version}" for v in found if v != version]


def audit_release_link(readme: str, version: str) -> list[str]:
    """② 至少一条 releases/tag/vX.Y.Z 必须指向当前版本。"""
    found = re.findall(r"releases/tag/v(\d+\.\d+\.\d+)", readme)
    if not found:
        return ["README 找不到 releases/tag/vX.Y.Z Release 链接"]
    if version not in found:
        return [
            f"README 的 Release 链接里没有一条指向 v{version}"
            f"（实测链接版本：{sorted(set(found))}）"
        ]
    return []


# ---------------------------------------------------------------- 真文件断言

def test_readme_status_line_matches_version():
    """① —— 状态行的「已发布」版本必须等于当前版本。"""
    version = _version(_read(PYPROJECT))
    problems = audit_status_line(_read(README), version)
    assert problems == [], "\n".join(problems)


def test_readme_release_link_reaches_current_version():
    """② —— 必须存在通往当前版本的 Release 链接。"""
    version = _version(_read(PYPROJECT))
    problems = audit_release_link(_read(README), version)
    assert problems == [], "\n".join(problems)


# ---------------------------------------------------------------- ③ 负控

def test_negative_control_status_line_detects_stale():
    stale = "**状态**：✅ v0.9.8 已发布（[Release](https://x/releases/tag/v0.9.8)）"
    assert audit_status_line(stale, "0.9.9") != []
    assert audit_status_line("**状态**：✅ v0.9.9 已发布", "0.9.9") == []


def test_negative_control_status_line_detects_missing():
    assert audit_status_line("**状态**：已发布", "0.9.9") != []


def test_negative_control_release_link_detects_stale():
    stale = "见 [Release](https://x/releases/tag/v0.9.8)"
    problems = audit_release_link(stale, "0.9.9")
    assert problems != []
    assert "v0.9.9" in problems[0]


def test_negative_control_release_link_allows_historical_alongside_current():
    """历史链接可以并存 —— 只要有一条指向当前版本就不算缺陷。

    这条防的是「门写得太严把合法的历史链接也判红」，那样人会去删历史。
    """
    mixed = (
        "见 [Release](https://x/releases/tag/v0.9.9) "
        "（上一版 [v0.9.8](https://x/releases/tag/v0.9.8)）"
    )
    assert audit_release_link(mixed, "0.9.9") == []
