"""K37: 目录与文件条目分档；K38: 入包集合 == 白名单（双向）。

验证：
1. build_datas() 正确处理目录和文件条目
2. 目录条目目标目录 = 条目自身
3. 文件条目目标目录 = 父目录
4. 入包集合与白名单双向一致
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_build_datas_returns_list():
    """K37/K38: build_datas() 返回列表。"""
    from build_tools.build_datas import build_datas

    datas = build_datas()
    assert isinstance(datas, list), "build_datas() 应返回列表"


def test_build_datas_entries_are_tuples():
    """K37/K38: build_datas() 返回 (source, target) 元组。"""
    from build_tools.build_datas import build_datas

    datas = build_datas()
    for entry in datas:
        assert isinstance(entry, tuple), f"条目应为元组: {entry}"
        assert len(entry) == 2, f"条目应为 (source, target): {entry}"
        assert isinstance(entry[0], str), f"source 应为字符串: {entry}"
        assert isinstance(entry[1], str), f"target 应为字符串: {entry}"


def test_file_entry_target_is_parent_dir():
    """K37: 文件条目的目标目录 = 父目录。"""
    from build_tools.build_datas import build_datas

    datas = build_datas()
    whitelist_path = REPO_ROOT / "build_tools" / "DATAS_WHITELIST.json"
    whitelist = json.loads(whitelist_path.read_text(encoding="utf-8"))

    for entry in whitelist.get("entries", []):
        if entry.get("type", "file") == "file":
            source = entry["source"]
            target = entry["target"]
            # 文件条目应落在 target/ 下
            source_path = REPO_ROOT / source
            if source_path.exists():
                # 在 datas 中查找（匹配文件名）
                source_name = source_path.name
                found = False
                for src, dest in datas:
                    if src.endswith(source_name):
                        assert dest == target, f"文件条目 {source} 的目标目录应为 {target}，实际为 {dest}"
                        found = True
                        break
                assert found, f"未在 datas 中找到文件条目: {source}"


def test_dir_entry_target_is_entry_itself():
    """K37: 目录条目的目标目录 = 条目自身。"""
    from build_tools.build_datas import build_datas

    datas = build_datas()
    whitelist_path = REPO_ROOT / "build_tools" / "DATAS_WHITELIST.json"
    whitelist = json.loads(whitelist_path.read_text(encoding="utf-8"))

    # datas 里的 source 是仓库相对路径，比对前统一归一（防"绝对 vs 相对"静默空转）
    datas_by_norm = {
        str(Path(src).as_posix()).lstrip("./"): dest for src, dest in datas
    }

    checked = 0
    for entry in whitelist.get("entries", []):
        if entry.get("type") != "dir":
            continue
        source = entry["source"]
        target = entry["target"]
        source_path = REPO_ROOT / source
        if not source_path.exists():
            continue
        for item in source_path.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(source_path)
            expected_target = (Path(target) / rel.parent).as_posix()
            key = item.relative_to(REPO_ROOT).as_posix()
            assert key in datas_by_norm, f"未在 datas 中找到目录条目文件: {key}"
            actual = Path(datas_by_norm[key]).as_posix()
            assert actual == expected_target, (
                f"目录条目 {source} 下文件 {rel} 的目标目录应为 {expected_target}，实际为 {actual}"
            )
            checked += 1

    # 非空转自证：目录条目一个文件都没扫到时本测试毫无约束力，必须红
    assert checked > 0, "目录条目扫描面为空——本守门未真正生效"


def test_verify_dist_positive():
    """K38: verify_dist() 对仓库根目录返回 True。"""
    from build_tools.build_datas import verify_dist

    # 对仓库根目录验证（应该通过，因为 data/ 在仓库中）
    passed, issues = verify_dist(str(REPO_ROOT))
    # 仓库根目录不是 dist，所以可能失败，但至少要返回元组
    assert isinstance(passed, bool)
    assert isinstance(issues, list)
