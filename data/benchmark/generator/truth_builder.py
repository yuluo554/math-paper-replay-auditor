"""真值构建器——从生成器产出构建真值台账。

K17: 真值库只存输入与期望，不存 observed。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List
from .deterministic_rng import SplitMix64
from .paper_template import generate_paper
from .error_injector import (
    ERROR_TYPES,
    inject_dimension_mismatch,
    inject_illegal_derivation,
    inject_numeric_mismatch,
    inject_dangling_ref,
    inject_dep_chain_break,
    make_clean,
)


INJECTORS = {
    "dimension_mismatch": inject_dimension_mismatch,
    "illegal_derivation": inject_illegal_derivation,
    "numeric_mismatch": inject_numeric_mismatch,
    "dangling_ref": inject_dangling_ref,
    "dep_chain_break": inject_dep_chain_break,
    "clean": make_clean,
}


def generate_sample(
    sample_id: str,
    error_type: str,
    seed: int,
    output_dir: Path,
    path_prefix: str = "data/benchmark",
) -> Dict[str, Any]:
    """生成一个样本（论文 + 真值条目）。

    Args:
        path_prefix: 真值库中 paper_tex 的规范前缀（仓库相对 POSIX）。
            与 output_dir 解耦，使产物**不随生成位置变化**（K20 位级一致）。
    """
    # 1. 生成基础论文
    base_tex = generate_paper(sample_id, seed)

    # 2. 植入错误
    injector = INJECTORS[error_type]
    modified_tex, truth = injector(base_tex, seed)

    # 3. 落盘论文
    sample_name = f"{sample_id}-{error_type}"
    sample_dir = output_dir / sample_name
    sample_dir.mkdir(parents=True, exist_ok=True)
    # 行尾一律 LF：Windows 文本模式会把 \n 翻成 \r\n，使"跨平台位级一致"失效。
    # Path.write_text(newline=) 是 3.10+ 参数，3.8 底线须走 open(newline="")。
    with open(sample_dir / "paper.tex", "w", encoding="utf-8", newline="") as f:
        f.write(modified_tex.replace("\r\n", "\n").replace("\r", "\n"))

    # 4. 构建真值条目
    # paper_tex 一律写**规范仓库相对 POSIX 路径**：绝对路径或含盘符路径会让
    # 产物随输出目录变化（跨机/跨平台位级不一致），冻结态还要另做路径翻译。
    entry = {
        "sample_id": sample_name,
        "input_card": {
            "paper_tex": f"{path_prefix}/{sample_name}/paper.tex",
            "paper_id": f"synth-{sample_id}",
        },
        "expect": truth,
        "generator_seed": seed,
        "generator_version": "1.0.0",
        # 不存 observed！
    }
    return entry


def generate_all(
    output_dir: Path,
    min_per_type: int = 3,
    clean_count: int = 3,
    base_seed: int = 42,
) -> Dict[str, Any]:
    """生成全部样本，返回真值台账与 manifest。"""
    truth_entries = []
    sample_counts = {}

    # 生成错误样本
    for i, error_type in enumerate(ERROR_TYPES):
        count = min_per_type
        sample_counts[error_type] = {"total": count, "min_required": count}
        for j in range(count):
            seed = base_seed + i * 100 + j
            entry = generate_sample(
                f"B{i+1:03d}-{j+1:03d}",
                error_type,
                seed,
                output_dir,
            )
            truth_entries.append(entry)

    # 生成干净样本
    sample_counts["clean"] = {"total": clean_count, "min_required": clean_count}
    for j in range(clean_count):
        seed = base_seed + 999 + j
        entry = generate_sample(
            f"C{j+1:03d}",
            "clean",
            seed,
            output_dir,
        )
        truth_entries.append(entry)

    manifest = {
        "total_samples": len(truth_entries),
        "sampling_note": "抽样覆盖非穷举",
        "by_error_type": sample_counts,
    }

    return {"truth": truth_entries, "manifest": manifest}
