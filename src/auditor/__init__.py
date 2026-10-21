"""auditor — 数学论文可验证重放审计器。

版本口径（D5）：**单一事实源 = 打包元数据**（`pyproject.toml` 的 version）。
装态用 `importlib.metadata.version()` 读；源码态（未安装 / editable 装的是
旧版本）退回本文件里的 `__version__`，它必须与 `pyproject.toml` 一致——
`tests/gate/test_k33_extras.py` 会断言两者相等。
"""

import sys

try:  # pragma: no cover - 装态与源码态走不同分支
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    try:
        __version__ = _pkg_version("math-paper-replay-auditor")
    except PackageNotFoundError:
        __version__ = "0.1.2"
except ImportError:  # pragma: no cover - 3.7 及更早
    __version__ = "0.1.2"


def _ensure_utf8_stdio() -> None:
    """K49: 所有入口调用，确保 stdout/stderr 为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding != "utf-8":
            stream.reconfigure(encoding="utf-8")


_ensure_utf8_stdio()
