"""编排层——CLI 与 GUI 共用同一 API。

K40: 此模块为编排层公开函数组，表现层只准经这些入口取数。
"""

from __future__ import annotations

from typing import Optional, List

from auditor.core.types import AuditResult, PaperStructure


def parse_paper(input_path: str) -> PaperStructure:
    """K1: 解析论文，返回结构树。"""
    from auditor.core.parser import parse
    return parse(input_path)


def audit_paper(input_path: str, with_llm: bool = False) -> int:
    """审计一篇论文。退出码：0=达标, 1=未达标, 2=用法错误, 3=缺依赖。"""
    # TODO M2: 实现
    return 0


def run_benchmark(only: Optional[List[str]] = None, verbose: bool = False) -> int:
    """运行基准套件。退出码：0=全绿, 1=未达标, 2=用法错误。"""
    from auditor.benchmark.runner import BenchmarkRunner

    runner = BenchmarkRunner()
    result = runner.run(only=only, verbose=verbose)
    return result.exit_code if hasattr(result, "exit_code") else 0


def fetch_arxiv(arxiv_id: str) -> int:
    """从 arXiv 获取论文。退出码：0=成功, 2=用法错误。"""
    # TODO M1: 实现
    return 0


def selftest() -> bool:
    """K42: 冻结态自检。返回 True 表示通过。"""
    # TODO M5: 实现
    return True
