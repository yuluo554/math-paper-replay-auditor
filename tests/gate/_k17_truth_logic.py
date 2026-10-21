"""K17 判据的**唯一实现**（被 K17 门与 K31 变异验证共用）。

D7 的问题：`test_k31_mutation.py` 里的 `_run_k17_gate()` 是**本地重写**的一段
判据——它不 import 真门，所以把真门改成 no-op 后它仍然绿（实测：4 passed），
"变异验证"就变成自我确认。

修法：把判据抽到这里，K17 门与 K31 都调用它——
真门被改成 no-op 或判据被改坏，K31 必然变红。
"""

from __future__ import annotations

from typing import Any, Dict, List


def find_observed_entries(truth: List[Dict[str, Any]]) -> List[str]:
    """返回真值台账里含 observed 字段的条目 sample_id 列表。

    K17 的判据本体：真值库只存输入与期望，**不存 observed**（观测运行时实算）。
    """
    offenders = []
    for entry in truth:
        if "observed" in entry:
            offenders.append(str(entry.get("sample_id", "unknown")))
    return offenders
