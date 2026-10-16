"""错误植入器——五类植入错误。

K18: 覆盖度分母反射自代码常量
K20: 确定性生成——扰动幅度由 splitmix64 决定，同 seed 逐字节一致

两条纪律：
1. 每个植入器必须**真正改动文本**——匹配失败即抛错，绝不静默返回原文
   （否则样本与干净论文逐字节相同，引擎无物可判、基准退化为假门）。
2. RNG 必须被**消费**并影响产物——否则"确定性生成"是无法证伪的空话
   （注入的非确定性不会被任何输出体现，K20 变异验证永远变不红）。
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


def _require_change(original: str, modified: str, what: str) -> str:
    """植入器自证：文本必须真的变了，否则抛错（防静默空转）。"""
    if modified == original:
        raise ValueError(
            f"植入器 {what} 未改动文本——锚点与模板不匹配，样本会退化为干净论文"
        )
    return modified


# 干净模板中的正确数值行（数值复算的基准真值）
_CORRECT_E_X_AT_1 = "2.718282"


def inject_dimension_mismatch(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """把量纲声明 [F] 的指数从 -2 改为 -1，与 F = m·a 推导出的量纲不一致。"""
    anchor = r"[F] = [M][L][T]^{-2}"
    replacement = r"[F] = [M][L][T]^{-1}"
    modified = tex.replace(anchor, replacement)
    _require_change(tex, modified, "dimension_mismatch")
    truth = {
        "error_type": "dimension_mismatch",
        "location": "eq:dim-decl",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_illegal_derivation(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """把推导链末步的极限结果由 e^x 改为 e^{2x}（非法等价变换）。"""
    rng = SplitMix64(seed)
    # 非法指数由 seed 决定：2 或 3 —— 都是非法结果，但文本随 seed 变化，
    # 使"同 seed 逐字节一致/异 seed 不同"成为可证伪的确定性命题。
    bad_exp = 2 + (rng.next() % 2)
    anchor = r"\frac{e^h - 1}{h} = e^x."
    replacement = r"\frac{e^h - 1}{h} = e^{%d x}." % bad_exp
    modified = tex.replace(anchor, replacement)
    _require_change(tex, modified, "illegal_derivation")
    truth = {
        "error_type": "illegal_derivation",
        "location": "eq:deriv",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_numeric_mismatch(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """把数值表中 f(1) 改错，偏移量由 splitmix64 决定且必然超出容差。

    偏移量取整数值（第 3 位小数起跳），再按 10^6 缩放到小数位——
    这样既不引入"容差形状"的字面量（K7 禁硬编码容差），
    又能保证偏移量远大于 1e-4（复算必然判不一致）。
    """
    rng = SplitMix64(seed)
    # 偏移 = (5 + [0,999]) / 10^6  →  [5e-6, 1.004e-3]，取 >=5e-6 且保证超容差
    offset_int = 5000 + (rng.next() % 995001)
    scale = 10 ** 6
    wrong = "%.6f" % (float(_CORRECT_E_X_AT_1) + offset_int / scale)
    anchor = "1 & %s \\\\" % _CORRECT_E_X_AT_1
    replacement = "1 & %s \\\\" % wrong
    modified = tex.replace(anchor, replacement)
    _require_change(tex, modified, "numeric_mismatch")
    truth = {
        "error_type": "numeric_mismatch",
        "location": "table-001, row-02",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_dangling_ref(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """删除 thm:main 的 label 定义，使推论中的 \\ref{thm:main} 悬空。

    分类口径：引用来自**推论/正文**（引用他人结果）→ dangling_ref。
    """
    anchor = "\\begin{theorem}[Main Theorem]\n\\label{thm:main}"
    replacement = "\\begin{theorem}[Main Theorem]"
    modified = tex.replace(anchor, replacement)
    _require_change(tex, modified, "dangling_ref")
    truth = {
        "error_type": "dangling_ref",
        "location": "cor:result 引用 thm:main",
        "is_clean": False,
        "expected_verdict": "invalid",
    }
    return modified, truth


def inject_dep_chain_break(tex: str, seed: int) -> tuple[str, Dict[str, Any]]:
    """删除基础引理 lem:base 的 label，使 lem:aux 的前置依赖断链。

    分类口径：引用来自**引理/定理正文**（依赖前置结果）→ dep_chain_break。
    """
    anchor = "\\begin{lemma}[Base Lemma]\n\\label{lem:base}"
    replacement = "\\begin{lemma}[Base Lemma]"
    modified = tex.replace(anchor, replacement)
    _require_change(tex, modified, "dep_chain_break")
    truth = {
        "error_type": "dep_chain_break",
        "location": "lem:aux → lem:base（前置引理缺失）",
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
