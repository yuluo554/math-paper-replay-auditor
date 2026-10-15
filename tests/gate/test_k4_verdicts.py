"""K4: verdict 三态守门。

断言所有 verdict 值只允许 ok / invalid / undecidable。
"""

from __future__ import annotations

from auditor.core.types import Verdict


def test_verdict_three_values():
    """K4: Verdict 枚举只含三态。"""
    assert set(v.value for v in Verdict) == {"ok", "invalid", "undecidable"}


def test_verdict_no_fourth_value():
    """K4: 文档中不得出现第四态词面。"""
    import re
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    fourth_state_words = {"compliant", "skipped", "unknown", "failed", "pass"}

    for md_file in (project_root / "plan").rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for word in fourth_state_words:
            # 排除 "undecidable" 中的 "decidable"
            if word in content and word != "decidable":
                assert False, f"{md_file} 含第四态词面: {word}"
