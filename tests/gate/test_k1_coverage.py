"""K1 守门：解析覆盖率如实报告（分母含未覆盖项）。"""

from __future__ import annotations

import tempfile
import pytest

from auditor.core.parser import parse


def test_k1_coverage_le_one():
    """K1: 覆盖率必须 ≤ 1.0。"""
    tex = r"""\documentclass{article}
\begin{document}
\section{Test}
\begin{equation}
E = mc^2
\end{equation}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert result.coverage <= 1.0


def test_k1_coverage_with_unrecognized():
    """K1: 有未覆盖项时覆盖率 < 1.0。"""
    tex = r"""\documentclass{article}
\begin{document}
\section{Test}
\begin{unknownenv}
Unknown content
\end{unknownenv}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert result.coverage < 1.0
    assert len(result.unrecognized_envs) > 0


def test_k1_coverage_denominator_includes_unrecognized():
    """K1: 分母必须包含未覆盖项。"""
    tex = r"""\documentclass{article}
\begin{document}
\section{Test}
\begin{equation}
E = mc^2
\end{equation}
\begin{unknownenv}
Unknown
\end{unknownenv}
\begin{anotherunknown}
Also unknown
\end{anotherunknown}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    # 两个未识别环境，覆盖率应明显低于 1.0
    assert result.coverage < 1.0
    assert len(result.unrecognized_envs) >= 2


def test_k1_coverage_perfect_parsing():
    """K1: 完全识别时覆盖率 = 1.0。"""
    tex = r"""\documentclass{article}
\usepackage{amsmath}
\begin{document}
\section{Test}
\begin{equation}
\label{eq:test}
E = mc^2
\end{equation}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    # 所有环境都被识别
    assert result.coverage == 1.0
    assert len(result.unrecognized_envs) == 0


def test_k1_coverage_synthetic_samples():
    """K1: 合成样本覆盖率报告。"""
    import json
    from pathlib import Path

    truth_path = Path("data/benchmark/truth.json")
    if truth_path.exists():
        with open(truth_path, 'r', encoding='utf-8') as f:
            truth = json.load(f)

        for entry in truth[:5]:  # 只测前 5 个
            sample_path = entry['input_card']['paper_tex']
            if Path(sample_path).exists():
                result = parse(sample_path)
                assert 0.0 <= result.coverage <= 1.0
