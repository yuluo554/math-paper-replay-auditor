"""K53: sympy LaTeX 解析器的运行时前提必须可满足。

M6 实录：`sympy.parsing.latex` 的 ANTLR 后端在运行时链路里硬校验
`antlr4-python3-runtime` 版本必须为 4.11.x（源码内 `version(...).startswith('4.11')`）。
pyproject 原先把上界写成 `<4.14`，干净环境里 pip 解析到 4.13.2 →
`parse_latex` 抛 ImportError → 符号重放整链退化、illegal_derivation 类漏检，
而**开发机因恰好装着 4.11 全程全绿**——典型的"本机全绿掩盖干净环境失败"。

本守门把"版本前提"变成可证伪的断言，而不是依赖开发者机器上的偶然状态。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _read_pyproject() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def test_k53_antlr_pin_narrowed_to_4_11():
    """K53: pyproject 对 antlr4 的上界必须收在 4.11.x（sympy 硬要求）。"""
    text = _read_pyproject()
    # 连同版本约束一起抓，如 "antlr4-python3-runtime>=4.11,<4.12"
    pins = re.findall(r"antlr4-python3-runtime\s*([^\"'\n,\]]+(?:,[^\"'\n\]]+)*)", text)
    assert pins, "K53: pyproject 未声明 antlr4-python3-runtime"

    for pin in pins:
        # 允许 >4.11,<4.12 / ==4.11.1 等；关键是**不得**允许 4.12+
        allowed_4_12_plus = not ("<4.12" in pin or "==4.11" in pin)
        assert not allowed_4_12_plus, (
            f"K53 违规: antlr4 版本约束 '{pin.strip()}' 允许 4.12+，"
            "而 sympy 的 LaTeX 后端硬要求 4.11.x——干净环境会静默降级"
        )


def test_k53_parse_latex_actually_works_here():
    """K53: 当前环境里 parse_latex 必须真的能解析（非"能 import 就算过"）。"""
    try:
        from sympy.parsing.latex import parse_latex
    except Exception as exc:  # pragma: no cover - 环境缺依赖
        pytest.fail(f"K53: 无法 import parse_latex: {exc}")

    # 用一个必然要经过 ANTLR 后端的样例；缺运行时前提时这里会抛 ImportError
    try:
        expr = parse_latex(r"e^x")
    except Exception as exc:
        pytest.fail(
            f"K53 违规: parse_latex 在当前环境不可用（{type(exc).__name__}: {exc}）"
            "——符号重放会静默退化"
        )

    assert expr is not None, (
        "K53 违规: parse_latex 返回 None（缺 antlr 运行时会被静默吞掉）"
    )


def test_k53_latex_backend_failure_is_not_silently_swallowed():
    """K53: 重放引擎必须把"解析全失败"暴露成 undecidable，而非伪造成 ok/invalid。

    防"引擎整体失效但基准照常给分"：当所有等式都解析不出时，
    应当产出 undecidable（引擎能力外），而不是靠某条畸形路径蒙混。
    """
    from auditor.core.replay import _verify_equality_chain
    from auditor.core.types import Verdict

    # 构造一条左右都无法解析的等式
    verdict, steps, _ = _verify_equality_chain([(r"\undefinedmacroA{", r"\undefinedmacroB{")])
    assert verdict in (Verdict.UNDECIDABLE, Verdict.INVALID), (
        f"K53: 无法解析的等式应记 undecidable/invalid，实得 {verdict}"
    )
    assert verdict != Verdict.OK, "K53 违规: 解析失败不得被判 ok"
