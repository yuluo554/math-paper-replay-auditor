"""K22: 探活打在消费处。

验证基准数据可消费：truth.json 可解析、样本文件可读取、覆盖度达标。
"""

from __future__ import annotations

import json
from pathlib import Path


def test_probe_truth_structure():
    """K17: 真值库只存输入与期望，无 observed 字段。"""
    truth_path = Path("data/benchmark/truth.json")
    assert truth_path.exists(), "truth.json 不存在"

    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    assert len(truth) > 0, "truth.json 为空"

    for entry in truth:
        # 必须有 input_card 和 expect
        assert "input_card" in entry, f"缺少 input_card: {entry.get('sample_id')}"
        assert "expect" in entry, f"缺少 expect: {entry.get('sample_id')}"
        # 不能有 observed
        assert "observed" not in entry, f"K17 违规: {entry['sample_id']} 含 observed 字段"


def test_probe_sample_files():
    """所有样本文件可读取。"""
    truth_path = Path("data/benchmark/truth.json")
    truth = json.loads(truth_path.read_text(encoding="utf-8"))

    for entry in truth:
        tex_path = Path(entry["input_card"]["paper_tex"])
        assert tex_path.exists(), f"样本文件不存在: {tex_path}"
        content = tex_path.read_text(encoding="utf-8")
        assert len(content) > 0, f"样本文件为空: {tex_path}"
        assert "\\documentclass" in content, f"非有效 LaTeX: {tex_path}"


def test_probe_coverage():
    """K18: 覆盖度分母反射自代码常量。"""
    manifest_path = Path("data/benchmark/manifest.json")
    assert manifest_path.exists(), "manifest.json 不存在"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 五类错误各 ≥3
    error_types = [
        "dimension_mismatch",
        "illegal_derivation",
        "numeric_mismatch",
        "dangling_ref",
        "dep_chain_break",
    ]
    for et in error_types:
        assert et in manifest["by_error_type"], f"缺少错误类型: {et}"
        assert manifest["by_error_type"][et]["total"] >= 3, (
            f"{et} 样本数不足: {manifest['by_error_type'][et]['total']}"
        )

    # 干净论文 ≥3
    assert manifest["by_error_type"]["clean"]["total"] >= 3, "干净论文不足"

    # 总数对账
    expected_total = sum(
        v["total"] for v in manifest["by_error_type"].values()
    )
    assert manifest["total_samples"] == expected_total, (
        f"总数对账失败: {manifest['total_samples']} != {expected_total}"
    )
