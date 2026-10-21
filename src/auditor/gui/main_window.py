"""GUI 主窗口入口（K41/K42）。

K41: 窗口版对未知参数 exit 2（不静默忽略）
K42: exe --selftest 内建参数

形态口径（preflight ㉕）：窗口不是"能开"就算交付——
  ① 主控件接业务：「开始审计」→ `pipelines.audit_paper()`；「导出报告」→ `pipelines.export_all()`
  ② 入口到产物有断言：`--selftest` 跑通「解析→四引擎→报告→导出」全链路
  ③ 产物进附件：`auditor.exe`（Release 附件）
无 PySide6 时窗口模式 exit 3；`--selftest` 走零 Qt 路径仍可跑。
"""

from __future__ import annotations

import sys
from pathlib import Path

from auditor._encoding import ensure_utf8_stdio


def _data_root() -> Path:
    """数据根（冻结态取解包根，源码态取仓库根，装态取 site-packages 根）。

    D2：新增装态分支（pip 非 editable 安装后数据可达）。
    冻结态的 `sys._MEIPASS` 分支**语义不变**（K52 依赖它）。
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    from auditor._datapaths import installed_data_root

    installed = installed_data_root()
    if installed is not None:
        return installed

    # src/auditor/gui/main_window.py → parents[3] = 仓库根
    return Path(__file__).resolve().parents[3]


def _sample_paper() -> Path:
    return _data_root() / "data" / "benchmark" / "C001-clean" / "paper.tex"


def run_gui(args: list = None) -> int:
    """GUI 入口。

    Args:
        args: 命令行参数（默认 sys.argv[1:]）

    Returns:
        退出码：0=成功, 2=未知参数, 3=缺依赖
    """
    ensure_utf8_stdio()

    if args is None:
        args = sys.argv[1:]

    # K41: 检查未知参数
    known_args = {"--selftest", "--help", "-h"}
    for arg in args:
        if arg.startswith("-") and arg not in known_args:
            print(f"未知参数: {arg}", file=sys.stderr)
            print("用法: auditor.exe [--selftest | --help]", file=sys.stderr)
            return 2

    # K42: --selftest 内建参数
    if "--selftest" in args:
        return _run_selftest()

    # 帮助
    if "--help" in args or "-h" in args:
        print("数学论文可验证重放审计器 - GUI 模式")
        print("用法: auditor.exe [--selftest | --help]")
        return 0

    # 尝试导入 PySide6
    try:
        from PySide6 import QtWidgets
    except ImportError:
        print("缺少 PySide6 依赖，请安装: pip install PySide6", file=sys.stderr)
        return 3

    from auditor.gui.window import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


def _run_selftest() -> int:
    """K42: 自检 = 内嵌数据定位 + 四引擎全链路 + 报告组装 + 三格式导出。

    与窗口走**同一个** `pipelines` 模块（不是另写一套检查），
    因此这条自检绿 == 窗口里点「开始审计 / 导出报告」能跑通。
    """
    ensure_utf8_stdio()
    print("=== 自检（GUI 链路，零 Qt）===")

    from auditor.gui import pipelines

    paper = _sample_paper()
    if not paper.exists():
        print(f"❌ 样本论文不存在: {paper}")
        return 1
    print(f"✅ 样本论文: {paper}")

    outcome = pipelines.audit_paper(str(paper))
    if not outcome.ok:
        print(f"❌ 审计失败: {outcome.error}")
        return 1
    summary = outcome.report["summary"]
    print(f"✅ 审计完成: ok={summary.get('ok', 0)} "
          f"invalid={summary.get('invalid', 0)} undecidable={summary.get('undecidable', 0)}")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        try:
            written = pipelines.export_all(outcome, Path(tmp) / "selftest")
        except Exception as exc:
            print(f"❌ 导出失败: {exc}")
            return 1
        for path in written:
            text = Path(path).read_text(encoding="utf-8")
            if path.suffix == ".html" and ("http://" in text or "https://" in text):
                print(f"❌ {path.name} 含外链（要求 0 外链）")
                return 1
        print(f"✅ 导出三格式: {', '.join(Path(p).name for p in written)}")

    print("=== 自检通过 ===")
    return 0


if __name__ == "__main__":
    sys.exit(run_gui())
