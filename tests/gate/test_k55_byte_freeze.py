"""K55: 文本行尾冻结（LF）与 zip 容器字节冻结。

skill 要求"字节冻结分层设防"：
- 文本行尾：源码与数据一律 LF，配 CR 守门（Windows 文本模式会静默注入 CRLF）
- zip 容器：ZIP_STORED + 固定 date_time + 条目排序，使"同输入双跑逐字节一致"

本守门覆盖第一层（文本行尾）；第二层在 zip 打包工具里由 K21 约束。
"""

from __future__ import annotations

import ast
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

TEXT_SUFFIXES = {
    ".py", ".md", ".json", ".yml", ".yaml", ".toml",
    ".tex", ".txt", ".cfg", ".html", ".css", ".js",
}

# 不入扫描面：构建产物、虚拟环境、缓存、git 内部、外部依赖
SKIP_PARTS = {
    ".git", ".cleanenv", ".venv", "venv", "build", "dist",
    "__pycache__", ".pytest_cache", ".eggs", "node_modules",
    # 发布产物目录（由 tools/make_release_zip.py 生成；源件在 docs/demo/ 下受本守门覆盖）
    "release",
    # 过程文档目录（迭代诊断交接物；与 K46 的排除名单保持同一口径，
    # 见 plan/RELEASE-M8.md）
    "update",
}


def _iter_text_files():
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_SUFFIXES:
            yield p


def test_k55_no_crlf_in_text_sources():
    """K55: 源码与数据文件不得含 CRLF（.gitattributes 声明 eol=lf）。"""
    offenders = []
    for p in _iter_text_files():
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\r\n" in data:
            offenders.append(str(p.relative_to(REPO_ROOT)))

    assert not offenders, (
        "K55 违规: 以下文本文件含 CRLF（Windows 文本模式注入，"
        "会破坏跨平台位级一致）:\n" + "\n".join(offenders[:20])
    )


def test_k55_generated_data_is_lf():
    """K55: 生成器产物（样本与真值库）必须是 LF——直接验 K20 位级一致的前提。"""
    bench = REPO_ROOT / "data" / "benchmark"
    if not bench.exists():
        pytest.skip("基准数据目录不存在")

    offenders = []
    for p in bench.rglob("*"):
        if p.is_file() and p.suffix in (".tex", ".json"):
            if b"\r\n" in p.read_bytes():
                offenders.append(str(p.relative_to(REPO_ROOT)))

    assert not offenders, (
        "K55 违规: 生成器产物含 CRLF:\n" + "\n".join(offenders[:20])
    )


def _is_zip_writer(text: str) -> bool:
    """判断该文件是否**写** zip（只读 zip 不影响打包确定性）。

    原判据是"文件里出现 zipfile.ZipFile 就算写 zip"——这会误伤
    "只读取 wheel 内容做校验"的代码（如 tests/gate/test_k58_installed_usable.py：
    它 `zipfile.ZipFile(wheel).namelist()` 只读，不产生任何字节）。
    这里改为按调用形态判定：只有**以写模式**打开 ZipFile 才算 zip writer。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "ZipFile"):
            continue
        # 位置参数第 2 个是 mode；关键字参数 mode= 亦可
        mode = None
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            mode = node.args[1].value
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if mode in ("w", "a", "x"):
            return True
    return False


def test_k55_zip_helpers_use_stored_and_fixed_mtime():
    """K55: 若仓库内**写** zip，必须 ZIP_STORED + 固定 date_time。

    防"打包确定性"落空：ZIP_DEFLATED 的压缩流与当前时间都会让
    同一个输入打出不同字节。

    只读 zip（校验 wheel 内容）不受此约束——它不产生任何字节。
    """
    offenders = []
    for p in REPO_ROOT.rglob("*.py"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if "zipfile.ZipFile" not in text and "ZipFile(" not in text:
            continue
        if not _is_zip_writer(text):
            continue
        if "ZIP_STORED" not in text:
            offenders.append(f"{p.relative_to(REPO_ROOT)}: 未用 ZIP_STORED")
        if "date_time" not in text:
            offenders.append(f"{p.relative_to(REPO_ROOT)}: 未固定 date_time")

    assert not offenders, "K55 违规:\n" + "\n".join(offenders)
