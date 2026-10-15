"""K42: 冻结态自检工具。

在临时中立目录调 exe --selftest，断言数据目录落在 dist 内。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def verify_package(exe_path: str, gui_selftest: bool = False) -> bool:
    """验证打包产物。"""
    exe = Path(exe_path)
    if not exe.exists():
        print(f"exe 不存在: {exe}")
        return False

    # 在临时目录运行
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        in_file = Path(tmpdir) / "selftest_in.json"
        out_file = Path(tmpdir) / "selftest_out.txt"
        in_file.write_text("{}", encoding="utf-8")

        result = subprocess.run(
            [str(exe), "--selftest", str(in_file), str(out_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"自检失败: {result.stderr}")
            return False

        # 断言数据目录落在 exe 目录内
        output = out_file.read_text(encoding="utf-8")
        data_dir = output.strip()
        exe_dir = exe.parent

        if not data_dir.startswith(str(exe_dir)):
            print(f"数据目录 {data_dir} 不在 exe 目录 {exe_dir} 内")
            return False

        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_package.py <exe_path>")
        sys.exit(1)
    ok = verify_package(sys.argv[1])
    sys.exit(0 if ok else 1)
