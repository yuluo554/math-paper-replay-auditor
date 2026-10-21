# plan/RELEASE-M8.md — v0.1.2 发布留档

> 仓库：`yuluo554/math-paper-replay-auditor`
> 里程碑：M8（二次迭代：真值库自证 + 装态可用 + 门禁质量）
> 留档日期：2026-10-21

本文件在 **tag 之前**写好并进 tag 树；发布后才产生的事实列在 §五「tag 后追加事实」。

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.1.2`（pyproject = `auditor.__version__` = `auditor --version`，**单一事实源**） |
| 起点 | `v0.1.1` = `76f295f96c497e9dd433436d0c8af59a1b24e9f7`；起点 HEAD `2e8b74ad1fae8eda999de8e7e99bb5c1539e5c98` |
| 发布形态 | 源码仓库 + 双 exe 数据 zip + sha256 台账 + demo HTML/GIF + 源码包（6 个附件） |
| 变更范围 | 门禁质量、版本单源、pip 渠道可用性、Python floor；**不动四引擎判定逻辑** |
| 测试 | **308 passed**（起点 291；新增 17 条：K20 ×5 / K57 ×5 / K58 ×2 / D10 ×2 / K48 +1） |
| 基准 | 18 样本（15 错误 + 3 干净）；检出率 **100.00%**（≥95%）；误报率 **0.00%**；五类各 3/3 |
| Python floor | **≥3.12**（3.8/3.10/3.11 已 EOL；3.8 腿随之下线） |
| 双 exe | `dist/auditor-cli.exe` 23,810,940 B；`dist/auditor.exe` 61,539,399 B（本轮重出） |

### 1.1 决策记录（用户拍板）

| 决策 | 选择 | 理由 |
|---|---|---|
| DEC1 Python floor | **B：抬到 ≥3.12** | 与另两仓统一；可删 `PySide6<6.7` 与 `setuptools<81` 两条 3.8 连带上限；可转 PEP 639 SPDX |
| DEC2 pip 渠道 | **A：把 data 打进 wheel** | 约 200 KB；装完 `selftest`/`bench` 都能真跑 |
| DEC3 demo 文件名 | **A：改 README 指向仓内实际文件** | 只动 README 两行，仓内文件与 Release 附件都不动 |
| DEC4 fetch 子命令 | **A：保留但 README 明写未实现** | 不动 CLI 契约，把"看起来有"变成诚实声明 |
| DEC5 `update/` 中文名 | **A：加进排除名单** | 与 `plan/`、`docs/` 同类，口径一致性修正 |

---

## 二、修复清单

### 2.1 P1（本批最重要）

| # | 缺陷 | 现象 | 处置 | 守门 |
|---|---|---|---|---|
| **D3** | **K20「生成器 `--check` 位级一致」从未实现** | 仓内**无** `--check`；`plan/00` 与 `HANDOFF-M2..M5` 五处都勾了它。实测：手改 `truth[0].expect.location` 与 `truth[1].generator_seed` → `288 passed, 3 skipped, EXIT=0`（**无门发现**） | `data/benchmark/generator/__init__.py` 新增**只读** `check_benchmark()`（重生成到临时目录 → 逐字节比对，**绝不写 `data/`**）+ `__main__.py` 入口 | **K20 新增 5 项**（正控 / 两类篡改负控 / CLI 形态 / 只读反控） |
| **D2** | **pip 装完不可用** | wheel 30 条目、`data/` 命中 **0**；装态 `selftest` exit 1、`bench` exit 2 | 数据装成 **`auditor.data`** 子包（不装顶层 `data`，避免 site-packages 撞名）；新增 `src/auditor/_datapaths.py` 统一三形态定位；**三处 `sys._MEIPASS` 分支语义不变** | **K58 新增 2 项**（真实构建 → 装干净 venv → 中立目录跑 selftest/bench/audit） |
| **D1** | **`verify_package.py` 在任何 exe 上都抛异常** | 期望 exe 写 `selftest_out.txt`，真实 exe 既不接受多余裸参数也不写文件 → `FileNotFoundError` exit 1 | 改为真契约：跑 `selftest` + `bench`，断言 rc 与关键输出，**在中立目录**执行 | NC4 负控：假 exe → rc=1 |
| **D5** | **版本双源且被测试写死** | pyproject `0.1.1` vs `__version__` `0.1.0`；`test_k33_extras.py:96` 硬断言 `"0.1.0"` | 版本改从 `importlib.metadata` 读（单源）；`--version` 补上；报告三格式补工具版本（**不加生成时间**，保持同输入同输出） | K33 改为与 pyproject 比对 |
| **D14** | **`update/` 中文名让门禁变红**（诊断方自引入） | `test_k46` 扫全树只排除 `plan`/`docs` → 1 failed, 290 passed | `update` 加进 K46 与 **K55** 的排除名单（K55 是同源问题，诊断未预见） | 补跑即 291 passed |

### 2.2 P2

| # | 缺陷 | 处置 |
|---|---|---|
| **D7** | 4 个门是空转或重实现 | **K17 判据抽到 `_k17_truth_logic.py`**，K17 门与 K31 共用；K31 追加"调用**真门函数**"的变异 → 真门 no-op 时 K31 必红；K44/K45/K48 的 `pass` 与"有则检查"改为无条件断言 |
| **D6** | README 指向不存在的 demo 文件 | 改为 `docs/demo/demo-clean.html` / `demo-error.html`；**K47 增门**：README 反引号里的相对路径必须存在 |
| **D8** | `fetch` 恒 exit 3 且 README 0 命中 | 错误信息改为如实说明"未实现的扩展项"（不再伪装成"需联网开关"）；README 写明 + 补进退出码表；**K57 增门** |
| **D9** | `data/real_papers/registry.json` 是占位 | README 与 `data/README.md` 写明"占位、尚未交付"，并说明"误报率 0 只覆盖合成基准"；**K57 增门** |
| **D10** | `unit_map` 里 `"n"` 重复键 | 取舍：物质的量用 `mol`，`"n"` 只留 `force`（牛顿）；补 2 项测试（语义不冲突 + AST 查重复键） |
| **D13** | K46 硬编码 `v0.1.0` 附件名 | 改为从 pyproject 读版本号拼装 |
| **D4** | `[all]` extra 指向不存在的分发名 `auditor` | 改为 `math-paper-replay-auditor[...]`；实测 `pip install --dry-run ".[all]"` exit 0 |
| **D11** | CI 时效与 floor | actions `checkout@v4→v7`、`setup-python@v5→v7`；矩阵去 3.8 腿；**K35 改为跟随 `requires-python`**（不再写死 3.8）并新增"不得再测 EOL 版本"一条 |

---

## 三、验证（tag 时点）

```bash
# 源码态（干净 venv %TEMP%\mpra-verify，Python 3.12.10）
python -m pytest tests/ -q                                # 308 passed
python -m auditor selftest                                # exit 0
python -m auditor bench                                   # 18 样本，检出率 100%、误报率 0%
python -m auditor --version                               # auditor 0.1.2
python -m data.benchmark.generator --check                # 20 个受控文件逐字节相同

# 冻结态（重出后）
pytest tests/gate/test_k52_frozen_parity.py -q           # 3 passed（真跑，非 skip）
python tools/verify_package.py dist/auditor-cli.exe      # exit 0
python tools/verify_package.py --gui dist/auditor.exe     # exit 0

# 装态（非 editable，干净 venv，中立目录）
pip install dist/math_paper_replay_auditor-0.1.2-py3-none-any.whl
auditor selftest                                          # exit 0
auditor bench                                             # exit 0（100% / 0%）
```

**门禁质量负控（逐条实跑）**：

| # | 变异 | 期望 | 实测 |
|---|---|---|---|
| NC1 | 真值库重生成 vs 仓库 | 逐字节相同 | ✅ 20/20 |
| NC2 | 篡改 `expect.location` | `--check` rc ≠ 0 | ✅ rc=1 |
| NC3 | K17 真门改成 `return` | K31 必须变红 | ✅ **1 failed**（修复前 4 passed） |
| NC4 | 假 exe 喂 `verify_package.py` | rc ≠ 0 | ✅ rc=1 |
| NC5 | 装态删掉数据目录 | 友好错误 + 约定退出码 | ✅ selftest 1 / bench 2，均带指引，**无 traceback** |
| NC6 | `Verdict.INVALID` 改 `Verdict.OK` | bench 检出率掉到 80% 且 exit 1 | ✅（见 §五） |
| NC7 | 干净论文 / 含错论文 | 0 / 1 | ✅ 0 / 1 |

**附件清单（tag 时点，`release/` 下）**：见 §五「tag 后追加事实」（发布后才产生）。

---

## 四、不做的事（明确边界）

- **不实现 `fetch`**（arXiv 抓取）：只把"未实现"如实写进 README。
- **不填 `data/real_papers/registry.json`**：真实论文回归集仍是扩展项、未交付。
- **不改四引擎判定逻辑**：`replay.py` / `numerical.py` / `dimensional.py` / `graph.py` 的算法不动
  （D10 只改**重复键的取舍**，不改量纲代数）。
- **不改 `data/benchmark/` 下任何 `paper.tex` / `truth.json` / `manifest.json`**（真值库由生成器自证）。
- **不降低阈值**：`DETECTION_RATE_TARGET`（95%）、误报率 0、各类 `min_required`（3）。
- **不删任何现有 gate**（允许收紧或重写为调用真逻辑）。
- **不动 `v0.1.0` / `v0.1.1` 两个 tag 及其 Release**。
- **不把 `update/` 提交进公开仓**（它含本机绝对路径）。

---

## 五、tag 后追加事实

> 以下事实产生于 tag 与 Release 之后，是**追加**内容，不改写上面的 tag 时点事实。

| 项 | 值 |
|---|---|
| tag | `v0.1.2`（annotated） |
| 指向提交 | 见 §五.2 |
| CI run | 见 §五.3 |
| Release | `v0.1.2`（6 个附件） |
| 附件 sha256 | 见 §五.4 |
| 真下载复核 | 见 §五.5 |
