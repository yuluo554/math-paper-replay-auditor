"""K52: 冻结态与源码态行为一致（值域级对账）。

M5 实录的教训：冻结态与源码态可以**静默分叉**——`sympy.parse_latex`
在 antlr4 运行时缺失时不抛错、直接返回 None，被上层当成"解析成功"，
使重放链在 exe 里退化为全 invalid。当时 128 个守门测试全绿，
因为没有一个测试跑过打包产物。

本守门要求：**冻结产物一旦存在，其基准结论必须与源码态逐项一致**。
产物不存在时明确 skip（不假装通过），由发布前构建步骤保证其存在。

K52 与 K50 的分工：K50 管"源码态引擎有没有能力"，
K52 管"这份能力有没有被完整打进 exe"。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLI_EXE = REPO_ROOT / "dist" / "auditor-cli.exe"


def _run(cmd) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _parse_metrics(stdout: str) -> dict:
    """从 bench 输出解析关键指标行。"""
    out = {}
    for line in stdout.splitlines():
        if "检出率:" in line:
            out["detection"] = line.strip()
        elif "误报率:" in line:
            out["false_positive"] = line.strip()
        elif line.strip().startswith("总体:"):
            out["overall"] = line.strip()
        elif line.strip().startswith(("dimension_mismatch:", "illegal_derivation:",
                                      "numeric_mismatch:", "dangling_ref:",
                                      "dep_chain_break:")):
            key = line.split(":")[0].strip()
            out[key] = line.strip()
    return out


@pytest.mark.skipif(not CLI_EXE.exists(), reason="冻结产物不存在（发布前构建后此门生效）")
def test_k52_frozen_cli_bench_matches_source():
    """K52: 冻结 CLI 的 bench 结论必须与源码态一致。"""
    frozen = _run([str(CLI_EXE), "bench"])
    source = _run([sys.executable, "-m", "auditor.benchmark.runner"])

    f_metrics = _parse_metrics(frozen.stdout)
    s_metrics = _parse_metrics(source.stdout)

    assert f_metrics, f"冻结态 bench 无输出（stderr: {frozen.stderr[:400]}）"
    assert s_metrics, f"源码态 bench 无输出（stderr: {source.stderr[:400]}）"

    assert f_metrics == s_metrics, (
        "K52 违规: 冻结态与源码态基准结论不一致（打包漏带依赖会导致静默降级）\n"
        f"  冻结态: {f_metrics}\n"
        f"  源码态: {s_metrics}"
    )


@pytest.mark.skipif(not CLI_EXE.exists(), reason="冻结产物不存在")
def test_k52_frozen_cli_detects_all_error_types():
    """K52: 冻结态必须逐类检出（不是靠"总体通过"掩盖某类归零）。"""
    frozen = _run([str(CLI_EXE), "bench"])
    text = frozen.stdout

    for error_type in ("dimension_mismatch", "illegal_derivation",
                       "numeric_mismatch", "dangling_ref", "dep_chain_break"):
        line = next(
            (ln for ln in text.splitlines() if ln.strip().startswith(error_type + ":")),
            None,
        )
        assert line is not None, f"K52: 冻结态输出缺少 {error_type} 一行"
        assert "3/3" in line, f"K52: 冻结态 {error_type} 未全检出: {line}"


@pytest.mark.skipif(not CLI_EXE.exists(), reason="冻结产物不存在")
def test_k52_frozen_cli_selftest_ok():
    """K52: 冻结态 selftest 必须 exit 0。"""
    result = _run([str(CLI_EXE), "selftest"])
    assert result.returncode == 0, (
        f"K52: 冻结态 selftest 退出码 {result.returncode}（期望 0）\n"
        f"stdout: {result.stdout[:300]}\nstderr: {result.stderr[:300]}"
    )
