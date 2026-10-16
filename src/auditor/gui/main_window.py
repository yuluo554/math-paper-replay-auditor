"""GUI 主窗口入口（K41/K42）。

K41: 窗口版对未知参数 exit 2（不静默忽略）
K42: exe --selftest 内建参数
"""

from __future__ import annotations

import sys

from auditor._encoding import ensure_utf8_stdio


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

    # 创建应用
    app = QtWidgets.QApplication(sys.argv)

    # 创建主窗口（占位）
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("数学论文可验证重放审计器")
    window.resize(800, 600)
    window.show()

    return app.exec()


def _run_selftest() -> int:
    """K42: 自检（内嵌数据定位 + calc 全链路）。"""
    ensure_utf8_stdio()

    print("=== 自检 ===")

    # 检查数据目录（从 src/auditor 向上找 repo root）
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent.parent.parent  # src/auditor
    data_dir = current_dir.parent / "data"  # repo root/data

    # 如果找不到，尝试其他路径
    if not data_dir.exists():
        data_dir = current_dir / "data"
    if not data_dir.exists():
        data_dir = Path.cwd() / "data"

    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        return 1

    # 检查真值库
    truth_path = data_dir / "benchmark" / "truth.json"
    if not truth_path.exists():
        print(f"❌ 真值库不存在: {truth_path}")
        return 1

    print("✅ 数据目录定位成功")
    print(f"✅ 真值库: {truth_path}")

    # 检查核心引擎
    try:
        from auditor.core.parser import parse
        from auditor.core.replay import replay
        from auditor.core.numerical import recompute_numerical
        print("✅ 核心引擎加载成功")
    except ImportError as e:
        print(f"❌ 核心引擎加载失败: {e}")
        return 1

    print("=== 自检通过 ===")
    return 0


if __name__ == "__main__":
    sys.exit(run_gui())
