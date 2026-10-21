"""K45: 姊妹项目用方向级描述。

验证：
1. 文档中姊妹项目用方向级描述（如"工程技术类"）
2. 不写具体领域名词

D7 修复：本文件此前算出 `has_direction` 却**从不使用**，最后只断言
`len(content) > 100` —— 只要文件够长就绿，"方向级描述"这个承诺从未被检查。
现在：只要文档里**出现了**具体领域名词且**没有**方向级描述兜底，就变红。
（方向级描述 = 允许出现的具体名词所属的"类"。）
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_DIR = REPO_ROOT / "plan"

# 方向级描述词（出现其一即视为"已用方向级口径"）
DIRECTION_TERMS = (
    "工程技术",
    "财务合规",
    "法律合规",
    "医疗健康",
    "教育科研",
    "工程",
    "合规",
)

# 具体领域名词（只允许在方向级描述的上下文里出现）
SPECIFIC_TERMS = ("招投标", "财税", "个税", "社保", "公积金")


def test_plan_documents_use_direction_level():
    """K45: plan/ 文档出现具体领域名词时，必须有方向级描述兜底。"""
    offenders = []
    for md_file in sorted(PLAN_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")

        assert len(content) > 100, f"文档 {md_file.name} 内容过短"

        hit_terms = [t for t in SPECIFIC_TERMS if t in content]
        if not hit_terms:
            continue

        has_direction = any(term in content for term in DIRECTION_TERMS)
        if not has_direction:
            offenders.append(
                f"{md_file.name}: 出现具体领域名词 {hit_terms} 但全文无方向级描述"
            )

    assert not offenders, (
        "K45 违规: 姊妹项目必须用方向级描述（具体领域名词须有方向级口径兜底）:\n"
        + "\n".join(offenders[:20])
    )


def test_handoff_files_use_direction_level_descriptions():
    """K45: HANDOFF 留档同样受方向级口径约束。"""
    handoff_files = sorted(PLAN_DIR.glob("HANDOFF-*.md"))
    assert handoff_files, "plan/ 下没有 HANDOFF-*.md 留档"

    offenders = []
    for handoff_path in handoff_files:
        content = handoff_path.read_text(encoding="utf-8")
        hit_terms = [t for t in SPECIFIC_TERMS if t in content]
        if not hit_terms:
            continue
        if not any(term in content for term in DIRECTION_TERMS):
            offenders.append(
                f"{handoff_path.name}: 出现具体领域名词 {hit_terms} 但无方向级描述"
            )

    assert not offenders, (
        "K45 违规: HANDOFF 留档必须用方向级描述:\n" + "\n".join(offenders[:20])
    )
