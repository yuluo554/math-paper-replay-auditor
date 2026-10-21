"""K44: 留档只写类别与实算来源，不写词面值。

验证：
1. 留档文件不包含敏感词面值（真实邮箱、密钥样式串）
2. 留档目录与内容存在且非空

D7 修复：本文件此前算出 `real_emails` 后只写 `pass  # 允许，但记录`
（"记录"并不存在），第 3 项只在目录存在时断言 —— 即"留档里有真邮箱"也能全绿。
现在改为**无条件断言**：真的检出敏感词面值就变红。
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_DIR = REPO_ROOT / "plan"

# 明显是示例/占位的邮箱，予以放行
_EMAIL_ALLOWLIST = ("noreply", "example", "example.com", "example.org")

# scp 形态的 git 远端（git@host:org/repo.git）不是邮箱，放行
_SCP_GIT = re.compile(r"^git@[A-Za-z0-9.\-]+:[A-Za-z0-9._\-/]+$")

# 常见的"密钥样式"字面值（本仓不该出现）
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def _is_allowed_email(email: str) -> bool:
    low = email.lower()
    if any(token in low for token in _EMAIL_ALLOWLIST):
        return True
    # scp 形态的 git 远端（git@host:org/repo.git）不是邮箱，放行
    if email.startswith("git@") or email.startswith("ssh://"):
        return True
    return bool(_SCP_GIT.match(email))


def test_archive_files_no_hardcoded_secrets():
    """K44: 留档文件不得包含真实邮箱或密钥样式字面值。"""
    offenders = []
    for md_file in sorted(PLAN_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")

        emails = re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", content
        )
        for email in emails:
            if not _is_allowed_email(email):
                offenders.append(f"{md_file.relative_to(REPO_ROOT)}: 邮箱 {email}")

        for pattern in _SECRET_PATTERNS:
            for match in pattern.findall(content):
                offenders.append(
                    f"{md_file.relative_to(REPO_ROOT)}: 疑似密钥字面值 {match[:16]}…"
                )

    assert not offenders, (
        "K44 违规: 留档中不得写词面值（只写类别与实算来源）:\n"
        + "\n".join(offenders[:20])
    )


def test_archive_files_use_categories():
    """K44: 留档文件使用类别描述而非具体词面（内容不得为空）。"""
    handoff_files = sorted(PLAN_DIR.glob("HANDOFF-*.md"))
    assert handoff_files, "plan/ 下没有 HANDOFF-*.md 留档"

    for handoff_path in handoff_files:
        content = handoff_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"留档文件不应为空: {handoff_path.name}"


def test_verify_directory_exists():
    """K44: plan/verify/ 目录存在且是目录（用于留档）。"""
    verify_dir = PLAN_DIR / "verify"
    assert verify_dir.is_dir(), f"留档目录不存在: {verify_dir}"
    files = sorted(p.name for p in verify_dir.iterdir() if p.is_file())
    assert files, "留档目录里没有任何文件"
