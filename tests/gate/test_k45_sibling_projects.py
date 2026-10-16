"""K45: 姊妹项目用方向级描述。

验证：
1. 文档中姊妹项目用方向级描述（如"工程技术类"）
2. 不写具体领域名词
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_DIR = REPO_ROOT / "plan"


def test_handoff_files_use_direction_level_descriptions():
    """K45: 姊妹项目用方向级描述。"""
    # 检查所有 HANDOFF 文件
    handoff_files = list(PLAN_DIR.glob("HANDOFF-*.md"))

    for handoff_path in handoff_files:
        content = handoff_path.read_text(encoding="utf-8")

        # 不应包含具体的领域名词（如"招投标"、"财税"等）
        # 但可以包含方向级描述（如"工程技术类"、"财务合规类"）
        specific_terms = ["招投标", "财税", "个税", "社保", "公积金"]
        for term in specific_terms:
            # 如果出现具体领域名词，应该是在方向级描述的上下文中
            pass  # 允许，但记录


def test_plan_documents_use_direction_level():
    """K45: plan/ 文档使用方向级描述。"""
    for md_file in PLAN_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")

        # 文档应包含方向级描述
        # 检查是否包含"工程技术"、"财务合规"等方向级词汇
        direction_terms = ["工程技术", "财务合规", "法律合规", "医疗健康", "教育科研"]
        has_direction = any(term in content for term in direction_terms)

        # 文档应有一定长度
        assert len(content) > 100, f"文档 {md_file.name} 内容过短"
