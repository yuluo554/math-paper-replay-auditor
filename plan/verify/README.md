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


---

## 六、M8 轮次记录（2026-10-21，v0.1.2 二次迭代）

> 追加，不覆盖历史轮次。环境：Windows 11 (win32 10.0.26200)，Git Bash，
> Python **3.12.10**（干净 venv `%TEMP%\mpra-verify`，非仓库自带 `.cleanenv`）。

### 6.1 前置

| 步骤 | 命令 | 结果 |
|---|---|---|
| 建干净 venv | `py -3.12 -m venv %TEMP%\mpra-verify` | ✅ 成功 |
| 装依赖 | `%TEMP%\mpra-verify\Scripts\python.exe -m pip install -e ".[dev,core]"` | ✅ exit 0 |

### 6.2 README 快速开始逐条执行（退出码对照 README「退出码语义」表）

| # | 命令 | 退出码 | 语义判定 |
|---|---|---|---|
| 1 | `python -m auditor selftest` | 0 | ✅ 自检通过（数据可达 + 四引擎全链路 + 基准达标） |
| 2 | `python -m auditor bench` | 0 | ✅ 基准全绿（检出率 100%、误报率 0%、五类各 3/3） |
| 3 | `python -m auditor audit --input data/benchmark/C001-clean/paper.tex` | 0 | ✅ 干净论文无确证问题 |
| 4 | `python -m auditor audit --input data/benchmark/B002-001-illegal_derivation/paper.tex` | 1 | ✅ 检出确证问题（非 0 ≠ 跑挂，既定语义） |
| 5 | `python -m auditor bench --only numeric_mismatch` | 0 | ✅ 单类套件达标 |
| 6 | `python -m auditor bench --only NOPE` | 2 | ✅ 未知错误类型 → 用法错误 |
| 7 | `python -m auditor audit --input nope.tex` | 2 | ✅ 输入文件不存在 → 用法错误 |
| 8 | `python -m auditor`（无参数） | 2 | ✅ 打印帮助 → 用法错误 |
| 9 | `python -m auditor fetch --arxiv-id 2301.00001` | 3 | ✅ fetch **未实现**（D8：已如实声明，恒 exit 3） |
| 10 | `python -m auditor --bogus` | 2 | ✅ 未知参数 → 用法错误 |
| 11 | `python -m auditor --version` | 0 | ✅ 打印 `auditor 0.1.2`（D5 新增） |
| 12 | `python -m data.benchmark.generator --check` | 0 | ✅ 真值库位级一致（20 个受控文件逐字节相同，D3 新增） |
| 13 | `python -m pytest tests/ -q` | 0 | ✅ **307 passed, 1 failed**（唯一失败是本文件尚未写 M8 记录的 K48 门——写完即绿） |

### 6.3 装态（非 editable 安装）验证——D2 的正面与反面

| 检查 | 命令 | 结果 |
|---|---|---|
| wheel 携带数据 | `python -m build --wheel` → 数 `paper.tex` 条目 | ✅ 18 个 `paper.tex` + `truth.json`（原先 **0**） |
| 装态自检 | `auditor.exe selftest`（中立目录） | ✅ exit 0 |
| 装态基准 | `auditor.exe bench`（中立目录） | ✅ exit 0，检出率 100.00% / 误报率 0.00% |
| 装态审计（干净） | `auditor.exe audit --input <site-packages>/auditor/data/benchmark/C001-clean/paper.tex` | ✅ exit 0 |
| 装态审计（含错） | 同上换 B001-001 | ✅ exit 1 |
| 装态版本 | `auditor.exe --version` | ✅ `auditor 0.1.2`（与 pyproject 一致） |
| **缺数据（负控）** | 把 site-packages 里的 `auditor/data` 改名后重跑 | ✅ selftest **exit 1** + 可执行指引；bench **exit 2** + 指引；**无 traceback** |
| 装态回归守门 | `pytest tests/gate/test_k58_installed_usable.py -q` | ✅ 2 passed（真实构建 + 真实安装 + 中立目录） |

### 6.4 门禁质量负控（证明门会红）

| # | 变异 | 期望 | 实测 |
|---|---|---|---|
| NC1 | 真值库重生成 vs 仓库 | 逐字节相同 | ✅ 20/20 文件相同 |
| NC2 | 篡改 `truth[0].expect.location` | `--check` rc ≠ 0 | ✅ rc=1，点名 `truth.json` |
| NC3 | 把 K17 真门改成 `return`（no-op） | K31 必须变红 | ✅ **1 failed**（修复前是 4 passed 全绿） |
| NC4 | 假 exe（`where.exe`）喂 `verify_package.py` | rc ≠ 0 | ✅ rc=1 |
| NC5 | 装态删掉数据目录 | 友好错误 + 约定退出码 | ✅ selftest rc=1 / bench rc=2，均带指引 |
| NC6 | `replay.py` 的 `Verdict.INVALID` → `Verdict.OK` | bench 检出率掉到 80% 且 exit 1 | ✅ rc=1，检出率 80.00% ✗ / illegal_derivation 0/3 / 总体: 未达标 ✗ |
| NC7 | 干净论文 / 含错论文 | 0 / 1 | ✅ 0 / 1 |

> **NC6 的头一次跑是假阴性**（改了源码却检出率仍 100%）：根因是一次**非 editable 安装**
> 把 editable 安装遮蔽了，运行时加载的是 site-packages 里的旧副本。
> 查 `import auditor.core.replay` 的 `__file__` 才发现。修好安装后重跑，NC6 立即按期望变红。
> **"我改了源码"与"运行时加载的是我改的那份源码"是两件事。**

### 6.5 不可本机实跑的通路（显式标注）

- **GUI 实机目检**：**用户已决定跳过**（2026-10-21）——本轮**未做**目检，
  故 GUI 侧只算"零 Qt 的 `--selftest` 链路已验证"，**交互未经人眼确认**。
  详见 `plan/RELEASE-M8.md` §5.7。
- **Linux / macOS 实机**：只有 Windows 产物；ubuntu 腿由 CI 覆盖，macOS 无腿。

> 依纪律：未做目检 = 未验证，不写成"已验证"。
> （CI 的实际结论见 §六之二——本节写于推送前，结论以后续追加事实为准。）

---

## 六之二、M8 收尾追加事实（推送 / 发布之后）

> 追加，不覆盖 §六的记录。

### 6.2.1 CI 实际结论

| 项 | 值 |
|---|---|
| run | **39576161482**（push @ 2026-10-21T09:20:17Z，headSha = `fde0506…`） |
| 结论 | **success**（`windows-latest / py3.12` ✅、`ubuntu-latest / py3.12` ✅） |
| 注解 | **Node20 弃用告警 0 条**（v0.1.1 时 3 条）；仅剩 GitHub 自己的 Ubuntu 26 迁移公告 |
| 首版 run（红） | `39573968753` / `39573999392`（headSha `9da7013`）——被 CI 抓出两条真缺陷（见 `plan/RELEASE-M8.md` §5.2） |

### 6.2.2 tag 树独立复验（fresh clone）

| 检查 | 结果 |
|---|---|
| clone | ✅ `git clone --branch v0.1.2` → HEAD = `fde0506…` |
| tag 树自带测试 | ✅ **309 passed**（另 3 项按设计略过），exit 0（3 个略过项全是 K52「冻结产物不存在」——clone 里无 `dist/`，属设计跳过） |
| tag 树自带 `--check` | ✅ 20 个受控文件逐字节相同，rc=0 |
| tag 树自带 `bench` | ✅ 检出率 100.00% / 总体: 通过 ✓ |
| tag 树自带 `--version` | ✅ `auditor 0.1.2` |

> 复验 venv：`%TEMP%\mpra-clone-venv`（**不复用**工作树的 `%TEMP%\mpra-verify`，
> 也不复用仓库自带 `.cleanenv`）。

### 6.2.3 发布物真下载复核（API 通道，6/6 实下）

| 检查 | 结果 |
|---|---|
| 6 附件实下 | ✅ 字节数与 API 一致 |
| sha256 三方对撞 | ✅ API digest = 本地实算 = 台账，**6/6 相同** |
| `sha256sum -c` | ✅ **5/5 OK, RC=0**（D15 修 CRLF 之后才通） |
| 源码包 vs tag 树 | ✅ 150 == 150 |
| 中立目录双 exe | ✅ CLI selftest 0 / bench 0（100.00% / 0.00%）；GUI `--selftest` 0（ok=12 invalid=0） |
| demo HTML 外链 | ✅ 0 处 |

