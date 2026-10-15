"""K49: 编码守卫——所有可执行入口必须调用。"""

import sys


def ensure_utf8_stdio() -> None:
    """确保 stdout/stderr 为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        if getattr(stream, "encoding", None) != "utf-8":
            stream.reconfigure(encoding="utf-8")


def _ensure_utf8_stdio() -> None:
    """别名，兼容旧调用。"""
    ensure_utf8_stdio()
