"""GUI 编排层——零 Qt，只调引擎函数。

GUI 通过此模块调用引擎，不直接 import Qt。
"""

from __future__ import annotations

from typing import Optional

from auditor.core.parser import Parser
from auditor.core.replay import ReplayEngine
from auditor.core.numerical import NumericalEngine
from auditor.core.dimensional import DimensionalEngine
from auditor.core.graph import DependencyGraphEngine


def audit_paper(input_path: str, with_llm: bool = False) -> dict:
    """审计一篇论文。

    Args:
        input_path: 论文 .tex 文件或目录
        with_llm: 是否启用模型辅助归一化

    Returns:
        审计结果字典
    """
    # 解析
    parser = Parser()
    structure = parser.parse_file(input_path)

    # 符号重放
    replay = ReplayEngine()
    replay_results = replay.replay(structure)

    # 数值复算
    numerical = NumericalEngine()
    numerical_results = numerical.recompute(structure)

    # 量纲代数
    dimensional = DimensionalEngine()
    dimensional_results = dimensional.check(structure)

    # 依赖图
    graph = DependencyGraphEngine()
    graph_results = graph.analyze(structure)

    return {
        "structure": structure,
        "replay": replay_results,
        "numerical": numerical_results,
        "dimensional": dimensional_results,
        "graph": graph_results,
        "with_llm": with_llm,
    }


def run_benchmark(only: Optional[list] = None) -> dict:
    """运行基准套件。

    Args:
        only: 只跑特定错误类型

    Returns:
        基准结果
    """
    from auditor.benchmark.runner import BenchmarkRunner

    runner = BenchmarkRunner()
    return runner.run(only=only)
