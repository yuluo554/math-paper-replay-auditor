"""K20: 生成器确定性守门。

两次运行逐字节一致（除临时路径外）。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from data.benchmark.generator import main as gen_main


def _normalize_truth(truth):
    """归一化 truth：将 paper_tex 路径替换为占位符。"""
    for entry in truth:
        if "input_card" in entry and "paper_tex" in entry["input_card"]:
            entry["input_card"]["paper_tex"] = "<SAMPLE_DIR>/paper.tex"
    return truth


def test_generator_deterministic():
    """K20: 生成器两次运行语义一致。"""
    with tempfile.TemporaryDirectory() as tmp1:
        with tempfile.TemporaryDirectory() as tmp2:
            # 第一次运行
            gen_main(tmp1, min_per_type=1, clean_count=1)
            # 第二次运行
            gen_main(tmp2, min_per_type=1, clean_count=1)

            # 比较 truth.json 内容（归一化路径）
            truth1 = _normalize_truth(
                json.loads((Path(tmp1) / "truth.json").read_text(encoding="utf-8"))
            )
            truth2 = _normalize_truth(
                json.loads((Path(tmp2) / "truth.json").read_text(encoding="utf-8"))
            )

            assert truth1 == truth2, "生成器两次运行结果不一致"

            # 比较 manifest.json
            manifest1 = json.loads(
                (Path(tmp1) / "manifest.json").read_text(encoding="utf-8")
            )
            manifest2 = json.loads(
                (Path(tmp2) / "manifest.json").read_text(encoding="utf-8")
            )
            assert manifest1 == manifest2, "manifest 两次运行不一致"
