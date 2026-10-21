"""生成器入口。

K20「再生成位级一致」守门：`--check` 是**只读**模式——
重生成到临时目录，再与目标目录逐文件逐字节比对，**绝不写盘到 data/**。
（另一仓踩过"--check 把证据治好"的坑：先写后比，篡改被静默抹平。）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

from .truth_builder import generate_all


def main(output_dir: str = "data/benchmark", min_per_type: int = 3, clean_count: int = 3) -> None:
    """生成全部合成论文样本与真值台账。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    result = generate_all(out, min_per_type=min_per_type, clean_count=clean_count)

    # 落盘真值台账（行尾一律 LF：Windows 文本模式会注入 CRLF，
    # 破坏"任意平台重生成位级一致"；3.8 无 write_text(newline=)，走 open）
    _write_ledger(out, result)

    print(f"Generated {result['manifest']['total_samples']} samples")


def _write_ledger(out: Path, result) -> None:
    """把真值台账与 manifest 落盘到 out（LF 行尾）。

    main() 与 --check 的重生成共用同一条落盘路径，
    保证"比对的基准"与"生成的基准"是同一段代码（否则检查的是另一次实现）。
    """
    for name, payload in (
        ("truth.json", result["truth"]),
        ("manifest.json", result["manifest"]),
    ):
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        with open(out / name, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace("\r\n", "\n"))


def _collect_generated(root: Path) -> set:
    """收集生成器产出的相对路径集合（台账 2 个 + 每个样本的 paper.tex）。"""
    rels = {"truth.json", "manifest.json"}
    for tex in root.rglob("paper.tex"):
        rels.add(tex.relative_to(root).as_posix())
    return rels


def check_benchmark(
    benchmark_dir: str = "data/benchmark",
    min_per_type: int = 3,
    clean_count: int = 3,
) -> int:
    """只读校验：目标目录的内容与"按同样参数重生成"的结果逐字节一致。

    返回 0 = 一致；非 0 = 有差异（并打印差异清单）。
    任何情况下都**不写目标目录**。
    """
    target = Path(benchmark_dir)
    if not target.is_dir():
        print(f"[K20] 目标目录不存在: {target}")
        return 2

    with tempfile.TemporaryDirectory(prefix="mpra-regen-") as tmp:
        regen = Path(tmp) / "benchmark"
        regen.mkdir(parents=True, exist_ok=True)

        # 复用与 main() 完全相同的生成 + 落盘路径
        result = generate_all(regen, min_per_type=min_per_type, clean_count=clean_count)
        _write_ledger(regen, result)

        expected = _collect_generated(regen)

        missing = []
        differing = []
        for rel in sorted(expected):
            src = regen / rel
            dst = target / rel
            if not dst.is_file():
                missing.append(rel)
                continue
            if src.read_bytes() != dst.read_bytes():
                differing.append(rel)

        # 目标目录里多出来的 paper.tex（应不存在——多一个样本即真值库被手加）
        extra = []
        for tex in target.rglob("paper.tex"):
            rel = tex.relative_to(target).as_posix()
            if rel not in expected:
                extra.append(rel)

    if not (missing or differing or extra):
        print(
            f"[K20] 位级一致: {target} 的 {len(expected)} 个受控文件与重生成结果逐字节相同"
        )
        return 0

    if missing:
        print(f"[K20] 缺失 {len(missing)} 个文件（目标目录应含重生成产物的全部文件）:")
        for rel in missing[:20]:
            print(f"    MISSING  {rel}")
    if differing:
        print(f"[K20] 内容不一致 {len(differing)} 个文件:")
        for rel in differing[:20]:
            print(f"    DIFFER   {rel}")
    if extra:
        print(f"[K20] 目标目录多出 {len(extra)} 个 paper.tex（真值库被手加的样本）:")
        for rel in extra[:20]:
            print(f"    EXTRA    {rel}")
    return 1


def _cli(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m data.benchmark.generator",
        description="合成基准生成器（--check 为只读位级一致校验）",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="data/benchmark",
        help="生成输出目录（默认 data/benchmark）",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="只读校验：重生成到临时目录，与 --benchmark-dir 逐字节比对，不写目标目录",
    )
    parser.add_argument(
        "--benchmark-dir",
        default=None,
        help="--check 的比对目标目录（默认与位置参数 output_dir 相同）",
    )
    parser.add_argument("--min-per-type", type=int, default=3, help="每类错误样本数")
    parser.add_argument("--clean-count", type=int, default=3, help="干净样本数")
    args = parser.parse_args(argv)

    if args.check:
        target = args.benchmark_dir or args.output_dir
        return check_benchmark(
            target,
            min_per_type=args.min_per_type,
            clean_count=args.clean_count,
        )

    main(
        args.output_dir,
        min_per_type=args.min_per_type,
        clean_count=args.clean_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
