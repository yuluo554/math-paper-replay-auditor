"""指标计算测试——验证 calculate_metrics 正确性。

K18: 覆盖度分母反射自代码常量
K19: 误报率 0 优先
"""

from __future__ import annotations

import pytest

from auditor.benchmark.metrics import (
    BenchmarkMetrics,
    calculate_metrics,
    DETECTION_RATE_TARGET,
    FALSE_POSITIVE_RATE_TARGET,
)


def test_empty_truth():
    """空真值库应返回零指标。"""
    metrics = calculate_metrics([], {})
    assert metrics.total_samples == 0
    assert metrics.detection_rate == 0.0
    assert metrics.false_positive_rate == 0.0
    assert metrics.overall_passed  # 空集视为通过


def test_all_clean_passed():
    """所有干净论文均通过 = 误报率 0。"""
    truth = [
        {
            "sample_id": "C001-clean",
            "expect": {
                "is_clean": True,
                "expected_verdict": "ok",
                "error_type": None,
            },
        },
        {
            "sample_id": "C002-clean",
            "expect": {
                "is_clean": True,
                "expected_verdict": "ok",
                "error_type": None,
            },
        },
    ]
    results = {"C001-clean": "ok", "C002-clean": "ok"}

    metrics = calculate_metrics(truth, results)
    assert metrics.total_clean == 2
    assert metrics.false_positive_rate == 0.0
    assert metrics.false_positive_rate_passed


def test_all_clean_detected_as_error():
    """干净论文被误报 = 误报率 100%。"""
    truth = [
        {
            "sample_id": "C001-clean",
            "expect": {
                "is_clean": True,
                "expected_verdict": "ok",
                "error_type": None,
            },
        },
    ]
    results = {"C001-clean": "invalid"}

    metrics = calculate_metrics(truth, results)
    assert metrics.false_positives == 1
    assert metrics.false_positive_rate == 1.0
    assert not metrics.false_positive_rate_passed


def test_all_errors_detected():
    """所有错误均检出 = 检出率 100%。"""
    truth = [
        {
            "sample_id": "B001",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
        {
            "sample_id": "B002",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "illegal_derivation",
            },
        },
    ]
    results = {"B001": "invalid", "B002": "invalid"}

    metrics = calculate_metrics(truth, results)
    assert metrics.total_errors == 2
    assert metrics.detected_errors == 2
    assert metrics.detection_rate == 1.0
    assert metrics.detection_rate_passed


def test_missed_errors():
    """错误未检出 = 检出率下降。"""
    truth = [
        {
            "sample_id": "B001",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
        {
            "sample_id": "B002",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "illegal_derivation",
            },
        },
    ]
    results = {"B001": "ok", "B002": "invalid"}

    metrics = calculate_metrics(truth, results)
    assert metrics.detected_errors == 1
    assert metrics.detection_rate == 0.5
    assert not metrics.detection_rate_passed


def test_undecidable_counts_as_not_detected():
    """undecidable 不算检出。"""
    truth = [
        {
            "sample_id": "B001",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
    ]
    results = {"B001": "undecidable"}

    metrics = calculate_metrics(truth, results)
    assert metrics.detected_errors == 0
    assert metrics.detection_rate == 0.0


def test_by_error_type_stats():
    """按错误类型统计。"""
    truth = [
        {
            "sample_id": "B001",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
        {
            "sample_id": "B002",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
        {
            "sample_id": "B003",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "illegal_derivation",
            },
        },
    ]
    results = {"B001": "invalid", "B002": "ok", "B003": "invalid"}

    metrics = calculate_metrics(truth, results)

    assert "dimension_mismatch" in metrics.by_error_type
    assert metrics.by_error_type["dimension_mismatch"]["total"] == 2
    assert metrics.by_error_type["dimension_mismatch"]["detected"] == 1

    assert "illegal_derivation" in metrics.by_error_type
    assert metrics.by_error_type["illegal_derivation"]["total"] == 1
    assert metrics.by_error_type["illegal_derivation"]["detected"] == 1


def test_overall_passed():
    """整体达标条件。"""
    # 检出率达标 + 误报率达标 = 通过
    truth = [
        {
            "sample_id": "B001",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
        {
            "sample_id": "C001",
            "expect": {
                "is_clean": True,
                "expected_verdict": "ok",
                "error_type": None,
            },
        },
    ]
    results = {"B001": "invalid", "C001": "ok"}

    metrics = calculate_metrics(truth, results)
    assert metrics.overall_passed


def test_overall_failed_detection():
    """检出率不达标 = 整体不通过。"""
    truth = [
        {
            "sample_id": "B001",
            "expect": {
                "is_clean": False,
                "expected_verdict": "invalid",
                "error_type": "dimension_mismatch",
            },
        },
    ]
    results = {"B001": "ok"}

    metrics = calculate_metrics(truth, results)
    assert not metrics.overall_passed
    assert not metrics.detection_rate_passed
    assert metrics.false_positive_rate_passed


def test_overall_failed_false_positive():
    """误报率不达标 = 整体不通过。"""
    truth = [
        {
            "sample_id": "C001",
            "expect": {
                "is_clean": True,
                "expected_verdict": "ok",
                "error_type": None,
            },
        },
    ]
    results = {"C001": "invalid"}

    metrics = calculate_metrics(truth, results)
    assert not metrics.overall_passed
    assert metrics.detection_rate_passed
    assert not metrics.false_positive_rate_passed


def test_targets_constants():
    """目标常量正确。"""
    assert DETECTION_RATE_TARGET == 0.95
    assert FALSE_POSITIVE_RATE_TARGET == 0.0
