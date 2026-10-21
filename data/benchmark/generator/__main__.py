"""`python -m data.benchmark.generator` 入口。

K20 只读位级一致校验：python -m data.benchmark.generator --check
"""

from __future__ import annotations

import sys

from . import _cli

if __name__ == "__main__":
    sys.exit(_cli())
