"""基准 runner 测试——验证 runner 正确性。

K18: 覆盖度分母反射自代码常量
K19: 误报率 0 优先
K22: 探活打在消费处
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from auditor.benchmark.runner import (
    BenchmarkResult,
    run_benchmark,
    load_truth,
    load_manifest,
    ERROR_TYPES,
    _aggregate_verdict,
)


def test_error_types_whitelist():
    """K18: 错误类型白名单正确。"""
    assert len(ERROR_TYPES) == 5
    assert "dimension_mismatch" in ERROR_TYPES
    assert "illegal_derivation" in ERROR_TYPES
    assert "numeric_mismatch" in ERROR_TYPES
    assert "dangling_ref" in ERROR_TYPES
    assert "dep_chain_break" in ERROR_TYPES


def test_load_truth():
    """真值库可加载。"""
    truth = load_truth("data/benchmark")
    assert len(truth) == 18

    # 验证结构
    for entry in truth:
        assert "sample_id" in entry
        assert "input_card" in entry
        assert "expect" in entry
        # K17: 无 observed 字段
        assert "observed" not in entry


def test_load_manifest():
    """manifest 可加载。"""
    manifest = load_manifest("data/benchmark")
    assert "total_samples" in manifest
    assert "by_error_type" in manifest
    assert manifest["total_samples"] == 18


def test_aggregate_verdict_priority():
    """verdict 聚合优先级：invalid > undecidable > ok。"""
    # 全 ok
    assert _aggregate_verdict([
        {"verdict": "ok"},
        {"verdict": "ok"},
    ]) == "ok"

    # 有 invalid
    assert _aggregate_verdict([
        {"verdict": "ok"},
        {"verdict": "invalid"},
    ]) == "invalid"

    # 有 undecidable 无 invalid
    assert _aggregate_verdict([
        {"verdict": "ok"},
        {"verdict": "undecidable"},
    ]) == "undecidable"

    # invalid 优先级最高
    assert _aggregate_verdict([
        {"verdict": "undecidable"},
        {"verdict": "invalid"},
        {"verdict": "ok"},
    ]) == "invalid"


def test_aggregate_verdict_empty():
    """空断言列表返回 undecidable。"""
    assert _aggregate_verdict([]) == "undecidable"


def test_run_benchmark_basic():
    """基准 runner 基本运行。"""
    result = run_benchmark(benchmark_dir="data/benchmark")
    assert isinstance(result, BenchmarkResult)
    assert result.total_samples == 18
    assert result.exit_code in (0, 1)
    assert result.metrics is not None


def test_run_benchmark_with_only():
    """--only 白名单过滤。"""
    result = run_benchmark(
        benchmark_dir="data/benchmark",
        only=["dimension_mismatch", "numeric_mismatch"],
    )
    # 2 类错误 × 3 样本 + 3 个干净样本（用于误报测试）= 9 个样本
    assert result.total_samples == 9


def test_run_benchmark_only_invalid_type():
    """--only 传入白名单外类型 = exit 2。"""
    result = run_benchmark(
        benchmark_dir="data/benchmark",
        only=["nonexistent_type"],
    )
    assert result.exit_code == 2


def test_run_benchmark_missing_dir():
    """基准目录不存在 = exit 2。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_benchmark(benchmark_dir=tmpdir)
        assert result.exit_code == 2


def test_sample_results_structure():
    """样本结果结构正确。"""
    result = run_benchmark(
        benchmark_dir="data/benchmark",
        only=["dimension_mismatch"],
    )
    # 3 个错误样本 + 3 个干净样本 = 6 个样本
    assert len(result.sample_results) == 6

    # 验证错误样本
    error_samples = [sr for sr in result.sample_results if sr.get("error_type") == "dimension_mismatch"]
    assert len(error_samples) == 3

    for sr in error_samples:
        assert "sample_id" in sr
        assert "verdict" in sr
        assert "expected" in sr
        assert sr["error_type"] == "dimension_mismatch"


def test_metrics_attached():
    """指标已挂载到结果。"""
    result = run_benchmark(benchmark_dir="data/benchmark")
    assert result.metrics is not None
    assert result.metrics.total_samples == 18
    assert result.metrics.total_errors == 15
    assert result.metrics.total_clean == 3


def test_k19_false_positive_gate():
    """K19: 误报率 0 守门。"""
    result = run_benchmark(benchmark_dir="data/benchmark")
    assert result.metrics.false_positive_rate <= 0.0, (
        f"K19 违规: 误报率 {result.metrics.false_positive_rate} > 0"
    )


def test_k18_coverage_reflection():
    """K18: 覆盖度分母反射自代码常量。"""
    manifest = load_manifest("data/benchmark")
    # manifest 中的 min_required 必须与 ERROR_TYPES 一致
    for error_type in ERROR_TYPES:
        assert error_type in manifest["by_error_type"]
        assert manifest["by_error_type"][error_type]["min_required"] >= 3


def test_batch_failure_isolation():
    """K30: 单件异常不中断整批。"""
    # 使用一个不存在的样本来触发异常
    # 验证 runner 继续处理其他样本
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建部分有效的 truth.json
        truth = [
            {
                "sample_id": "bad-sample",
                "input_card": {"paper_tex": "nonexistent.tex", "paper_id": "bad"},
                "expect": {
                    "error_type": "dimension_mismatch",
                    "location": "test",
                    "is_clean": False,
                    "expected_verdict": "invalid",
                },
                "generator_seed": 1,
                "generator_version": "1.0.0",
            },
            {
                "sample_id": "good-sample",
                "input_card": {"paper_tex": "data/benchmark/C001-clean/paper.tex", "paper_id": "good"},
                "expect": {
                    "error_type": None,
                    "location": None,
                    "is_clean": True,
                    "expected_verdict": "ok",
                },
                "generator_seed": 2,
                "generator_version": "1.0.0",
            },
        ]

        truth_path = Path(tmpdir) / "truth.json"
        truth_path.write_text(json.dumps(truth, indent=2))

        manifest = {
            "total_samples": 2,
            "sampling_note": "test",
            "by_error_type": {
                "dimension_mismatch": {"total": 1, "min_required": 1},
                "clean": {"total": 1, "min_required": 1},
            },
        }
        manifest_path = Path(tmpdir) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        result = run_benchmark(benchmark_dir=tmpdir)
        # 应该处理了 2 个样本，不是只处理了 1 个
        assert result.total_samples == 2
