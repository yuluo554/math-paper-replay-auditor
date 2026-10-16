"""K43: HANDOFF 库内写相对路径（脱敏硬门）。

M6 实录：原版守门遇到"含盘符路径 + 引号"就放行（本意是容忍 /goal 启动命令
前缀里的绝对路径），结果**整条绝对路径启动命令被原样留在 HANDOFF 文件里**，
并随公开仓库发布——正是 skill 点名的脱敏泄漏形态。

根因是判据写成了"这一行有没有引号"（笼统），而不是"这条路径是不是本机绝对路径"
（该守的东西）。修正后的判据：**HANDOFF 文件内任何位置都不得出现盘符绝对路径**
（库内一律相对路径；绝对路径只存在于用户侧会话启动命令，不入库）。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_DIR = REPO_ROOT / "plan"

# 判据设计（锚"本机真实路径"，不锚形状）：
# 真泄漏 = 盘符 + 具体路径段（如 D:\[开发机盘符目录]\...、C:\Users\x\...）；
# 占位符与正则口径（`X:/`、`[A-Za-z]:[\\/]`、`https:/`）不算——
# 它们描述"要查什么形态"，不是本机实际路径。
DRIVE_ABS = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s`\)\]]")
# 用户目录形态：\Users\<name>\ 或 /home/<name>/（用户名属个人标记）
HOME_DIR = re.compile(r"[\\/](?:Users|home)[\\/][^\\/\s\"']+")

# 允许的例外：脱敏扫描器自身的"口径/复盘"描述行——
# 这些行在**说明要查什么形态**（占位符或正则），不是本机真实路径。
# 判据锚在"本机真实路径"，故用仓库专属标记（本机盘符目录名）而非形状匹配。
ALLOWED_MARKERS = (
    "git grep -E",          # 扫描器正则行
    "git grep … --",        # 扫描失败复盘行
    "宽口径 ",              # 扫描口径说明行
    "收紧为 ",              # 扫描口径说明行
    "LOW 本机路径",         # 扫描口径说明行
    "不写 ",                # 约定说明行
)


def _handoff_files():
    return sorted(PLAN_DIR.glob("HANDOFF-*.md"))


def test_handoff_files_exist():
    """K43: 所有 HANDOFF 文件存在。"""
    expected = ["HANDOFF-M1.md", "HANDOFF-M2.md", "HANDOFF-M3.md",
                "HANDOFF-M4.md", "HANDOFF-M5.md", "HANDOFF-M6.md"]
    for name in expected:
        assert (PLAN_DIR / name).exists(), f"HANDOFF 文件不存在: {name}"


def test_handoff_files_use_relative_paths():
    """K43: HANDOFF 文件内不得出现任何盘符绝对路径（含引号内的启动命令）。"""
    offenders = []
    for path in _handoff_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not DRIVE_ABS.search(line):
                continue
            if any(marker in line for marker in ALLOWED_MARKERS):
                continue
            offenders.append(f"{path.name}:{lineno}: {line.strip()[:100]}")

    assert not offenders, (
        "K43 违规: HANDOFF 含本机绝对路径（库内一律相对路径；"
        "绝对路径只出现在用户侧会话启动命令，不入库）:\n" + "\n".join(offenders)
    )


def test_handoff_files_have_no_home_directory_markers():
    """K43: HANDOFF 不得含用户目录标记（个人标记脱敏）。"""
    offenders = []
    for path in _handoff_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if HOME_DIR.search(line):
                offenders.append(f"{path.name}:{lineno}: {line.strip()[:100]}")

    assert not offenders, (
        "K43 违规: HANDOFF 含用户目录标记:\n" + "\n".join(offenders)
    )


def test_handoff_has_relative_usage_line():
    """K43: 每个 HANDOFF 必须有一条相对路径的用法行（非空转自证）。"""
    for path in _handoff_files():
        text = path.read_text(encoding="utf-8")
        assert f"plan/{path.name}" in text, (
            f"K43: {path.name} 未见相对路径用法行 plan/{path.name}"
        )


def test_plan_documents_have_no_drive_paths():
    """K43: plan/ 全目录（不止 HANDOFF）不得含盘符绝对路径。"""
    offenders = []
    for path in sorted(PLAN_DIR.rglob("*.md")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not DRIVE_ABS.search(line):
                continue
            if any(marker in line for marker in ALLOWED_MARKERS):
                continue
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")

    assert not offenders, (
        "K43 违规: plan/ 文档含盘符绝对路径:\n" + "\n".join(offenders[:20])
    )
