"""K54: audit 编排链与报告双轨必须真实可用。

M5 遗留：`pipeline.audit_paper()` 与 `selftest()` 曾是 `return 0` / `return True`
的空壳，README 的头号功能 `audit` 对**不存在的路径也返回 0**——
即"命令跑通"是假绿。本守门把"编排链真的执行了审计"变成可证伪断言。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLEAN = REPO_ROOT / "data" / "benchmark" / "C001-clean" / "paper.tex"
ERROR_SAMPLE = REPO_ROOT / "data" / "benchmark" / "B002-001-illegal_derivation" / "paper.tex"


def test_k54_audit_rejects_nonexistent_input():
    """K54: 审计不存在的路径必须 exit 2（不是"跑通返回 0"）。"""
    from auditor.pipeline import audit_paper

    rc = audit_paper(input_path=str(REPO_ROOT / "data" / "definitely_missing.tex"))
    assert rc == 2, f"K54 违规: 缺文件应 exit 2，实得 {rc}"


def test_k54_audit_clean_paper_returns_zero():
    """K54: 干净论文审计 exit 0。"""
    from auditor.pipeline import audit_paper

    rc = audit_paper(input_path=str(CLEAN))
    assert rc == 0, f"K54: 干净论文应 exit 0，实得 {rc}"


def test_k54_audit_error_paper_returns_one():
    """K54: 含确证问题的论文 audit 必须 exit 1。"""
    from auditor.pipeline import audit_paper

    rc = audit_paper(input_path=str(ERROR_SAMPLE))
    assert rc == 1, f"K54: 含确证问题的论文应 exit 1，实得 {rc}"


def test_k54_report_dual_track_is_consistent(tmp_path):
    """K54: 人读与机读双轨内容一致（同一渲染源，非人工比对）。"""
    from auditor.pipeline import audit_paper

    md_path = tmp_path / "r.md"
    json_path = tmp_path / "r.json"
    audit_paper(input_path=str(ERROR_SAMPLE), output_format="markdown",
                output_path=str(md_path))
    audit_paper(input_path=str(ERROR_SAMPLE), output_format="json",
                output_path=str(json_path))

    md = md_path.read_text(encoding="utf-8")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # 机读汇总与人读汇总必须同源
    assert data["summary"]["invalid"] > 0
    assert f"| 确证问题 | {data['summary']['invalid']} |" in md

    # 每条机读断言都要能在人读里找到 claim_id
    for claim in data["claims"]:
        assert claim["claim_id"] in md, f"K54: 人读报告缺断言 {claim['claim_id']}"


def test_k54_report_json_is_byte_reproducible(tmp_path):
    """K54: 机读产物逐字节可复现（自写最小 writer 的意义所在）。"""
    from auditor.pipeline import audit_paper

    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    audit_paper(input_path=str(ERROR_SAMPLE), output_format="json", output_path=str(a))
    audit_paper(input_path=str(ERROR_SAMPLE), output_format="json", output_path=str(b))

    assert a.read_bytes() == b.read_bytes(), (
        "K54: 同一输入两次导出的 JSON 不逐字节一致"
    )


def test_k54_report_has_no_external_resources(tmp_path):
    """K54: 报告零外链（断网可读）。"""
    from auditor.pipeline import audit_paper

    md_path = tmp_path / "r.md"
    audit_paper(input_path=str(CLEAN), output_format="markdown",
                output_path=str(md_path))
    md = md_path.read_text(encoding="utf-8")

    for scheme in ("http://", "https://", "//cdn", "src=", "href="):
        assert scheme not in md, f"K54: 报告含外链/外部资源引用: {scheme}"


def test_k54_selftest_is_falsifiable(monkeypatch):
    """K54: selftest 必须真的能失败（不是恒 True 的空壳）。"""
    import tempfile

    from auditor import pipeline

    monkeypatch.setattr(pipeline, "_data_root", lambda: Path(tempfile.mkdtemp()))
    assert pipeline.selftest() is False, (
        "K54 违规: 数据不可达时 selftest 仍返回 True——空壳自检"
    )


def test_k54_selftest_passes_in_repo():
    """K54: 仓库内 selftest 必须通过。"""
    from auditor.pipeline import selftest

    assert selftest() is True
