"""基准 runner——加载真值库 + 运行引擎 + 计算指标。

K18: 覆盖度分母反射自代码常量
K19: 误报率 0 优先
K22: 探活打在消费处
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from .metrics import BenchmarkMetrics, calculate_metrics, format_metrics


# 错误类型白名单（K18: 覆盖度分母反射自代码常量）
ERROR_TYPES = [
    "dimension_mismatch",
    "illegal_derivation",
    "numeric_mismatch",
    "dangling_ref",
    "dep_chain_break",
]


@dataclass
class BenchmarkResult:
    """基准结果。"""

    total_samples: int = 0
    metrics: Optional[BenchmarkMetrics] = None
    sample_results: List[Dict[str, Any]] = field(default_factory=list)
    passed: bool = False
    exit_code: int = 0


def load_truth(benchmark_dir: str = "data/benchmark") -> List[Dict[str, Any]]:
    """加载真值库。

    Args:
        benchmark_dir: 基准数据目录

    Returns:
        真值库条目列表
    """
    truth_path = Path(benchmark_dir) / "truth.json"
    if not truth_path.exists():
        raise FileNotFoundError(f"真值库不存在: {truth_path}")

    with open(truth_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest(benchmark_dir: str = "data/benchmark") -> Dict[str, Any]:
    """加载覆盖度口径。

    Args:
        benchmark_dir: 基准数据目录

    Returns:
        manifest 字典
    """
    manifest_path = Path(benchmark_dir) / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json 不存在: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _aggregate_verdict(claims: List[Dict[str, Any]]) -> str:
    """从多条断言结果聚合为单一样本 verdict。

    优先级：invalid > undecidable > ok

    Args:
        claims: 断言结果列表

    Returns:
        聚合后的 verdict
    """
    if not claims:
        return "undecidable"

    has_invalid = False
    has_undecidable = False

    for claim in claims:
        verdict = claim.get("verdict", "undecidable")
        if verdict == "invalid":
            has_invalid = True
        elif verdict == "undecidable":
            has_undecidable = True

    if has_invalid:
        return "invalid"
    if has_undecidable:
        return "undecidable"
    return "ok"


def _audit_sample(sample_id: str, paper_tex: str) -> List[Dict[str, Any]]:
    """审计单个样本。

    Args:
        sample_id: 样本 ID
        paper_tex: 论文 LaTeX 文件路径

    Returns:
        断言结果列表
    """
    from auditor.core.parser import parse
    from auditor.core.replay import replay
    from auditor.core.numerical import recompute_numerical
    from auditor.core.dimensional import check_dimensions
    from auditor.core.graph import check_dependency_graph

    # 解析论文
    tree = parse(paper_tex)

    # 将 Pydantic 模型转为字典
    tree_dict = tree.model_dump() if hasattr(tree, 'model_dump') else tree.__dict__

    # 运行所有引擎
    all_claims = []

    # 符号重放
    replay_claims = replay(tree_dict)
    all_claims.extend([
        {
            "claim_id": c.claim_id,
            "verdict": c.verdict.value if hasattr(c.verdict, 'value') else str(c.verdict),
            "engine": "replay",
        }
        for c in replay_claims
    ])

    # 数值复算
    numerical_claims = recompute_numerical(tree_dict)
    all_claims.extend([
        {
            "claim_id": c.claim_id,
            "verdict": c.verdict.value if hasattr(c.verdict, 'value') else str(c.verdict),
            "engine": "numerical",
        }
        for c in numerical_claims
    ])

    # 量纲审计
    dim_claims = check_dimensions(tree_dict)
    all_claims.extend([
        {
            "claim_id": c.claim_id,
            "verdict": c.verdict.value if hasattr(c.verdict, 'value') else str(c.verdict),
            "engine": "dimensional",
        }
        for c in dim_claims
    ])

    # 依赖图
    graph_claims = check_dependency_graph(tree_dict)
    all_claims.extend([
        {
            "claim_id": c.claim_id,
            "verdict": c.verdict.value if hasattr(c.verdict, 'value') else str(c.verdict),
            "engine": "graph",
        }
        for c in graph_claims
    ])

    return all_claims


def run_benchmark(
    benchmark_dir: str = "data/benchmark",
    only: Optional[List[str]] = None,
    verbose: bool = False,
) -> BenchmarkResult:
    """运行基准套件。

    Args:
        benchmark_dir: 基准数据目录
        only: 只跑特定错误类型（白名单）
        verbose: 是否输出详细信息

    Returns:
        BenchmarkResult: 基准结果
    """
    result = BenchmarkResult()

    # 加载真值库
    try:
        truth = load_truth(benchmark_dir)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        result.exit_code = 2
        return result

    # 加载 manifest
    try:
        manifest = load_manifest(benchmark_dir)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        result.exit_code = 2
        return result

    # K18: --only 白名单校验
    if only:
        for error_type in only:
            if error_type not in ERROR_TYPES:
                print(
                    f"错误: 未知错误类型 '{error_type}'，"
                    f"白名单: {ERROR_TYPES}",
                    file=sys.stderr,
                )
                result.exit_code = 2
                return result

    # 过滤样本
    filtered_truth = truth
    if only:
        filtered_truth = [
            entry for entry in truth
            if entry["expect"].get("is_clean", False)
            or entry["expect"].get("error_type") in only
        ]

    result.total_samples = len(filtered_truth)

    # 运行审计
    sample_results: Dict[str, str] = {}

    for entry in filtered_truth:
        sample_id = entry["sample_id"]
        paper_tex = entry["input_card"]["paper_tex"]

        if verbose:
            print(f"审计样本: {sample_id}", file=sys.stderr)

        try:
            claims = _audit_sample(sample_id, paper_tex)
            verdict = _aggregate_verdict(claims)
            sample_results[sample_id] = verdict

            result.sample_results.append({
                "sample_id": sample_id,
                "verdict": verdict,
                "expected": entry["expect"]["expected_verdict"],
                "is_clean": entry["expect"].get("is_clean", False),
                "error_type": entry["expect"].get("error_type"),
            })
        except Exception as e:
            # 单件异常不中断整批（K30）
            print(f"警告: 样本 {sample_id} 审计失败: {e}", file=sys.stderr)
            sample_results[sample_id] = "undecidable"
            result.sample_results.append({
                "sample_id": sample_id,
                "verdict": "undecidable",
                "expected": entry["expect"]["expected_verdict"],
                "is_clean": entry["expect"].get("is_clean", False),
                "error_type": entry["expect"].get("error_type"),
                "error": str(e),
            })

    # 计算指标
    result.metrics = calculate_metrics(filtered_truth, sample_results)
    result.passed = result.metrics.overall_passed

    # 退出码：0=全绿, 1=未达标, 2=用法错误
    if result.passed:
        result.exit_code = 0
    else:
        result.exit_code = 1

    return result


def main() -> int:
    """CLI 入口。退出码：0=全绿, 1=未达标, 2=用法错误。"""
    import argparse

    parser = argparse.ArgumentParser(
        prog="auditor bench",
        description="运行基准套件",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="只跑特定错误类型（逗号分隔）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="输出详细信息",
    )
    parser.add_argument(
        "--benchmark-dir",
        default="data/benchmark",
        help="基准数据目录",
    )

    args = parser.parse_args()

    only = args.only.split(",") if args.only else None

    result = run_benchmark(
        benchmark_dir=args.benchmark_dir,
        only=only,
        verbose=args.verbose,
    )

    # 输出指标
    if result.metrics:
        print(format_metrics(result.metrics))

    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
