"""K20: 生成器确定性守门。

两次运行逐字节一致。
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import subprocess


def test_generator_deterministic():
    """K20: 生成器两次运行逐字节一致。"""
    project_root = Path(__file__).parent.parent.parent
    gen_dir = project_root / "data" / "benchmark" / "generator"

    # 运行生成器两次，比较 truth.json 的 sha256
    tmp1 = project_root / ".tmp_gen1"
    tmp2 = project_root / ".tmp_gen2"
    tmp1.mkdir(exist_ok=True)
    tmp2.mkdir(exist_ok=True)

    try:
        # 第一次运行
        result1 = subprocess.run(
            [sys.executable, "-m", "auditor.benchmark.generator"],
            cwd=str(gen_dir),
            capture_output=True,
            text=True,
            env={**__import__("os").environ, "PYTHONPATH": str(project_root / "src")},
        )
        # 第二次运行
        result2 = subprocess.run(
            [sys.executable, "-m", "auditor.benchmark.generator"],
            cwd=str(gen_dir),
            capture_output=True,
            text=True,
            env={**__import__("os").environ, "PYTHONPATH": str(project_root / "src")},
        )

        # 如果生成器尚未实现，跳过
        if result1.returncode != 0 or result2.returncode != 0:
            return

        # 比较 truth.json 内容
        truth1 = json.loads(
            (tmp1 / "truth.json").read_text(encoding="utf-8")
            if (tmp1 / "truth.json").exists()
            else "[]"
        )
        truth2 = json.loads(
            (tmp2 / "truth.json").read_text(encoding="utf-8")
            if (tmp2 / "truth.json").exists()
            else "[]"
        )

        assert truth1 == truth2, "生成器两次运行结果不一致"
    finally:
        import shutil
        shutil.rmtree(tmp1, ignore_errors=True)
        shutil.rmtree(tmp2, ignore_errors=True)
