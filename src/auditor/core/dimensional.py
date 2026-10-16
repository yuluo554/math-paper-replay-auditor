"""量纲一致性审计引擎——确定性量纲代数。

K10: 未标单位不猜测
K11: 量纲平衡不等于公式正确
K12: 量纲代数确定性
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from auditor.core.types import ClaimResult, Verdict


class BaseDimension(str, Enum):
    """SI 基本量纲（7 个）。"""
    MASS = "M"           # 质量
    LENGTH = "L"         # 长度
    TIME = "T"           # 时间
    CURRENT = "I"        # 电流
    TEMPERATURE = "Θ"    # 温度
    AMOUNT = "N"         # 物质的量
    LUMINOUS = "J"       # 发光强度


@dataclass
class DimensionVector:
    """量纲向量——7 维整数向量。

    每个物理量映射为 7 维向量，如 [v] = [L][T]^{-1} → (0, 1, -1, 0, 0, 0, 0)
    """
    m: int = 0  # [M]
    l: int = 0  # [L]
    t: int = 0  # [T]
    i: int = 0  # [I]
    theta: int = 0  # [Θ]
    n: int = 0  # [N]
    j: int = 0  # [J]

    def to_tuple(self) -> Tuple[int, ...]:
        """转换为元组。"""
        return (self.m, self.l, self.t, self.i, self.theta, self.n, self.j)

    def to_dict(self) -> Dict[str, int]:
        """转换为字典。"""
        return {
            "M": self.m,
            "L": self.l,
            "T": self.t,
            "I": self.i,
            "Θ": self.theta,
            "N": self.n,
            "J": self.j
        }

    def __add__(self, other: "DimensionVector") -> "DimensionVector":
        """量纲加法（乘法运算）。"""
        return DimensionVector(
            m=self.m + other.m,
            l=self.l + other.l,
            t=self.t + other.t,
            i=self.i + other.i,
            theta=self.theta + other.theta,
            n=self.n + other.n,
            j=self.j + other.j
        )

    def __sub__(self, other: "DimensionVector") -> "DimensionVector":
        """量纲减法（除法运算）。"""
        return DimensionVector(
            m=self.m - other.m,
            l=self.l - other.l,
            t=self.t - other.t,
            i=self.i - other.i,
            theta=self.theta - other.theta,
            n=self.n - other.n,
            j=self.j - other.j
        )

    def __mul__(self, scalar: int) -> "DimensionVector":
        """量纲标量乘（幂运算）。"""
        return DimensionVector(
            m=self.m * scalar,
            l=self.l * scalar,
            t=self.t * scalar,
            i=self.i * scalar,
            theta=self.theta * scalar,
            n=self.n * scalar,
            j=self.j * scalar
        )

    def __eq__(self, other: object) -> bool:
        """量纲相等判断。"""
        if not isinstance(other, DimensionVector):
            return False
        return self.to_tuple() == other.to_tuple()

    def __str__(self) -> str:
        """量纲字符串表示。"""
        parts = []
        for dim, value in self.to_dict().items():
            if value == 1:
                parts.append(f"[{dim}]")
            elif value > 1:
                parts.append(f"[{dim}]^{{{value}}}")
            elif value == -1:
                parts.append(f"[{dim}]^{{-1}}")
            elif value < -1:
                parts.append(f"[{dim}]^{{{value}}}")

        if not parts:
            return "[1]"  # 无量纲
        return "".join(parts)

    def is_dimensionless(self) -> bool:
        """判断是否无量纲。"""
        return all(v == 0 for v in self.to_tuple())


# 常见物理量的量纲定义
COMMON_DIMENSIONS: Dict[str, DimensionVector] = {
    # 基本量纲
    "mass": DimensionVector(m=1),
    "length": DimensionVector(l=1),
    "time": DimensionVector(t=1),
    "current": DimensionVector(i=1),
    "temperature": DimensionVector(theta=1),
    "amount": DimensionVector(n=1),
    "luminous": DimensionVector(j=1),

    # 导出量纲
    "velocity": DimensionVector(l=1, t=-1),
    "acceleration": DimensionVector(l=1, t=-2),
    "force": DimensionVector(m=1, l=1, t=-2),
    "energy": DimensionVector(m=1, l=2, t=-2),
    "power": DimensionVector(m=1, l=2, t=-3),
    "pressure": DimensionVector(m=1, l=-1, t=-2),
    "frequency": DimensionVector(t=-1),
    "charge": DimensionVector(i=1, t=1),
    "voltage": DimensionVector(m=1, l=2, t=-3, i=-1),
    "resistance": DimensionVector(m=1, l=2, t=-3, i=-2),
    "capacitance": DimensionVector(m=-1, l=-2, t=4, i=2),
    "inductance": DimensionVector(m=1, l=2, t=-2, i=-2),
    "magnetic_flux": DimensionVector(m=1, l=2, t=-2, i=-1),
    "momentum": DimensionVector(m=1, l=1, t=-1),
    "angular_momentum": DimensionVector(m=1, l=2, t=-1),
    "moment_of_inertia": DimensionVector(m=1, l=2),
    "viscosity": DimensionVector(m=1, l=-1, t=-1),
    "surface_tension": DimensionVector(m=1, t=-2),
    "gravitational_constant": DimensionVector(m=-1, l=3, t=-2),
    "planck_constant": DimensionVector(m=1, l=2, t=-1),
    "boltzmann_constant": DimensionVector(m=1, l=2, t=-2, theta=-1),
    "speed_of_light": DimensionVector(l=1, t=-1),
    "permittivity": DimensionVector(m=-1, l=-3, t=4, i=2),
    "permeability": DimensionVector(m=1, l=1, t=-2, i=-2),
}


def _parse_unit(unit_str: str) -> Optional[DimensionVector]:
    """解析单位字符串为量纲向量。

    Args:
        unit_str: 单位字符串，如 "m/s", "kg", "N"

    Returns:
        量纲向量，无法解析返回 None
    """
    unit_str = unit_str.strip().lower()

    # 直接匹配常见单位
    if unit_str in COMMON_DIMENSIONS:
        return COMMON_DIMENSIONS[unit_str]

    # 单位映射
    unit_map = {
        "m": "length",
        "kg": "mass",
        "s": "time",
        "a": "current",
        "k": "temperature",
        "mol": "amount",
        "cd": "luminous",
        "n": "amount",
        "hz": "frequency",
        "n": "force",  # 牛顿
        "j": "energy",
        "w": "power",
        "pa": "pressure",
        "c": "charge",
        "v": "voltage",
        "ohm": "resistance",
        "f": "capacitance",
        "h": "inductance",
        "wb": "magnetic_flux",
        "t": "magnetic_flux",  # 特斯拉
        "lm": "luminous",
        "lx": "luminous",  # 勒克斯
    }

    if unit_str in unit_map:
        return COMMON_DIMENSIONS.get(unit_map[unit_str])

    # 解析复合单位
    if "/" in unit_str:
        parts = unit_str.split("/")
        if len(parts) == 2:
            numerator = _parse_unit(parts[0])
            denominator = _parse_unit(parts[1])
            if numerator and denominator:
                return numerator - denominator

    # 解析幂次单位
    if "^" in unit_str:
        parts = unit_str.split("^")
        if len(parts) == 2:
            base = _parse_unit(parts[0])
            try:
                power = int(parts[1])
                if base:
                    return base * power
            except ValueError:
                pass

    return None


def _extract_dimension_from_expr(expr_str: str) -> Optional[DimensionVector]:
    """从表达式中提取量纲。

    Args:
        expr_str: 表达式字符串

    Returns:
        量纲向量，无法提取返回 None
    """
    # 简化实现：查找单位标注
    import re

    # 匹配单位模式
    # 注意：需要排除数学变量（如 f, h, x 等）
    # 单位应该是独立的，不跟在变量后面或后面跟括号
    unit_patterns = [
        # 匹配单位，但排除后面跟括号的情况（函数调用）
        # 也排除前面是字母的情况（变量名的一部分）
        r'(?<![a-zA-Z])\b(m|kg|s|A|K|mol|cd|Hz|N|J|W|Pa|C|V|Ω|F|H|Wb|T|lm|lx)\b(?!\')',
        r'\b(m/s|kg/m\^3|N·m|J/s)\b',
    ]

    for pattern in unit_patterns:
        matches = re.findall(pattern, expr_str, re.IGNORECASE)
        if matches:
            # 返回第一个匹配单位的量纲
            for match in matches:
                dim = _parse_unit(match.lower())
                if dim:
                    return dim

    return None


def _check_dimension_balance(lhs_str: str, rhs_str: str) -> Tuple[Verdict, Optional[DimensionVector], Optional[DimensionVector], str]:
    """检查等式两边的量纲平衡。

    Args:
        lhs_str: 左表达式
        rhs_str: 右表达式

    Returns:
        (verdict, lhs_dim, rhs_dim, evidence)
    """
    lhs_dim = _extract_dimension_from_expr(lhs_str)
    rhs_dim = _extract_dimension_from_expr(rhs_str)

    # K10: 未标单位不猜测
    if lhs_dim is None and rhs_dim is None:
        return Verdict.UNDECIDABLE, None, None, "等式两边均未标注单位，无法判定量纲平衡"

    if lhs_dim is None:
        return Verdict.UNDECIDABLE, None, rhs_dim, "左表达式未标注单位，无法判定量纲平衡"

    if rhs_dim is None:
        return Verdict.UNDECIDABLE, lhs_dim, None, "右表达式未标注单位，无法判定量纲平衡"

    # 检查量纲是否平衡
    if lhs_dim == rhs_dim:
        return Verdict.OK, lhs_dim, rhs_dim, f"量纲平衡: {lhs_dim} = {rhs_dim}"
    else:
        return Verdict.INVALID, lhs_dim, rhs_dim, f"量纲不平衡: {lhs_dim} ≠ {rhs_dim}"


def check_dimensions(tree: Dict[str, Any]) -> List[ClaimResult]:
    """审计公式量纲一致性。

    Args:
        tree: 论文结构树（来自解析器）

    Returns:
        断言审计结果列表
    """
    results: List[ClaimResult] = []
    claim_counter = 0

    # 从方程中提取量纲信息
    equations = tree.get("equations", [])
    for eq in equations:
        claim_counter += 1
        claim_id = f"dim-{claim_counter:03d}"

        content = eq.get("content", "")

        # 分割等式
        if "=" in content:
            parts = [p.strip() for p in content.split("=")]
            if len(parts) >= 2:
                lhs = parts[0]
                rhs = parts[1]

                verdict, lhs_dim, rhs_dim, evidence = _check_dimension_balance(lhs, rhs)

                # K11: 量纲平衡不等于公式正确
                if verdict == Verdict.OK:
                    evidence += "（注：量纲平衡不等于公式正确）"

                steps = []
                if lhs_dim:
                    steps.append({
                        "expr": f"左表达式量纲: {lhs_dim}",
                        "rule": "dimension_extraction",
                        "valid": True
                    })
                if rhs_dim:
                    steps.append({
                        "expr": f"右表达式量纲: {rhs_dim}",
                        "rule": "dimension_extraction",
                        "valid": True
                    })

                results.append(ClaimResult(
                    claim_id=claim_id,
                    claim_type="dimension",
                    verdict=verdict,
                    evidence=evidence,
                    steps=steps,
                    error_type="dimension_mismatch" if verdict == Verdict.INVALID else None
                ))

    # 如果没有方程，添加 undecidable 结果
    if not results:
        results.append(ClaimResult(
            claim_id="none-001",
            claim_type="dimension",
            verdict=Verdict.UNDECIDABLE,
            evidence="论文中无可量纲化断言",
            steps=[]
        ))

    return results
