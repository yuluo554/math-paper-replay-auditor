"""PyInstaller 双 exe 构建器（K39/K40/K41/K42）。

职责：
1. CLI 目标：排除 Qt 栈，体积 < 20MB
2. GUI 目标：包含 PySide6，窗口模式
3. 冻结入口用薄模块（绝对导入）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple

# 仓库根目录
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = REPO_ROOT / "build"

# 允许以 `python build_tools/build_exe.py` 直接运行（脚本态下仓库根不在 sys.path）
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build_tools.build_datas import build_datas  # noqa: E402

# CLI 隐藏导入（核心引擎）
CLI_HIDDENIMPORTS = [
    "auditor.core.parser",
    "auditor.core.replay",
    "auditor.core.numerical",
    "auditor.core.dimensional",
    "auditor.core.graph",
    "auditor.core.types",
    "auditor.core.numerical_tolerance",
    "auditor.benchmark.runner",
    "auditor.benchmark.metrics",
    "auditor.pipeline",
    # sympy.parsing.latex 需要 antlr4 运行时；缺失时 parse_latex 会静默返回 None，
    # 使重放链退化为全 invalid（冻结态与源码态行为分叉），故必须显式收进包。
    # 注意：_parse_latex_antlr 是**动态 import**（import_module），
    # PyInstaller 静态分析看不到，必须逐个点名，否则冻结态静默降级。
    "antlr4",
    "sympy.parsing.latex",
    "sympy.parsing.latex._parse_latex_antlr",
    "sympy.parsing.latex._antlr",
    "sympy.parsing.latex._antlr.latexlexer",
    "sympy.parsing.latex._antlr.latexparser",
]

# CLI 排除项（Qt 栈）
CLI_EXCLUDES = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtQuick",
    "PySide6.QtQml",
    "shiboken6",
    "matplotlib",
    "PIL",
    "Pillow",
]

# GUI 隐藏导入
GUI_HIDDENIMPORTS = [
    "auditor.core.parser",
    "auditor.core.replay",
    "auditor.core.numerical",
    "auditor.core.dimensional",
    "auditor.core.graph",
    "auditor.core.types",
    "auditor.core.numerical_tolerance",
    "auditor.pipeline",
    "auditor.gui.main_window",
    "auditor.gui.window",
    "auditor.gui.pipelines",
    # 同 CLI：antlr4 是 parse_latex 的运行时前提，缺则冻结态静默降级。
    "antlr4",
    "sympy.parsing.latex",
    "sympy.parsing.latex._parse_latex_antlr",
    "sympy.parsing.latex._antlr",
    "sympy.parsing.latex._antlr.latexlexer",
    "sympy.parsing.latex._antlr.latexparser",
]

# GUI 排除项：只用到 QtCore/QtGui/QtWidgets。PySide6 的 hook 会把 Quick/Qml/Pdf/
# OpenGL 等 DLL 一并收进来（onefile 从 ~45MB 涨到 ~112MB），对纯窗口应用无用。
# 2026-10-18：v0.1.0 的 GUI exe 72MB，本轮补导出后一度涨到 112MB，排除后回落。
GUI_EXCLUDES = [
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtMultimedia",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtDesigner",
    "PySide6.QtUiTools",
    "PySide6.QtNetwork",
    "PySide6.QtSvg",
    "PySide6.QtPrintSupport",
]


def _ensure_utf8_stdio() -> None:
    """K49: 所有入口调用，确保 stdout/stderr 为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        if getattr(stream, "encoding", None) != "utf-8":
            stream.reconfigure(encoding="utf-8")


def _python_cmd() -> List[str]:
    """返回本机可用的 Python 解释器命令（argv 形式）。

    优先用**当前解释器**（sys.executable）——它才是装了 PyInstaller / PySide6
    的那个环境；只有当当前解释器里没有 PyInstaller 时，才回落到 py 启动器。

    此前固定用 `py -3.12`（系统解释器），于是"在装了 build extra 的 venv 里
    跑 build_exe"会去找一个**没有 PyInstaller** 的解释器 → 构建失败或产出用旧环境打的包。
    """
    import importlib.util
    import shutil

    if importlib.util.find_spec("PyInstaller") is not None:
        return [sys.executable]
    if shutil.which("py"):
        return ["py", "-3.12"]
    return [sys.executable]


def _datas_args() -> List[str]:
    """由白名单单一事实源生成 PyInstaller --add-data 参数。"""
    args: List[str] = []
    for src, dest in build_datas():
        args.extend(["--add-data", f"{src}{os.pathsep}{dest}"])
    return args


def build_cli_exe(python_path: str = None) -> int:
    """构建 CLI exe。

    Args:
        python_path: 已废弃（保留形参兼容旧调用）；解释器由 _python_cmd() 决定

    Returns:
        退出码
    """
    _ensure_utf8_stdio()

    cmd = _python_cmd() + [
        "-m", "PyInstaller",
        "--name", "auditor-cli",
        "--console",
        "--onefile",
        "--paths", str(SRC_DIR),
        "--hiddenimport", "auditor.cli",
    ]

    # 添加隐藏导入
    for hi in CLI_HIDDENIMPORTS:
        cmd.extend(["--hiddenimport", hi])

    # 添加排除项
    for ex in CLI_EXCLUDES:
        cmd.extend(["--exclude-module", ex])

    # 添加数据文件（白名单单一事实源）
    cmd.extend(_datas_args())

    cmd.append(str(SRC_DIR / "auditor" / "cli.py"))

    print("=== 构建 CLI exe ===")
    print(f"命令: {' '.join(cmd)}")

    import subprocess
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return result.returncode


def build_gui_exe(python_path: str = None) -> int:
    """构建 GUI exe。

    Args:
        python_path: 已废弃（保留形参兼容旧调用）；解释器由 _python_cmd() 决定

    Returns:
        退出码
    """
    _ensure_utf8_stdio()

    cmd = _python_cmd() + [
        "-m", "PyInstaller",
        "--name", "auditor",
        "--windowed",
        "--onefile",
        "--paths", str(SRC_DIR),
        "--hiddenimport", "auditor.cli",
    ]

    # 添加隐藏导入
    for hi in GUI_HIDDENIMPORTS:
        cmd.extend(["--hiddenimport", hi])

    # 添加排除项
    for ex in GUI_EXCLUDES:
        cmd.extend(["--exclude-module", ex])

    # 添加数据文件（白名单单一事实源）
    cmd.extend(_datas_args())

    cmd.append(str(SRC_DIR / "auditor" / "gui" / "main_window.py"))

    print("=== 构建 GUI exe ===")
    print(f"命令: {' '.join(cmd)}")

    import subprocess
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return result.returncode


def verify_frozen_entry() -> Tuple[bool, List[str]]:
    """K40: 冻结入口用薄模块（绝对导入）。

    Returns:
        (是否通过, 问题列表)
    """
    _ensure_utf8_stdio()
    issues: List[str] = []

    # 检查 cli.py 是否使用相对导入
    cli_path = SRC_DIR / "auditor" / "cli.py"
    if cli_path.exists():
        content = cli_path.read_text(encoding="utf-8")
        if "from ." in content or "import ." in content:
            issues.append("cli.py 使用了相对导入")

    # 检查入口是否有 __main__
    if "if __name__" not in content:
        issues.append("cli.py 缺少 __main__ 入口")

    return len(issues) == 0, issues


def verify_unknown_args() -> Tuple[bool, List[str]]:
    """K41: 窗口版对未知参数 exit 2。

    Returns:
        (是否通过, 问题列表)
    """
    _ensure_utf8_stdio()
    issues: List[str] = []

    # 检查 GUI 入口是否处理未知参数
    gui_path = SRC_DIR / "auditor" / "gui" / "main_window.py"
    if gui_path.exists():
        content = gui_path.read_text(encoding="utf-8")
        # 检查是否有参数解析逻辑
        if "argparse" not in content and "sys.argv" not in content:
            issues.append("GUI 入口未处理命令行参数")

    return len(issues) == 0, issues


def main() -> int:
    """主入口。"""
    _ensure_utf8_stdio()

    target = sys.argv[1] if len(sys.argv) > 1 else "cli"

    if target == "cli":
        return build_cli_exe()
    elif target == "gui":
        return build_gui_exe()
    elif target == "verify":
        # 验证冻结入口
        passed, issues = verify_frozen_entry()
        if passed:
            print("✅ 冻结入口验证通过")
            return 0
        else:
            print("❌ 冻结入口验证失败:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
    else:
        print(f"未知目标: {target}")
        print("用法: python build_exe.py [cli|gui|verify]")
        return 2


if __name__ == "__main__":
    sys.exit(main())
