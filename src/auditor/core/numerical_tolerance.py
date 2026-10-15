"""K9: 数值口径唯一定义点（plan/02 §三）。

所有容差必须从此字典派生，禁止在代码中硬编码容差值。
守门测试 tests/gate/test_k7_tolerance.py 扫描源码断言无硬编码容差。
"""

NUMERICAL_TOLERANCE = {
    "default": 1e-6,        # 默认容差
    "table_value": 1e-4,    # 表格数值
    "convergence": 1e-8,    # 收敛性判定
    "integral": 1e-6,       # 数值积分
    "series": 1e-8,         # 级数求和
}


def tolerance_note(category: str) -> str:
    """K9: 注记文本同源派生。"""
    t = NUMERICAL_TOLERANCE[category]
    return f"容差口径：{t}（唯一定义点：src/auditor/core/numerical_tolerance.py）"
