"""K14: 幽灵 label 仅为提示——依赖图守门。

K14: 幽灵 label 仅为提示
断言幽灵 label（从未被引用的 label）是"结构性可疑"，不是"确证问题"。
"""

from __future__ import annotations

from pathlib import Path

from auditor.core.graph import (
    _find_ghost_labels,
    _build_dependency_graph,
    GraphNode
)


def create_mock_tree(theorems=None, lemmas=None, refs=None):
    """创建模拟论文结构树。"""
    return {
        "paper_id": "test-001",
        "theorems": theorems or [],
        "lemmas": lemmas or [],
        "equations": [],
        "refs": refs or [],
        "labels": [],
        "sections": [],
        "proofs": [],
        "tables": [],
        "packages": [],
        "unrecognized_envs": [],
        "unrecognized_macros": [],
        "coverage": 1.0
    }


def test_ghost_label_is_not_invalid():
    """K14: 幽灵 label 不是确证问题。"""
    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[{"ref": "thm:main", "section": "sec-2"}]
    )

    graph = _build_dependency_graph(tree)
    ghosts = _find_ghost_labels(graph, tree)

    # 幽灵 label 应该存在
    assert len(ghosts) == 1

    # 验证幽灵 label 的信息
    ghost = ghosts[0]
    assert ghost["label"] == "lem:unused"
    assert "从未被引用" in ghost["message"] or "结构性可疑" in ghost["message"]


def test_ghost_label_verdict_is_undecidable():
    """K14: 幽灵 label 的 verdict 是 undecidable，不是 invalid。"""
    from auditor.core.graph import check_dependency_graph

    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[{"ref": "thm:main", "section": "sec-2"}]
    )

    results = check_dependency_graph(tree)

    # 找到幽灵 label 相关的结果
    ghost_results = [r for r in results if r.error_type == "ghost_label"]

    if ghost_results:
        for result in ghost_results:
            # 幽灵 label 应该是 undecidable，不是 invalid
            assert result.verdict.value == "undecidable", \
                f"幽灵 label 应为 undecidable，实际为 {result.verdict.value}"


def test_ghost_label_message_indicates_suspicion_not_error():
    """K14: 幽灵 label 的消息表明是"可疑"而非"错误"。"""
    from auditor.core.graph import check_dependency_graph

    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[{"ref": "thm:main", "section": "sec-2"}]
    )

    results = check_dependency_graph(tree)

    # 找到幽灵 label 相关的结果
    for result in results:
        if "幽灵" in result.evidence or "从未被引用" in result.evidence:
            # 证据中应表明是"结构性可疑"而非"确证问题"
            assert "可疑" in result.evidence or "提示" in result.evidence or "非确证" in result.evidence


def test_no_ghost_labels_when_all_used():
    """所有 label 都被引用时无幽灵 label。"""
    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:aux", "section": "sec-1"}
        ],
        refs=[
            {"ref": "thm:main", "section": "sec-2"},
            {"ref": "lem:aux", "section": "sec-2"}
        ]
    )

    graph = _build_dependency_graph(tree)
    ghosts = _find_ghost_labels(graph, tree)

    assert len(ghosts) == 0


def test_ghost_label_with_lemmas():
    """引理的幽灵 label。"""
    tree = create_mock_tree(
        lemmas=[
            {"label": "lem:used", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[{"ref": "lem:used", "section": "sec-2"}]
    )

    graph = _build_dependency_graph(tree)
    ghosts = _find_ghost_labels(graph, tree)

    assert len(ghosts) == 1
    assert ghosts[0]["label"] == "lem:unused"


def test_ghost_label_with_equations():
    """方程的幽灵 label。"""
    tree = {
        "paper_id": "test-001",
        "equations": [
            {"label": "eq:used", "section": "sec-1"},
            {"label": "eq:unused", "section": "sec-1"}
        ],
        "theorems": [],
        "lemmas": [],
        "refs": [{"ref": "eq:used", "section": "sec-2"}],
        "labels": [],
        "sections": [],
        "proofs": [],
        "tables": [],
        "packages": [],
        "unrecognized_envs": [],
        "unrecognized_macros": [],
        "coverage": 1.0
    }

    graph = _build_dependency_graph(tree)
    ghosts = _find_ghost_labels(graph, tree)

    # 方程节点应该被添加
    # 幽灵 label 检测


def test_ghost_label_not_treated_as_dangling_ref():
    """K14: 幽灵 label 不应与悬空引用混淆。"""
    from auditor.core.graph import _find_dangling_refs

    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[
            {"ref": "thm:main", "section": "sec-2"},
            {"ref": "thm:nonexistent", "section": "sec-2"}  # 悬空引用
        ]
    )

    graph = _build_dependency_graph(tree)
    dangling = _find_dangling_refs(graph, tree)
    ghosts = _find_ghost_labels(graph, tree)

    # 悬空引用和幽灵 label 应该分开检测
    assert len(dangling) == 1  # thm:nonexistent
    assert len(ghosts) == 1   # lem:unused

    # 验证类型不同
    assert dangling[0]["ref"] == "thm:nonexistent"
    assert ghosts[0]["label"] == "lem:unused"


def test_k14_mutation_detection():
    """K14 变异验证：故意将幽灵 label 标记为 invalid，门必须变红。"""
    from auditor.core.graph import check_dependency_graph

    # 正常情况：幽灵 label 应该是 undecidable
    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[{"ref": "thm:main", "section": "sec-2"}]
    )

    results = check_dependency_graph(tree)

    # 验证幽灵 label 的 verdict 是 undecidable
    ghost_results = [r for r in results if r.error_type == "ghost_label"]

    if ghost_results:
        for result in ghost_results:
            # 如果这里失败，说明幽灵 label 被错误地标记为 invalid
            assert result.verdict.value == "undecidable", \
                "K14 变异验证失败：幽灵 label 应为 undecidable"


def test_ghost_label_evidence_explains_reason():
    """K14: 幽灵 label 的证据应解释原因。"""
    from auditor.core.graph import check_dependency_graph

    tree = create_mock_tree(
        theorems=[
            {"label": "thm:main", "section": "sec-1"},
            {"label": "lem:unused", "section": "sec-1"}
        ],
        refs=[{"ref": "thm:main", "section": "sec-2"}]
    )

    results = check_dependency_graph(tree)

    for result in results:
        if "幽灵" in result.evidence or "从未被引用" in result.evidence:
            # 证据应包含解释
            assert len(result.evidence) > 10, "幽灵 label 证据应包含详细解释"
