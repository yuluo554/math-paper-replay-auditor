"""支持 `python -m auditor <command>` 形式。

README 快速开始用 `python -m auditor selftest` 这一形态；缺此模块时
Python 会报 "No module named auditor.__main__"，README 的每条命令都跑不通。
"""

from __future__ import annotations

import sys

from auditor.cli import main

if __name__ == "__main__":
    sys.exit(main())
