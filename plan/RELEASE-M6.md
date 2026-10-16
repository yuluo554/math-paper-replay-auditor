# plan/RELEASE-M6.md

> 发布留档（M6 三件套之三）。记录时间：2026-10-16。
> 本文件只写**实测到**的事实；未执行的项标 ⬜ 并说明原因，不预填、不留空。

---

## 一、发布基线

| 项 | 值 |
|---|---|
| 版本 | v0.1.0 |
| 发布基线提交 | 见 §五（tag 打在 CI 绿的收尾提交上） |
| 双解释器 | Python 3.8.8-64 / 3.12.10（本机 `py -0p` 实测） |
| 构建通道 | Python 3.12 + PyInstaller 6.22.3 |
| GUI 运行时 | PySide6 6.6.3.1 |

---

## 二、交付物与校验

### 2.1 产物清单

| 附件 | 说明 | 大小 |
|---|---|---|
| `auditor-cli.exe` | CLI（无 Qt，含 antlr4 全栈） | 27,274,163 字节 |
| `auditor.exe` | GUI（含 PySide6，窗口模式） | 72,660,794 字节 |

### 2.2 sha256（以最终基线为准）

| 附件 | sha256 |
|---|---|
| `auditor-cli.exe` | `793857b54aa123d63b87644d7985f5cf6f65559e33f374c83e412b31deb9d805` |
| `auditor.exe` | `120c4ba1e6bdc8d7ffe90a1204809c87e0b20bf6d3b84f6b2d79163912162838` |

> 发布基线纪律：本轮构建发生在 **CI 绿提交 `a5ce6ff`**、工作树与该提交一致
> （`git status` 干净）之后，故这三个数（大小/sha256）对应最终上传件。
> 早前几轮的哈希已随源码修复作废，不在正文保留。

> **构建可复现性口径**（skill 纪律）：上表是**本次基线**的产物哈希。
> PyInstaller 产物含构建期 PE 时间戳，**跨次重建不承诺逐字节一致**——
> 可承诺的是"同一棵树 + 同一次构建 → 同哈希"。故对账分两情形：
> 树一致 → 哈希强对账；换机/重建 → 只验结构口径（章节 ✓ 入口 ✓ 冻结冒烟 ✓）。

---

## 三、发布前验证证据

### 3.1 基准指标（真值库全量实跑）

```
总样本数: 18   错误样本: 15   干净样本: 3
检出率: 100.00% (目标 ≥ 95%) ✓
误报率: 0.00%  (目标 ≤ 0%)  ✓
dimension_mismatch 3/3 · illegal_derivation 3/3 · numeric_mismatch 3/3
dangling_ref 3/3 · dep_chain_break 3/3
总体: 通过 ✓
```

**错误类型归属**：15/15 样本检出的 `error_type` 与真值逐一相符（K50 断言）。

### 3.2 测试

| 面 | 命令 | 结果 |
|---|---|---|
| 3.12 全量 | `py -3.12 -m pytest tests/ -q` | **275 passed** |
| 3.8 全量 | `py -3.8 -m pytest tests/ -q` | **275 passed**（收集数一致） |
| 干净 venv 全量 | `./.cleanenv/Scripts/python.exe -m pytest tests/ -q` | **271 passed**（该轮早于 K56 加入） |

守门文件数：36（K1–K56）。

### 3.2b CI 实跑（首推后）

| 项 | 结果 |
|---|---|
| 矩阵 | windows-latest/py3.8 · windows-latest/py3.12 · ubuntu-latest/py3.12 |
| 首跑（`677e703`） | ❌ ubuntu 红：POSIX 绝对路径被 `lstrip("/")` 归一成仓库相对路径 |
| 首次修复后（`c16534f`→`2cb3dc9`，run `38859335607`） | ✅ 三 job 全绿 |
| 收尾提交（`78e1dbd`→`74297aa`，main，run `38859903126`） | ✅ 全绿 |
| 历史改写后（`4b2a21b`，main，run `38861249412`） | ✅ 全绿（最终发布基线） |

**run 对账**（口径：每个 push 事件恰一 run，head_sha 逐条配对）

| 事件 | run id | head_sha（改写前） | head_sha（改写后） | 结论 |
|---|---|---|---|---|
| push main | 38858693069 | `677e703` | `facfebb` | ❌ 失败（如实留档：路径形态缺陷） |
| push main | 38859335607 | `c16534f` | `2cb3dc9` | ✅ 成功（修复后） |
| push main | 38859903126 | `78e1dbd` | `74297aa` | ✅ 成功 |
| push tag v0.1.0 | 38859909350 | `78e1dbd` | `74297aa` | ✅ 成功 |
| push main（改写后） | 38861249412 | — | `4b2a21b` | ✅ 成功 |
| push main（发布留档补全） | 38862249413 | — | `a5ce6ff` | ✅ 成功（**最终发布基线**） |

> **历史改写说明（如实留档，非回填美化）**：脱敏扫描发现 plan/HANDOFF-M1~M5
> 含本机绝对路径启动命令（已随公开仓库发布），依 skill 纪律用
> `git filter-repo --replace-text` 重写全历史并 force push。
> 改写后旧的 head_sha 已不可达，故上表并列"改写前/改写后"两列，
> 并给出旧→新提交映射：`677e703→facfebb`、`c16534f→2cb3dc9`、`78e1dbd→74297aa`。
> 改写前那 4 次 CI run 的结论**原样保留**（改动仅限 head_sha 可追溯性），
> 非改写产物。最终发布基线 = `a5ce6ff`（run `38862249413` 全绿）。

### 3.3 冻结产物本体验证

| 检查 | 命令 | 结果 |
|---|---|---|
| CLI 基准 == 源码态 | `dist/auditor-cli.exe bench` | ✅ 逐行一致 |
| CLI 自检 | `dist/auditor-cli.exe selftest` | ✅ exit 0 |
| CLI 审计（干净 / 含问题） | `audit --input ...` | ✅ exit 0 / exit 1 |
| GUI 未知参数 | `dist/auditor.exe --bogus` | ✅ exit 2 |
| 冻结/源码自动对账 | `pytest tests/gate/test_k52_frozen_parity.py` | ✅ 3 passed |

### 3.3b 发布物本体已验（回下载 + 中立目录）

1. `gh release download v0.1.0` 下载两附件到仓库外中立目录
2. 回下载件 sha256 与 §2.2 台账**逐位一致**
3. GitHub 侧资产 digest 亦与台账一致（`gh release view --json assets`）
4. 中立目录内冻结态冒烟：`selftest` exit 0、`bench` exit 0（检出率 100%）、
   GUI 未知参数 exit 2

### 3.4 干净环境验证

逐条留档见 **`plan/verify/README.md`**（7 条命令 + 退出码语义判定 + 本轮暴露的三处缺陷）。

---

## 四、本轮（M6）修复与新增守门

### 4.1 修复的缺陷

| # | 层 | 缺陷 | 修复 |
|---|---|---|---|
| 1 | 数据 | 4/5 植入器静默空转（锚点不匹配即返回原文），样本退化为干净论文 | 重写注入器锚点 + `_require_change` 自证 |
| 2 | 数据 | 生成器 `paper_tex` 写绝对/含盘符路径 → 产物随输出目录变化 | 改仓库相对 POSIX 路径 |
| 3 | 引擎 | 数值引擎 `computed_value = paper_value`（拿报告值自比） | 实现 mpmath 独立复算（从 caption 取公式） |
| 4 | 引擎 | 量纲引擎在无单位模板上无物可判；且把裸变量名当单位（F→farad、T→tesla） | 实现方括号量纲声明代数 + K10 只认带数值系数的单位 |
| 5 | 引擎 | 图引擎 `_find_broken_chains` 恒返回空 | 按引用者环境区分 `dangling_ref` / `dep_chain_break` |
| 6 | 引擎 | 重放把定义式当推导链判 invalid；解析失败误判 invalid | 定义式识别 + 解析失败归 `undecidable`（K4） |
| 7 | 引擎 | 无共享符号的解析残渣被判 `ok`（假阴性） | 收窄定义式判据（右侧须为复合式） |
| 8 | 编排 | `audit_paper` / `selftest` 是 `return 0` / `return True` 空壳 | 实现真实编排链 + 人读/机读双轨报告 |
| 9 | 打包 | antlr 的 `_parse_latex_antlr` 是动态 import，PyInstaller 漏收 → 冻结态静默降级 | 逐个点名 hiddenimports |
| 10 | 打包 | 辅助目录名 `packaging/` 遮蔽 PyPI `packaging`，PyInstaller 无法启动 | 改名 `build_tools/` |
| 11 | 安装 | README 用 `python -m auditor` 但缺 `__main__.py` | 新增薄入口模块 |
| 12 | 安装 | `antlr4-python3-runtime` 上界 `<4.14` → 干净环境装 4.13、sympy `parse_latex` 抛错 | 收窄 `>=4.11,<4.12` |
| 13 | 文档 | README 审计命令路径不存在；K47 只查子串所以全绿 | 修正路径 + 强化 K47 为"路径必须存在" |
| 14 | 字节 | 生成器在 Windows 文本模式注入 CRLF | 显式 `newline=""` 写 LF |

### 4.2 新增守门

| K | 内容 | 文件 |
|---|---|---|
| K50 | 检出率 + 逐样本点名 + 逐类覆盖 + **错误类型归属** | `test_k50_detection_rate.py` |
| K51 | 上述守门的变异验证（重放放行 / 数值弄坏 / 图关检测 / 注入器空转） | 同上 |
| K52 | 冻结态与源码态逐项对账（含 selftest） | `test_k52_frozen_parity.py` |
| K53 | sympy LaTeX 运行时前提（antlr pin + 实跑 parse_latex + 失败不得判 ok） | `test_k53_latex_runtime.py` |
| K54 | audit 编排链 + 双轨报告（同源/可复现/零外链）+ selftest 可证伪 | `test_k54_audit_pipeline.py` |
| K55 | 文本行尾冻结（CR 守门 + 生成物 LF + zip 确定性口径） | `test_k55_byte_freeze.py` |
| K56 | 路径形态归一（POSIX 绝对路径不得被 rebase） | `test_k56_path_forms.py` |

**增强**：K35（原先 CI 缺失时静默通过 → 现要求 CI 存在 + 双解释器矩阵 + PYTHONUTF8 + 裸 console script 冒烟）、
K47（原只查子串 → 现要求 README 路径真实存在、模块可执行）。

---

## 四之二、脱敏扫描与历史改写（如实留档）

### 扫描口径

- **HARD 个人标记**：邮箱 / 用户目录（`\Users\<name>`、`/home/<name>`）/ 手机号 /
  身份证 / API key（`sk-…`）/ GitHub token（`ghp_…`）/ 私钥头
- **LOW 本机路径**：盘符绝对路径（`X:\…` / `X:/…`）
- 扫描面：**工作树 + 全历史（含 tag 可达对象）**，两处都扫

### 扫描工具自身的假绿（两次踩坑，如实记录）

1. `git grep … -- <revs>` 把 rev 当成 **pathspec**，导致 14 个 rev 全部
   "0 命中"——**连阳性对照 `def ` 都是 0**，即整条扫描通道静默空扫。
   修正为 `git grep <revs>` 后阳性对照 **568 行命中**，结论才可信。
2. 宽口径 `[A-Za-z]:[\\/]` 把 `https:/` 里的 `s:/` 判成盘符路径（误报）。
   收紧为 `(?<![A-Za-z])[A-Za-z]:[\\/]`（盘符须为独立 token）。

> 依 skill 纪律：**多 rev 扫描必配阳性对照**——"扫了 0 命中"与"扫描没工作"
> 必须能区分，否则脱敏结论是假绿。

### 发现与处置

| 项 | 结果 |
|---|---|
| HARD（个人标记） | **0 命中**（工作树与全历史） |
| LOW（本机路径） | 工作树修复前 6 处 / 全历史 97 行——**plan/HANDOFF-M1~M5 的"或完整路径"示例块** |
| 处置 | `git filter-repo --replace-text` 重写全历史 + force push |
| 改写后复扫 | HARD 0 / 本机路径标记（`[开发机盘符目录]`、`[用户名]`）**工作树 0、全历史 0** |
| 全新 clone 终验 | `git clone` 后工作树与全历史均 0 命中；K43 守门 5 项通过 |
| 引用清理 | `filter-repo` 后 `rev-list --all` 15 rev，无悬挂引用 |

**K43 守门根因修正**：原判据是"这一行有没有引号"（本意容忍 `/goal` 启动命令前缀），
于是**整条绝对路径启动命令被当成合法启动命令放行**。改为
"任何盘符绝对路径即红"（例外仅限扫描器自身正则行与「不写 X」约定行），
并加用户目录标记扫描、相对用法行非空转自证、`plan/` 全目录扫描。
变异验证：写回绝对路径启动命令 → 红；移除 → 回绿。

---

## 五、发布执行（逐项如实留档）

| 项 | 状态 | 说明 |
|---|---|---|
| 建仓 + 首推 | ✅ | `github.com/yuluo554/math-paper-replay-auditor`（公开，SSH/443 推送） |
| CI 首跑 + 修复 | ✅ | 首跑 ubuntu 红（路径形态缺陷）→ 修复 → 三矩阵全绿 |
| tag `v0.1.0` | ✅ | 打在 CI 绿提交 `a5ce6ff` 上（run `38862249413` 全绿） |
| GitHub Release + 附件 | ✅ | `releases/tag/v0.1.0`，附 `auditor-cli.exe` + `auditor.exe` |
| Release 资产核验 | ✅ | `gh release view --json assets`：draft=false，两附件在列，digest 与台账一致 |
| 附件回下载校验 | ✅ | 下载件 sha256 与台账逐位一致 + 中立目录冻结冒烟通过 |

> **CI 绿是本轮实跑结果**（非"本地等价校验"）：三矩阵全绿，push 事件数=run 数（2=2）逐条配对。
> 首跑失败如实留档（`677e703` 红、原因、修复提交 `c16534f`），未遮掩。
