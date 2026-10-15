"""错误植入器——五类植入错误。

K18: 覆盖度分母反射自代码常量
"""

from __future__ import annotations

from typing import Dict, Any
from .deterministic_rng import SplitMix64


ERROR_TYPES = [
    "dimension_mismatch",
    "illegal_derivation",
    "numeric_mismatch",
    "dangling_ref",
    "dep_chain_break",
]


def inject_dimension_mismatch(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """在等式 F = ma 中，将右侧 m 改为 m^2，导致量纲不一致。"""
    rng = SplitMix64(seed)
    # 在 eq:deriv 等式中注入量纲错误
    modified = tex.replace(
        "f'(x) = e^x",
        "f'(x) = e^{x^2}"  # 量纲不一致
    )
    truth = {
        "error_type": "dimension_mismatch",
        "location": "eq:deriv",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_illegal_derivation(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """在推导链中插入一步：sin^2(x) + cos^2(x) = 2（非法）。"""
    rng = SplitMix64(seed)
    modified = tex.replace(
        "e^x \\lim_{{h \\to 0}} \\frac{{e^h - 1}}{{h}} = e^x.",
        "e^x \\lim_{{h \\to 0}} \\frac{{e^h - 1}}{{h}} = e^x \\cdot 2 = 2e^x."  # 非法步
    )
    truth = {
        "error_type": "illegal_derivation",
        "location": "eq:deriv",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_numeric_mismatch(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """在数值表中将 2.71828 改为 2.71829。"""
    rng = SplitMix64(seed)
    modified = tex.replace("2.71828", "2.71829")
    truth = {
        "error_type": "numeric_mismatch",
        "location": "table-001, row-02",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_dangling_ref(tex: str, seed: int) -> tuple[str, Any]:
    """删除一个被引用的 label，但保留 ref。"""
    rng = SplitMix64(seed)
    # 删除 lem:aux 定义，但保留 cor:result 中的引用
    modified = tex.replace(
        "\\begin{lemma}[Auxiliary Lemma]\n\\label{lem:aux}",
        "\\begin{lemma}[Auxiliary Lemma]"
    )
    # 实际删除 label 行
    modified = modified.replace(
        "\\label{lem:aux}",
        ""
    )
    truth = {
        "error_type": "dangling_ref",
        "location": "cor:result 引用 lem:aux",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_dep_chain_break(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """删除一个中间引理，导致依赖链断裂。"""
    rng = SplitMix64(seed)
    # 删除 lem:aux 整个 lemma 环境
    modified = tex.replace(
        "\\begin{lemma}[Auxiliary Lemma]\\n\\label{lem:aux}\\nFor all $x \\in \\mathbb{R}$, $e^x > 0$.\\n\\end{lemma}",
        ""
    )
    truth = {
        "error_type": "dep_chain_break",
        "location": "thm:main → lem:aux → cor:result",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def make_clean(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """干净论文（无植入错误）。"""
    truth = {
        "error_type": None,
        "location": None,
        "is_clean": True,
        "expected_verdict": "ok",
    }
    return tex, truth
