"""符号重放引擎单元测试。

测试 replay.py 的核心功能。
"""

from __future__ import annotations

import pytest
from auditor.core.replay import replay


def create_mock_tree(equations=None, theorems=None, proofs=None):
    """创建模拟论文结构树。"""
    return {
        "paper_id": "test-001",
        "equations": equations or [],
        "theorems": theorems or [],
        "proofs": proofs or [],
        "sections": [],
        "lemmas": [],
        "tables": [],
        "refs": [],
        "labels": [],
        "packages": [],
        "unrecognized_envs": [],
        "unrecognized_macros": [],
        "coverage": 1.0
    }


class TestReplayEngine:
    """符号重放引擎测试。"""

    def test_empty_tree_returns_undecidable(self):
        """空论文树返回 undecidable 结果。"""
        tree = create_mock_tree()
        results = replay(tree)

        assert len(results) > 0
        assert results[0].verdict == "undecidable"

    def test_tree_with_equations(self):
        """包含等式的论文树。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2", "type": "equation", "label": "eq-001"}
        ])
        results = replay(tree)

        assert len(results) > 0
        # 等式应被处理

    def test_tree_with_theorems(self):
        """包含定理的论文树。"""
        tree = create_mock_tree(theorems=[
            {"content": "a^2 + b^2 = c^2", "label": "thm-pythagoras"}
        ])
        results = replay(tree)

        assert len(results) > 0

    def test_tree_with_proofs(self):
        """包含证明的论文树。"""
        tree = create_mock_tree(proofs=[
            {"content": "x^2 + y^2 = z^2", "label": "proof-001"}
        ])
        results = replay(tree)

        assert len(results) > 0

    def test_verdict_values_are_valid(self):
        """所有 verdict 值必须是 ok/invalid/undecidable 之一。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"}
        ])
        results = replay(tree)

        valid_verdicts = {"ok", "invalid", "undecidable"}
        for result in results:
            assert result.verdict.value in valid_verdicts

    def test_claim_id_format(self):
        """断言 ID 格式正确。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"},
            {"content": "F = ma"}
        ])
        results = replay(tree)

        # 检查 ID 格式
        claim_ids = [r.claim_id for r in results]
        assert any(cid.startswith("eq-") for cid in claim_ids)

    def test_evidence_not_empty(self):
        """证据字段不为空。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"}
        ])
        results = replay(tree)

        for result in results:
            assert result.evidence is not None
            assert len(result.evidence) > 0

    def test_multiple_equations(self):
        """多个等式被正确处理。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"},
            {"content": "F = ma"},
            {"content": "v = d/t"}
        ])
        results = replay(tree)

        assert len(results) >= 3

    def test_mixed_content(self):
        """混合内容（等式、定理、证明）被正确处理。"""
        tree = create_mock_tree(
            equations=[{"content": "E = mc^2"}],
            theorems=[{"content": "a^2 + b^2 = c^2"}],
            proofs=[{"content": "x = y"}]
        )
        results = replay(tree)

        assert len(results) > 0


class TestReplayDeterminism:
    """确定性测试。"""

    def test_same_input_same_output(self):
        """相同输入产生相同输出（K6）。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"}
        ])

        results1 = replay(tree)
        results2 = replay(tree)

        # 结果数量一致
        assert len(results1) == len(results2)

        # 每个结果的 verdict 一致
        for r1, r2 in zip(results1, results2):
            assert r1.verdict == r2.verdict
            assert r1.claim_id == r2.claim_id

    def test_deterministic_with_multiple_runs(self):
        """多次运行结果一致。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"},
            {"content": "F = ma"}
        ])

        results_list = [replay(tree) for _ in range(5)]

        # 所有运行结果一致
        for i in range(1, len(results_list)):
            assert len(results_list[i]) == len(results_list[0])
            for r1, r2 in zip(results_list[i], results_list[0]):
                assert r1.verdict == r2.verdict
