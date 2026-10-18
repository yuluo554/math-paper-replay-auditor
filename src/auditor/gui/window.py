"""主窗口（PySide6）：论文审计 → 断言表 → 导出报告。

窗口只做控件的创建与接线，取数/渲染全部在 `auditor.gui.pipelines`（零 Qt）。
这样 `--selftest` 与 `tests/test_gui_controller.py` 能在无显示器环境验证同一条链路。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget,
)

from auditor.gui import pipelines

VERDICT_COLOR = {"ok": "#1a7f37", "invalid": "#cf222e", "undecidable": "#9a6700"}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数学论文可验证重放审计器")
        self.resize(1080, 720)
        self._outcome = None
        self._build_ui()

    # ---------------------------------------------------------------- UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)

        # 输入行
        row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择论文 .tex 文件或目录")
        row.addWidget(self.path_input, 1)
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._on_browse)
        row.addWidget(browse)
        self.audit_button = QPushButton("开始审计")
        self.audit_button.clicked.connect(self._on_audit)
        row.addWidget(self.audit_button)
        outer.addLayout(row)

        # 导出行
        row2 = QHBoxLayout()
        self.status_label = QLabel("就绪")
        row2.addWidget(self.status_label, 1)
        self.export_button = QPushButton("导出报告（MD + JSON + HTML）")
        self.export_button.clicked.connect(self._on_export)
        self.export_button.setEnabled(False)
        row2.addWidget(self.export_button)
        outer.addLayout(row2)

        # 结果区：左表右报告
        splitter = QSplitter(Qt.Horizontal)
        self.claim_table = QTableWidget(0, 4)
        self.claim_table.setHorizontalHeaderLabels(["断言", "类型", "判定", "证据"])
        splitter.addWidget(self.claim_table)
        self.report_view = QTextBrowser()
        self.report_view.setOpenExternalLinks(False)
        splitter.addWidget(self.report_view)
        splitter.setSizes([620, 460])
        outer.addWidget(splitter, 1)

    # ------------------------------------------------------------- 事件

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择论文 LaTeX 源文件", "", "LaTeX (*.tex);;所有文件 (*.*)")
        if path:
            self.path_input.setText(path)

    def _on_audit(self):
        target = self.path_input.text().strip()
        if not target:
            self.status_label.setText("⚠ 请先选择论文文件")
            return
        self.status_label.setText("审计中…")
        QApplication.processEvents()
        outcome = pipelines.audit_paper(target)
        self._outcome = outcome
        if not outcome.ok:
            self.status_label.setText(f"⚠ {outcome.error}")
            self.export_button.setEnabled(False)
            return
        self._fill_table(outcome.report)
        self._fill_preview(outcome.report)
        summary = outcome.report["summary"]
        self.status_label.setText(
            f"审计完成：ok {summary.get('ok', 0)} / invalid {summary.get('invalid', 0)} / "
            f"undecidable {summary.get('undecidable', 0)}")
        self.export_button.setEnabled(True)

    def _on_export(self):
        if not self._outcome or not self._outcome.ok:
            self.status_label.setText("⚠ 请先执行审计")
            return
        stem, _ = QFileDialog.getSaveFileName(
            self, "导出报告（基础文件名，将生成 .md/.json/.html）",
            "paper-audit-report", "报告 (*.md *.json *.html)")
        if not stem:
            return
        try:
            written = pipelines.export_all(self._outcome, Path(stem))
        except Exception as exc:  # 写盘失败要报出来，不静默
            QMessageBox.critical(self, "错误", f"导出失败: {exc}")
            return
        self.status_label.setText("已导出：" + ", ".join(Path(p).name for p in written))

    # ------------------------------------------------------------- 渲染

    def _fill_table(self, report):
        claims = report.get("claims", [])
        self.claim_table.setRowCount(0)
        for row, claim in enumerate(claims):
            self.claim_table.insertRow(row)
            values = [
                str(claim.get("claim_id", "")),
                str(claim.get("claim_type", "")),
                str(claim.get("verdict", "")),
                str(claim.get("evidence", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 2:
                    item.setForeground(
                        Qt.GlobalColor.darkGreen if value == "ok"
                        else Qt.GlobalColor.darkRed if value == "invalid"
                        else Qt.GlobalColor.darkYellow)
                self.claim_table.setItem(row, col, item)

    def _fill_preview(self, report):
        from auditor.report.renderer import render_markdown

        self.report_view.setPlainText(render_markdown(report))
