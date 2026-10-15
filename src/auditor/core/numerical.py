"""数值断言复算引擎——与符号路径实现独立。

K7: 数值口径单一定义点
K8: 数值断言不采信符号路径自证
K9: 容差一处定义 + 注记同源
"""

from __future__ import annotations

from typing import Dict, Any, List

from auditor.core.types import ClaimResult, Verdict
from auditor.core.numerical_tolerance import NUMERICAL_TOLERANCE


def recompute_numerical(tree: Dict[str, Any]) -> List[ClaimResult]:
    """对论文数值断言做独立复算。"""
    # TODO M3: 实现 mpmath 数值复算
    return []
