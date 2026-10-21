"""K58: pip 渠道「装完能用」（非 editable 安装）。

D2：本仓此前 wheel/sdist 里 `data/` 命中 0，非 editable 安装后
    selftest → "自检失败: 内嵌数据不可达" exit 1
    bench    → "错误: 真值库不存在" exit 2
即"pip 装完不可用"。DEC2 选 A：把 data 打进 wheel。

本门是**发布前的真实安装验证**：构建 wheel → 装进一个干净的临时 venv →
在中立目录（非仓库根）跑 selftest / bench / audit，断言退出码与 README 一致。

为什么必须真实安装而不是"看 wheel 里有几个文件"：
- 「wheel 含数据条目」不等于「装完能定位到数据」（定位逻辑要另测）；
- 本门跑的是**中立目录**，因此它同时证明了"不依赖 CWD"。

若本机没有可用的 pip / 网络（安装需从本地 wheel，不需网络），本门会 skip；
skip 是"未验证"，不是"通过"。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _build_wheel(outdir: Path) -> Path:
    """构建 wheel（用本机 python -m build；不可用时抛 pytest.skip）。"""
    try:
        import build  # noqa: F401
    except ImportError:
        pytest.skip("本机未安装 build（pip install build）——本门未验证")

    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"构建 wheel 失败:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")

    wheels = sorted(outdir.glob("*.whl"))
    assert wheels, "未产出 wheel"
    return wheels[-1]


def _wheel_contains_data(wheel: Path) -> bool:
    names = zipfile.ZipFile(wheel).namelist()
    return (
        sum(1 for n in names if n.endswith("paper.tex")) >= 18
        and any(n.endswith("benchmark/truth.json") for n in names)
    )


def _install_and_run(wheel: Path, workdir: Path):
    """装进干净 venv，在中立目录跑三条命令，返回 (selftest_rc, bench_rc, audit_rc)。"""
    venv_dir = workdir / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )
    python = venv_dir / "Scripts" / "python.exe"
    if not python.exists():  # pragma: no cover - 非 Windows
        python = venv_dir / "bin" / "python"

    install = subprocess.run(
        [str(python), "-m", "pip", "install", str(wheel)],
        capture_output=True,
        text=True,
    )
    if install.returncode != 0:
        # 无网络/无本地 wheel 缓存时无法装依赖 → 明确 skip，不假装通过
        pytest.skip(
            "无法在干净 venv 中安装 wheel（可能无网络）:\n"
            f"{install.stdout[-800:]}\n{install.stderr[-800:]}"
        )

    # console script（auditor.exe / auditor）
    scripts_dir = venv_dir / "Scripts"
    if not scripts_dir.exists():  # pragma: no cover - 非 Windows
        scripts_dir = venv_dir / "bin"
    exe = scripts_dir / ("auditor.exe" if sys.platform == "win32" else "auditor")
    assert exe.exists(), f"未生成 console script: {exe}"

    # 中立目录：必须在**非仓库根**运行，才能证明"不依赖 CWD"
    neutral = workdir / "neutral"
    neutral.mkdir()

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)  # 防止 editable 安装的路径泄漏进来

    def run(args):
        return subprocess.run(
            [str(exe), *args],
            cwd=str(neutral),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

    selftest = run(["selftest"])
    bench = run(["bench"])

    # audit 用**装出来的数据里的样本**，绝对路径（与 CWD 无关）。
    # site-packages 的位置**必须问解释器本身**，不能按 Windows 布局硬拼
    # （`Scripts/../Lib/site-packages`）——Linux 上是 `lib/python3.12/site-packages`
    # （CI 首跑时正是栽在这里：装态 audit 退出码 2，样本路径不存在）。
    locate = subprocess.run(
        [str(python), "-c",
         "import auditor.data, pathlib; print(pathlib.Path(auditor.data.__file__).parent)"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert locate.returncode == 0, (
        f"装态下无法定位 auditor.data 包:\n{locate.stdout}\n{locate.stderr}"
    )
    data_dir = Path(locate.stdout.strip())
    sample = data_dir / "benchmark" / "C001-clean" / "paper.tex"
    assert sample.is_file(), f"装态下找不到样本文件: {sample}"
    audit = run(["audit", "--input", str(sample)])

    return selftest, bench, audit


@pytest.mark.slow
def test_k58_non_editable_install_is_usable(tmp_path):
    """K58: 非 editable 安装后，selftest / bench / audit 必须都按 README 语义工作。"""
    wheel = _build_wheel(tmp_path / "dist")

    assert _wheel_contains_data(wheel), (
        f"wheel 未携带数据（需 ≥18 个 paper.tex 与 truth.json）: {wheel.name}"
    )

    selftest, bench, audit = _install_and_run(wheel, tmp_path)

    assert selftest.returncode == 0, (
        f"K58 违规: 装态 selftest 退出码 {selftest.returncode}（期望 0）\n"
        f"stdout: {selftest.stdout[-800:]}\nstderr: {selftest.stderr[-800:]}"
    )
    assert bench.returncode == 0, (
        f"K58 违规: 装态 bench 退出码 {bench.returncode}（期望 0）\n"
        f"stdout: {bench.stdout[-1200:]}\nstderr: {bench.stderr[-800:]}"
    )
    assert "总体: 通过" in bench.stdout, (
        f"K58 违规: 装态 bench 未报'总体: 通过'\n{bench.stdout[-1200:]}"
    )
    assert audit.returncode == 0, (
        f"K58 违规: 装态 audit（干净论文）退出码 {audit.returncode}（期望 0）\n"
        f"stderr: {audit.stderr[-800:]}"
    )


@pytest.mark.slow
def test_k58_installed_version_is_single_source(tmp_path):
    """K58: 装态的 `auditor --version` 必须与 pyproject 一致（D5 装态复验）。"""
    wheel = _build_wheel(tmp_path / "dist")
    venv_dir = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )
    python = venv_dir / "Scripts" / "python.exe"
    if not python.exists():  # pragma: no cover
        python = venv_dir / "bin" / "python"
    install = subprocess.run(
        [str(python), "-m", "pip", "install", str(wheel)],
        capture_output=True,
        text=True,
    )
    if install.returncode != 0:
        pytest.skip(
            "无法在干净 venv 中安装 wheel（可能无网络）:\n"
            f"{install.stdout[-800:]}\n{install.stderr[-800:]}"
        )

    code = (
        "import auditor;"
        "print(auditor.__version__)"
    )
    out = subprocess.run(
        [str(python), "-c", code],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
    )
    assert out.returncode == 0, out.stderr

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        expected = tomllib.load(f)["project"]["version"]

    assert out.stdout.strip() == expected, (
        f"K58 违规: 装态版本 {out.stdout.strip()!r} != pyproject {expected!r}"
    )
