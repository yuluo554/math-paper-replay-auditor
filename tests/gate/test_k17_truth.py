"""K17: 真值库无 observed 字段。

防"比对两份冻结字典"假门（引擎坏掉也全绿）。
"""

from __future__ import annotations

import json
from pathlib import Path


def test_no_observed_in_truth():
    """K17: 真值库中不得出现 observed 字段。"""
    project_root = Path(__file__).parent.parent.parent
    truth_file = project_root / "data" / "benchmark" / "truth.json"

    if not truth_file.exists():
        # 真值库尚未生成，跳过（M1 生成器产出后自动生效）
        return

    truth = json.loads(truth_file.read_text(encoding="utf-8"))
    for entry in truth:
        assert "observed" not in entry, (
            f"真值条目 {entry.get('sample_id', 'unknown')} 含 observed 字段"
        )
