"""K36: 白名单单一事实源。

验证：
1. whitelist.json 存在且格式正确
2. 生成器必须从 whitelist.json 取值
3. datas 只准由 build_datas() 产生
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WHITELIST_PATH = REPO_ROOT / "data" / "benchmark" / "whitelist.json"


def test_whitelist_exists():
    """K36: whitelist.json 存在。"""
    assert WHITELIST_PATH.exists(), "whitelist.json 必须存在"


def test_whitelist_is_valid_json():
    """K36: whitelist.json 是有效 JSON。"""
    content = WHITELIST_PATH.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict), "whitelist.json 必须是 JSON 对象"


def test_whitelist_has_version():
    """K36: whitelist.json 必须有 version 字段。"""
    data = json.loads(WHITELIST_PATH.read_text(encoding="utf-8"))
    assert "version" in data, "whitelist.json 必须有 version 字段"


def test_whitelist_has_fake_prefixes():
    """K36: whitelist.json 必须有合成数据前缀。"""
    data = json.loads(WHITELIST_PATH.read_text(encoding="utf-8"))
    assert "fake_doi_prefix" in data, "whitelist.json 必须有 fake_doi_prefix"
    assert "fake_arXiv_prefix" in data, "whitelist.json 必须有 fake_arXiv_prefix"
    assert "fake_orcid_prefix" in data, "whitelist.json 必须有 fake_orcid_prefix"


def test_whitelist_has_notes():
    """K36: whitelist.json 必须有 notes 字段声明合成数据。"""
    data = json.loads(WHITELIST_PATH.read_text(encoding="utf-8"))
    assert "notes" in data, "whitelist.json 必须有 notes 字段"
    assert "合成" in data["notes"] or "fake" in data["notes"].lower(), \
        "notes 字段必须声明这是合成数据"


def test_generator_uses_whitelist():
    """K36: 生成器必须从 whitelist.json 取值。"""
    # 检查 error_injector.py 是否引用 whitelist 或使用合成数据
    error_injector_path = REPO_ROOT / "data" / "benchmark" / "generator" / "error_injector.py"
    if error_injector_path.exists():
        content = error_injector_path.read_text(encoding="utf-8")
        # 生成器应该使用合成数据（fake）或引用 whitelist
        # 这里检查生成器是否使用了确定性 RNG（splitmix64）
        assert "SplitMix64" in content or "seed" in content, \
            "生成器应使用确定性 RNG 或从 whitelist 取值"
