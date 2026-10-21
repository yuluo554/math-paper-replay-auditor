"""K57: 自述与实现一致（README 承诺的东西必须真的存在 / 真没做要说清）。

D6/D8/D9 的守门化：此前这三处都靠"人肉核对 README"，没有任何门：

- D6：README 写 `docs/demo/demo-clean-report.html`，仓内实际是 `demo-clean.html`
  （K47 只查 `--input/--output` 形态的路径，反引号里的相对路径无人查）
- D8：`fetch` 子命令恒 exit 3（`src/auditor/fetch/` 根本不存在），
  而 README 全文 0 命中 "fetch"——`--help` 里却列着它
- D9：`data/real_papers/registry.json` 只有一条占位记录，
  README 却写 `data/ # 数据（合成基准 + 真实论文元数据）`

本门把三条承诺钉成断言。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"
DATA_README = REPO_ROOT / "data" / "README.md"
REGISTRY = REPO_ROOT / "data" / "real_papers" / "registry.json"


def _readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_declares_fetch_unimplemented():
    """K57: README 必须明写 fetch 子命令未实现（否则 --help 里的它会误导人）。"""
    text = _readme()
    assert "fetch" in text, "README 必须提及 fetch 子命令"
    assert "未实现" in text, "README 必须明写 fetch 是未实现的功能"
    # 且不能再说成"需联网开关"（那会让人以为开个开关就能用）
    assert "需联网开关" not in text, (
        "README 不得把 fetch 描述成『需联网开关』——它根本没实现"
    )


def test_fetch_module_really_absent_or_really_present():
    """K57: fetch 的"未实现"声明必须与代码事实一致。

    若将来真的实现了 `src/auditor/fetch/`，本门会失败——那时应当
    改 README 的措辞（而不是让声明悄悄过期）。
    """
    fetch_pkg = REPO_ROOT / "src" / "auditor" / "fetch"
    implemented = fetch_pkg.is_dir() and any(fetch_pkg.glob("*.py"))
    if implemented:
        pytest.skip("fetch 已实现，请更新 README 的'未实现'措辞并重写本门")
    assert not implemented, "fetch 包已存在但 README 仍写未实现——措辞过期了"


def test_readme_declares_real_papers_not_delivered():
    """K57: README 必须声明真实论文回归集尚未交付。"""
    text = _readme()
    assert "real_papers" in text or "真实论文回归集" in text, (
        "README 必须交代 data/real_papers/ 的交付状态"
    )
    assert "尚未交付" in text or "未交付" in text or "占位" in text, (
        "README 必须明写真实论文回归集尚未交付（当前只有占位记录）"
    )


def test_data_readme_declares_placeholder_status():
    """K57: data/README.md 必须声明 registry.json 是占位记录。"""
    text = DATA_README.read_text(encoding="utf-8")
    assert "占位" in text, "data/README.md 必须明写 registry.json 当前是占位记录"
    assert "尚未交付" in text, "data/README.md 必须明写真实论文回归集尚未交付"


def test_registry_is_documented_as_placeholder():
    """K57: registry.json 里的占位记录必须与自述一致（不得有真论文却仍说未交付）。"""
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    papers = payload.get("papers", [])
    assert papers, "registry.json 的 papers 列表不应为空"

    placeholders = [
        p for p in papers
        if "XXXX" in str(p.get("paper_id", "")) or p.get("local_parse_sha256") is None
    ]
    if not placeholders:
        # 有真实条目 → README 的"尚未交付"措辞必须改
        pytest.fail(
            "registry.json 里已有非占位记录，但 README 仍称'尚未交付'——"
            "自述与事实不符，请更新 README 与 data/README.md"
        )

    # 占位记录必须自带说明，不得看起来像一条真实论文
    for p in placeholders:
        notes = str(p.get("notes", ""))
        assert notes, "占位记录必须带 notes 说明"
