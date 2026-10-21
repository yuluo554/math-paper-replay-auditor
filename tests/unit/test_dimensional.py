"""量纲代数引擎单元测试。

测试 dimensional.py 的核心功能。
"""

from __future__ import annotations

import pytest
from auditor.core.dimensional import (
    check_dimensions,
    DimensionVector,
    COMMON_DIMENSIONS,
    _parse_unit,
    _extract_dimension_from_expr,
    _check_dimension_balance
)


def create_mock_tree(equations=None):
    """创建模拟论文结构树。"""
    return {
        "paper_id": "test-001",
        "equations": equations or [],
        "sections": [],
        "theorems": [],
        "lemmas": [],
        "proofs": [],
        "tables": [],
        "refs": [],
        "labels": [],
        "packages": [],
        "unrecognized_envs": [],
        "unrecognized_macros": [],
        "coverage": 1.0
    }


class TestDimensionVector:
    """量纲向量测试。"""

    def test_create_dimensionless(self):
        """创建无量纲向量。"""
        dim = DimensionVector()
        assert dim.is_dimensionless()
        assert dim.to_tuple() == (0, 0, 0, 0, 0, 0, 0)

    def test_create_with_values(self):
        """创建带值的量纲向量。"""
        dim = DimensionVector(m=1, l=1, t=-2)
        assert not dim.is_dimensionless()
        assert dim.m == 1
        assert dim.l == 1
        assert dim.t == -2

    def test_addition(self):
        """量纲加法（乘法运算）。"""
        dim1 = DimensionVector(m=1, l=1, t=-2)  # 力
        dim2 = DimensionVector(l=1, t=-1)  # 速度
        result = dim1 + dim2
        assert result.m == 1
        assert result.l == 2
        assert result.t == -3

    def test_subtraction(self):
        """量纲减法（除法运算）。"""
        dim1 = DimensionVector(l=1, t=-1)  # 速度
        dim2 = DimensionVector(t=-1)  # 时间倒数
        result = dim1 - dim2
        assert result.l == 1
        assert result.t == 0

    def test_multiplication(self):
        """量纲标量乘（幂运算）。"""
        dim = DimensionVector(l=1, t=-1)
        result = dim * 2
        assert result.l == 2
        assert result.t == -2

    def test_equality(self):
        """量纲相等判断。"""
        dim1 = DimensionVector(m=1, l=1, t=-2)
        dim2 = DimensionVector(m=1, l=1, t=-2)
        dim3 = DimensionVector(m=1, l=1, t=-1)

        assert dim1 == dim2
        assert dim1 != dim3

    def test_string_representation(self):
        """量纲字符串表示。"""
        dim1 = DimensionVector(m=1, l=1, t=-2)
        s = str(dim1)
        assert "M" in s
        assert "L" in s
        assert "T" in s

        dim2 = DimensionVector()  # 无量纲
        assert str(dim2) == "[1]"

    def test_is_dimensionless(self):
        """无量纲判断。"""
        assert DimensionVector().is_dimensionless()
        assert not DimensionVector(m=1).is_dimensionless()


class TestCommonDimensions:
    """常见物理量量纲测试。"""

    def test_basic_dimensions_exist(self):
        """基本量纲存在。"""
        assert "mass" in COMMON_DIMENSIONS
        assert "length" in COMMON_DIMENSIONS
        assert "time" in COMMON_DIMENSIONS

    def test_derived_dimensions_exist(self):
        """导出量纲存在。"""
        assert "velocity" in COMMON_DIMENSIONS
        assert "force" in COMMON_DIMENSIONS
        assert "energy" in COMMON_DIMENSIONS

    def test_force_dimension(self):
        """力的量纲正确。"""
        force_dim = COMMON_DIMENSIONS["force"]
        assert force_dim.m == 1
        assert force_dim.l == 1
        assert force_dim.t == -2

    def test_energy_dimension(self):
        """能量的量纲正确。"""
        energy_dim = COMMON_DIMENSIONS["energy"]
        assert energy_dim.m == 1
        assert energy_dim.l == 2
        assert energy_dim.t == -2


class TestUnitParsing:
    """单位解析测试。"""

    def test_parse_basic_units(self):
        """解析基本单位。"""
        dim = _parse_unit("m")
        assert dim is not None
        assert dim.l == 1

        dim = _parse_unit("kg")
        assert dim is not None
        assert dim.m == 1

        dim = _parse_unit("s")
        assert dim is not None
        assert dim.t == 1

    def test_parse_derived_units(self):
        """解析导出单位。"""
        dim = _parse_unit("N")
        assert dim is not None
        assert dim.m == 1
        assert dim.l == 1
        assert dim.t == -2

    def test_parse_unknown_unit(self):
        """解析未知单位返回 None。"""
        dim = _parse_unit("unknown_unit")
        assert dim is None

    def test_parse_compound_units(self):
        """解析复合单位。"""
        dim = _parse_unit("m/s")
        # 速度的量纲
        assert dim is not None
        assert dim.l == 1
        assert dim.t == -1

    def test_parse_n_is_force_not_amount(self):
        """D10: "n" 的量纲只能是 force，不能与 amount 混。

        此前 unit_map 里 "n" 出现两次（先 amount 后 force），后写者覆盖前者，
        pyflakes 报 "dictionary key 'n' repeated with different values"。
        取舍：物质的量的单位是 mol（小写 n 单独留给物质的量会让
        "N"（牛顿）永远拿不到 force）——本测试把这个取舍钉死。
        """
        newton = _parse_unit("N")
        assert newton is not None, "N（牛顿）必须能解析"
        assert newton.m == 1 and newton.l == 1 and newton.t == -2, (
            f"N（牛顿）应解析为 force，实际为 {newton}"
        )
        assert newton.n == 0, "force 的量纲里不含物质的量分量 n"

        mol = _parse_unit("mol")
        assert mol is not None, "mol（物质的量）必须能解析"
        assert mol.n == 1, f"mol 应解析为 amount（n=1），实际为 {mol}"
        assert mol.m == 0 and mol.l == 0 and mol.t == 0, (
            f"mol 的量纲不应含质量/长度/时间分量，实际为 {mol}"
        )

        # N 与 mol 的语义不得互相污染
        assert newton != mol

    def test_unit_map_has_no_duplicate_keys(self):
        """D10: 单位映射表不得有重复键（静态口径，与 pyflakes 同源）。"""
        import ast
        import inspect

        from auditor.core import dimensional

        source = inspect.getsource(dimensional._parse_unit)
        tree = ast.parse(source.strip())

        unit_map_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "unit_map" for t in node.targets
            ):
                unit_map_node = node.value
                break
        assert unit_map_node is not None, "未找到 unit_map 字面量"

        seen = set()
        for key_node in unit_map_node.keys:
            key = key_node.value
            assert key not in seen, f"unit_map 里有重复键: {key!r}"
            seen.add(key)


class TestDimensionBalance:
    """量纲平衡测试。"""

    def test_balanced_dimensions(self):
        """量纲平衡的等式。"""
        verdict, lhs_dim, rhs_dim, evidence = _check_dimension_balance("energy = mc^2", "energy = mc^2")
        # 由于无法解析单位，返回 undecidable
        assert verdict.value == "undecidable"

    def test_unbalanced_dimensions(self):
        """量纲不平衡的等式。"""
        # 简化测试
        verdict, _, _, _ = _check_dimension_balance("unknown", "unknown")
        assert verdict.value == "undecidable"


class TestDimensionEngine:
    """量纲引擎测试。"""

    def test_empty_tree_returns_undecidable(self):
        """空论文树返回 undecidable 结果。"""
        tree = create_mock_tree()
        results = check_dimensions(tree)

        assert len(results) > 0
        assert results[0].verdict == "undecidable"

    def test_tree_with_equations(self):
        """包含等式的论文树。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"}
        ])
        results = check_dimensions(tree)

        assert len(results) > 0

    def test_verdict_values_are_valid(self):
        """所有 verdict 值必须是 ok/invalid/undecidable 之一。"""
        tree = create_mock_tree(equations=[
            {"content": "F = ma"}
        ])
        results = check_dimensions(tree)

        valid_verdicts = {"ok", "invalid", "undecidable"}
        for result in results:
            assert result.verdict.value in valid_verdicts

    def test_evidence_not_empty(self):
        """证据字段不为空。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"}
        ])
        results = check_dimensions(tree)

        for result in results:
            assert result.evidence is not None
            assert len(result.evidence) > 0

    def test_multiple_equations(self):
        """多个等式被正确处理。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"},
            {"content": "F = ma"},
            {"content": "v = d/t"}
        ])
        results = check_dimensions(tree)

        assert len(results) >= 3


class TestDimensionDeterminism:
    """确定性测试。"""

    def test_same_input_same_output(self):
        """相同输入产生相同输出（K12）。"""
        tree = create_mock_tree(equations=[
            {"content": "E = mc^2"}
        ])

        results1 = check_dimensions(tree)
        results2 = check_dimensions(tree)

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.verdict == r2.verdict

    def test_deterministic_with_multiple_runs(self):
        """多次运行结果一致。"""
        tree = create_mock_tree(equations=[
            {"content": "F = ma"}
        ])

        results_list = [check_dimensions(tree) for _ in range(5)]

        for i in range(1, len(results_list)):
            assert len(results_list[i]) == len(results_list[0])
            for r1, r2 in zip(results_list[i], results_list[0]):
                assert r1.verdict == r2.verdict
