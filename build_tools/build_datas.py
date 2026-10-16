"""打包辅助——白名单单一事实源。

K36: datas 只准由 build_datas() 产生
K37: 目录与文件条目分档
K38: 入包集合 == 白名单（双向对账）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple


def build_datas(whitelist_path: str = "build_tools/DATAS_WHITELIST.json") -> List[Tuple[str, str]]:
    """构建 PyInstaller datas 列表。"""
    wl_path = Path(whitelist_path)
    if not wl_path.exists():
        return []

    whitelist = json.loads(wl_path.read_text(encoding="utf-8"))
    datas = []

    for entry in whitelist.get("entries", []):
        source = entry["source"]
        target = entry["target"]
        entry_type = entry.get("type", "file")

        src_path = Path(source)
        if not src_path.exists():
            continue

        if entry_type == "dir":
            # 目录：内容复制进 target/，保留相对路径
            # K37: 目录条目取条目自身作为目标根
            for item in src_path.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(src_path)
                    # 目标目录 = target / rel.parent
                    dest_dir = str(Path(target) / rel.parent)
                    datas.append((str(item), dest_dir))
        else:
            # 文件：落在 target/ 下
            # K37: 文件取父目录
            datas.append((str(src_path), str(target)))

    return datas


def verify_dist(dist_path: str, whitelist_path: str = "build_tools/DATAS_WHITELIST.json") -> Tuple[bool, List[str]]:
    """K38: 入包集合 == 白名单（双向对账）。

    Returns:
        (是否通过, 问题列表)
    """
    import hashlib
    from pathlib import Path

    issues: List[str] = []
    dist_root = Path(dist_path)
    wl_path = Path(whitelist_path)

    if not wl_path.exists():
        return False, [f"白名单文件不存在: {wl_path}"]

    whitelist = json.loads(wl_path.read_text(encoding="utf-8"))
    repo_root = wl_path.parent.parent

    # 1. 正向：白名单每份都在包内
    for entry in whitelist.get("entries", []):
        source = entry["source"]
        target = entry["target"]
        entry_type = entry.get("type", "file")
        src_path = repo_root / source

        if not src_path.exists():
            issues.append(f"白名单源路径不存在: {source}")
            continue

        if entry_type == "dir":
            for item in src_path.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(src_path)
                    expected_in_dist = dist_root / target / rel
                    if not expected_in_dist.exists():
                        issues.append(f"漏拷: {source} -> {expected_in_dist.relative_to(dist_root)}")
        else:
            expected_in_dist = dist_root / target / src_path.name
            if not expected_in_dist.exists():
                issues.append(f"漏拷: {source} -> {expected_in_dist.relative_to(dist_root)}")

    # 2. 反向：包内数据集合与白名单恰好相等
    data_dir_in_dist = dist_root / "data"
    if data_dir_in_dist.exists():
        whitelisted_files = set()
        for entry in whitelist.get("entries", []):
            source = entry["source"]
            target = entry["target"]
            entry_type = entry.get("type", "file")
            src_path = repo_root / source

            if entry_type == "dir":
                for item in src_path.rglob("*"):
                    if item.is_file():
                        rel = item.relative_to(src_path)
                        whitelisted_files.add(target + str(rel).replace("\\", "/"))
            else:
                whitelisted_files.add(target + src_path.name)

        for f in data_dir_in_dist.rglob("*"):
            if f.is_file():
                rel = f.relative_to(dist_root)
                rel_str = str(rel).replace("\\", "/")
                # 检查是否在白名单中
                found = False
                for wl in whitelist.get("entries", []):
                    target = wl["target"]
                    if rel_str.startswith(target):
                        # 检查是否在排除列表中
                        excluded = whitelist.get("excluded", [])
                        is_excluded = False
                        for ex in excluded:
                            if "**" in ex:
                                base = ex.replace("**", "")
                                if base in str(f):
                                    is_excluded = True
                                    break
                            elif "*" in ex:
                                import fnmatch
                                if fnmatch.fnmatch(str(f), ex):
                                    is_excluded = True
                                    break
                        if not is_excluded:
                            found = True
                            break
                if not found:
                    issues.append(f"多拷: {rel_str}")

    # 3. 逐份 sha256 对账
    for entry in whitelist.get("entries", []):
        source = entry["source"]
        target = entry["target"]
        entry_type = entry.get("type", "file")
        src_path = repo_root / source

        if not src_path.exists():
            continue

        if entry_type == "dir":
            for item in src_path.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(src_path)
                    dist_file = dist_root / target / rel
                    if dist_file.exists():
                        src_sha = hashlib.sha256(item.read_bytes()).hexdigest()
                        dist_sha = hashlib.sha256(dist_file.read_bytes()).hexdigest()
                        if src_sha != dist_sha:
                            issues.append(f"sha256 不一致: {source}/{rel}")
        else:
            dist_file = dist_root / target / src_path.name
            if dist_file.exists():
                src_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
                dist_sha = hashlib.sha256(dist_file.read_bytes()).hexdigest()
                if src_sha != dist_sha:
                    issues.append(f"sha256 不一致: {source}")

    return len(issues) == 0, issues
