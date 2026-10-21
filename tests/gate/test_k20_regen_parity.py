"""K20: 真值库「再生成位级一致」守门。

背景（D3）：本仓此前在 plan/00 与 HANDOFF-M2..M5 里多处勾选
「生成器 `--check` 位级一致守门测试（K20）」，但仓内**没有** `--check` 实现——
`generator.main()` 当时只有三个位置参数。结果是：手改 `truth.json` 的
`expect.location` / `generator_seed` 可以**完全不被任何门发现**
（实测：288 passed, 3 skipped, EXIT=0）。

本文件补齐这道门：
- 正控：仓库真值库与"按同样参数重生成"的结果逐字节相同（rc 0）
- 负控：篡改副本的一条 `expect.location` → `--check` 必须 rc != 0

纪律：`--check` 是**只读**的（重生成到临时目录，不写目标目录）——
另一仓踩过"先写后比、把篡改静默抹平"的坑。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCH_DIR = REPO_ROOT / "data" / "benchmark"

sys.path.insert(0, str(REPO_ROOT))

from data.benchmark.generator import check_benchmark  # noqa: E402


def test_k20_check_passes_on_repo_data():
    """K20 正控：仓库真值库与重生成结果逐字节一致。"""
    assert BENCH_DIR.is_dir(), f"基准数据目录不存在: {BENCH_DIR}"
    rc = check_benchmark(str(BENCH_DIR))
    assert rc == 0, f"K20 违规: 仓库真值库与重生成结果不一致（rc={rc}）"


def test_k20_check_detects_tampered_location(tmp_path):
    """K20 负控：篡改 expect.location 的一个字符 → --check 必须失败。"""
    copy = tmp_path / "bench-copy"
    shutil.copytree(BENCH_DIR, copy)

    truth_path = copy / "truth.json"
    payload = json.loads(truth_path.read_text(encoding="utf-8"))
    original_location = payload[0]["expect"]["location"]
    tampered = original_location + "-TAMPERED"
    payload[0]["expect"]["location"] = tampered

    # 用与生成器完全相同的落盘格式写回（LF + 2 空格缩进 + 末尾换行）
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with open(truth_path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\r\n", "\n"))

    assert tampered != original_location, "负控构造失败：篡改值与原值相同"

    rc = check_benchmark(str(copy))
    assert rc != 0, (
        "K20 违规: 篡改 expect.location 后 --check 仍返回 0——"
        "说明这道门抓不到真值库被手改（本次改动之前就是这种状态）"
    )


def test_k20_check_detects_tampered_generator_seed(tmp_path):
    """K20 负控（补充）：篡改 generator_seed → --check 必须失败。"""
    copy = tmp_path / "bench-seed-copy"
    shutil.copytree(BENCH_DIR, copy)

    truth_path = copy / "truth.json"
    payload = json.loads(truth_path.read_text(encoding="utf-8"))
    original_seed = payload[1]["generator_seed"]
    payload[1]["generator_seed"] = 999999
    assert payload[1]["generator_seed"] != original_seed

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with open(truth_path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\r\n", "\n"))

    rc = check_benchmark(str(copy))
    assert rc != 0, (
        "K20 违规: 篡改 generator_seed 后 --check 仍返回 0——"
        "说明这道门抓不到真值库被手改"
    )


def test_k20_check_cli_exit_codes(tmp_path):
    """K20: CLI 形态的 --check 与函数形态一致（正控 rc 0 / 负控 rc != 0）。"""
    env_python = sys.executable

    ok = subprocess.run(
        [env_python, "-m", "data.benchmark.generator", "--check"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, (
        f"CLI --check 对仓库数据返回 {ok.returncode}（期望 0）:\n{ok.stdout}\n{ok.stderr}"
    )

    copy = tmp_path / "bench-cli-copy"
    shutil.copytree(BENCH_DIR, copy)
    truth_path = copy / "truth.json"
    payload = json.loads(truth_path.read_text(encoding="utf-8"))
    payload[0]["expect"]["location"] = "eq:FAKE-LOCATION"
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with open(truth_path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\r\n", "\n"))

    bad = subprocess.run(
        [
            env_python,
            "-m",
            "data.benchmark.generator",
            "--check",
            "--benchmark-dir",
            str(copy),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert bad.returncode != 0, (
        f"CLI --check 对篡改副本返回 0（期望 != 0）:\n{bad.stdout}\n{bad.stderr}"
    )


def test_k20_check_does_not_write_target(tmp_path):
    """K20: --check 是只读的——校验前后目标目录的字节内容不得改变。

    这是"另一仓踩过的坑"的直接反控：若 --check 先写后比，
    篡改会被静默抹平，负控就永远抓不到差异。
    """
    copy = tmp_path / "bench-readonly-copy"
    shutil.copytree(BENCH_DIR, copy)

    truth_path = copy / "truth.json"
    payload = json.loads(truth_path.read_text(encoding="utf-8"))
    payload[0]["expect"]["location"] = "eq:FAKE-LOCATION"
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with open(truth_path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\r\n", "\n"))

    before = {
        p.relative_to(copy).as_posix(): p.read_bytes()
        for p in sorted(copy.rglob("*"))
        if p.is_file()
    }

    rc = check_benchmark(str(copy))
    assert rc != 0, "负控构造失败：篡改副本竟然通过了 --check"

    after = {
        p.relative_to(copy).as_posix(): p.read_bytes()
        for p in sorted(copy.rglob("*"))
        if p.is_file()
    }
    assert before == after, (
        "K20 违规: --check 修改了目标目录的内容——它必须是只读的"
        "（先写后比会把篡改静默抹平）"
    )
