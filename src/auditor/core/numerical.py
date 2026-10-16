"""数值断言复算引擎——与符号路径实现独立。

K7: 数值口径单一定义点
K8: 数值断言不采信符号路径自证
K9: 容差一处定义 + 注记同源
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, getcontext

from auditor.core.types import ClaimResult, Verdict
from auditor.core.numerical_tolerance import NUMERICAL_TOLERANCE, tolerance_note


# 设置 Decimal 高精度
getcontext().prec = 50


def _mpmath_compute(expr_str: str, var_values: Dict[str, float]) -> Optional[float]:
    """使用 mpmath 计算数值表达式。

    这是数值路径的核心实现，与符号路径不共享核心函数。
    """
    try:
        import mpmath

        # 构建 mpmath 上下文
        mpmath.mp.dps = 50  # 50位十进制精度

        # 解析简单表达式
        # 注意：这是一个简化实现，实际应用中需要完整的表达式解析器
        expr_str = expr_str.lower()

        # 替换常见数学函数
        expr_str = expr_str.replace("sin", "mpmath.sin")
        expr_str = expr_str.replace("cos", "mpmath.cos")
        expr_str = expr_str.replace("tan", "mpmath.tan")
        expr_str = expr_str.replace("exp", "mpmath.exp")
        expr_str = expr_str.replace("log", "mpmath.log")
        expr_str = expr_str.replace("sqrt", "mpmath.sqrt")
        expr_str = expr_str.replace("pi", "mpmath.pi")
        expr_str = expr_str.replace("e", "mpmath.e")

        # 替换变量
        for var, val in var_values.items():
            expr_str = expr_str.replace(var, f"mpmath.mpf('{val}')")

        # 计算
        result = eval(expr_str, {"mpmath": mpmath})
        return float(result)
    except Exception:
        return None


def _decimal_compute(expr_str: str, var_values: Dict[str, Decimal]) -> Optional[Decimal]:
    """使用 Decimal 进行高精度计算。

    这是数值路径的备选实现，用于验证。
    """
    try:
        # 简化实现：只处理基本算术
        # 实际应用中需要完整的表达式解析
        expr_str = expr_str.replace(" ", "")

        # 替换变量
        for var, val in var_values.items():
            expr_str = expr_str.replace(var, f"Decimal('{val}')")

        # 计算
        result = eval(expr_str, {"Decimal": Decimal})
        return result
    except Exception:
        return None


def _compute_with_symbolic(expr_str: str, var_values: Dict[str, float]) -> Optional[float]:
    """使用 SymPy 进行符号计算（符号路径）。

    这是符号路径的实现，与数值路径独立。
    """
    try:
        from sympy import symbols, sympify, N

        # 解析变量
        var_names = list(var_values.keys())
        sympy_vars = symbols(var_names)
        var_dict = dict(zip(var_names, sympy_vars if isinstance(sympy_vars, tuple) else [sympy_vars]))

        # 解析表达式
        expr = sympify(expr_str, locals=var_dict)

        # 代入数值
        result = expr.subs([(var_dict[name], val) for name, val in var_values.items()])

        # 转换为数值
        return float(N(result, 15))
    except Exception:
        return None


def _compare_values(paper_value: float, computed_value: float, category: str = "default") -> Tuple[Verdict, str, float]:
    """比较论文值与计算值。

    Args:
        paper_value: 论文中报告的值
        computed_value: 计算得到的值
        category: 容差类别

    Returns:
        (verdict, evidence, deviation)
    """
    tolerance = NUMERICAL_TOLERANCE.get(category, NUMERICAL_TOLERANCE["default"])

    deviation = abs(paper_value - computed_value)

    if deviation <= tolerance:
        return Verdict.OK, f"偏差 {deviation:.2e} 在容差 {tolerance:.0e} 内", deviation
    else:
        return Verdict.INVALID, f"偏差 {deviation:.2e} 超出容差 {tolerance:.0e}", deviation


def _extract_formula(text: str) -> Optional[str]:
    """从 caption/正文中提取函数公式，如 ``$f(x) = e^x$`` → ``e^x``。"""
    import re

    for m in re.finditer(r"\$([^$]+)\$", text):
        body = m.group(1)
        if "=" not in body:
            continue
        lhs, rhs = body.split("=", 1)
        if re.match(r"^\s*[a-zA-Z]\s*\(\s*[a-zA-Z]\s*\)\s*$", lhs):
            return rhs.strip()
    return None


def _extract_table_rows(content: str) -> List[Tuple[float, float]]:
    """从 tabular 内容提取 (x, y) 数值行。"""
    import re

    rows: List[Tuple[float, float]] = []
    for line in content.splitlines():
        # 形如 "1 & 2.718282 \\"
        m = re.match(r"\s*([-+]?\d+(?:\.\d+)?)\s*&\s*([-+]?\d+(?:\.\d+)?)\s*\\\\?\s*$", line)
        if m:
            rows.append((float(m.group(1)), float(m.group(2))))
    return rows


def _evaluate_formula_mpmath(formula: str, x_value: float) -> Optional[float]:
    """用 mpmath 独立复算 f(x)（数值路径，不借道 SymPy）。

    支持形如 ``e^x``、``e^{x}``、``exp(x)`` 的单变量表达式。
    """
    import re

    try:
        import mpmath

        mpmath.mp.dps = 50

        expr = formula.strip().replace("{", "(").replace("}", ")")
        expr = re.sub(r"\\(?:cdot|times)", "*", expr)
        expr = re.sub(r"\s+", "", expr)

        # e^{...} / e^x → exp(...)
        expr = re.sub(r"e\^\(([^()]+)\)", r"exp(\1)", expr)
        expr = re.sub(r"e\^([A-Za-z0-9])", r"exp(\1)", expr)
        expr = expr.replace("exp(", "mpmath.exp(")
        # 独立 e 底数
        expr = re.sub(r"(?<![A-Za-z_.])e(?![A-Za-z_(])", "mpmath.e", expr)
        # 变量 x
        expr = re.sub(r"(?<![A-Za-z_.])x(?![A-Za-z_])", "mpmath.mpf('%s')" % x_value, expr)

        # 只允许 mpmath 调用、数字与算术
        if not re.fullmatch(r"[A-Za-z0-9_.+\-*/(),_']+", expr):
            return None

        result = eval(expr, {"__builtins__": {}}, {"mpmath": mpmath})  # noqa: S307
        return float(result)
    except Exception:
        return None


def _verify_table_value(paper_value: float, computed_value: float) -> Tuple[Verdict, str, float]:
    """验证表格数值。"""
    return _compare_values(paper_value, computed_value, "table_value")


def _verify_convergence(sequence: List[float], limit: float) -> Tuple[Verdict, str]:
    """验证收敛性。

    检查序列是否收敛到指定极限。
    """
    tolerance = NUMERICAL_TOLERANCE["convergence"]

    if len(sequence) < 3:
        return Verdict.UNDECIDABLE, "序列长度不足，无法验证收敛性"

    # 检查最后几项是否接近极限
    last_values = sequence[-3:]
    deviations = [abs(v - limit) for v in last_values]

    if all(d <= tolerance for d in deviations):
        return Verdict.OK, f"序列收敛到 {limit}（容差 {tolerance:.0e}）"
    else:
        return Verdict.INVALID, f"序列不收敛到 {limit}"


def _verify_integral_value(paper_value: float, computed_value: float) -> Tuple[Verdict, str, float]:
    """验证积分值。"""
    return _compare_values(paper_value, computed_value, "integral")


def _verify_series_sum(paper_value: float, computed_value: float) -> Tuple[Verdict, str, float]:
    """验证级数和。"""
    return _compare_values(paper_value, computed_value, "series")


def _dedup_nested_tables(tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """剔除嵌套在 table 环境内的 tabular 条目（同一张表只审计一次）。

    解析器按契约同时登记 table 与 tabular 两种环境（K1 覆盖度口径），
    但审计面只应认外层 table（它带 caption，公式信息更全）。
    """
    table_contents = [
        t.get("content", "") for t in tables if t.get("type") == "table"
    ]
    out: List[Dict[str, Any]] = []
    for t in tables:
        if t.get("type") == "tabular":
            content = t.get("content", "")
            if any(content and content in tc for tc in table_contents):
                continue
        out.append(t)
    return out


def recompute_numerical(tree: Dict[str, Any]) -> List[ClaimResult]:
    """对论文数值断言做独立复算。

    数值路径使用 mpmath 实现，与符号路径（SymPy）不共享核心函数。
    复算 = 从表格 caption 提取公式 f(x)，对每个 x 用 mpmath 独立求值，
    再与表中报告值按容差比对——**绝不拿报告值自己比自己**。

    Args:
        tree: 论文结构树（来自解析器）

    Returns:
        断言审计结果列表
    """
    results: List[ClaimResult] = []
    claim_counter = 0
    note = tolerance_note("table_value")

    def _add_undecidable(tbl_idx: int, reason: str, n_rows: int) -> None:
        nonlocal claim_counter
        claim_counter += 1
        results.append(ClaimResult(
            claim_id=f"num-{claim_counter:03d}",
            claim_type="table_value",
            verdict=Verdict.UNDECIDABLE,
            evidence=f"{reason}（{note}）",
            steps=[{"expr": f"表格行数: {n_rows}", "rule": "recompute_skipped", "valid": False}],
        ))

    tables = _dedup_nested_tables(tree.get("tables", []))
    for tbl_idx, table in enumerate(tables):
        content = table.get("content", "") if isinstance(table, dict) else ""
        rows = _extract_table_rows(content)

        if not rows:
            # 数值行不可提取（表头非数值或格式特殊）→ 无法独立复算，如实记 undecidable
            _add_undecidable(tbl_idx, "表格未给出可提取的数值行，无法独立复算", 0)
            continue

        formula = _extract_formula(content)
        if formula is None:
            # 无公式可依 → 无法独立复算（不虚高判 ok）
            _add_undecidable(tbl_idx, "表格未给出可复算公式，无法独立复算", len(rows))
            continue

        for x_value, paper_value in rows:
            claim_counter += 1
            claim_id = f"num-{claim_counter:03d}"

            computed = _evaluate_formula_mpmath(formula, x_value)
            if computed is None:
                results.append(ClaimResult(
                    claim_id=claim_id,
                    claim_type="table_value",
                    verdict=Verdict.UNDECIDABLE,
                    evidence=f"公式 {formula} 无法用数值路径求值（{note}）",
                    steps=[{"expr": f"f({x_value})", "rule": "recompute_failed", "valid": False}],
                ))
                continue

            verdict, evidence, deviation = _verify_table_value(paper_value, computed)
            results.append(ClaimResult(
                claim_id=claim_id,
                claim_type="table_value",
                verdict=verdict,
                evidence=(
                    f"f({x_value:g}) 报告 {paper_value}，独立复算 {computed:.6f}，"
                    + evidence
                    + f"（{note}）"
                ),
                steps=[{
                    "expr": f"f({x_value:g}): 报告 {paper_value} vs 复算 {computed:.6f}",
                    "rule": "numerical_recompute",
                    "valid": verdict == Verdict.OK,
                    "deviation": deviation,
                }],
                error_type="numeric_mismatch" if verdict == Verdict.INVALID else None,
            ))

    # 如果没有数值断言，添加 undecidable 结果
    if not results:
        results.append(ClaimResult(
            claim_id="none-001",
            claim_type="table_value",
            verdict=Verdict.UNDECIDABLE,
            evidence=f"论文中无可数值化断言（{note}）",
            steps=[]
        ))

    return results
