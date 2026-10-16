"""K50: 基准检出率与错误类型归属守门。

本守门补上 M1–M5 的真空：既有守门只断言"误报率 0"（K19），
从未断言"检出率"——引擎检出率跌到 20% 时 128 个测试仍然全绿，
因植入错误被静默空转、引擎只对唯一一类错误（dangling_ref）有效。

K50 三问（每次断言必须能答"是"）：
1. 检出率是否 ≥ 阈值（真值库中所有错误样本都被判 invalid）？
2. 每类错误的检出是否达到 manifest 的最低覆盖项数？
3. 检出的 error_type 是否与真值归属一致（防"张冠李戴"：
   任意一类错误触发就宣称检出，等于断言了所有判据）？

配套 K51 变异验证：故意弄坏被测行为 → 门必须变红。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_benchmark():
    """加载真值库与 manifest。"""
    bench = REPO_ROOT / "data" / "benchmark"
    truth = json.loads((bench / "truth.json").read_text(encoding="utf-8"))
    manifest = json.loads((bench / "manifest.json").read_text(encoding="utf-8"))
    return truth, manifest


def _audit_all():
    """运行基准，返回 (metrics, 逐样本结果)。"""
    from auditor.benchmark.runner import run_benchmark
    result = run_benchmark()
    return result.metrics, result.sample_results


# ── K50 主门：检出率 ──


def test_k50_detection_rate_meets_target():
    """K50: 检出率必须达 95%（真值库全量实跑，不是构造样本）。"""
    from auditor.benchmark.metrics import DETECTION_RATE_TARGET

    metrics, _ = _audit_all()
    assert metrics.total_errors > 0, "真值库无错误样本，检出率无从谈起"
    assert metrics.detection_rate >= DETECTION_RATE_TARGET, (
        f"K50 违规: 检出率 {metrics.detection_rate:.2%} < {DETECTION_RATE_TARGET:.0%}"
        f"（{metrics.detected_errors}/{metrics.total_errors}）"
    )


def test_k50_every_error_sample_detected():
    """K50: 每个错误样本都必须被判 invalid（逐样本点名，差异落到具体样本）。"""
    truth, _ = _load_benchmark()
    _, sample_results = _audit_all()

    by_id = {sr["sample_id"]: sr for sr in sample_results}
    missed = []
    for entry in truth:
        if entry["expect"]["is_clean"]:
            continue
        sid = entry["sample_id"]
        got = by_id.get(sid, {}).get("verdict")
        if got != "invalid":
            missed.append(f"{sid}(想 invalid，实得 {got})")

    assert not missed, "K50 违规: 以下错误样本未被检出:\n" + "\n".join(missed)


def test_k50_per_error_type_coverage():
    """K50: 每类错误检出数须达 manifest 的 min_required（防"各有件"被读成"全检出"）。"""
    _, manifest = _load_benchmark()
    metrics, _ = _audit_all()

    shortfalls = []
    for error_type, spec in manifest["by_error_type"].items():
        if error_type == "clean":
            continue
        stats = metrics.by_error_type.get(error_type, {"detected": 0, "total": 0})
        if stats["detected"] < spec["min_required"]:
            shortfalls.append(
                f"{error_type}: 检出 {stats['detected']} < 要求 {spec['min_required']}"
                f"（总数 {stats['total']}）"
            )
    assert not shortfalls, "K50 违规: 错误类型覆盖不足:\n" + "\n".join(shortfalls)


def test_k50_error_type_attribution():
    """K50: 检出的 error_type 必须与真值归属一致（防张冠李戴）。

    只查"是否判 invalid"会被"任意一类错误一律命中"蒙混过关；
    必须逐样本核对**归属的那一类**是否真的出现在 invalid 断言里。
    """
    from auditor.benchmark.runner import _audit_sample

    truth, _ = _load_benchmark()
    mismatches = []

    for entry in truth:
        if entry["expect"]["is_clean"]:
            continue
        want = entry["expect"]["error_type"]
        claims = _audit_sample(
            entry["sample_id"], entry["input_card"]["paper_tex"]
        )
        got = {
            c.get("error_type")
            for c in claims
            if c.get("verdict") == "invalid"
        }
        if want not in got:
            mismatches.append(
                f"{entry['sample_id']}: 真值 {want}，实际命中 {sorted(x for x in got if x)}"
            )

    assert not mismatches, "K50 违规: 错误类型归属不符:\n" + "\n".join(mismatches)


def test_k50_upstream_claims_are_not_all_undecidable():
    """K50: 错误样本的上游断言不得整片 undecidable。

    防"引擎对错误样本一律说判不了"——那会让检出率靠某一类畸形断言撑起来，
    而其余引擎实际是空转。要求：错误样本至少有一条非 undecidable 的 invalid 断言。
    """
    from auditor.benchmark.runner import _audit_sample

    truth, _ = _load_benchmark()
    problems = []
    for entry in truth:
        if entry["expect"]["is_clean"]:
            continue
        claims = _audit_sample(
            entry["sample_id"], entry["input_card"]["paper_tex"]
        )
        engines = {c["engine"] for c in claims if c.get("verdict") == "invalid"}
        if not engines:
            problems.append(f"{entry['sample_id']}: 无任何 invalid 断言")
    assert not problems, "K50 违规:\n" + "\n".join(problems)


# ── K51 变异验证：弄坏被测行为 → 门必须变红 ──


def test_k51_mutation_engine_blind_to_step_errors():
    """K51: 让重放引擎对不等价步一律放行 → 检出率门必须变红。

    变异打在**被测行为**上（改 replay 的判定），不是改测试的存在形式。
    """
    import auditor.core.replay as replay_mod
    from auditor.benchmark.runner import run_benchmark

    original = replay_mod._verify_equality_chain

    def blind_chain(equations, function_defs=None):
        from auditor.core.types import Verdict
        steps = [{"expr": f"{a} = {b}", "rule": "mutated_pass", "valid": True}
                 for a, b in equations]
        return Verdict.OK, steps, "变异：一律放行"

    replay_mod._verify_equality_chain = blind_chain
    try:
        result = run_benchmark()
        assert not result.metrics.overall_passed or \
            result.metrics.detection_rate < 1.0, (
            "K51 变异失败: 重放引擎对不等价步一律放行后，检出率门仍全绿——假门"
        )
    finally:
        replay_mod._verify_equality_chain = original


def test_k51_mutation_numerical_self_compare():
    """K51: 数值引擎退回"拿报告值自比" → numeric_mismatch 必须漏检。"""
    import auditor.core.numerical as num_mod
    from auditor.benchmark.runner import _audit_sample

    original = num_mod._evaluate_formula_mpmath

    def self_compare(formula, x_value):
        # 变异：不真算，直接回一个"必然吻合"的值是做不到的，
        # 故改为让求值恒定失败 → 复算退化为 undecidable → 该类型漏检
        return None

    num_mod._evaluate_formula_mpmath = self_compare
    try:
        claims = _audit_sample(
            "B003-001-numeric_mismatch",
            "data/benchmark/B003-001-numeric_mismatch/paper.tex",
        )
        got = {c.get("error_type") for c in claims if c.get("verdict") == "invalid"}
        assert "numeric_mismatch" not in got, (
            "K51 变异失败: 数值路径被弄坏后仍检出 numeric_mismatch——探针没打在消费处"
        )
    finally:
        num_mod._evaluate_formula_mpmath = original


def test_k51_mutation_grid_blind_to_dangling():
    """K51: 让依赖图不放行悬空引用检测 → dangling_ref 必须漏检。"""
    import auditor.core.graph as graph_mod
    from auditor.benchmark.runner import _audit_sample

    original = graph_mod._find_dangling_refs

    graph_mod._find_dangling_refs = lambda g, t: []
    try:
        claims = _audit_sample(
            "B004-001-dangling_ref",
            "data/benchmark/B004-001-dangling_ref/paper.tex",
        )
        got = {c.get("error_type") for c in claims if c.get("verdict") == "invalid"}
        assert "dangling_ref" not in got, (
            "K51 变异失败: 悬空引用检测被关掉后仍检出——守门没覆盖该通路"
        )
    finally:
        graph_mod._find_dangling_refs = original


def test_k51_mutation_generator_silent_noop():
    """K51: 注入器静默空转（返回原文）→ 样本退化为干净论文，必须被自证拦下。"""
    from data.benchmark.generator.error_injector import inject_dimension_mismatch

    with pytest.raises(ValueError):
        inject_dimension_mismatch("this text has no anchor", 42)
