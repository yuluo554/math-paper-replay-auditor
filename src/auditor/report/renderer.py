"""报告渲染——人读 + 机读双轨，零外链、零判定。

K26（渲染层零判定）：本模块**只消费**已有 ClaimResult，不重算任何判定，
不读取规则/阈值，保证"报告与引擎结论同源"。

机读产物逐字节可复现：自写最小 writer（json.dumps 固定 ensure_ascii/sort_keys/
separators），不引第三方序列化器。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

# 判定词汇（K15 三态，与 core.types.Verdict 同源词面）
_VERDICT_LABEL = {
    "ok": "通过",
    "invalid": "确证问题",
    "undecidable": "无法判定",
}

_ERROR_TYPE_LABEL = {
    "dimension_mismatch": "量纲不一致",
    "illegal_derivation": "推导链非法步",
    "numeric_mismatch": "数值断言算错",
    "dangling_ref": "label/ref 悬空",
    "dep_chain_break": "定理依赖断链",
    "ghost_label": "幽灵 label（结构性可疑，非确证问题）",
}


def render_markdown(result: Dict[str, Any]) -> str:
    """渲染人读报告（Markdown）。"""
    lines: List[str] = []
    lines.append(f"# 审计报告：{result.get('paper_id', 'unknown')}")
    lines.append("")

    summary = result.get("summary", {})
    lines.append("## 判定汇总")
    lines.append("")
    lines.append("| 判定 | 条数 |")
    lines.append("|---|---|")
    for verdict in ("ok", "invalid", "undecidable"):
        lines.append(f"| {_VERDICT_LABEL[verdict]} | {summary.get(verdict, 0)} |")
    lines.append("")

    coverage = result.get("coverage_report", {})
    lines.append("## 解析覆盖率")
    lines.append("")
    lines.append(f"- 解析覆盖率：{coverage.get('coverage', 1.0)}")
    unrecognized_envs = coverage.get("unrecognized_envs", [])
    unrecognized_macros = coverage.get("unrecognized_macros", [])
    lines.append(f"- 未识别环境：{unrecognized_envs if unrecognized_envs else '无'}")
    lines.append(f"- 未识别宏：{unrecognized_macros if unrecognized_macros else '无'}")
    lines.append("")
    if unrecognized_envs or unrecognized_macros:
        lines.append("> 未识别项已如实登记并计入覆盖率分母，**不静默丢弃**（K2）。")
        lines.append("")

    claims = result.get("claims", [])
    if claims:
        lines.append("## 断言明细")
        lines.append("")
        lines.append("| 断言 | 类型 | 判定 | 归属 | 证据 |")
        lines.append("|---|---|---|---|---|")
        for c in claims:
            err = c.get("error_type")
            err_label = _ERROR_TYPE_LABEL.get(err, err) if err else "—"
            evidence = str(c.get("evidence", "")).replace("|", "\\|")
            lines.append(
                f"| {c.get('claim_id', '')} | {c.get('claim_type', '')} | "
                f"{_VERDICT_LABEL.get(c.get('verdict'), c.get('verdict'))} | "
                f"{err_label} | {evidence} |"
            )
        lines.append("")

    meta = result.get("meta", {})
    if meta.get("degraded"):
        lines.append("## 降级声明")
        lines.append("")
        lines.append(f"- {meta.get('reason', '引擎不可用，全部判定降级为无法判定')}")
        lines.append("")

    lines.append("## 边界声明")
    lines.append("")
    lines.append("- 量纲平衡是**必要非充分**条件：量纲平衡不等于公式正确（K11）。")
    lines.append("- 幽灵 label 仅为结构性提示，不是确证错误（K14）。")
    lines.append("- 本报告为提示性结论，不构成对论文正确性、作者或期刊的评判。")
    lines.append("")
    return "\n".join(lines)


def render_json(result: Dict[str, Any]) -> str:
    """渲染机读报告（JSON，逐字节可复现）。"""
    return json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        separators=(",", ": "),
    )


def build_report(
    paper_id: str,
    claims: List[Any],
    coverage: Dict[str, Any],
    meta: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """把引擎产物组装成报告结构（零判定，只做计数与字段搬运）。"""
    dict_claims: List[Dict[str, Any]] = []
    summary = {"ok": 0, "invalid": 0, "undecidable": 0}

    for c in claims:
        if hasattr(c, "verdict"):
            verdict = c.verdict.value if hasattr(c.verdict, "value") else str(c.verdict)
            entry = {
                "claim_id": c.claim_id,
                "claim_type": c.claim_type,
                "verdict": verdict,
                "evidence": c.evidence,
                "error_type": getattr(c, "error_type", None),
            }
        else:
            verdict = c.get("verdict", "undecidable")
            entry = {
                "claim_id": c.get("claim_id", ""),
                "claim_type": c.get("claim_type", ""),
                "verdict": verdict,
                "evidence": c.get("evidence", ""),
                "error_type": c.get("error_type"),
            }
        summary[verdict] = summary.get(verdict, 0) + 1
        dict_claims.append(entry)

    return {
        "paper_id": paper_id,
        "claims": dict_claims,
        "summary": summary,
        "coverage_report": coverage,
        "meta": meta or {},
    }
