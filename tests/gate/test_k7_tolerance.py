"""K7: 数值口径单一定义点守门。

扫描 src/、benchmark/、tests/ 下所有 .py 文件，
断言除 NUMERICAL_TOLERANCE 定义处与引用处外无硬编码容差。
"""

from __future__ import annotations

import ast
from pathlib import Path


def _find_hardcoded_tolerances(file_path: Path) -> list[str]:
    """在单个文件中查找硬编码容差值。"""
    source = file_path.read_text(encoding="utf-8")

    # 跳过 raw string 文件（含 LaTeX 模板，ast.parse 会失败）
    if 'r"""' in source or "r'''" in source:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # 无法解析的文件（如 raw string 模板），跳过
        return []

    hits = []
    for node in ast.walk(tree):
        # 科学计数法：1e-6, 1e-8 等
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            val = node.value
            if 0 < val < 1e-3 and (abs(val) < 1e-3 or (1 / val) > 1e4):
                hits.append(f"{file_path}:{node.lineno}: float {val}")
        # 字符串形式的科学计数法
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            import re
            if re.match(r'^1e-\d+$', node.value.strip()):
                hits.append(f"{file_path}:{node.lineno}: str {node.value}")

    return hits


def test_no_hardcoded_tolerance():
    """K7: 扫描引擎/基准/测试源码，除 NUMERICAL_TOLERANCE 外无硬编码容差。"""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    bench_dir = project_root / "data" / "benchmark"
    tests_dir = project_root / "tests"

    excluded_files = {
        src_dir / "auditor" / "core" / "numerical_tolerance.py",
    }

    all_hits = []
    for dir_path in (src_dir, bench_dir, tests_dir):
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            if py_file in excluded_files:
                continue
            hits = _find_hardcoded_tolerances(py_file)
            all_hits.extend(hits)

    assert len(all_hits) == 0, f"发现硬编码容差:\n" + "\n".join(all_hits)
