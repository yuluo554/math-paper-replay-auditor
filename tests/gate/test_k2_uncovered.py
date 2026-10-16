"""K2 守门：未覆盖清单不得静默丢弃。"""

from __future__ import annotations

import tempfile
import pytest

from auditor.core.parser import parse


def test_k2_unrecognized_not_discarded():
    """K2: 未识别环境必须登记。"""
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

    # K2: 未覆盖清单不得静默丢弃
    assert 'unknownenv' in result.unrecognized_envs


def test_k2_multiple_unrecognized():
    """K2: 多个未识别环境都登记。"""
    tex = r"""\documentclass{article}
\begin{document}
\section{Test}
\begin{unknownenv}
Unknown 1
\end{unknownenv}
\begin{anotherunknown}
Unknown 2
\end{anotherunknown}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert 'unknownenv' in result.unrecognized_envs
    assert 'anotherunknown' in result.unrecognized_envs


def test_k2_unrecognized_reflected_in_coverage():
    """K2: 未覆盖清单必须反映在覆盖率中。"""
    tex = r"""\documentclass{article}
\begin{document}
\section{Test}
\begin{equation}
E = mc^2
\end{equation}
\begin{unknownenv}
Unknown
\end{unknownenv}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    # 有未覆盖项时覆盖率 < 1.0
    if len(result.unrecognized_envs) > 0:
        assert result.coverage < 1.0


def test_k2_no_false_positives():
    """K2: 已知环境不进入未覆盖清单。"""
    tex = r"""\documentclass{article}
\usepackage{amsmath}
\begin{document}
\section{Test}
\begin{equation}
E = mc^2
\end{equation}
\begin{table}
Test
\end{table}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    # 已知环境不应进入未覆盖清单
    assert 'equation' not in result.unrecognized_envs
    assert 'table' not in result.unrecognized_envs


def test_k2_synthetic_samples_unrecognized():
    """K2: 合成样本未覆盖清单。"""
    import json
    from pathlib import Path

    truth_path = Path("data/benchmark/truth.json")
    if truth_path.exists():
        with open(truth_path, 'r', encoding='utf-8') as f:
            truth = json.load(f)

        for entry in truth[:5]:
            sample_path = entry['input_card']['paper_tex']
            if Path(sample_path).exists():
                result = parse(sample_path)
                # 未覆盖清单必须存在（可能为空列表，但不能为 None）
                assert result.unrecognized_envs is not None
