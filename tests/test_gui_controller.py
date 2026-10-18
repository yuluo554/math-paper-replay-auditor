"""桌面形态验收（preflight ㉕）：控制器行为 + 窗口接线 + 打包入口。

v0.1.0 的 `auditor.exe` 是占位空窗口（`QMainWindow()` + 标题），`gui/pipelines.py`
写得完整但**全仓无调用方**——测试全绿，因为没有任何测试触碰 GUI。
本文件把三条证据钉死：控制器真出报告、按钮真 connect、入口真在包里。
"""

import ast
import json
from pathlib import Path

import pytest

from auditor.gui import pipelines

REPO_ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = REPO_ROOT / "src" / "auditor" / "gui"
SAMPLE = REPO_ROOT / "data" / "benchmark" / "C001-clean" / "paper.tex"
ERROR_SAMPLE = REPO_ROOT / "data" / "benchmark" / "B003-001-numeric_mismatch" / "paper.tex"


class TestController:
    def test_clean_paper_has_no_invalid(self):
        outcome = pipelines.audit_paper(str(SAMPLE))
        assert outcome.ok, outcome.error
        assert outcome.report["summary"]["invalid"] == 0, "干净论文零误报（K4）"
        assert outcome.report["summary"]["ok"] > 0, "必须真的产出断言（不是空报告）"

    def test_error_paper_detects_invalid(self):
        outcome = pipelines.audit_paper(str(ERROR_SAMPLE))
        assert outcome.ok, outcome.error
        assert outcome.report["summary"]["invalid"] >= 1, "植入错误的论文必须被检出"
        verdicts = {c["verdict"] for c in outcome.report["claims"]}
        assert verdicts <= {"ok", "invalid", "undecidable"}, "三级语义之外不得出现新状态"

    def test_missing_input_reports_error_without_crash(self):
        outcome = pipelines.audit_paper(str(REPO_ROOT / "no" / "such.tex"))
        assert not outcome.ok and "不存在" in outcome.error

    def test_export_three_formats(self, tmp_path):
        outcome = pipelines.audit_paper(str(SAMPLE))
        written = pipelines.export_all(outcome, tmp_path / "rep")
        assert sorted(p.suffix for p in written) == [".html", ".json", ".md"]
        assert all(p.is_file() and p.stat().st_size > 0 for p in written)

    def test_html_export_has_no_external_links(self, tmp_path):
        outcome = pipelines.audit_paper(str(SAMPLE))
        html_path = pipelines.export_report(outcome, tmp_path / "r", "html")
        text = html_path.read_text(encoding="utf-8")
        assert "http://" not in text and "https://" not in text

    def test_json_export_roundtrip(self, tmp_path):
        outcome = pipelines.audit_paper(str(SAMPLE))
        path = pipelines.export_report(outcome, tmp_path / "r", "json")
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["summary"] == outcome.report["summary"]
        assert data["claims"] == outcome.report["claims"]

    def test_export_without_report_raises(self, tmp_path):
        with pytest.raises(ValueError):
            pipelines.export_report(pipelines.AuditOutcome(error="x"), tmp_path / "x")


class TestWindowWiring:
    """静态接线：控件没 connect 就是死壳"""

    def _source(self):
        return (GUI_DIR / "window.py").read_text(encoding="utf-8")

    def test_buttons_are_connected(self):
        src = self._source()
        tree = ast.parse(src)
        lines = src.splitlines()
        targets = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "connect"):
                continue
            seg = ast.get_source_segment(src, func.value)
            if seg is None:
                seg = lines[func.value.lineno - 1][
                    func.value.col_offset:func.value.end_col_offset]
            targets.append(seg.replace(" ", ""))
        for expect in ("audit_button.clicked", "export_button.clicked", "browse.clicked"):
            assert any(expect in t for t in targets), \
                f"{expect} 未 connect（空壳）；实际: {targets}"

    def test_window_calls_pipelines(self):
        src = self._source()
        assert "pipelines.audit_paper(" in src, "审计按钮未接业务层"
        assert "pipelines.export_all(" in src, "导出按钮未接业务层"

    def test_main_entry_uses_real_window(self):
        src = (GUI_DIR / "main_window.py").read_text(encoding="utf-8")
        assert "from auditor.gui.window import MainWindow" in src, \
            "入口仍在用占位 QMainWindow"
        assert "占位" not in src, "入口不应再有'占位'注释"

    def test_selftest_is_qt_free(self):
        src = (GUI_DIR / "main_window.py").read_text(encoding="utf-8")
        head, _, _ = src.partition("def run_gui")
        assert "import PySide6" not in head, "--selftest 路径不得在模块顶层导入 Qt"


class TestPackaging:
    def test_gui_entry_in_hiddenimports(self):
        src = (REPO_ROOT / "build_tools" / "build_exe.py").read_text(encoding="utf-8")
        assert "auditor.gui.main_window" in src
        assert "auditor.gui.pipelines" in src
        assert "auditor.gui.window" in src, "新的窗口模块必须进打包 hiddenimports"

    def test_demo_gif_present(self):
        gif = REPO_ROOT / "docs" / "demo" / "demo.gif"
        assert gif.is_file() and gif.stat().st_size > 1000, "§三 承诺的演示 GIF 必须存在"
