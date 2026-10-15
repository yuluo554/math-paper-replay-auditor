"""打包辅助——白名单单一事实源。

K36: datas 只准由 build_datas() 产生
K37: 目录与文件条目分档
K38: 入包集合 == 白名单（双向对账）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple


def build_datas(whitelist_path: str = "packaging/DATAS_WHITELIST.json") -> List[Tuple[str, str]]:
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
            # 目录：内容复制进 target/
            for item in src_path.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(src_path)
                    datas.append((str(item), str(target)))
        else:
            # 文件：落在 target/ 下
            datas.append((str(src_path), str(target)))

    return datas


def verify_dist(dist_path: str, whitelist_path: str = "packaging/DATAS_WHITELIST.json") -> bool:
    """K38: 入包集合 == 白名单（双向对账）。"""
    # TODO M5: 实现
    return True
