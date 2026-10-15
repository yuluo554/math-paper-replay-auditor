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
) -> Dict[str, Any]:
    """生成一个样本（论文 + 真值条目）。"""
    # 1. 生成基础论文
    base_tex = generate_paper(sample_id, seed)

    # 2. 植入错误
    injector = INJECTORS[error_type]
    modified_tex, truth = injector(base_tex, seed)

    # 3. 落盘论文
    sample_dir = output_dir / f"{sample_id}-{error_type}"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "paper.tex").write_text(modified_tex, encoding="utf-8")

    # 4. 构建真值条目
    entry = {
        "sample_id": f"{sample_id}-{error_type}",
        "input_card": {
            "paper_tex": str(sample_dir / "paper.tex"),
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
