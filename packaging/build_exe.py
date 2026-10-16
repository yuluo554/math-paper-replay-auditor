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
    "auditor.gui.pipelines",
]

# GUI 排除项（CLI 不需要的）
GUI_EXCLUDES = []


def _ensure_utf8_stdio() -> None:
    """K49: 所有入口调用，确保 stdout/stderr 为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        if getattr(stream, "encoding", None) != "utf-8":
            stream.reconfigure(encoding="utf-8")


def build_cli_exe(python_path: str = None) -> int:
    """构建 CLI exe。

    Args:
        python_path: Python 解释器路径（默认用 py -3.12）

    Returns:
        退出码
    """
    _ensure_utf8_stdio()

    if python_path is None:
        python_path = "py -3.12"

    # 构建 PyInstaller 命令
    cmd = [
        python_path,
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

    # 添加数据文件
    from packaging.build_datas import build_datas
    datas = build_datas()
    for src, dest in datas:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])

    cmd.append(str(SRC_DIR / "auditor" / "cli.py"))

    print(f"=== 构建 CLI exe ===")
    print(f"命令: {' '.join(cmd)}")

    import subprocess
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def build_gui_exe(python_path: str = None) -> int:
    """构建 GUI exe。

    Args:
        python_path: Python 解释器路径（默认用 py -3.12）

    Returns:
        退出码
    """
    _ensure_utf8_stdio()

    if python_path is None:
        python_path = "py -3.12"

    # 构建 PyInstaller 命令
    cmd = [
        python_path,
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

    # 添加数据文件
    from packaging.build_datas import build_datas
    datas = build_datas()
    for src, dest in datas:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])

    cmd.append(str(SRC_DIR / "auditor" / "gui" / "main_window.py"))

    print(f"=== 构建 GUI exe ===")
    print(f"命令: {' '.join(cmd)}")

    import subprocess
    result = subprocess.run(cmd, cwd=REPO_ROOT)
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
