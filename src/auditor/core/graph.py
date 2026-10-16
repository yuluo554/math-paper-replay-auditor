"""定理依赖图完整性引擎——确定性图算法。

K13: 依赖图可复跑
K14: 幽灵 label 仅为提示
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

from auditor.core.types import ClaimResult, Verdict


@dataclass
class GraphNode:
    """图节点。"""
    id: str
    label: str
    node_type: str  # theorem, lemma, proof, equation
    location: str


@dataclass
class GraphEdge:
    """图边。"""
    from_id: str
    to_id: str
    relation: str  # depends_on, references


@dataclass
class DependencyGraph:
    """依赖图。"""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        """添加节点。"""
        self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        """添加边。"""
        self.edges.append(edge)

    def get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
        """根据 ID 获取节点。"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_node_by_label(self, label: str) -> Optional[GraphNode]:
        """根据 label 获取节点。"""
        for node in self.nodes:
            if node.label == label:
                return node
        return None

    def get_edges_from(self, node_id: str) -> List[GraphEdge]:
        """获取从某节点出发的边。"""
        return [e for e in self.edges if e.from_id == node_id]

    def get_edges_to(self, node_id: str) -> List[GraphEdge]:
        """获取指向某节点的边。"""
        return [e for e in self.edges if e.to_id == node_id]


def _build_dependency_graph(tree: Dict[str, Any]) -> DependencyGraph:
    """从论文结构树构建依赖图。

    Args:
        tree: 论文结构树

    Returns:
        依赖图
    """
    graph = DependencyGraph()

    # 添加定理节点
    for i, thm in enumerate(tree.get("theorems", [])):
        label = thm.get("label", f"thm-{i+1:03d}")
        node = GraphNode(
            id=f"thm-{i+1:03d}",
            label=label,
            node_type="theorem",
            location=thm.get("section", "unknown")
        )
        graph.add_node(node)

    # 添加引理节点
    for i, lem in enumerate(tree.get("lemmas", [])):
        label = lem.get("label", f"lem-{i+1:03d}")
        node = GraphNode(
            id=f"lem-{i+1:03d}",
            label=label,
            node_type="lemma",
            location=lem.get("section", "unknown")
        )
        graph.add_node(node)

    # 添加方程节点
    for i, eq in enumerate(tree.get("equations", [])):
        label = eq.get("label", f"eq-{i+1:03d}")
        node = GraphNode(
            id=f"eq-{i+1:03d}",
            label=label,
            node_type="equation",
            location=eq.get("section", "unknown")
        )
        graph.add_node(node)

    # 添加引用边
    # 建立 label 到节点的映射
    label_to_node = {node.label: node for node in graph.nodes}

    for ref in tree.get("refs", []):
        ref_label = ref.get("ref", "")

        # 找到被引用的节点
        to_node = label_to_node.get(ref_label)

        if to_node:
            # 创建引用边（引用者 -> 被引用者）
            # 由于我们不知道引用者的具体节点，创建一个虚拟的引用者节点
            # 或者直接记录这个引用关系
            edge = GraphEdge(
                from_id=f"ref-{ref_label}",
                to_id=to_node.id,
                relation="references"
            )
            graph.add_edge(edge)

    return graph


# 依赖型引用所在环境：引理/定理/命题/证明引用的是**前置结果**，
# 其缺失属于依赖断链；其余（推论、正文）引用他人成果，缺失属于悬空引用。
DEPENDENCY_ENVS = {"lemma", "theorem", "proposition", "proof"}


def _classify_missing_refs(tree: Dict[str, Any], graph: DependencyGraph) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """把"引用了不存在的 label"按引用者环境分两类。

    Returns:
        (dangling_refs, dep_chain_breaks)
    """
    existing_labels = {node.label for node in graph.nodes}
    dangling: List[Dict[str, Any]] = []
    broken: List[Dict[str, Any]] = []

    for ref in tree.get("refs", []):
        ref_label = ref.get("ref", "")
        if not ref_label or ref_label in existing_labels:
            continue
        env = ref.get("env")
        item = {
            "ref": ref_label,
            "env": env,
            "location": env or "unknown",
            "message": f"引用了不存在的 label: {ref_label}",
        }
        if env in DEPENDENCY_ENVS:
            item["message"] = f"依赖链断裂：{env} 依赖的 {ref_label} 不存在"
            broken.append(item)
        else:
            dangling.append(item)

    return dangling, broken


def _find_dangling_refs(graph: DependencyGraph, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """查找悬空引用。

    悬空引用：ref 指向的 label 不存在，且引用者不是"依赖前置结果"的结构
    （推论/正文引用他人成果）。

    Args:
        graph: 依赖图
        tree: 论文结构树

    Returns:
        悬空引用列表
    """
    dangling, _ = _classify_missing_refs(tree, graph)
    return dangling


def _find_ghost_labels(graph: DependencyGraph, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """查找幽灵 label。

    幽灵 label：label 从未被任何 ref 引用。
    K14: 幽灵 label 仅为提示，不是确证问题。

    Args:
        graph: 依赖图
        tree: 论文结构树

    Returns:
        幽灵 label 列表
    """
    ghost_labels = []

    # 收集所有被引用的 label
    referenced_labels = set()
    for edge in graph.edges:
        if edge.relation == "references":
            to_node = graph.get_node_by_id(edge.to_id)
            if to_node:
                referenced_labels.add(to_node.label)

    # 检查每个 label 是否被引用
    for node in graph.nodes:
        if node.label not in referenced_labels:
            ghost_labels.append({
                "label": node.label,
                "location": node.location,
                "message": f"从未被引用的 {node.node_type}: {node.label}"
            })

    return ghost_labels


def _find_broken_chains(graph: DependencyGraph, tree: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """查找依赖断链。

    依赖断链：结构体（引理/定理/命题/证明）依赖的前置结果 label 不存在。

    Args:
        graph: 依赖图
        tree: 论文结构树（提供 ref 的所在环境）

    Returns:
        依赖断链列表
    """
    if tree is None:
        return []
    _, broken = _classify_missing_refs(tree, graph)
    return broken


def _check_topology(graph: Dict[str, Any]) -> Dict[str, Any]:
    """检查图拓扑。

    检测循环依赖。

    Args:
        graph: 依赖图（字典形式）

    Returns:
        拓扑信息
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # 构建邻接表
    adj: Dict[str, List[str]] = defaultdict(list)
    for edge in edges:
        adj[edge["from"]].append(edge["to"])

    # 检测循环（DFS）
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # 找到循环
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        rec_stack.remove(node)
        path.pop()

    for node in nodes:
        if node not in visited:
            dfs(node, [])

    return {
        "acyclic": len(cycles) == 0,
        "cycles": cycles
    }


def check_dependency_graph(tree: Dict[str, Any]) -> List[ClaimResult]:
    """审计定理依赖图完整性。

    Args:
        tree: 论文结构树（来自解析器）

    Returns:
        断言审计结果列表
    """
    results: List[ClaimResult] = []
    claim_counter = 0

    # 构建依赖图
    graph = _build_dependency_graph(tree)

    # 查找悬空引用
    dangling_refs = _find_dangling_refs(graph, tree)
    claim_counter += 1
    if dangling_refs:
        results.append(ClaimResult(
            claim_id=f"graph-{claim_counter:03d}",
            claim_type="dependency",
            verdict=Verdict.INVALID,
            evidence=f"发现 {len(dangling_refs)} 个悬空引用",
            steps=dangling_refs,
            error_type="dangling_ref"
        ))
    else:
        results.append(ClaimResult(
            claim_id=f"graph-{claim_counter:03d}",
            claim_type="dependency",
            verdict=Verdict.OK,
            evidence="无悬空引用",
            steps=[]
        ))

    # 查找幽灵 label
    ghost_labels = _find_ghost_labels(graph, tree)
    claim_counter += 1
    if ghost_labels:
        # K14: 幽灵 label 仅为提示
        results.append(ClaimResult(
            claim_id=f"graph-{claim_counter:03d}",
            claim_type="dependency",
            verdict=Verdict.UNDECIDABLE,  # 不是确证问题
            evidence=f"发现 {len(ghost_labels)} 个幽灵 label（结构性可疑，非确证问题）",
            steps=ghost_labels,
            error_type="ghost_label"
        ))
    else:
        results.append(ClaimResult(
            claim_id=f"graph-{claim_counter:03d}",
            claim_type="dependency",
            verdict=Verdict.OK,
            evidence="无幽灵 label",
            steps=[]
        ))

    # 查找依赖断链
    broken_chains = _find_broken_chains(graph, tree)
    claim_counter += 1
    if broken_chains:
        results.append(ClaimResult(
            claim_id=f"graph-{claim_counter:03d}",
            claim_type="dependency",
            verdict=Verdict.INVALID,
            evidence=f"发现 {len(broken_chains)} 个依赖断链",
            steps=broken_chains,
            error_type="dep_chain_break"
        ))
    else:
        results.append(ClaimResult(
            claim_id=f"graph-{claim_counter:03d}",
            claim_type="dependency",
            verdict=Verdict.OK,
            evidence="无依赖断链",
            steps=[]
        ))

    # 如果没有任何节点，添加 undecidable 结果
    if not graph.nodes:
        results.append(ClaimResult(
            claim_id="none-001",
            claim_type="dependency",
            verdict=Verdict.UNDECIDABLE,
            evidence="论文中无可分析的定理/引理结构",
            steps=[]
        ))

    return results
