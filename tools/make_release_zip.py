"""打包 Release 附件（v0.1.1 起）。

产物（与 plan/05 §5.2 声明逐名一致）：
  auditor-v<tag>-win64.zip          双 exe + 数据
  auditor-v<tag>-win64-sha256.txt   sha256 台账
  demo-clean-vs-error.gif           演示 GIF
  demo-clean-report.html            干净论文报告
  demo-error-report.html            含错论文报告
  auditor-source-v<tag>.zip         源码包（git archive from tag）

用法：
    python tools/make_release_zip.py --tag v0.1.1
    python tools/make_release_zip.py --tag v0.1.1 --no-source
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
FIXED_DATE_TIME = (2026, 1, 1, 0, 0, 0)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_zip(sources, zip_path: Path, arc_root: str) -> Path:
    """确定性 zip：ZIP_STORED + 条目排序 + 固定时间戳。"""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for path in sorted(sources, key=lambda p: Path(p).name):
            path = Path(path)
            info = zipfile.ZipInfo(f"{arc_root}/{path.name}", date_time=FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o755 << 16 if path.suffix.lower() == ".exe" else 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return zip_path


def main(argv=None) -> int:
    from auditor._encoding import ensure_utf8_stdio

    ensure_utf8_stdio()

    ap = argparse.ArgumentParser(description="打包 Release 附件")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--dist", type=Path, default=REPO_ROOT / "dist")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "release")
    ap.add_argument("--no-source", action="store_true", help="不生成源码包")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    demo = REPO_ROOT / "docs" / "demo"

    # 1) 双 exe + 数据 → zip
    exes = [args.dist / "auditor.exe", args.dist / "auditor-cli.exe"]
    missing = [str(p) for p in exes if not p.is_file()]
    if missing:
        print(f"错误：缺少构建产物 {missing}", file=sys.stderr)
        return 1
    zip_path = args.out / f"auditor-{args.tag}-win64.zip"
    build_zip(exes, zip_path, "auditor")
    print(f"✅ {zip_path.name}  {zip_path.stat().st_size} 字节")

    # 2) 演示素材（文件名与 plan/05 声明一致）
    demo_map = {
        "demo.gif": "demo-clean-vs-error.gif",
        "demo-clean.html": "demo-clean-report.html",
        "demo-error.html": "demo-error-report.html",
    }
    for src_name, dst_name in demo_map.items():
        src = demo / src_name
        if not src.is_file():
            print(f"错误：缺演示素材 {src}（先跑 tools/make_demo_assets.py）", file=sys.stderr)
            return 1
        shutil.copy2(src, args.out / dst_name)
        print(f"✅ {dst_name}")

    # 3) 源码包（from tag 树，杜绝 dist/build 混入）
    if not args.no_source:
        source_zip = args.out / f"auditor-source-{args.tag}.zip"
        proc = subprocess.run(
            ["git", "archive", "--format=zip",
             f"--prefix=math-paper-replay-auditor/", "-o", str(source_zip), args.tag],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"错误：git archive 失败：{proc.stderr}", file=sys.stderr)
            return 1
        print(f"✅ {source_zip.name}  {source_zip.stat().st_size} 字节")

    # 4) sha256 台账
    sums = args.out / f"auditor-{args.tag}-win64-sha256.txt"
    entries = []
    for path in sorted(args.out.glob("*")):
        if path.is_file() and path.name != sums.name:
            entries.append(f"{_sha256(path)}  {path.name}")
    sums.write_text("\n".join(entries) + "\n", encoding="utf-8")
    print(f"✅ {sums.name}")

    print(json.dumps(sorted(p.name for p in args.out.glob("*")),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
