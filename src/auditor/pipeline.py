"""编排层——CLI 与 GUI 共用同一 API。

K40: 此模块为编排层公开函数组，表现层只准经这些入口取数。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, List

from auditor.core.types import AuditResult, PaperStructure


def parse_paper(input_path: str) -> PaperStructure:
    """K1: 解析论文，返回结构树。"""
    from auditor.core.parser import parse
    return parse(input_path)


def _data_root() -> Path:
    """数据根目录（冻结态取解包根，源码态取 CWD）。"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(".")


def resolve_input_path(input_path: str) -> str:
    """把仓库相对路径挂到数据根；绝对路径原样返回。"""
    p = Path(input_path)
    if p.is_absolute():
        return str(p)
    return str(_data_root() / input_path)


def audit_paper(
    input_path: str,
    with_llm: bool = False,
    output_format: str = "markdown",
    output_path: Optional[str] = None,
) -> int:
    """审计一篇论文。退出码：0=无确证问题, 1=检出确证问题, 2=用法错误, 3=缺依赖。

    只跑确定性引擎（符号重放/数值复算/量纲/依赖图）；LLM 仅为可插拔辅助，
    默认关闭，且**从不参与数值结论**。
    """
    resolved = resolve_input_path(input_path)
    if not Path(resolved).exists():
        print(f"错误: 输入文件不存在: {input_path}", file=sys.stderr)
        return 2

    try:
        from auditor.core.parser import parse
        from auditor.core.replay import replay
        from auditor.core.numerical import recompute_numerical
        from auditor.core.dimensional import check_dimensions
        from auditor.core.graph import check_dependency_graph
    except ImportError as exc:  # 缺依赖 → exit 3（K24 语义）
        print(f"错误: 缺依赖 {exc}", file=sys.stderr)
        return 3

    try:
        tree = parse(resolved)
    except Exception as exc:
        print(f"错误: 解析失败: {exc}", file=sys.stderr)
        return 2

    tree_dict = tree.model_dump() if hasattr(tree, "model_dump") else tree.__dict__

    meta = {"degraded": False}
    if with_llm:
        from auditor.llm.bridge import check_llm_available
        available, reason = check_llm_available()
        if not available:
            # K16: 降级路径显式声明
            meta = {
                "degraded": True,
                "reason": f"模型开关已开启但端点不可用（{reason}），全部判定按确定性引擎给出",
            }

    claims = []
    claims.extend(replay(tree_dict))
    claims.extend(recompute_numerical(tree_dict))
    claims.extend(check_dimensions(tree_dict))
    claims.extend(check_dependency_graph(tree_dict))

    coverage = {
        "coverage": getattr(tree, "coverage", 1.0),
        "unrecognized_envs": list(getattr(tree, "unrecognized_envs", [])),
        "unrecognized_macros": list(getattr(tree, "unrecognized_macros", [])),
    }

    from auditor.report.renderer import build_report, render_markdown, render_json

    report = build_report(getattr(tree, "paper_id", input_path), claims, coverage, meta)

    if output_format == "json":
        text = render_json(report)
    else:
        text = render_markdown(report)

    if output_path:
        # K55：显式 newline="\n" 防 CRLF；write_text(newline=) 需 3.10+，故用 open()
        with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"报告已写入: {output_path}")
    else:
        print(text)

    # 退出码：有确证问题 → 1；否则 0
    return 1 if report["summary"].get("invalid", 0) > 0 else 0


def run_benchmark(only: Optional[List[str]] = None, verbose: bool = False) -> int:
    """运行基准套件。退出码：0=全绿, 1=未达标, 2=用法错误。"""
    from auditor.benchmark.runner import run_benchmark
    from auditor.benchmark.metrics import format_metrics

    result = run_benchmark(only=only, verbose=verbose)
    # 输出指标
    if result.metrics:
        print(format_metrics(result.metrics))
    return result.exit_code if hasattr(result, "exit_code") else 0


def fetch_arxiv(arxiv_id: str) -> int:
    """从 arXiv 获取论文。退出码：0=成功, 2=用法错误, 3=缺依赖。"""
    try:
        from auditor.fetch.arxiv import fetch
    except ImportError:
        print("错误: 抓取模块不可用（需联网开关）", file=sys.stderr)
        return 3
    return fetch(arxiv_id)


def selftest() -> bool:
    """K42: 冻结态自检——内嵌数据可达 + 核心引擎全链路可跑。

    不是"返回 True"的空壳：真的定位数据文件、真的跑四引擎、
    真的断言基准可复算。任一环失败即 False。
    """
    root = _data_root()

    # 1. 内嵌数据可达（冻结态必须落在解包目录内）
    truth = root / "data" / "benchmark" / "truth.json"
    manifest = root / "data" / "benchmark" / "manifest.json"
    if not truth.exists() or not manifest.exists():
        print(f"自检失败: 内嵌数据不可达（{truth}）", file=sys.stderr)
        return False

    # 2. 核心引擎可 import 且可跑
    try:
        import json as _json

        from auditor.core.parser import parse
        from auditor.core.replay import replay
        from auditor.core.numerical import recompute_numerical
        from auditor.core.dimensional import check_dimensions
        from auditor.core.graph import check_dependency_graph

        entries = _json.loads(truth.read_text(encoding="utf-8"))
        if not entries:
            print("自检失败: 真值库为空", file=sys.stderr)
            return False

        sample = entries[0]
        paper_path = root / sample["input_card"]["paper_tex"]
        if not paper_path.exists():
            print(f"自检失败: 样本不可达（{paper_path}）", file=sys.stderr)
            return False

        tree = parse(str(paper_path))
        tree_dict = tree.model_dump() if hasattr(tree, "model_dump") else tree.__dict__

        claims = (
            list(replay(tree_dict))
            + list(recompute_numerical(tree_dict))
            + list(check_dimensions(tree_dict))
            + list(check_dependency_graph(tree_dict))
        )
        if not claims:
            print("自检失败: 四引擎未产出任何断言", file=sys.stderr)
            return False
    except Exception as exc:
        print(f"自检失败: 引擎执行异常: {exc}", file=sys.stderr)
        return False

    # 3. 基准可复算且达标（全链路）
    try:
        from auditor.benchmark.runner import run_benchmark as _rb

        result = _rb()
        if not result.metrics or not result.metrics.overall_passed:
            fpr = result.metrics.false_positive_rate if result.metrics else float("nan")
            det = result.metrics.detection_rate if result.metrics else float("nan")
            print(
                f"自检失败: 基准未达标（检出率 {det:.2%}，误报率 {fpr:.2%}）",
                file=sys.stderr,
            )
            return False
    except Exception as exc:
        print(f"自检失败: 基准执行异常: {exc}", file=sys.stderr)
        return False

    return True
