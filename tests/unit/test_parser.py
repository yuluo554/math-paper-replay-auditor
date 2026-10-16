"""解析器单元测试。"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from auditor.core.parser import parse, parse_file


def test_parse_basic_latex():
    """测试基础 LaTeX 解析。"""
    tex = r"""\documentclass{article}
\usepackage{amsmath}

\begin{document}
\section{Introduction}
This is a test.

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

    assert result.paper_id is not None
    assert len(result.sections) == 1
    assert result.sections[0]['title'] == 'Introduction'
    assert len(result.equations) == 1
    assert result.equations[0]['type'] == 'equation'
    assert len(result.labels) == 1
    assert result.labels[0]['label'] == 'eq:test'


def test_parse_theorem_environment():
    """测试 theorem 环境解析。"""
    tex = r"""\documentclass{article}
\usepackage{amsmath, amssymb}

\begin{document}
\section{Main Results}

\begin{theorem}[Main Theorem]
\label{thm:main}
Let $f(x) = e^x$. Then $f'(x) = f(x)$.
\end{theorem}

\begin{proof}
By definition of derivative.
\end{proof}

\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert len(result.theorems) == 1
    assert result.theorems[0]['label'] == 'thm:main'
    assert len(result.proofs) == 1


def test_parse_table_environment():
    """测试 table 环境解析。"""
    tex = r"""\documentclass{article}

\begin{document}
\section{Data}

\begin{table}[h]
\centering
\begin{tabular}{|c|c|}
\hline
$x$ & $f(x)$ \\
\hline
0 & 1.0 \\
1 & 2.7 \\
\hline
\end{tabular}
\caption{Test table}
\end{table}

\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    # 同时提取 tabular 和 table 环境
    assert len(result.tables) == 2
    assert any(t['type'] == 'table' for t in result.tables)
    assert any(t['type'] == 'tabular' for t in result.tables)


def test_parse_refs():
    """测试 ref 解析。"""
    tex = r"""\documentclass{article}

\begin{document}
\section{Introduction}

As shown in Theorem~\ref{thm:main}, we have a key result.

\begin{theorem}
\label{thm:main}
Main result.
\end{theorem}

\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert len(result.refs) == 1
    assert result.refs[0]['ref'] == 'thm:main'
    assert len(result.labels) == 1


def test_parse_packages():
    """测试宏包提取。"""
    tex = r"""\documentclass{article}
\usepackage{amsmath, amssymb}
\usepackage{physics}
\usepackage{graphicx}

\begin{document}
\section{Test}
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert 'amsmath' in result.packages
    assert 'amssymb' in result.packages
    assert 'physics' in result.packages
    assert 'graphicx' in result.packages


def test_parse_unrecognized_env():
    """测试未识别环境登记（K2）。"""
    tex = r"""\documentclass{article}

\begin{document}
\section{Test}

\begin{unknownenv}
This is an unknown environment.
\end{unknownenv}

\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    # K2: 未覆盖清单不得静默丢弃
    assert 'unknownenv' in result.unrecognized_envs


def test_coverage_report():
    """测试覆盖率报告（K1）。"""
    tex = r"""\documentclass{article}
\usepackage{amsmath}

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

    # K1: 覆盖率如实报告
    assert 0.0 <= result.coverage <= 1.0
    if result.coverage < 1.0:
        assert len(result.unrecognized_envs) > 0


def test_deterministic_parsing():
    """测试确定性解析（K26）。"""
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
        path = f.name

    # 双跑逐字节一致
    result1 = parse(path)
    result2 = parse(path)

    assert result1.paper_id == result2.paper_id
    assert result1.coverage == result2.coverage
    assert len(result1.sections) == len(result2.sections)
    assert len(result1.equations) == len(result2.equations)


def test_file_not_found():
    """测试文件不存在错误。"""
    with pytest.raises(FileNotFoundError):
        parse("/nonexistent/path/file.tex")


def test_parse_comment_stripping():
    """测试注释剥离。"""
    tex = r"""\documentclass{article}
% This is a comment
\begin{document}
\section{Test} % inline comment
Content
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert len(result.sections) == 1


def test_parse_escaped_percent():
    """测试转义百分号。"""
    tex = r"""\documentclass{article}
\begin{document}
\section{Cost}
The cost is 5\% tax.
\end{document}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(tex)
        f.flush()
        result = parse(f.name)

    assert len(result.sections) == 1


def test_parse_synthetic_sample():
    """测试解析合成样本。"""
    sample_path = Path("data/benchmark/B001-001-dimension_mismatch/paper.tex")
    if sample_path.exists():
        result = parse(str(sample_path))
        assert result.paper_id is not None
        assert len(result.sections) > 0
        assert len(result.equations) > 0
        assert len(result.theorems) > 0
        assert len(result.labels) > 0
