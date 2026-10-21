"""GUI 编排层——零 Qt，只调引擎函数（K40）。

窗口只做「控件 ↔ 本模块」的接线；所有取数与渲染都在这里，便于无显示器环境测试。
口径（preflight ㉕）：
  ① 主控件接业务：审计按钮 → `audit_paper()`；导出按钮 → `export_report()`
  ② 入口到产物有断言：`auditor.exe --selftest` 与 `tests/test_gui_controller.py` 同链路
  ③ 产物进附件：`auditor.exe` 随 Release 分发
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuditOutcome:
    """一次 GUI 审计的结果（可序列化，便于测试断言）。"""

    paper_id: str = ""
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    exported: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.report is not None and self.error is None


def _tree_to_dict(tree: Any) -> Dict[str, Any]:
    return tree.model_dump() if hasattr(tree, "model_dump") else dict(tree.__dict__)


def audit_paper(input_path: str, with_llm: bool = False) -> AuditOutcome:
    """解析 + 四引擎 + 组装报告。

    与 CLI 的 `pipeline.audit_paper` 走**同一组引擎函数**（不是另写一套判定），
    差别只在输出形态：这里返回结构化 dict 供表格渲染。
    """
    path = Path(input_path)
    if not path.exists():
        return AuditOutcome(error=f"输入不存在：{input_path}")

    try:
        from auditor.core.dimensional import check_dimensions
        from auditor.core.graph import check_dependency_graph
        from auditor.core.numerical import recompute_numerical
        from auditor.core.parser import parse
        from auditor.core.replay import replay
        from auditor.report.renderer import build_report
    except ImportError as exc:  # 缺依赖：显式报出，不静默
        return AuditOutcome(error=f"缺依赖：{exc}")

    try:
        tree = parse(str(path))
        tree_dict = _tree_to_dict(tree)
        claims = (
            list(replay(tree_dict))
            + list(recompute_numerical(tree_dict))
            + list(check_dimensions(tree_dict))
            + list(check_dependency_graph(tree_dict))
        )
    except Exception as exc:
        return AuditOutcome(error=f"审计失败：{exc}")

    coverage = {
        "coverage": getattr(tree, "coverage", 1.0),
        "unrecognized_envs": list(getattr(tree, "unrecognized_envs", [])),
        "unrecognized_macros": list(getattr(tree, "unrecognized_macros", [])),
    }
    meta = {"degraded": False}
    if with_llm:
        try:
            from auditor.llm.bridge import check_llm_available

            available, reason = check_llm_available()
            if not available:
                meta = {"degraded": True,
                        "reason": f"模型端点不可用（{reason}），全部判定按确定性引擎给出"}
        except Exception as exc:
            meta = {"degraded": True, "reason": f"模型桥接不可用：{exc}"}

    report = build_report(getattr(tree, "paper_id", str(path)), claims, coverage, meta)
    return AuditOutcome(paper_id=report.get("paper_id", ""), report=report)


def render_html(report: Dict[str, Any]) -> str:
    """单文件 HTML（0 外链），供 GUI 导出与演示素材生成使用。"""
    import html as _html

    summary = report.get("summary", {})
    coverage = report.get("coverage_report", {})
    claims = report.get("claims", [])
    rows = "\n".join(
        "<tr><td>{}</td><td>{}</td><td class='{}'>{}</td><td>{}</td><td>{}</td></tr>".format(
            _html.escape(str(c.get("claim_id", ""))),
            _html.escape(str(c.get("claim_type", ""))),
            _html.escape(str(c.get("verdict", ""))),
            _html.escape(str(c.get("verdict", ""))),
            _html.escape(str(c.get("error_type") or "—")),
            _html.escape(str(c.get("evidence", ""))),
        )
        for c in claims
    )
    degraded = report.get("meta", {}).get("degraded")
    degrade_block = ""
    if degraded:
        degrade_block = "<p class='warn'><b>降级声明</b>：{}</p>".format(
            _html.escape(str(report.get("meta", {}).get("reason", ""))))
    tool_version = report.get("meta", {}).get("tool_version")
    version_block = (
        "<p class='note'>工具版本：{}</p>".format(_html.escape(str(tool_version)))
        if tool_version else ""
    )
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>论文数学断言审计报告 · {paper_id}</title>
<style>
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:1080px;margin:2rem auto;padding:0 1rem;color:#1f2328}}
h1{{font-size:1.35rem;border-bottom:1px solid #d0d7de;padding-bottom:.4rem}}
table{{border-collapse:collapse;width:100%;margin-top:1rem}}
th,td{{border:1px solid #d0d7de;padding:.35rem .55rem;font-size:.86rem;text-align:left}}
th{{background:#f6f8fa}}
.ok{{color:#1a7f37}}.invalid{{color:#cf222e}}.undecidable{{color:#9a6700}}
.summary div{{display:inline-block;background:#f6f8fa;border-radius:6px;padding:.5rem .9rem;margin-right:1rem}}
.warn{{background:#fff8c5;border:1px solid #d4a72c;padding:.6rem;border-radius:6px}}
.note{{color:#57606a;font-size:.84rem;margin-top:1.5rem}}
</style></head><body>
<h1>论文数学断言审计报告</h1>
<p>{paper_id}</p>
{version}
<div class="summary">
  <div><b>ok</b> {ok}</div><div><b>invalid</b> {invalid}</div>
  <div><b>undecidable</b> {undecidable}</div>
  <div><b>解析覆盖</b> {coverage:.1%}</div>
</div>
{degrade}
<table><thead><tr><th>断言</th><th>类型</th><th>判定</th><th>归属错误类型</th><th>证据</th></tr></thead>
<tbody>
{rows}
</tbody></table>
<p class="note">量纲平衡是必要非充分条件；幽灵 label 仅为结构性提示；
本报告为提示性结论，不构成对论文正确性、作者或期刊的评判。</p>
</body></html>
""".format(
        paper_id=_html.escape(str(report.get("paper_id", ""))),
        version=version_block,
        ok=summary.get("ok", 0),
        invalid=summary.get("invalid", 0),
        undecidable=summary.get("undecidable", 0),
        coverage=float(coverage.get("coverage", 0) or 0),
        degrade=degrade_block,
        rows=rows,
    )


def export_report(outcome: AuditOutcome, output: Path, fmt: str = "markdown") -> Path:
    """导出报告（markdown / json / html），返回实际路径。"""
    if not outcome.report:
        raise ValueError(outcome.error or "无可导出的报告")
    from auditor.report.renderer import render_json, render_markdown

    output = Path(output)
    if fmt in ("markdown", "md"):
        text = render_markdown(outcome.report)
        output = output.with_suffix(".md")
    elif fmt == "json":
        text = render_json(outcome.report)
        output = output.with_suffix(".json")
    elif fmt == "html":
        text = render_html(outcome.report)
        output = output.with_suffix(".html")
    else:
        raise ValueError(f"未知格式：{fmt}")
    output.parent.mkdir(parents=True, exist_ok=True)
    # K55：显式 newline="\n" 防止 Windows 把换行翻成 CRLF。
    # 注意 Path.write_text(newline=) 是 3.10+ 才有；用 open() 对 3.10+ 同样正确，
    # 且不引入版本相关的写法差异。
    with open(output, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    outcome.exported.append(str(output))
    return output


def export_all(outcome: AuditOutcome, stem: Path) -> List[Path]:
    """一次导出三种格式（GUI「导出全部」按钮）。"""
    return [export_report(outcome, Path(stem), fmt) for fmt in ("markdown", "json", "html")]


def load_json_report(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
