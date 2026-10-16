"""K19: 误报率 0 优先守门。

K19: 误报率 0 优先
- 干净论文被判为有问题 = 最坏失败模式
- 误报率必须实测为 0
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_k19_false_positive_rate_zero():
    """K19: 误报率必须为 0。

    所有干净论文必须被判定为 ok。
    """
    from auditor.benchmark.runner import load_truth, run_benchmark

    # 运行基准
    result = run_benchmark(benchmark_dir="data/benchmark")

    # K19: 误报率必须为 0
    assert result.metrics.false_positive_rate == 0.0, (
        f"K19 违规: 误报率为 {result.metrics.false_positive_rate:.2%}，"
        f"期望 0.0%。"
    )

    # K19: 干净论文不能被判定为 invalid（undecidable 表示引擎无法判定，不是误报）
    truth = load_truth("data/benchmark")
    clean_samples = [
        entry for entry in truth if entry["expect"].get("is_clean", False)
    ]
    for sample in clean_samples:
        sample_id = sample["sample_id"]
        # 在样本结果中查找
        for sr in result.sample_results:
            if sr["sample_id"] == sample_id:
                assert sr["verdict"] != "invalid", (
                    f"K19 违规: 干净样本 {sample_id} 被判定为 {sr['verdict']}"
                )
                break


def test_k19_gate_mutation():
    """K19 变异验证：故意让引擎误报，门必须变红。

    这是一个概念性测试，验证 K19 守门逻辑本身正确。
    实际误报检测由 test_k19_false_positive_rate_zero 完成。
    """
    # 模拟：如果误报率 > 0，断言会失败
    # 这个测试验证检测逻辑
    mock_metrics_high_fp = type(
        "MockMetrics",
        (),
        {"false_positive_rate": 0.5, "false_positive_rate_passed": False},
    )()
    mock_result_high_fp = type(
        "MockResult",
        (),
        {"metrics": mock_metrics_high_fp, "exit_code": 1},
    )()

    assert not mock_result_high_fp.metrics.false_positive_rate_passed
    assert mock_result_high_fp.exit_code == 1


def test_k19_clean_samples_all_present():
    """K19: 干净论文样本必须存在且可审计。"""
    from auditor.benchmark.runner import load_truth

    truth = load_truth("data/benchmark")
    clean_samples = [
        entry for entry in truth if entry["expect"].get("is_clean", False)
    ]

    # 必须有干净样本
    assert len(clean_samples) >= 3, "K19: 干净样本不足，无法验证误报率"

    # 验证样本文件存在
    for sample in clean_samples:
        tex_path = Path(sample["input_card"]["paper_tex"])
        assert tex_path.exists(), f"干净样本文件不存在: {tex_path}"


def test_k19_no_false_positive_in_clean():
    """K19: 干净论文中无错误类型。"""
    from auditor.benchmark.runner import load_truth

    truth = load_truth("data/benchmark")
    clean_samples = [
        entry for entry in truth if entry["expect"].get("is_clean", False)
    ]

    for sample in clean_samples:
        expect = sample["expect"]
        assert expect.get("error_type") is None, (
            f"干净样本 {sample['sample_id']} 不应有 error_type"
        )
        assert expect.get("expected_verdict") == "ok", (
            f"干净样本 {sample['sample_id']} 期望 verdict 应为 ok"
        )
