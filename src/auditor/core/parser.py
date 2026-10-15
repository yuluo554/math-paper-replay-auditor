"""LaTeX 解析器——确定性解析，零模型。

K1: 解析覆盖率如实报告（分母含未覆盖项）
K2: 未覆盖清单不得静默丢弃
K3: 自定义宏需显式声明映射
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from auditor.core.types import PaperStructure


def parse(input_path: str) -> PaperStructure:
    """解析 LaTeX 论文，返回结构树。"""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # TODO M2: 实现完整解析逻辑
    return PaperStructure(
        paper_id=f"local:{path.name}",
        coverage=0.0,
        unrecognized_envs=[],
        unrecognized_macros=[],
    )
