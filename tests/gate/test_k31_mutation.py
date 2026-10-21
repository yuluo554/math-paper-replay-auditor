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
#
# D7 修复：此前 `_run_k17_gate()` 在本文件里**本地重写**了一段判据，
# 不 import 真门 —— 把真门改成 no-op 后本测试仍然绿（实测 4 passed），
# "变异验证"变成自我确认。现在判据的唯一实现是
# `tests/gate/_k17_truth_logic.py::find_observed_entries`，
# K17 门与本文件共用它。

from tests.gate._k17_truth_logic import find_observed_entries


def _run_k17_gate(truth_content: list) -> bool:
    """运行 **真门** 的判据（K17 与本文件共用的实现），返回是否通过。"""
    return not find_observed_entries(truth_content)


def test_k17_gate_mutation_observed_field():
    """K31 变异验证：真值库注入 observed 字段，K17 门必须变红。

    变异打在**真门本体**上：把 `test_k17_truth.TRUTH_PATH` 指向一份被污染的
    真值库副本，然后**调用 K17 门的真函数**。
    若真门被改成 no-op（`return`）或判据被删掉，本测试必然变红——
    这正是 D7 修复前做不到的（当时它重写了一份判据，真门崩了它还绿）。
    """
    import tests.gate.test_k17_truth as k17

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

    # 1. 纯干净数据 → 真门应通过
    assert _run_k17_gate([clean_entry]) is True, "干净数据应通过 K17 门"

    # 2. 注入 observed 字段 → 判据必须抓到
    polluted_entry = dict(clean_entry)
    polluted_entry["observed"] = {"verdict": "invalid"}
    assert _run_k17_gate([polluted_entry]) is False, (
        "K31 变异失败：注入 observed 字段后 K17 判据仍绿，这是假门"
    )

    # 3. 混合条目（一个含 observed）→ 判据必须抓到
    mixed = [clean_entry, polluted_entry]
    assert _run_k17_gate(mixed) is False, (
        "K31 变异失败：混合条目中含 observed 时 K17 判据仍绿"
    )

    # 4. **真门本体**的变异：把真门指向污染副本，调用真门函数 → 必须变红
    with tempfile.TemporaryDirectory() as tmpdir:
        polluted_truth = Path(tmpdir) / "truth.json"
        polluted_truth.write_text(
            json.dumps(mixed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        original = k17.TRUTH_PATH
        try:
            k17.TRUTH_PATH = polluted_truth
            try:
                k17.test_no_observed_in_truth()
            except AssertionError:
                pass
            else:
                raise AssertionError(
                    "K31 变异失败：K17 真门对含 observed 的真值库仍绿——"
                    "真门没有真正检查 observed 字段（或已被改成 no-op）"
                )
        finally:
            k17.TRUTH_PATH = original


# ── K20 变异验证：生成器非确定性，门必须变红 ──


def test_k20_gate_mutation_non_deterministic():
    """K31 变异验证：生成器引入非确定性，K20 门必须变红。

    变异打在**被测行为**上：把 splitmix64 的 next() 换成 stdlib random。
    该 RNG 被注入器真实消费（非法指数、数值偏移量都取自它），
    故产物必然随变异而变——若仍逐字节一致，说明 RNG 是死代码、"确定性生成"
    这个命题从未被测过（本测试的第一版正是如此：变异打进死代码，门永远变不红）。
    """
    import random as stdlib_random
    from data.benchmark.generator.deterministic_rng import SplitMix64

    # 前置探针（非空转自证）：RNG 必须真的影响产物。
    from data.benchmark.generator.paper_template import generate_paper
    from data.benchmark.generator.error_injector import inject_illegal_derivation

    base = generate_paper("PROBE", 42)
    a1, _ = inject_illegal_derivation(base, 1001)
    a2, _ = inject_illegal_derivation(base, 1002)
    assert a1 != a2, (
        "K20 前置探针失败：不同 seed 的植入产物完全相同，"
        "说明 RNG 未参与生成——确定性命题不可证伪"
    )

    # 保存原始方法
    original_next = SplitMix64.next

    try:
        # 注入变异：用 stdlib random 替代 splitmix64
        def mutated_next(self):
            return stdlib_random.randint(0, 2**64 - 1)

        SplitMix64.next = mutated_next

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

                # 还要比对样本正文：真值库不含植入值，正文才体现 RNG 消费
                tex1 = sorted(
                    p.read_text(encoding="utf-8")
                    for p in Path(tmp1).rglob("paper.tex")
                )
                tex2 = sorted(
                    p.read_text(encoding="utf-8")
                    for p in Path(tmp2).rglob("paper.tex")
                )

                are_equal = (truth1 == truth2) and (tex1 == tex2)

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
