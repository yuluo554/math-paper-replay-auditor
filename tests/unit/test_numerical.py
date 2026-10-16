"""数值复算引擎单元测试。

测试 numerical.py 的核心功能。
"""

from __future__ import annotations

import pytest
from auditor.core.numerical import recompute_numerical
from auditor.core.numerical_tolerance import NUMERICAL_TOLERANCE, tolerance_note


def create_mock_tree(tables=None, equations=None):
    """创建模拟论文结构树。"""
    return {
        "paper_id": "test-001",
        "tables": tables or [],
        "equations": equations or [],
        "sections": [],
        "theorems": [],
        "lemmas": [],
        "proofs": [],
        "refs": [],
        "labels": [],
        "packages": [],
        "unrecognized_envs": [],
        "unrecognized_macros": [],
        "coverage": 1.0
    }


class TestNumericalEngine:
    """数值复算引擎测试。"""

    def test_empty_tree_returns_undecidable(self):
        """空论文树返回 undecidable 结果。"""
        tree = create_mock_tree()
        results = recompute_numerical(tree)

        assert len(results) > 0
        assert results[0].verdict == "undecidable"

    def test_tree_with_tables(self):
        """包含表格的论文树。"""
        tree = create_mock_tree(tables=[
            {"content": "x & 3.14159 \\\\ y & 2.71828"}
        ])
        results = recompute_numerical(tree)

        assert len(results) > 0

    def test_tree_with_equations_containing_numbers(self):
        """包含数值的方程。"""
        tree = create_mock_tree(equations=[
            {"content": "E = 9.8 \\times 10^{16}"}
        ])
        results = recompute_numerical(tree)

        assert len(results) > 0

    def test_verdict_values_are_valid(self):
        """所有 verdict 值必须是 ok/invalid/undecidable 之一。"""
        tree = create_mock_tree(tables=[
            {"content": "value & 3.14159"}
        ])
        results = recompute_numerical(tree)

        valid_verdicts = {"ok", "invalid", "undecidable"}
        for result in results:
            assert result.verdict.value in valid_verdicts

    def test_evidence_contains_tolerance_note(self):
        """证据包含容差注记（K9）。"""
        tree = create_mock_tree(tables=[
            {"content": "value & 3.14159"}
        ])
        results = recompute_numerical(tree)

        for result in results:
            if result.evidence:
                # 证据应包含容差注记
                assert "容差" in result.evidence or "undecidable" in result.evidence

    def test_multiple_tables(self):
        """多个表格被正确处理。"""
        tree = create_mock_tree(tables=[
            {"content": "x & 1.0"},
            {"content": "y & 2.0"}
        ])
        results = recompute_numerical(tree)

        assert len(results) >= 2


class TestNumericalTolerance:
    """容差定义测试。"""

    def test_tolerance_defined(self):
        """容差字典已定义。"""
        assert NUMERICAL_TOLERANCE is not None
        assert "default" in NUMERICAL_TOLERANCE

    def test_tolerance_values_are_positive(self):
        """容差值为正数。"""
        for key, value in NUMERICAL_TOLERANCE.items():
            assert value > 0

    def test_tolerance_note_function(self):
        """容差注记函数工作正常。"""
        note = tolerance_note("default")
        assert "容差" in note
        assert "1e-06" in note or "1e-6" in note

    def test_tolerance_note_for_all_categories(self):
        """所有容差类别都有注记。"""
        for category in NUMERICAL_TOLERANCE:
            note = tolerance_note(category)
            assert "容差" in note
            # 注记包含容差值（可能是科学计数法或小数形式）
            assert "0." in note or "1e" in note or "e-" in note


class TestNumericalDeterminism:
    """确定性测试。"""

    def test_same_input_same_output(self):
        """相同输入产生相同输出（K6）。"""
        tree = create_mock_tree(tables=[
            {"content": "value & 3.14159"}
        ])

        results1 = recompute_numerical(tree)
        results2 = recompute_numerical(tree)

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.verdict == r2.verdict

    def test_deterministic_with_multiple_runs(self):
        """多次运行结果一致。"""
        tree = create_mock_tree(tables=[
            {"content": "value & 3.14159"}
        ])

        results_list = [recompute_numerical(tree) for _ in range(5)]

        for i in range(1, len(results_list)):
            assert len(results_list[i]) == len(results_list[0])
            for r1, r2 in zip(results_list[i], results_list[0]):
                assert r1.verdict == r2.verdict
