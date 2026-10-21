"""K59: 发布附件的 sha256 台账必须能在 Linux 上直接校验。

D15（本轮新发现，非原诊断项）：`tools/make_release_zip.py` 写台账时用
`write_text()`——Windows 上默认把 `\\n` 翻成 `\\r\\n`，于是**发布出去的台账是 CRLF**。
后果（实测）：`sha256sum -c auditor-v0.1.2-win64-sha256.txt` 在 Linux/Git Bash 上
逐条报 `FAILED open or read`（`\r` 被当成文件名的一部分），
即"给用户的那把尺子"在用户那边是坏的。v0.1.1 的台账同样是 CRLF（潜伏至今）。

本门把这条钉死：
1. 台账生成器写出的字节必须是 LF（不依赖运行平台的默认换行）
2. 台账里的每一条 sha256 都必须与当前 `release/` 下的文件实算一致
3. 格式必须是 GNU coreutils 认的 `<sha256>␠␠<name>`（两个空格、无 `*` 前缀）
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = REPO_ROOT / "release"
MAKE_ZIP = REPO_ROOT / "tools" / "make_release_zip.py"

# GNU sha256sum 认的格式：<64 hex> + 两个空格 + 文件名（无二进制标记 '*'）
_LEDGER_LINE = re.compile(r"^([0-9a-f]{64})  (\S+)$")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_ledger_generator_writes_lf_only():
    """K59: 台账生成器必须显式写 LF（不能依赖平台默认换行）。"""
    source = MAKE_ZIP.read_text(encoding="utf-8")
    # 找写台账的那一段
    assert "sha256.txt" in source, "未找到台账生成逻辑"
    segment = source[source.index("sha256.txt"):][:1200]
    assert 'newline=""' in segment, (
        "K59 违规: 写 sha256 台账时未显式 newline=\"\"——"
        "Windows 上 write_text() 会把 \\n 翻成 \\r\\n，"
        "导致 `sha256sum -c` 在 Linux 上逐条 FAILED open or read"
    )


def test_existing_ledgers_are_lf_only():
    """K59: 已产出的台账（若存在）不得含 CRLF。"""
    if not RELEASE_DIR.is_dir():
        return
    ledgers = sorted(RELEASE_DIR.glob("*-sha256.txt"))
    offenders = []
    for p in ledgers:
        if b"\r\n" in p.read_bytes():
            offenders.append(p.name)
    assert not offenders, (
        "K59 违规: sha256 台账含 CRLF（Linux 上 `sha256sum -c` 会失败）: "
        + ", ".join(offenders)
    )


def test_ledger_format_is_gnu_compatible():
    """K59: 台账每一行都必须是 GNU coreutils 认的格式。"""
    if not RELEASE_DIR.is_dir():
        return
    ledgers = sorted(RELEASE_DIR.glob("*-sha256.txt"))
    for ledger in ledgers:
        text = ledger.read_bytes().decode("utf-8")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        assert lines, f"台账为空: {ledger.name}"
        for line in lines:
            m = _LEDGER_LINE.match(line)
            assert m, (
                f"K59 违规: 台账 {ledger.name} 的行不符合 `<sha256>␠␠<name>` 格式: {line!r}"
            )


def test_ledger_hashes_match_actual_files():
    """K59: 台账里的 sha256 必须与实际文件逐条一致。"""
    if not RELEASE_DIR.is_dir():
        return
    ledgers = sorted(RELEASE_DIR.glob("*-sha256.txt"))
    problems = []
    for ledger in ledgers:
        text = ledger.read_bytes().decode("utf-8")
        for line in [ln for ln in text.splitlines() if ln.strip()]:
            m = _LEDGER_LINE.match(line)
            if not m:
                problems.append(f"{ledger.name}: 格式错: {line!r}")
                continue
            expected, name = m.group(1), m.group(2)
            target = RELEASE_DIR / name
            if not target.is_file():
                problems.append(f"{ledger.name}: 指向不存在的文件 {name}")
                continue
            actual = _sha256(target)
            if actual != expected:
                problems.append(
                    f"{ledger.name}: {name} 的 sha256 不符\n"
                    f"    台账: {expected}\n    实算: {actual}"
                )
    assert not problems, "K59 违规:\n" + "\n".join(problems)
