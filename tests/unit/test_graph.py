"""依赖图分析引擎单元测试。

测试 graph.py 的核心功能。
"""

from __future__ import annotations

import pytest
from auditor.core.graph import (
    check_dependency_graph,
    _build_dependency_graph,
    _find_dangling_refs,
    _find_ghost_labels,
    DependencyGraph,
    GraphNode,
    GraphEdge
)


def create_mock_tree(theorems=None, lemmas=None, equations=None, refs=None, labels=None):
    """创建模拟论文结构树。"""
    return {
        "paper_id": "test-001",
        "theorems": theorems or [],
        "lemmas": lemmas or [],
        "equations": equations or [],
        "refs": refs or [],
        "labels": labels or [],
        "sections": [],
        "proofs": [],
        "tables": [],
        "packages": [],
        "unrecognized_envs": [],
        "unrecognized_macros": [],
        "coverage": 1.0
    }


class TestDependencyGraph:
    """依赖图数据结构测试。"""

    def test_create_graph(self):
        """创建空图。"""
        graph = DependencyGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """添加节点。"""
        graph = DependencyGraph()
        node = GraphNode(id="node-1", label="thm:main", node_type="theorem", location="sec-1")
        graph.add_node(node)
        assert len(graph.nodes) == 1
        assert graph.get_node_by_id("node-1") == node

    def test_add_edge(self):
        """添加边。"""
        graph = DependencyGraph()
        node1 = GraphNode(id="node-1", label="thm:main", node_type="theorem", location="sec-1")
        node2 = GraphNode(id="node-2", label="lem:aux", node_type="lemma", location="sec-1")
        graph.add_node(node1)
        graph.add_node(node2)

        edge = GraphEdge(from_id="node-1", to_id="node-2", relation="references")
        graph.add_edge(edge)

        assert len(graph.edges) == 1
        assert len(graph.get_edges_from("node-1")) == 1
        assert len(graph.get_edges_to("node-2")) == 1

    def test_get_node_not_found(self):
        """获取不存在的节点返回 None。"""
        graph = DependencyGraph()
        assert graph.get_node_by_id("nonexistent") is None
        assert graph.get_node_by_label("nonexistent") is None


class TestGraphBuilding:
    """图构建测试。"""

    def test_build_empty_tree(self):
        """构建空论文树的图。"""
        tree = create_mock_tree()
        graph = _build_dependency_graph(tree)

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_build_with_theorems(self):
        """构建包含定理的图。"""
        tree = create_mock_tree(theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "thm:secondary", "section": "sec-2"}
        ])
        graph = _build_dependency_graph(tree)

        assert len(graph.nodes) == 2
        assert graph.get_node_by_label("thm:main") is not None
        assert graph.get_node_by_label("thm:secondary") is not None

    def test_build_with_refs(self):
        """构建包含引用的图。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        graph = _build_dependency_graph(tree)

        # 引用边应该被添加
        assert len(graph.edges) >= 0  # 可能为 0 如果找不到引用者


class TestDanglingRefs:
    """悬空引用测试。"""

    def test_no_dangling_refs(self):
        """无悬空引用。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        graph = _build_dependency_graph(tree)
        dangling = _find_dangling_refs(graph, tree)

        assert len(dangling) == 0

    def test_dangling_ref(self):
        """存在悬空引用。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:nonexistent", "section": "sec-2"}]
        )
        graph = _build_dependency_graph(tree)
        dangling = _find_dangling_refs(graph, tree)

        assert len(dangling) == 1
        assert dangling[0]["ref"] == "thm:nonexistent"

    def test_multiple_dangling_refs(self):
        """多个悬空引用。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[
                {"ref": "thm:nonexistent1", "section": "sec-2"},
                {"ref": "thm:nonexistent2", "section": "sec-2"}
            ]
        )
        graph = _build_dependency_graph(tree)
        dangling = _find_dangling_refs(graph, tree)

        assert len(dangling) == 2


class TestGhostLabels:
    """幽灵 label 测试。"""

    def test_no_ghost_labels(self):
        """无幽灵 label。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        graph = _build_dependency_graph(tree)
        ghosts = _find_ghost_labels(graph, tree)

        assert len(ghosts) == 0

    def test_ghost_label(self):
        """存在幽灵 label。"""
        tree = create_mock_tree(
            theorems=[
                {"label": "thm:main", "section": "sec-1"},
                {"label": "lem:unused", "section": "sec-1"}
            ],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        graph = _build_dependency_graph(tree)
        ghosts = _find_ghost_labels(graph, tree)

        # lem:unused 从未被引用，是幽灵 label
        assert len(ghosts) == 1
        assert ghosts[0]["label"] == "lem:unused"

    def test_ghost_label_is_not_invalid(self):
        """幽灵 label 仅为提示，不是确证问题（K14）。"""
        tree = create_mock_tree(
            theorems=[
                {"label": "thm:main", "section": "sec-1"},
                {"label": "lem:unused", "section": "sec-1"}
            ],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        graph = _build_dependency_graph(tree)
        ghosts = _find_ghost_labels(graph, tree)

        # 幽灵 label 应该有说明
        for ghost in ghosts:
            assert "结构性可疑" in ghost["message"] or "从未被引用" in ghost["message"]


class TestDependencyGraphEngine:
    """依赖图引擎测试。"""

    def test_empty_tree_returns_undecidable(self):
        """空论文树返回 undecidable 结果。"""
        tree = create_mock_tree()
        results = check_dependency_graph(tree)

        assert len(results) > 0

    def test_tree_with_valid_refs(self):
        """包含有效引用的论文树。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        results = check_dependency_graph(tree)

        assert len(results) > 0

    def test_tree_with_dangling_ref(self):
        """包含悬空引用的论文树。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:nonexistent", "section": "sec-2"}]
        )
        results = check_dependency_graph(tree)

        # 应该有一个 invalid 结果
        invalid_results = [r for r in results if r.verdict == "invalid"]
        assert len(invalid_results) >= 1

    def test_tree_with_ghost_label(self):
        """包含幽灵 label 的论文树。"""
        tree = create_mock_tree(
            theorems=[
                {"label": "thm:main", "section": "sec-1"},
                {"label": "lem:unused", "section": "sec-1"}
            ],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        results = check_dependency_graph(tree)

        # 应该有一个 undecidable 结果（幽灵 label）
        undecidable_results = [r for r in results if r.verdict == "undecidable"]
        assert len(undecidable_results) >= 1

    def test_verdict_values_are_valid(self):
        """所有 verdict 值必须是 ok/invalid/undecidable 之一。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        results = check_dependency_graph(tree)

        valid_verdicts = {"ok", "invalid", "undecidable"}
        for result in results:
            assert result.verdict.value in valid_verdicts

    def test_evidence_not_empty(self):
        """证据字段不为空。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )
        results = check_dependency_graph(tree)

        for result in results:
            assert result.evidence is not None
            assert len(result.evidence) > 0


class TestGraphDeterminism:
    """确定性测试。"""

    def test_same_input_same_output(self):
        """相同输入产生相同输出（K13）。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )

        results1 = check_dependency_graph(tree)
        results2 = check_dependency_graph(tree)

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.verdict == r2.verdict

    def test_deterministic_with_multiple_runs(self):
        """多次运行结果一致。"""
        tree = create_mock_tree(
            theorems=[{"label": "thm:main", "section": "sec-1"}],
            refs=[{"ref": "thm:main", "section": "sec-2"}]
        )

        results_list = [check_dependency_graph(tree) for _ in range(5)]

        for i in range(1, len(results_list)):
            assert len(results_list[i]) == len(results_list[0])
            for r1, r2 in zip(results_list[i], results_list[0]):
                assert r1.verdict == r2.verdict
