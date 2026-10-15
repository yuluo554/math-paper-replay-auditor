"""K20: 确定性 RNG——splitmix64。

禁 stdlib random（不承诺跨版本序列一致）。
禁 set 迭代序。
禁系统时钟。
两次运行/构建逐字节一致。
"""

from __future__ import annotations


class SplitMix64:
    """确定性伪随机数生成器（splitmix64 算法）。"""

    def __init__(self, seed: int = 42):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next(self) -> int:
        """生成下一个 64 位随机整数。"""
        z = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        self.state = z
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def randint(self, a: int, b: int) -> int:
        """生成 [a, b] 范围内的随机整数。"""
        return a + (self.next() % (b - a + 1))

    def choice(self, seq: list):
        """从序列中随机选择一个元素。"""
        return seq[self.randint(0, len(seq) - 1)]

    def float(self) -> float:
        """生成 [0, 1) 范围内的随机浮点数。"""
        return (self.next() >> 11) / (1 << 53)


# 全局生成器（默认 seed=42，可复现）
_default_rng = SplitMix64(42)


def get_rng(seed: int = 42) -> SplitMix64:
    """获取生成器实例。"""
    return SplitMix64(seed)
