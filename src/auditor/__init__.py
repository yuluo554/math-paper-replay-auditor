"""auditor — 数学论文可验证重放审计器。"""

__version__ = "0.1.0"

import sys


def _ensure_utf8_stdio() -> None:
    """K49: 所有入口调用，确保 stdout/stderr 为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding != "utf-8":
            stream.reconfigure(encoding="utf-8")


_ensure_utf8_stdio()
