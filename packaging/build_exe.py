"""打包入口。"""

from __future__ import annotations

import sys
from pathlib import Path


def build_exe(target: str = "cli") -> None:
    """构建 exe。target: cli 或 gui。"""
    # TODO M5: 实现 PyInstaller 调用
    print(f"Building {target} exe...")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "cli"
    build_exe(target)
