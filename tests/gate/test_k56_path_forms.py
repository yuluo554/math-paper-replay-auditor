"""K56: 路径形态归一（POSIX 绝对路径在 Windows 上不得被误判为相对路径）。

CI 首跑实录：`_resolve_repo_path` 原先用 `lstrip("/")` 归一相对路径，
把 POSIX 绝对路径 `/tmp/xxx` 削成仓库相对的 `tmp/xxx`——
Windows（开发机）上恰好所有路径都是相对的所以全绿，
ubuntu runner 上临时目录是 `/tmp/...`，直接被解析成仓库内不存在的位置，
报"真值库不存在"。这是"本机全绿、CI 必红"家族里**判据依赖平台路径形态**的一支。

判别口诀：**"这个路径字符串是绝对的，是靠什么判定的？"**——
`Path(s).is_absolute()` 在 Windows 上对 `/tmp/x` 返回 False（无盘符），
必须按**形态**（前导 `/` 或 `X:/`）判定。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_k56_posix_absolute_path_is_not_rebased():
    """K56: POSIX 绝对路径必须原样保留（不得拼到仓库根下）。"""
    from auditor.benchmark.runner import _resolve_repo_path

    resolved = str(_resolve_repo_path("/tmp/aaa/bbb/truth.json"))
    # 不得出现"仓库根 + tmp"这种被 rebase 的形态
    assert not resolved.replace("\\", "/").endswith("tmp/aaa/bbb/truth.json") or \
        resolved.replace("\\", "/").startswith("/"), (
        f"K56 违规: POSIX 绝对路径被 rebase 成仓库相对路径: {resolved}"
    )
    assert "aaa" in resolved and "bbb" in resolved


def test_k56_windows_drive_absolute_path_is_not_rebased():
    """K56: Windows 盘符绝对路径必须原样保留。"""
    from auditor.benchmark.runner import _resolve_repo_path

    resolved = str(_resolve_repo_path("C:/tmp/aaa/truth.json"))
    assert resolved.replace("\\", "/").startswith("C:/"), (
        f"K56 违规: 盘符绝对路径被改写: {resolved}"
    )


def test_k56_repo_relative_path_is_rebased():
    """K56: 仓库相对路径仍须挂到数据根下（不能因修绝对路径而破坏相对路径）。"""
    from auditor.benchmark.runner import _resolve_repo_path

    resolved = _resolve_repo_path("data/benchmark/truth.json")
    assert resolved.exists(), f"K56: 相对路径未正确解析: {resolved}"


def test_k56_tempdir_truth_library_is_loadable(tmp_path):
    """K56: 临时目录里的真值库必须能被加载（CI 上 /tmp 形态的现场复现）。"""
    import json

    from auditor.benchmark.runner import load_truth

    bench = tmp_path / "bench"
    bench.mkdir()
    (bench / "truth.json").write_text(
        json.dumps([{"sample_id": "x", "expect": {"is_clean": True}}]),
        encoding="utf-8",
    )

    truth = load_truth(str(bench))
    assert len(truth) == 1, "K56: 临时目录真值库加载失败（路径形态处理有误）"
