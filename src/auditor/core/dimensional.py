"""量纲一致性审计引擎——确定性量纲代数。

K10: 未标单位不猜测
K11: 量纲平衡不等于公式正确
K12: 量纲代数确定性
"""

from __future__ import annotations

import re
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
    # 注意："n" 只保留一个含义 = force（牛顿）。此前此处有两处 "n"
    # （先 "amount" 后 "force"），后写者覆盖前者——pyflakes 直接报
    # "dictionary key 'n' repeated with different values"（D10）。
    # 取舍依据：
    #   1) 物质的量的单位符号是 mol（已在表内映射到 amount），
    #      单独把小写 n 映射到 amount 会让 "N"（牛顿）永远拿不到 force；
    #   2) 现有行为（大写 N 经 lower() → n → force）已被测试固化，
    #      保留 force 即保持行为逐字节不变（删掉的是被覆盖的死条目）。
    unit_map = {
        "m": "length",
        "kg": "mass",
        "s": "time",
        "a": "current",
        "k": "temperature",
        "mol": "amount",
        "cd": "luminous",
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

    K10 纪律：只有**带数值系数的单位**才算单位标注（如 ``v = 10 m/s``）。
    裸单字母符号（F、T、m、N…）在物理文本里通常是变量名而非单位——
    把它们当单位会凭空造出量纲判定（F 被读成 farad、T 被读成 tesla），
    属"猜测"，一律不认。

    Args:
        expr_str: 表达式字符串

    Returns:
        量纲向量，无法提取返回 None
    """
    import re

    # 形如 "10 m/s"、"3.5 kg"、"2 N·m"：数值系数 + 单位符号
    quantity_pattern = re.compile(
        r"[-+]?\d+(?:\.\d+)?(?:\s*[eE][-+]?\d+)?\s*"
        r"([A-Za-zΩ][A-Za-zΩ^0-9/·*\-]*)"
    )

    for match in quantity_pattern.finditer(expr_str):
        unit_str = match.group(1).strip()
        # 归一 LaTeX 幂次与乘号
        unit_str = unit_str.replace("^", "^").replace("·", "*")
        dim = _parse_unit(unit_str)
        if dim is not None:
            return dim

    return None


def _parse_bracket_dimension(spec: str) -> Optional[DimensionVector]:
    """解析方括号量纲声明，如 ``[M][L][T]^{-2}`` → DimensionVector(m=1,l=1,t=-2)。

    仅接受方括号乘积形式；出现未知符号（非 7 个基本量纲）返回 None。
    """
    spec = spec.strip()
    if not spec or "[" not in spec:
        return None

    base = {
        "M": "m", "L": "l", "T": "t", "I": "i",
        "Θ": "theta", "N": "n", "J": "j",
    }
    result = DimensionVector()

    # 形如 [X] 或 [X]^{n} / [X]^n
    for sym, exp_str in re.findall(r"\[([^\]]+)\](?:\s*\^\s*\{?(-?\d+)\}?)?", spec):
        if sym not in base:
            return None
        try:
            exp = int(exp_str) if exp_str else 1
        except ValueError:
            return None
        field_name = base[sym]
        setattr(result, field_name, getattr(result, field_name) + exp)

    return result


def _clean_equation_content(content: str) -> str:
    """剥离环境标记与 label/caption，留下纯数学内容。"""
    import re

    content = re.sub(r"\\begin\{[^}]+\}", "", content)
    content = re.sub(r"\\end\{[^}]+\}", "", content)
    content = re.sub(r"\\label\{[^}]+\}", "", content)
    content = re.sub(r"\\caption\{[^}]+\}", "", content)
    return content.strip()


def _collect_dimension_declarations(equations: List[Dict[str, Any]]) -> Dict[str, DimensionVector]:
    """从所有方程中收集量纲声明：符号 → 声明量纲。

    支持 ``[F] = [M][L][T]^{-2}`` 以及逗号/quad 分隔的多条声明。
    """
    decls: Dict[str, DimensionVector] = {}
    for eq in equations:
        raw = eq.get("content", "") if isinstance(eq, dict) else ""
        content = _clean_equation_content(raw)
        for sym, spec in re.findall(r"\[([A-Za-z])\]\s*=\s*([^,;]+)", content):
            # 截断到下一个声明起点
            spec = re.split(r"\\quad|\\;|\\,", spec)[0]
            dim = _parse_bracket_dimension(spec)
            if dim is not None:
                decls[sym] = dim
    return decls


def _derive_dimension_from_product(
    rhs_str: str, decls: Dict[str, DimensionVector]
) -> Optional[DimensionVector]:
    """由声明的量纲表推导右式（乘积形式，如 ``m \\cdot a``）的量纲。

    仅处理单字母符号的乘除幂；遇到未声明符号或非代数内容返回 None。
    """
    import re

    # 去掉 LaTeX 乘号
    expr = re.sub(r"\\(?:cdot|times|,|;|!|quad)", " ", rhs_str)
    expr = expr.replace("{", "").replace("}", "").replace("\\", " ")
    expr = expr.strip()

    # 只允许符号、乘除、幂、空格
    if not re.fullmatch(r"[A-Za-z0-9\s*/^.\-()]+", expr):
        return None

    total = DimensionVector()
    sign = 1  # +1 分子，-1 分母
    # 逐 token 解析，支持 a/b 与 a^2
    tokens = re.findall(r"([*/]?)\s*([A-Za-z])\s*(?:\^\s*\{?(-?\d+)\}?)?", expr)
    if not tokens:
        return None

    consumed = 0
    for op, sym, exp_str in tokens:
        if op == "/":
            sign = -1
        elif op == "*":
            sign = 1
        if sym not in decls:
            return None
        try:
            exp = int(exp_str) if exp_str else 1
        except ValueError:
            return None
        total = total + (decls[sym] * (exp * sign))
        consumed += 1

    # 必须覆盖右式的全部字母（防"只认出一个符号就下结论"）
    letters = re.findall(r"[A-Za-z]", expr)
    if consumed != len(letters):
        return None

    return total


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

    两级口径：
    1. 量纲声明校验：``[F] = [M][L][T]^{-2}`` 与乘积律 ``F = m·a`` 交叉推导对账。
       声明与推导不一致 → invalid（dimension_mismatch）。
    2. 单位标注校验（原口径）：等式两侧带单位标注时比对；未标注 → undecidable（K10）。

    Args:
        tree: 论文结构树（来自解析器）

    Returns:
        断言审计结果列表
    """
    results: List[ClaimResult] = []
    claim_counter = 0

    equations = tree.get("equations", [])

    # ── 第一级：量纲声明与乘积律对账 ──
    decls = _collect_dimension_declarations(equations)
    if decls:
        for eq in equations:
            raw = eq.get("content", "") if isinstance(eq, dict) else ""
            content = _clean_equation_content(raw)
            # 跳过声明方程本身（含方括号）
            if "[" in content:
                continue
            if "=" not in content:
                continue
            lhs_str, rhs_str = content.split("=", 1)
            lhs_sym = lhs_str.strip()
            if len(lhs_sym) != 1 or lhs_sym not in decls:
                continue

            derived = _derive_dimension_from_product(rhs_str, decls)
            if derived is None:
                continue

            claim_counter += 1
            declared = decls[lhs_sym]
            balanced = declared == derived
            results.append(ClaimResult(
                claim_id=f"dim-{claim_counter:03d}",
                claim_type="dimension",
                verdict=Verdict.OK if balanced else Verdict.INVALID,
                evidence=(
                    f"量纲声明与乘积律一致: [{lhs_sym}] = {declared} "
                    f"（由 {rhs_str.strip()} 推导得 {derived}）"
                    "（注：量纲平衡不等于公式正确）"
                    if balanced else
                    f"量纲不平衡: 声明 [{lhs_sym}] = {declared}，"
                    f"但由 {rhs_str.strip()} 推导得 {derived}"
                ),
                steps=[{
                    "expr": f"[{lhs_sym}] 声明 {declared} vs 推导 {derived}",
                    "rule": "dimension_balance",
                    "valid": balanced,
                }],
                error_type="dimension_mismatch" if not balanced else None,
            ))

    # ── 第二级：单位标注校验（保留原口径，K10）──
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

                # 声明级已给出结论时，不再重复登记同一条方程
                if verdict == Verdict.UNDECIDABLE and decls:
                    continue

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
