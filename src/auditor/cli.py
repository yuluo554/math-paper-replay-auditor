"""CLI 入口。"""

from __future__ import annotations

import sys
import argparse
from typing import Optional

from auditor._encoding import ensure_utf8_stdio
from auditor import __version__


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="auditor",
        description="数学论文可验证重放审计器",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="打印工具版本并退出",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # audit
    audit_parser = subparsers.add_parser("audit", help="审计一篇论文")
    audit_parser.add_argument("--input", required=True, help="论文 .tex 文件或目录")
    audit_parser.add_argument("--with-llm", action="store_true", help="启用模型辅助归一化（默认关）")
    audit_parser.add_argument("--llm-endpoint", default=None, help="模型端点 URL")
    audit_parser.add_argument(
        "--format", default="markdown", choices=["markdown", "json"],
        help="报告格式（markdown=人读 / json=机读）",
    )
    audit_parser.add_argument("--output", default=None, help="报告输出路径（缺省打到 stdout）")

    # bench
    bench_parser = subparsers.add_parser("bench", help="运行基准套件")
    bench_parser.add_argument("--only", default=None, help="只跑特定错误类型（逗号分隔）")
    bench_parser.add_argument("--verbose", action="store_true")

    # selftest
    subparsers.add_parser("selftest", help="自检（内嵌数据定位 + calc 全链路）")

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="从 arXiv 获取论文")
    fetch_parser.add_argument("--arxiv-id", required=True, help="arXiv ID")

    return parser


def main() -> int:
    """CLI 主入口。退出码语义：0=达标, 1=未达标, 2=用法错误, 3=缺依赖。"""
    ensure_utf8_stdio()

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 2

    if args.command == "selftest":
        from auditor.pipeline import selftest
        return 0 if selftest() else 1

    if args.command == "bench":
        from auditor.pipeline import run_benchmark
        only = args.only.split(",") if args.only else None
        return run_benchmark(only=only, verbose=args.verbose)

    if args.command == "audit":
        from auditor.pipeline import audit_paper
        return audit_paper(
            input_path=args.input,
            with_llm=args.with_llm,
            output_format=args.format,
            output_path=args.output,
        )

    if args.command == "fetch":
        from auditor.pipeline import fetch_arxiv
        return fetch_arxiv(arxiv_id=args.arxiv_id)

    return 2


if __name__ == "__main__":
    sys.exit(main())
