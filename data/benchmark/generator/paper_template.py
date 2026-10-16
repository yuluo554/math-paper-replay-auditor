"""合成论文 LaTeX 模板。

生成完整论文骨架：section / equation / theorem / lemma / proof / table / ref / label。

模板必须为五类植入错误各留可检出锚点（否则植入器静默空转、引擎无物可判）：
- 符号推导链（eq:deriv）→ illegal_derivation
- 显式量纲声明（eq:dim-decl）→ dimension_mismatch
- 可复算数值表（table，公式 f(x)=e^x）→ numeric_mismatch
- 被正文引用的 label（thm:main）→ dangling_ref
- 两级依赖链（cor:result → lem:aux → lem:base）→ dep_chain_break

干净模板纪律：**每个 label 都被至少引用一次**——K14 规定"幽灵 label"
（从未被引用的 label）判 undecidable，若干净样本残留幽灵 label，
其聚合结论就不是 ok，误报率口径会被结构性噪音污染。
"""

from __future__ import annotations

from typing import Dict, Any
from .deterministic_rng import SplitMix64


PAPER_TEMPLATE = r"""\documentclass{{article}}
\usepackage{{amsmath, amssymb}}

\title{{Synthetic Paper for Benchmark {sample_id}}}
\author{{A. Example \\ Example University}}
\date{{\today}}

\begin{{document}}
\maketitle

\section{{Introduction}}
This is a synthetic paper for benchmarking the math paper replay auditor.
The main statement is Theorem~\ref{{thm:main}} and its consequence is
Corollary~\ref{{cor:result}}.

\section{{Main Results}}
\begin{{theorem}}[Main Theorem]
\label{{thm:main}}
Let $f(x) = e^x$. Then for all $x \in \mathbb{{R}}$, we have
\begin{{equation}}
\label{{eq:main}}
f'(x) = f(x).
\end{{equation}}
\end{{theorem}}

\begin{{proof}}
By definition of the derivative,
\begin{{equation}}
\label{{eq:deriv}}
f'(x) = \lim_{{h \to 0}} \frac{{f(x+h) - f(x)}}{{h}} = \lim_{{h \to 0}} \frac{{e^{{x+h}} - e^x}}{{h}} = e^x \lim_{{h \to 0}} \frac{{e^h - 1}}{{h}} = e^x.
\end{{equation}}
\end{{proof}}

\begin{{lemma}}[Auxiliary Lemma]
\label{{lem:aux}}
By Lemma~\ref{{lem:base}}, for all $x \in \mathbb{{R}}$, $e^x > 0$.
\end{{lemma}}

\begin{{lemma}}[Base Lemma]
\label{{lem:base}}
For all $x \in \mathbb{{R}}$, $e^x$ is strictly increasing.
\end{{lemma}}

\begin{{corollary}}
\label{{cor:result}}
From Theorem~\ref{{thm:main}} and Lemma~\ref{{lem:aux}}, $f'(x) > 0$ for all $x \in \mathbb{{R}}$.
\end{{corollary}}

\section{{Dimensional Analysis}}
The force law is
\begin{{equation}}
\label{{eq:dim}}
F = m \cdot a
\end{{equation}}
with the dimensional declaration
\begin{{equation}}
\label{{eq:dim-decl}}
[F] = [M][L][T]^{{-2}}, \quad [m] = [M], \quad [a] = [L][T]^{{-2}}
\end{{equation}}
Equation~\ref{{eq:dim}} together with Equation~\ref{{eq:dim-decl}} fixes the dimensions.

\section{{Numerical Examples}}
The function $f(x) = e^x$ is evaluated at integer points below; see
Equation~\ref{{eq:main}} and Equation~\ref{{eq:deriv}} for the analytic basis.
\begin{{table}}[h]
\centering
\begin{{tabular}}{{|c|c|}}
\hline
$x$ & $f(x)$ \\
\hline
0 & 1.000000 \\
1 & 2.718282 \\
2 & 7.389056 \\
\hline
\end{{tabular}}
\caption{{Numerical example for $f(x) = e^x$}}
\end{{table}}

\end{{document}}
"""


def generate_paper(sample_id: str, seed: int = 42) -> str:
    """生成合成论文 LaTeX。"""
    rng = SplitMix64(seed)
    return PAPER_TEMPLATE.format(sample_id=sample_id)
