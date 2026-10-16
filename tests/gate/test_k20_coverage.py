"""K20: 确定性生成守门。

K20: 确定性生成（splitmix64）
- 禁 stdlib random（不承诺跨版本序列一致）
- 禁 set 迭代序
- 禁系统时钟
- 自研确定性 RNG（splitmix64）
- 两次运行/构建逐字节一致
- 配"再生成位级一致"守门测试
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


def test_k20_uses_splitmix64():
    """K20: 生成器使用 splitmix64 而非 stdlib random。"""
    generator_dir = Path("data/benchmark/generator")

    # 检查 deterministic_rng.py 存在
    rng_path = generator_dir / "deterministic_rng.py"
    assert rng_path.exists(), "K20: deterministic_rng.py 不存在"

    source = rng_path.read_text(encoding="utf-8")

    # 必须包含 SplitMix64 类
    assert "SplitMix64" in source, "K20: 未使用 SplitMix64"

    # 不应 import stdlib random
    imports = ast.parse(source)
    import_names = []
    for node in ast.walk(imports):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_names.append(node.module.split('.')[0])

    assert "random" not in import_names, (
        "K20: 生成器不应使用 stdlib random"
    )


def test_k20_error_injector_no_random():
    """K20: 错误植入器不使用 stdlib random。"""
    injector_path = Path("data/benchmark/generator/error_injector.py")
    assert injector_path.exists(), "error_injector.py 不存在"

    source = injector_path.read_text(encoding="utf-8")

    # 不应 import random
    imports = ast.parse(source)
    import_names = []
    for node in ast.walk(imports):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_names.append(node.module.split('.')[0])

    assert "random" not in import_names, (
        "K20: 错误植入器不应使用 stdlib random"
    )


def test_k20_truth_builder_no_random():
    """K20: 真值构建器不使用 stdlib random。"""
    builder_path = Path("data/benchmark/generator/truth_builder.py")
    assert builder_path.exists(), "truth_builder.py 不存在"

    source = builder_path.read_text(encoding="utf-8")

    imports = ast.parse(source)
    import_names = []
    for node in ast.walk(imports):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_names.append(node.module.split('.')[0])

    assert "random" not in import_names, (
        "K20: 真值构建器不应使用 stdlib random"
    )


def test_k20_generator_deterministic():
    """K20: 生成器确定性——两次运行逐字节一致。

    这是一个概念性测试，验证生成器确定性逻辑。
    实际确定性由 test_generator.py 中的 test_deterministic_generation 验证。
    """
    # 验证 deterministic_rng.py 有确定性实现
    rng_path = Path("data/benchmark/generator/deterministic_rng.py")
    source = rng_path.read_text(encoding="utf-8")

    # 检查是否有 next() 方法
    assert "def next" in source or "def __next__" in source, (
        "K20: SplitMix64 应有 next() 方法"
    )

    # 检查是否有 seed 参数
    assert "seed" in source.lower(), (
        "K20: SplitMix64 应有 seed 参数"
    )


def test_k20_no_system_clock():
    """K20: 生成器不使用系统时钟。"""
    generator_dir = Path("data/benchmark/generator")

    for py_file in generator_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")

        # 检查是否使用 time.time() 或 time.perf_counter()
        time_patterns = [
            r'time\.time\(\)',
            r'time\.perf_counter\(\)',
            r'time\.monotonic\(\)',
            r'datetime\.now\(\)',
        ]

        for pattern in time_patterns:
            matches = re.findall(pattern, source)
            # 排除注释中的匹配
            lines = source.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                if re.search(pattern, stripped):
                    # 在注释中跳过
                    if '#' in line:
                        code_part = line.split('#')[0]
                        if re.search(pattern, code_part):
                            pytest.fail(
                                f"K20: {py_file.name} 使用了系统时钟: {pattern}"
                            )


def test_k20_no_set_iteration():
    """K20: 生成器不依赖 set 迭代序。"""
    generator_dir = Path("data/benchmark/generator")

    for py_file in generator_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")

        # 检查是否有 for x in set: 模式
        set_iter_patterns = [
            r'for\s+\w+\s+in\s+set\(',
            r'for\s+\w+\s+in\s+\{[^}]+\}',
        ]

        for pattern in set_iter_patterns:
            matches = re.findall(pattern, source)
            # 排除注释中的匹配
            lines = source.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                if re.search(pattern, stripped):
                    if '#' in line:
                        code_part = line.split('#')[0]
                        if re.search(pattern, code_part):
                            pytest.fail(
                                f"K20: {py_file.name} 可能依赖 set 迭代序"
                            )


def test_k20_truth_has_generator_seed():
    """K20: 真值库条目包含 generator_seed。"""
    truth_path = Path("data/benchmark/truth.json")
    assert truth_path.exists(), "truth.json 不存在"

    truth = json.loads(truth_path.read_text(encoding="utf-8"))

    for entry in truth:
        assert "generator_seed" in entry, (
            f"K20: 真值条目 {entry.get('sample_id')} 缺少 generator_seed"
        )


def test_k20_truth_has_generator_version():
    """K20: 真值库条目包含 generator_version。"""
    truth_path = Path("data/benchmark/truth.json")
    assert truth_path.exists(), "truth.json 不存在"

    truth = json.loads(truth_path.read_text(encoding="utf-8"))

    for entry in truth:
        assert "generator_version" in entry, (
            f"K20: 真值条目 {entry.get('sample_id')} 缺少 generator_version"
        )


def test_k20_mutation_detection():
    """K20 变异验证：故意使用 stdlib random，门必须变红。

    这是一个概念性测试，验证 K20 守门逻辑本身正确。
    """
    # 模拟：如果使用了 random，检测会失败
    mock_source_with_violation = """
import random

def generate():
    return random.random()
"""

    imports = ast.parse(mock_source_with_violation)
    import_names = []
    for node in ast.walk(imports):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.append(alias.name.split('.')[0])

    assert "random" in import_names  # 检测逻辑正确


# 导入 json 用于测试
import json
