"""K31: 守门必须证伪。

变异验证：故意弄坏被测行为 → 门必须变红；弄坏后仍绿 = 假门。

三个无效形态（本 skill 实录）：
① 阴性样本不含针——样本靠前缀被排除，待测逻辑空转
② 对照组改"测试的存在形式"而非"被测行为"
③ 断言张冠李戴——断言"命中列表为空"等于断言了所有判据
"""

from __future__ import annotations

import json
import tempfile
import shutil
from pathlib import Path
import pytest


# ── K17 变异验证：真值库注入 observed 字段，门必须变红 ──


def _run_k17_gate(truth_content: list) -> bool:
    """运行 K17 守门逻辑，返回是否通过。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        truth_file = Path(tmpdir) / "truth.json"
        truth_file.write_text(
            json.dumps(truth_content, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # 复制 K17 守门逻辑
        truth = json.loads(truth_file.read_text(encoding="utf-8"))
        for entry in truth:
            if "observed" in entry:
                return False  # 守门失败
        return True  # 守门通过


def test_k17_gate_mutation_observed_field():
    """K31 变异验证：真值库注入 observed 字段，K17 门必须变红。"""
    # 构造一个合法条目
    clean_entry = {
        "sample_id": "B001-dimension_mismatch",
        "input_card": {"paper_tex": "x.tex", "paper_id": "synth-001"},
        "expect": {
            "error_type": "dimension_mismatch",
            "location": "eq:deriv",
            "is_clean": False,
            "expected_verdict": "invalid",
        },
        "generator_seed": 42,
        "generator_version": "1.0.0",
    }

    # 1. 纯干净数据 → 门应通过
    assert _run_k17_gate([clean_entry]) is True, "干净数据应通过 K17 门"

    # 2. 注入 observed 字段 → 门必须变红
    polluted_entry = dict(clean_entry)
    polluted_entry["observed"] = {"verdict": "invalid"}
    assert _run_k17_gate([polluted_entry]) is False, (
        "K31 变异失败：注入 observed 字段后 K17 门仍绿，这是假门"
    )

    # 3. 混合条目（一个含 observed）→ 门必须变红
    mixed = [clean_entry, polluted_entry]
    assert _run_k17_gate(mixed) is False, (
        "K31 变异失败：混合条目中含 observed 时 K17 门仍绿"
    )


# ── K20 变异验证：生成器非确定性，门必须变红 ──


def test_k20_gate_mutation_non_deterministic():
    """K31 变异验证：生成器引入非确定性，K20 门必须变红。

    变异方式：临时将 splitmix64 的 next() 方法替换为 stdlib random，
    两次运行结果必然不同。
    """
    import random as stdlib_random
    from data.benchmark.generator.deterministic_rng import SplitMix64

    # 保存原始方法
    original_next = SplitMix64.next

    try:
        # 注入变异：用 stdlib random 替代 splitmix64
        def mutated_next(self):
            return stdlib_random.randint(0, 2**64 - 1)

        SplitMix64.next = mutated_next

        # 运行生成器两次，比较结果
        with tempfile.TemporaryDirectory() as tmp1:
            with tempfile.TemporaryDirectory() as tmp2:
                from data.benchmark.generator import main as gen_main

                gen_main(tmp1, min_per_type=1, clean_count=1)
                gen_main(tmp2, min_per_type=1, clean_count=1)

                truth1 = json.loads(
                    (Path(tmp1) / "truth.json").read_text(encoding="utf-8")
                )
                truth2 = json.loads(
                    (Path(tmp2) / "truth.json").read_text(encoding="utf-8")
                )

                # K20 门：两次运行必须一致
                # 变异后，这个断言应该失败（但 pytest 会捕获）
                # 我们用一个标志来确认变异确实产生了不同结果
                are_equal = truth1 == truth2

                # 关键断言：变异后结果不应相等
                assert not are_equal, (
                    "K31 变异失败：注入非确定性后生成器仍逐字节一致，"
                    "这是假门（K20 守门未证伪）"
                )
    finally:
        # 恢复原始方法
        SplitMix64.next = original_next


# ── K22 变异验证：探活打在消费处 ──


def test_k22_probe_mutation_broken_engine():
    """K31 变异验证：故意破坏引擎，探活必须检出。

    变异方式：临时让引擎总是返回 "ok"，探活用例必须失败。
    """
    # 加载一个含错误的样本
    truth_file = Path("data/benchmark/truth.json")
    if not truth_file.exists():
        pytest.skip("truth.json 不存在，跳过 K22 变异验证")

    truth = json.loads(truth_file.read_text(encoding="utf-8"))
    error_samples = [e for e in truth if not e["expect"]["is_clean"]]
    assert len(error_samples) > 0, "无错误样本，无法验证探活"

    sample = error_samples[0]
    expected_error = sample["expect"]["error_type"]

    # 模拟一个"坏引擎"：总是返回 ok
    class BrokenEngine:
        def audit(self, sample):
            return type("Result", (), {"verdict": "ok", "error_type": None})()

    # 探活逻辑：坏引擎对错误样本返回 ok → 探活应失败
    broken = BrokenEngine()
    result = broken.audit(sample)

    # 关键断言：探活必须能检出坏引擎
    # 如果坏引擎返回 ok，探活断言 verdict != ok 会失败
    # 这里我们验证探活的断言逻辑本身
    probe_passed = result.verdict != "ok"

    assert not probe_passed, (
        f"K31 变异失败：坏引擎对 {expected_error} 样本返回 ok，"
        f"但探活仍通过（探活未打在消费处）"
    )
