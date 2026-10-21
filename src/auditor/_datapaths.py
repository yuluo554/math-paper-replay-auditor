"""数据根定位（装态 / 源码态 / 冻结态三形态）。

D2：此前 wheel/sdist 里 `data/` 命中 0，非 editable 安装后：
    selftest → "自检失败: 内嵌数据不可达（data\\benchmark\\truth.json）" exit 1
    bench    → "错误: 真值库不存在: data\\benchmark\\truth.json" exit 2
即"pip 装完不能用"。DEC2 选 A：把 data 打进 wheel。

打包后数据装在 **`auditor.data`** 子包里（不装成顶层 `data` 包，
以免往 site-packages 塞一个极易撞名的泛化包名），
故装态下 `<root>` = site-packages 根，`<root>/data/...` 不成立——
真正可达的是 `<root>/auditor/data/...`。为让三种形态的**相对路径形状**一致
（K52 要求冻结态与源码态结构完全相同），装态下用 `auditor/data` 作为数据根，
并由 `_data_root_relative_to()` 把 `data/benchmark/...` 映射成
`auditor/data/benchmark/...`。

本模块提供**唯一**的装态定位入口，三处调用点
（`pipeline._data_root` / `benchmark.runner._get_root` / `gui.main_window._data_root`）
共用它；**三处原有的 `sys._MEIPASS` 冻结态分支一律不动**（K52 依赖它）。

三种形态：

| 形态 | 数据根 | 判定方式 |
|---|---|---|
| 冻结态（PyInstaller） | `sys._MEIPASS` | `sys.frozen` + `_MEIPASS`（**不变**） |
| 源码态（仓库根运行） | `Path(".")` | 当前目录下有 `data/benchmark/truth.json` |
| 装态（pip 装 wheel） | `<site-packages>/auditor/data` | `auditor.data` 包存在且带数据 |
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# 装态下随包分发的数据标记文件（用它确认"这个包确实带数据"）
_DATA_MARKER = Path("benchmark") / "truth.json"

# 装态下的数据包子包名（打包映射见 pyproject.toml 的 package-dir）
_INSTALLED_DATA_PACKAGE = "auditor.data"


def _frozen_root() -> Optional[Path]:
    """冻结态数据根（sys._MEIPASS）。**本轮不改这里的语义。**"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return None


def installed_data_root() -> Optional[Path]:
    """装态数据根：随 wheel 安装的 `auditor.data` 包所在目录。

    返回 None 表示"装态但找不到带数据的 data 包"（例如只装了代码没装数据）。
    """
    try:
        from importlib.util import find_spec
    except ImportError:  # pragma: no cover
        return None

    try:
        spec = find_spec(_INSTALLED_DATA_PACKAGE)
    except (ImportError, ValueError):  # pragma: no cover
        return None
    if spec is None:
        return None

    locations = list(getattr(spec, "submodule_search_locations", None) or [])
    if not locations:
        return None

    pkg_dir = Path(locations[0])
    if not (pkg_dir / _DATA_MARKER).exists():
        # 找到了同名但不带数据的包 —— 不当成本仓的数据
        return None

    # 返回 **包的父目录**，使 <root>/data/benchmark/truth.json 成立——
    # 与源码态（仓库根）、冻结态（_MEIPASS）**形状完全一致**，
    # 真值台账里的仓库相对路径（data/benchmark/...）在三种形态下都能直接拼。
    return pkg_dir.parent


def source_data_root() -> Optional[Path]:
    """源码态数据根：当前工作目录（其下须有 data/benchmark/truth.json）。"""
    cwd = Path(".")
    if (cwd / "data" / _DATA_MARKER).exists():
        return cwd
    return None


def resolve_data_root() -> Path:
    """统一的数据根解析。

    优先级：冻结态（_MEIPASS）→ 源码态（CWD）→ 装态（auditor.data 包）。
    都不命中时回落到 `Path(".")`，由调用点按"数据不可达"处理（并给出可执行指引）。
    """
    frozen = _frozen_root()
    if frozen is not None:
        return frozen

    source = source_data_root()
    if source is not None:
        return source

    installed = installed_data_root()
    if installed is not None:
        return installed

    return Path(".")


def data_unreachable_hint() -> str:
    """数据不可达时的可执行指引（装完不能用是最难查的一类问题）。"""
    return (
        "数据不可达的三种可能：(1) 用了 pip 安装且该版本未携带数据 —— "
        "请改用免安装 exe，或从仓库根运行（data/ 在仓库内）；"
        "(2) 不在仓库根目录运行 —— 请 cd 到仓库根再执行；"
        "(3) data/ 被删除或未随包分发。"
    )
