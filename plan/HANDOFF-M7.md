# plan/HANDOFF-M7.md

> 跨会话交接快照——M6 发布完成、M7 收尾/品牌化待执行。
> 版本：v1（2026-10-16）。
> **用法**：新对话启动用 `/goal 读取 "plan/HANDOFF-M7.md" 继续完成任务`（库内写相对路径 `plan/HANDOFF-M7.md`，启动命令从用户侧拼绝对路径）。

---

## 一、当前进度与证据

### 1.1 里程碑状态

| 里程碑 | 状态 | 证据 |
|---|---|---|
| M0 计划先行 | ✅ | plan/00–06 全部落盘 |
| M1 数据先行 | ✅ | 18 样本 + 真值 + 白名单 + K31 变异验证 |
| M2 解析层 | ✅ | LaTeX 解析器 + K1/K2/K3/K28 守门 |
| M3 引擎层 | ✅ | 四大引擎 + K8/K10/K14 守门 |
| M4 基准层 | ✅ | 基准 runner + 指标 + K19/K20 |
| M5 交付层 | ⚠️→✅ | 原判"完成"实为**三层结构性缺陷**（见 §1.3），已在 M6 修复 |
| **M6 发布层** | ✅ | **tag + Release + RELEASE-M6.md 三件套齐；CI 三矩阵全绿** |

### 1.2 关键交付物

| 文件 | 用途 |
|---|---|
| `plan/RELEASE-M6.md` | 发布留档（三件套之三）：基线 / sha256 / 验证证据 / 脱敏留档 |
| `plan/verify/README.md` | 干净环境验证逐条留档（7 命令 + 退出码语义 + 缺陷清单） |
| `src/auditor/report/renderer.py` | 报告渲染（人读 Markdown + 机读 JSON，零判定、零外链） |
| `src/auditor/pipeline.py` | 编排层（audit / bench / selftest，K40 唯一对外 API） |
| `src/auditor/__main__.py` | `python -m auditor` 入口（M6 新增，原缺失） |
| `build_tools/` | 打包辅助（原 `packaging/` 遮蔽 PyPI packaging，M6 改名） |
| `.github/workflows/ci.yml` | CI 三矩阵（win 3.8 / win 3.12 / ubuntu 3.12） |
| `tests/gate/test_k50~k56` | M6 新增守门（检出率 / 冻结对账 / 运行时前提 / 编排链 / 字节冻结 / 路径形态） |

### 1.3 M6 修复的三层结构性缺陷（复盘要点）

| 层 | 缺陷 | 为何 128 个守门全绿 |
|---|---|---|
| 数据 | 5 类植入错误中 **4 类注入器静默空转**（锚点不匹配即返回原文） | 无守门验证"注入真的改动了文本" |
| 引擎 | 数值引擎 `computed_value = paper_value`（拿报告值自比）；量纲引擎在无单位模板上无物可判；图引擎断链检测恒返回空；重放把定义式当推导链判 invalid | 守门只断言"误报率 0"，从不断言"检出率" |
| 守门 | 128 个测试**从未断言检出率** | 检出率 20% 的引擎 + 全空编排层（`audit`/`selftest` 是 `return 0`/`return True`）全绿通过 |

### 1.4 最终验证证据

```
py -3.12 -m pytest tests/ -q   →  278 passed
py -3.8  -m pytest tests/ -q   →  278 passed（收集数一致）
基准：检出率 100%、误报率 0%、五类错误各 3/3、错误类型归属 15/15 相符
冻结态与源码态基准逐行一致
CI：三矩阵全绿（run 38862782175 / 38862788765）
脱敏：全历史 + 工作树 个人标记 0、本机路径 0
```

---

## 二、下一棒待办（M7 收尾固化）

| 项 | 说明 | 优先级 |
|---|---|---|
| ① 发布后元信息终检 | `gh repo view` 核 description/topics 与 README 定位一致（已设 7 个 topics，复核即可） | 中 |
| ② 缓议项清零 | 逐条全表落档（含显式"跳过"决策） | 中 |
| ③ README 状态行转正 | 若 README 有"开发中"类措辞，改为已发布 | 低 |
| ④ 收尾台账入库 | 若收尾项少，用单文件 `plan/WRAPUP-M7.md` 完结档 | 低 |
| ⑤ 真实论文回归（可选扩展） | `data/real_papers/registry.json` 目前为空骨架，可补真实 arXiv 元数据（不存全文） | 低 |
| ⑥ LLM 兜底路径（可选扩展） | `llm/bridge.py` 已实现开关与降级，但未接端点实测 | 低 |

### 已知遗留（如实记录，非阻塞）

- `fetch` 命令（arXiv 抓取）返回 exit 3（模块未实现），README 未宣传该能力。
- `data/real_papers/registry.json` 为空骨架，真实论文回归集未填充。
- 模型端点为可插拔开关，未做端到端联网实测（设计上不随包分发权重）。

---

## 三、既定口径清单（K 编号，"动了会打挂测试"）

### 3.1 M1–M4 已守门

| K | 守门内容 | 文件 |
|---|---|---|
| K1/K2 | 覆盖率 ≤1 / 未识别不静默丢弃 | test_k1_coverage.py / test_k2_uncovered.py |
| K3/K4 | 自定义宏不映射 / 三态判定 | test_k3_macros.py / test_k4_verdicts.py |
| K7/K8 | 无硬编码容差 / 两路径独立 | test_k7_tolerance.py / test_k8_paths.py |
| K10/K14 | 不猜单位 / 幽灵标签仅提示 | test_k10_units.py / test_k14_ghost_labels.py |
| K17/K19/K20 | 真值不含 observed / 误报率 0 / 确定性生成 | test_k17/k19/k20 |
| K28/K31 | 编码不猜测 / 变异验证 | test_k28_encoding.py / test_k31_mutation.py |

### 3.2 M5 已守门（K33–K49）

extras/dev deps/README-CI 一致/白名单单一事实源/目录文件分档/双 exe 分档/
冻结入口薄模块/未知参数 exit 2/selftest 参数/HANDOFF 相对路径/留档类别/
附件 ASCII/README 命令可跑/干净环境留档/UTF-8 stdio。

### 3.3 **M6 新增（K50–K56）——下一位务必遵守**

| K | 守门内容 | 关键约束 |
|---|---|---|
| **K50** | 检出率 ≥95% + 逐样本点名 + 逐类覆盖 + **错误类型归属** | 改引擎判定逻辑后必跑；归属不符即红 |
| **K51** | 检出率守门的变异验证 | 新增/改写守门必须证伪一次 |
| **K52** | 冻结态 == 源码态（bench 指标行逐项对账） | 改打包配置或引擎后必跑；产物不存在时 skip |
| **K53** | sympy LaTeX 运行时前提（antlr pin `>=4.11,<4.12` + 实跑 parse_latex） | **不得放宽 antlr 上界**（4.12+ 会让 parse_latex 抛错、符号重放静默退化） |
| **K54** | audit 编排链 + 双轨报告同源/可复现/零外链 + selftest 可证伪 | 渲染层零判定（只消费结论） |
| **K55** | 文本行尾 LF（CR 守门）+ 生成物 LF + zip 确定性 | 脚本写盘一律用 `open(newline="")`，勿用 `write_text`（Windows 注入 CRLF） |
| **K56** | 路径形态归一（POSIX 绝对路径不得被 rebase） | 判绝对性按**形态**（前导 `/` 或 `X:/`），勿用 `Path.is_absolute()`（Windows 上对 `/tmp/x` 返回 False） |

### 3.4 跨阶段硬纪律（本批新增/强化）

1. **注入器必须自证改动**：`str.replace` 未命中即抛错——静默返回原文会造出假样本。
2. **解析失败一律 undecidable**：不得把"没看懂"报成 invalid 或 ok（K4/K53）。
3. **冻结态必须对账**：打包漏收动态 import 会造成静默降级，产物存在时 K52 必跑。
4. **多 rev 历史扫描必配阳性对照**：`git grep … -- <revs>` 会把 rev 当 pathspec 静默空扫。
5. **脱敏扫描 HARD/LOW 两档**：个人标记为硬门，本机路径同为硬门（K43）。

---

## 四、本机环境坑（只写实测过的）

| 坑 | 现象 | 修复 |
|---|---|---|
| `packaging/` 遮蔽 PyPI packaging | PyInstaller 报 `No module named packaging.requirements` | 辅助目录改名 `build_tools/` |
| antlr 动态 import 被漏收 | 冻结态 `parse_latex` 静默返回 None → `illegal_derivation` 归零 | hiddenimports 逐个点名 `_parse_latex_antlr` / `_antlr.latexlexer` / `_antlr.latexparser` |
| sympy 硬校验 antlr 4.11.x | 干净环境装 4.13 → `parse_latex` 抛 ImportError | pyproject 收窄 `>=4.11,<4.12` |
| Windows 文本模式注入 CRLF | 生成器产物带 `\r\n`，破坏位级一致 | `open(newline="")` 显式写 LF |
| `Path(s).is_absolute()` 对 `/tmp/x` 在 Windows 返回 False | POSIX 绝对路径被当相对路径 rebase（CI ubuntu 才暴露） | 按形态判定（前导 `/` 或 `X:/`） |
| `git grep … -- <revs>` | rev 被当 pathspec → 多 rev 扫描静默空扫（连阳性对照都 0） | `git grep <revs>`，并配阳性对照 |
| Python `write_text` 在 Windows 注入 CRLF | 脚本改文档后 K55 变红 | 改文档用 `write_bytes(text.replace("\r\n","\n").encode())` |
| GitHub `github.com:443` 被墙 | `git push` 超时（api.github.com 正常） | 走 SSH over 443：`git@ssh.github.com:...` + `GIT_SSH_COMMAND="ssh -p 443"` |
| 无本地代理 | `127.0.0.1:7897` 无监听；pip 需 `NO_PROXY="*"` | pip 用清华镜像 + `NO_PROXY="*"` |
| `python` 是商店占位符 | 命令无输出/exit 49 | 一律用 `py -3.12` / `py -3.8` |
| PyInstaller 5.x 在 Windows 崩溃 | 确定性 crash | 用 ≥6.22.3 |
| PySide6 6.7+ 需 Python ≥3.9 | 3.8 上 import 失败 | 用 6.6.3.1 max |

---

## 五、DoD 检查清单

- [x] M6 三件套：tag `v0.1.0` + GitHub Release（双 exe）+ `plan/RELEASE-M6.md`
- [x] CI 三矩阵全绿，push/tag 事件与 run 逐条配对
- [x] 冻结产物回下载校验（sha256 逐位一致 + 中立目录冒烟）
- [x] 干净环境验证逐条留档（`plan/verify/README.md`）
- [x] 脱敏：全历史 + 工作树 个人标记 0、本机路径 0；K43 强化并变异验证
- [x] K50–K56 守门落地，含变异验证
- [x] 双解释器全量 278 项（3.8 / 3.12 收集数一致）
- [x] plan/00·04 状态与决策记录回写
- [ ] M7 收尾固化（见 §二）

---

## 六、命令速查

```bash
# 运行所有守门测试（本机）
py -3.8  -m pytest tests/ -q
py -3.12 -m pytest tests/ -q

# 基准 / 自检 / 审计
py -3.12 -m auditor bench
py -3.12 -m auditor selftest
py -3.12 -m auditor audit --input data/benchmark/C001-clean/paper.tex
py -3.12 -m auditor audit --input data/benchmark/C001-clean/paper.tex --format json

# 重新生成样本 + 真值（改模板/注入器后必跑）
py -3.12 -c "from data.benchmark.generator import main; main('data/benchmark')"

# 构建双 exe（需 Python 3.12 通道 + PyInstaller ≥6.22.3）
py -3.12 build_tools/build_exe.py cli
py -3.12 build_tools/build_exe.py gui

# 冻结态对账（需 dist/ 产物存在）
py -3.12 -m pytest tests/gate/test_k52_frozen_parity.py -v
```

---

## 七、回写指针

- M6 完成 → plan/00-README总览.md 第四节 M6 行 = ✅；M5 行附"三层缺陷已在 M6 修复"说明
- M6 新增 K → plan/04-测试与验收.md 第七节（K50–K54 口径与决策记录）
- 发布留档 → plan/RELEASE-M6.md
- 干净环境留档 → plan/verify/README.md
- 上一阶段交接 → plan/HANDOFF-M6.md
