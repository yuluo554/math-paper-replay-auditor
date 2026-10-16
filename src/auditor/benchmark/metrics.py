"""指标计算——从真值库 + 引擎输出派生。

K18: 覆盖度分母反射自代码常量
K19: 误报率 0 优先
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class Verdict(str, Enum):
    """三态判定词汇（与 core.types.Verdict 同源）。"""

    OK = "ok"
    INVALID = "invalid"
    UNDECIDABLE = "undecidable"


# 指标目标
DETECTION_RATE_TARGET = 0.95  # 检出率 ≥ 95%
FALSE_POSITIVE_RATE_TARGET = 0.0  # 误报率 = 0


@dataclass
class BenchmarkMetrics:
    """基准指标。"""

    total_samples: int = 0
    total_errors: int = 0
    total_clean: int = 0

    # 检出率：正确检出的错误数 / 总错误数
    detected_errors: int = 0
    detection_rate: float = 0.0

    # 误报率：干净论文被判有问题数 / 总干净论文数
    false_positives: int = 0
    false_positive_rate: float = 0.0

    # 按错误类型的检出情况
    by_error_type: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # 达标判定
    detection_rate_passed: bool = False
    false_positive_rate_passed: bool = False
    overall_passed: bool = False

    # 未达标原因
    failures: List[str] = field(default_factory=list)


def calculate_metrics(
    truth: List[Dict[str, Any]],
    results: Dict[str, str],
) -> BenchmarkMetrics:
    """从真值库 + 引擎输出计算指标。

    Args:
        truth: 真值库条目列表
        results: sample_id -> verdict 映射

    Returns:
        BenchmarkMetrics: 计算得到的指标
    """
    metrics = BenchmarkMetrics()
    metrics.total_samples = len(truth)

    # 按错误类型统计
    error_type_stats: Dict[str, Dict[str, int]] = {}

    for entry in truth:
        sample_id = entry["sample_id"]
        expect = entry["expect"]
        is_clean = expect.get("is_clean", False)
        expected_verdict = expect.get("expected_verdict", "ok")
        error_type = expect.get("error_type")

        # 获取引擎判定
        actual_verdict = results.get(sample_id, "undecidable")

        if is_clean:
            metrics.total_clean += 1
            # K19: 干净论文：期望 verdict = ok 或 undecidable（不能是 invalid）
            # undecidable 表示引擎无法判定，不是误报
            if actual_verdict == "invalid":
                metrics.false_positives += 1
        else:
            metrics.total_errors += 1
            # 错误论文：期望 verdict = invalid
            if actual_verdict == "invalid":
                metrics.detected_errors += 1

        # 按错误类型统计
        if error_type:
            if error_type not in error_type_stats:
                error_type_stats[error_type] = {
                    "total": 0,
                    "detected": 0,
                    "false_positive": 0,
                }
            error_type_stats[error_type]["total"] += 1
            if actual_verdict == "invalid":
                error_type_stats[error_type]["detected"] += 1
            elif is_clean and actual_verdict == "invalid":
                error_type_stats[error_type]["false_positive"] += 1

    # 计算比率
    if metrics.total_errors > 0:
        metrics.detection_rate = metrics.detected_errors / metrics.total_errors
    else:
        # 无错误样本时，检出率为 0（没有错误可检出）
        metrics.detection_rate = 0.0

    if metrics.total_clean > 0:
        metrics.false_positive_rate = metrics.false_positives / metrics.total_clean
    else:
        metrics.false_positive_rate = 0.0

    # 达标判定
    # 无错误样本时，检出率视为通过（没有错误可检出）
    if metrics.total_errors == 0:
        metrics.detection_rate_passed = True
    else:
        metrics.detection_rate_passed = metrics.detection_rate >= DETECTION_RATE_TARGET

    metrics.false_positive_rate_passed = (
        metrics.false_positive_rate <= FALSE_POSITIVE_RATE_TARGET
    )
    metrics.overall_passed = (
        metrics.detection_rate_passed and metrics.false_positive_rate_passed
    )

    # 记录未达标原因
    if not metrics.detection_rate_passed:
        metrics.failures.append(
            f"检出率 {metrics.detection_rate:.2%} < {DETECTION_RATE_TARGET:.0%}"
        )
    if not metrics.false_positive_rate_passed:
        metrics.failures.append(
            f"误报率 {metrics.false_positive_rate:.2%} > {FALSE_POSITIVE_RATE_TARGET:.0%}"
        )

    metrics.by_error_type = error_type_stats

    return metrics


def format_metrics(metrics: BenchmarkMetrics) -> str:
    """格式化指标为可读字符串。"""
    lines = [
        "=== 基准指标 ===",
        f"总样本数: {metrics.total_samples}",
        f"错误样本: {metrics.total_errors}",
        f"干净样本: {metrics.total_clean}",
        "",
        f"检出率: {metrics.detection_rate:.2%} (目标 ≥ {DETECTION_RATE_TARGET:.0%}) {'✓' if metrics.detection_rate_passed else '✗'}",
        f"误报率: {metrics.false_positive_rate:.2%} (目标 ≤ {FALSE_POSITIVE_RATE_TARGET:.0%}) {'✓' if metrics.false_positive_rate_passed else '✗'}",
    ]

    if metrics.by_error_type:
        lines.append("")
        lines.append("按错误类型:")
        for error_type, stats in metrics.by_error_type.items():
            detection = (
                stats["detected"] / stats["total"] if stats["total"] > 0 else 0
            )
            lines.append(
                f"  {error_type}: {stats['detected']}/{stats['total']} 检出, "
                f"误报 {stats['false_positive']} ({detection:.0%})"
            )

    if metrics.failures:
        lines.append("")
        lines.append("未达标原因:")
        for failure in metrics.failures:
            lines.append(f"  - {failure}")

    lines.append("")
    lines.append(f"总体: {'通过 ✓' if metrics.overall_passed else '未达标 ✗'}")

    return "\n".join(lines)
