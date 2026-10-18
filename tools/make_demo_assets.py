"""K47: 演示素材生成器（v0.1.1 真实现）。

产物（全部写入 `docs/demo/`，供 plan/05 §5.2 的 Release 附件使用）：
  - `demo-clean.html`  —— 干净论文的审计报告（0 外链单文件）
  - `demo-error.html`  —— 含植入错误的论文报告（0 外链单文件）
  - `demo.gif`         —— 窗口三步演示（干净 → 含错 → 导出），offscreen 渲染

用法：
    python tools/make_demo_assets.py            # 生成全部
    python tools/make_demo_assets.py --no-gif   # 只生成 HTML（无 Qt 环境）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

CLEAN = REPO_ROOT / "data" / "benchmark" / "C001-clean" / "paper.tex"
ERROR = REPO_ROOT / "data" / "benchmark" / "B003-001-numeric_mismatch" / "paper.tex"
OUT = REPO_ROOT / "docs" / "demo"


def make_reports() -> dict:
    """生成两份演示 HTML（走 GUI 的同一编排层，保证与窗口产物一致）。"""
    from auditor.gui import pipelines

    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, src in (("demo-clean", CLEAN), ("demo-error", ERROR)):
        outcome = pipelines.audit_paper(str(src))
        if not outcome.ok:
            raise SystemExit(f"审计失败（{name}）：{outcome.error}")
        path = pipelines.export_report(outcome, OUT / name, "html")
        text = Path(path).read_text(encoding="utf-8")
        if "http://" in text or "https://" in text:
            raise SystemExit(f"{path.name} 含外链，违反 0 外链口径")
        results[name] = (path, outcome.report["summary"])
        print(f"✅ {path.name}  {outcome.report['summary']}")
    return results


def make_gif() -> Path:
    """offscreen 渲染窗口三步并合成 GIF。"""
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform.startswith("win") and not os.environ.get("QT_QPA_FONTDIR"):
        os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

    from PySide6.QtWidgets import QApplication

    from auditor.gui.window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1080, 720)
    window.show()

    tmp = OUT / "_frames"
    tmp.mkdir(parents=True, exist_ok=True)
    frames = []

    def shot(name):
        app.processEvents()
        path = tmp / name
        window.grab().save(str(path))
        frames.append(path)

    shot("f1-empty.png")
    window.path_input.setText(str(CLEAN.relative_to(REPO_ROOT)))
    window._on_audit()
    shot("f2-clean.png")
    window.path_input.setText(str(ERROR.relative_to(REPO_ROOT)))
    window._on_audit()
    shot("f3-error.png")
    shot("f4-ready.png")

    from PIL import Image

    images = [Image.open(f).convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]
    gif = OUT / "demo.gif"
    images[0].save(gif, save_all=True, append_images=images[1:],
                   duration=1600, loop=0, optimize=True)
    for f in frames:
        f.unlink(missing_ok=True)
    try:
        tmp.rmdir()
    except OSError:
        pass
    print(f"✅ {gif.name}  {gif.stat().st_size} 字节")
    return gif


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成演示素材（HTML + GIF）")
    ap.add_argument("--no-gif", action="store_true", help="只生成 HTML（无 Qt/Pillow 环境）")
    args = ap.parse_args(argv)

    make_reports()
    if not args.no_gif:
        make_gif()
    return 0


if __name__ == "__main__":
    sys.exit(main())
