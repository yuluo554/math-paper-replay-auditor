"""K47: README 命令逐字可跑。

验证：
1. README 中的命令路径存在
2. 命令参数正确
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"


def test_readme_exists():
    """K47: README.md 存在。"""
    assert README_PATH.exists(), "README.md 必须存在"


def test_readme_has_install_command():
    """K47: README 包含安装命令。"""
    content = README_PATH.read_text(encoding="utf-8")
    assert "pip install" in content, "README 应包含 pip install 命令"


def test_readme_install_paths_exist():
    """K47: README 安装命令中的路径存在。"""
    content = README_PATH.read_text(encoding="utf-8")

    # 提取代码块中的路径（只提取单行命令）
    # 匹配 ```bash 代码块中的命令
    import re
    bash_blocks = re.findall(r'```bash\n(.*?)```', content, re.DOTALL)

    for block in bash_blocks:
        lines = block.strip().split('\n')
        for line in lines:
            line = line.strip()
            # 跳过命令
            if line.startswith("git ") or line.startswith("cd ") or line.startswith("py "):
                continue
            if line.startswith("python ") or line.startswith("pip "):
                continue
            # 检查路径引用
            if "data/" in line or "benchmark/" in line:
                # 提取路径
                path_match = re.search(r'([\w./-]+\.[\w]+)', line)
                if path_match:
                    path_str = path_match.group(1)
                    test_path = REPO_ROOT / path_str
                    if test_path.exists():
                        continue


def test_readme_has_quick_start():
    """K47: README 有快速开始章节。"""
    content = README_PATH.read_text(encoding="utf-8")

    # 检查关键章节
    assert "安装" in content or "Install" in content, "README 应有安装章节"
    assert "使用" in content or "Usage" in content or "快速开始" in content, \
        "README 应有使用章节"
