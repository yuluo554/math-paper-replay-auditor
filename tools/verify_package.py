"""发布前验证工具：跑真实 CLI 契约，断言退出码与关键输出。

历史（D1）：本工具早年是调 `[exe, "--selftest", <in.json>, <out.txt>]`
再读那个 out 文件——而真实的 exe **既不接受多余裸参数，也不写任何文件**，
于是它在任何 exe 上都抛 `FileNotFoundError`（exit 1），
"发布前验证工具"等于永久不可用 → 没人用 → 没有价值。

现在的契约（与 `src/auditor/cli.py` 的实际子命令一致）：
- CLI 冻结产物（auditor-cli.exe）：`selftest` 与 `bench` 都必须 rc==0，
  且输出含关键行（"自检通过" / "总体: 通过"）
- GUI 冻结产物（auditor.exe）：只跑 `--selftest`，rc==0 且输出含自检成功标志
- **在中立目录**执行（不许在仓库根下跑，否则会读到仓库里的 data/）
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

# CLI 子命令的必过标志（与 src/auditor/cli.py 的实际输出一致）
# 注意：CLI 版 `selftest` **成功时不打印任何东西**（失败才往 stderr 写"自检失败: ..."），
# 所以 CLI 的 selftest 判据是"rc==0 且输出里没有'自检失败'"；
# GUI 版 `--selftest` 成功时会打印 "=== 自检通过 ==="，用那个标志。
SELFTEST_FAIL_MARKER = "自检失败"
GUI_SELFTEST_MARKER = "自检通过"
BENCH_MARKERS = ("总体: 通过",)


def _run(exe: Path, args, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(exe), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _check_output(text: str, markers, label: str) -> bool:
    for m in markers:
        if m not in text:
            print(f"{label} 输出缺少关键标志 {m!r}：")
            print(text[:800])
            return False
    return True


def _check_no_failure(text: str, label: str) -> bool:
    """CLI 的 selftest 成功时静默；失败时 stderr 含"自检失败"。"""
    if SELFTEST_FAIL_MARKER in text:
        print(f"{label} 输出含失败标志 {SELFTEST_FAIL_MARKER!r}：")
        print(text[:800])
        return False
    return True


def verify_package(exe_path: str, gui_selftest: bool = False) -> bool:
    """验证打包产物（真契约：跑子命令、断言 rc 与关键输出）。

    Args:
        exe_path: 冻结产物路径。
        gui_selftest: True 表示 GUI 产物（只跑 `--selftest`）；
                      False 表示 CLI 产物（跑 `selftest` + `bench`）。
    """
    exe = Path(exe_path)
    if not exe.exists():
        print(f"exe 不存在: {exe}")
        return False

    # 中立目录：绝不在仓库根下跑（否则读到仓库里的 data/，测不到"内嵌数据"）
    with tempfile.TemporaryDirectory(prefix="mpra-verify-") as tmpdir:
        cwd = Path(tmpdir)

        if gui_selftest:
            result = _run(exe, ["--selftest"], cwd)
            if result.returncode != 0:
                print(f"自检失败: rc={result.returncode}")
                print(result.stdout[-800:])
                print(result.stderr[-800:])
                return False
            if not _check_output(result.stdout, (GUI_SELFTEST_MARKER,), "自检"):
                return False
            print(f"OK: {exe.name} --selftest 通过")
            return True

        # CLI 产物：selftest
        result = _run(exe, ["selftest"], cwd)
        if result.returncode != 0:
            print(f"selftest 失败: rc={result.returncode}")
            print(result.stdout[-800:])
            print(result.stderr[-800:])
            return False
        if not _check_no_failure(result.stdout + result.stderr, "selftest"):
            return False

        # CLI 产物：bench（真值库可达 + 检出率达标）
        bench = _run(exe, ["bench"], cwd)
        if bench.returncode != 0:
            print(f"bench 失败: rc={bench.returncode}")
            print(bench.stdout[-800:])
            print(bench.stderr[-800:])
            return False
        if not _check_output(bench.stdout, BENCH_MARKERS, "bench"):
            return False

        print(f"OK: {exe.name} selftest + bench 均通过")
        return True


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: python verify_package.py <exe_path> [--gui]")
        return 1
    gui = "--gui" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print("Usage: python verify_package.py <exe_path> [--gui]")
        return 1
    ok = True
    for p in paths:
        print(f"--- 验证 {p} ---")
        ok = verify_package(p, gui_selftest=gui) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
