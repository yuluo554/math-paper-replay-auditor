"""K17: 真值库无 observed 字段。

防"比对两份冻结字典"假门（引擎坏掉也全绿）。

D7：本门此前只有 1 项、只查 observed 字段，且 `test_k31_mutation.py` 里
**另写了一份**同样的判据（不 import 真门），导致"变异验证"自我确认
（实测：把本门改成 no-op 后 K31 仍 4 passed）。

现在：
- 判据的唯一实现是 `tests/gate/_k17_truth_logic.py::find_observed_entries`；
- 真值库路径提到模块级常量 `TRUTH_PATH`，让 K31 能把它指向污染副本后
  **调用本门的真函数**——本门被改成 no-op 时，K31 必然变红。
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.gate._k17_truth_logic import find_observed_entries

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 模块级常量：K31 变异验证会把它指向一份被污染的副本再调用本门
TRUTH_PATH = REPO_ROOT / "data" / "benchmark" / "truth.json"


def test_no_observed_in_truth():
    """K17: 真值库中不得出现 observed 字段。"""
    truth_file = TRUTH_PATH

    if not truth_file.exists():
        # 真值库尚未生成，跳过（M1 生成器产出后自动生效）
        return

    truth = json.loads(truth_file.read_text(encoding="utf-8"))
    offenders = find_observed_entries(truth)
    assert not offenders, (
        "真值条目含 observed 字段: " + ", ".join(offenders[:10])
    )
