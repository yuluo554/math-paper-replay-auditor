# 干净环境验证留档

> 本文件是 K48 要求的"逐条命令 + 退出码语义"成表；M6 发布里程碑**追加**本轮记录，
> 不覆盖历史轮次。
> 记录环境：Windows 11 (win32 10.0.26200)，Git Bash，Python 3.12.10（venv）。
> 记录日期：2026-10-16。

---

## 一、前置：干净 venv 创建与安装

裸 `python` 在本机是商店占位符，故 venv 创建用 `py -3.12`（README 原文的
`python -m venv` 语义等价，创建工具换成本机可用通道）。

| 步骤 | 命令 | 结果 |
|---|---|---|
| 建 venv | `py -3.12 -m venv .cleanenv` | ✅ 成功 |
| 装依赖 | `NO_PROXY="*" no_proxy="*" ./.cleanenv/Scripts/python.exe -m pip install -e ".[dev,core]"` | ✅ exit 0 |

**关键校验**：`antlr4-python3-runtime` 解析为 **4.11.1**（非 4.13.x）。

> 为什么单列这一条：sympy 的 LaTeX 后端硬校验 antlr4 必须为 4.11.x
> （`sympy/parsing/latex/_parse_latex_antlr.py` 内
> `version('antlr4-python3-runtime').startswith('4.11')`）。
> pyproject 原先写 `<4.14`，干净环境解析到 4.13.2 → `parse_latex` 抛 ImportError
> → 符号重放整链退化、`illegal_derivation` 类漏检，而**开发机恰好装着 4.11 全程全绿**。
> 已收窄为 `>=4.11,<4.12`，并加守门 K53 锁死。

---

## 二、README 快速开始逐条执行

按 README「快速开始」顺序逐条跑（`python` 代以 venv 解释器），退出码对照
README「退出码语义」表判定。

| # | 命令 | 退出码 | 语义判定 |
|---|---|---|---|
| 1 | `python -m auditor selftest` | 0 | ✅ 符合：自检通过（内嵌数据可达 + 四引擎全链路 + 基准达标） |
| 2 | `python -m auditor bench` | 0 | ✅ 符合：基准全绿（检出率 100%、误报率 0%、五类错误各 3/3） |
| 3 | `python -m auditor audit --input data/benchmark/C001-clean/paper.tex` | 0 | ✅ 符合：干净论文无确证问题 |
| 4 | `python -m auditor audit --input data/benchmark/B002-001-illegal_derivation/paper.tex` | 1 | ✅ 符合：检出确证问题（**非 0 ≠ 跑挂**，这是既定语义） |
| 5 | `python -m auditor bench --only numeric_mismatch` | 0 | ✅ 符合：单类套件达标 |
| 6 | `python -m auditor bench --only NOPE` | 2 | ✅ 符合：未知错误类型 → 用法错误 |
| 7 | `python -m auditor audit --input nope.tex` | 2 | ✅ 符合：输入文件不存在 → 用法错误 |
| 8 | `python -m pytest tests/ -q` | 0 | ✅ 符合：**264 passed** |

**收集数对账**：干净 venv 264 项 == 开发机 264 项（同一 extras 集合 `.[dev,core]`）。

---

## 三、本轮干净环境暴露并修复的缺陷（逐条留档）

M5 声称"干净环境验证通过"，但当时 `plan/verify/` 目录为空、K48 测试只做
`if exists: 检查` 的空转。本轮补做，暴露三处**开发机全绿、干净环境/用户侧会炸**的缺陷：

| # | 缺陷 | 现象 | 修复 | 回归守门 |
|---|---|---|---|---|
| 1 | `src/auditor/__main__.py` 缺失 | README 每条 `python -m auditor ...` 都报 `No module named auditor.__main__` | 新增薄入口模块 | K47「quoted module invocations are importable」 |
| 2 | `antlr4-python3-runtime` 上界过宽 | 干净环境装到 4.13.2 → sympy `parse_latex` 抛 ImportError → `illegal_derivation` 0/3 检出（检出率掉到 80%） | pyproject 收窄到 `>=4.11,<4.12` | K53 三条（pin + 实跑 parse_latex + 解析失败不得判 ok） |
| 3 | README 审计命令路径不存在 | 指向 `data/benchmark/samples/C001-clean/paper.tex`（实际在 `data/benchmark/C001-clean/`），旧 K47 只查子串所以全绿 | 修正 README 路径 | K47「commands reference existing paths」 |

---

## 四、冻结产物验证（发布物本体）

| 检查 | 命令 | 结果 |
|---|---|---|
| CLI 基准与源码态一致 | `dist/auditor-cli.exe bench` | ✅ 与源码态逐行一致（100% / 0% / 五类 3/3） |
| CLI 自检 | `dist/auditor-cli.exe selftest` | ✅ exit 0 |
| CLI 审计（干净） | `dist/auditor-cli.exe audit --input data/benchmark/C001-clean/paper.tex` | ✅ exit 0 |
| CLI 审计（含问题） | `dist/auditor-cli.exe audit --input data/benchmark/B002-001-illegal_derivation/paper.tex` | ✅ exit 1（符合既定语义） |
| GUI 未知参数 | `dist/auditor.exe --bogus` | ✅ exit 2（非静默挂起） |
| 冻结态 vs 源码态自动对账 | `pytest tests/gate/test_k52_frozen_parity.py` | ✅ 3 passed |

---

## 五、不可本机实跑的通路（显式标注）

- **CI 四矩阵**：仓库尚无远端，CI 从未跑过。**待首推验证**。
- **跨平台行为**（ubuntu runner 的文件名大小写/路径分隔符）：本机 Windows 无法覆盖，
  仅能以"路径一律 POSIX 规范化 + 白名单镜像仓库相对路径"降低风险。**待首推验证**。

> 依 skill 纪律：未推送 = 未跑 CI，本文件不写"CI 绿"，只写"本地等价校验"并标注缺口。
