"""基准套件——模块⑥：基准 runner + 指标计算 + 探活。

K19: 误报率 0 优先
K20: 确定性生成（splitmix64）
K22: 探活打在消费处
"""

from __future__ import annotations

from .metrics import (
    BenchmarkMetrics,
    calculate_metrics,
    DETECTION_RATE_TARGET,
    FALSE_POSITIVE_RATE_TARGET,
)
from .runner import (
    BenchmarkResult,
    ERROR_TYPES,
    run_benchmark,
    load_truth,
    load_manifest,
)

__all__ = [
    "BenchmarkMetrics",
    "BenchmarkResult",
    "ERROR_TYPES",
    "calculate_metrics",
    "DETECTION_RATE_TARGET",
    "FALSE_POSITIVE_RATE_TARGET",
    "run_benchmark",
    "load_truth",
    "load_manifest",
]
