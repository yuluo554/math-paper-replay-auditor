# plan/HANDOFF-M3.md

> 跨会话交接快照——M1 数据先行 → M2 解析层 → M3 引擎层。
> 版本：v1（2026-10-16）。
> **用法**：新对话启动用 `/goal 读取 "plan/HANDOFF-M3.md" 继续完成任务`（库内写相对路径 `plan/HANDOFF-M3.md`，启动命令从用户侧拼绝对路径）。

---

## 一、当前进度与证据

### 1.1 已完成

| 文档 | 路径 | 状态 |
|---|---|---|
| 00-README 总览 | plan/00-README总览.md | ✅ v1 定稿（M2 状态已回写） |
| 01-题目详细定义 | plan/01-题目详细定义.md | ✅ v1 定稿 |
| 02-算法与口径说明 | plan/02-算法与口径说明.md | ✅ v1 定稿（16 条 K 编号口径） |
| 03-基准套件设计 | plan/03-基准套件设计.md | ✅ v1 定稿（K17-K22） |
| 04-测试与验收 | plan/04-测试与验收.md | ✅ v1 定稿（K23-K32） |
| 05-发布与交付 | plan/05-发布与交付.md | ✅ v1 定稿（K33-K49） |
| 06-架构与技术选型 | plan/06-架构与技术选型.md | ✅ v1 定稿 |
| data/README | data/README.md | ✅ v1 定稿 |
| **HANDOFF-M1** | plan/HANDOFF-M1.md | ✅ v1 定稿 |
| **HANDOFF-M2** | plan/HANDOFF-M2.md | ✅ v1 定稿 |
| **HANDOFF-M3** | plan/HANDOFF-M3.md | ✅ v1 定稿（本对话落盘） |

### 1.2 M1 交付物（已落盘并验证）

| 项目 | 路径 | 状态 |
|---|---|---|
| 确定性 RNG | data/benchmark/generator/deterministic_rng.py | ✅ splitmix64 |
| 论文模板 | data/benchmark/generator/paper_template.py | ✅ |
| 错误植入器 | data/benchmark/generator/error_injector.py | ✅ 修复语法错误 |
| 真值构建器 | data/benchmark/generator/truth_builder.py | ✅ 修复 ID 冲突 |
| 生成器入口 | data/benchmark/generator/__init__.py | ✅ |
| 合成论文样本 | data/benchmark/ (18 个 .tex) | ✅ 5 类错误各 3 + 3 篇干净 |
| 真值台账 | data/benchmark/truth.json | ✅ 无 observed 字段（K17） |
| 覆盖度口径 | data/benchmark/manifest.json | ✅ 总数/采样数双登记（K18） |
| 假数据白名单 | data/benchmark/whitelist.json | ✅ 单一事实源（K36） |
| 真实论文回归集 | data/real_papers/registry.json | ✅ 骨架 |
| 生成器确定性守门 | tests/unit/test_generator.py | ✅ 双跑语义一致 |
| 探活测试 | tests/benchmark/test_probe.py | ✅ 结构/可读/覆盖度 |
| K17 守门 | tests/gate/test_k17_truth.py | ✅ |
| K31 变异验证 | tests/gate/test_k31_mutation.py | ✅ 3 个变异用例 |
| K4 守门 | tests/gate/test_k4_verdicts.py | ✅ |
| K7 守门 | tests/gate/test_k7_tolerance.py | ✅ |

### 1.3 M2 交付物（本对话落盘）

| 项目 | 路径 | 状态 |
|---|---|---|
| 解析器核心 | src/auditor/core/parser.py | ✅ 确定性解析，零模型 |
| 类型定义 | src/auditor/core/types.py | ✅ PaperStructure 等 |
| 解析器单元测试 | tests/unit/test_parser.py | ✅ 12 个用例 |
| K1 守门 | tests/gate/test_k1_coverage.py | ✅ 5 个用例 |
| K2 守门 | tests/gate/test_k2_uncovered.py | ✅ 5 个用例 |
| K3 守门 | tests/gate/test_k3_macros.py | ✅ 4 个用例 |
| K28 守门 | tests/gate/test_k28_encoding.py | ✅ 5 个用例 |

### 1.4 测试证据

```
3.8: 42 passed in 0.37s
3.12: 42 passed in 0.25s
收集数一致（42 items）
```

### 1.5 关键证据

- 16 条 K 编号口径落盘（plan/02）
- 18 个合成样本唯一 ID（B001-001 ~ C003-clean）
- 真值库无 observed 字段（K17 守门 + 变异验证）
- 生成器双跑语义一致（K20 守门 + 变异验证）
- 假数据白名单落盘（K36）
- 双解释器（3.8 + 3.12）全量复跑全绿（42 items）
- 解析器确定性（双跑逐字节一致）
- K1/K2/K3/K28 守门全部落盘

---

## 二、下一里程碑待办（M3 引擎层）

### 2.1 M3 目标

模块②③④⑤ 重放/复算/量纲/依赖图。三级判定语义锁进测试；数值口径单一定义点落地+守门同源断言；两路径实现独立；HTML 无外链。

### 2.2 M3 DoD

- [ ] 符号重放引擎（SymPy 推导链验证）
- [ ] 数值复算引擎（独立路径，不共享核心函数）
- [ ] 量纲代数引擎（SI 7 基向量运算）
- [ ] 依赖图分析引擎（悬空引用/幽灵 label/断链检测）
- [ ] 三级判定语义（ok/invalid/undecidable）
- [ ] 数值口径单一定义点（NUMERICAL_TOLERANCE）
- [ ] 两路径实现独立（守门断言不共享核心函数）
- [ ] 编码守卫覆盖所有入口（K28）
- [ ] 双解释器复跑全绿（K32）
- [ ] 新增守门做变异验证（K31）

### 2.3 M3 待办清单

1. 实现 `src/auditor/core/replay.py`（符号重放）
2. 实现 `src/auditor/core/numerical.py`（数值复算）
3. 实现 `src/auditor/core/dimensional.py`（量纲代数）
4. 实现 `src/auditor/core/graph.py`（依赖图分析）
5. 写 `tests/unit/test_replay.py`
6. 写 `tests/unit/test_numerical.py`
7. 写 `tests/unit/test_dimensional.py`
8. 写 `tests/unit/test_graph.py`
9. 写 `tests/gate/test_k4_verdicts.py`（升级为完整版）
10. 写 `tests/gate/test_k8_paths.py`（两路径独立守门）
11. 写 `tests/gate/test_k10_units.py`（单位不猜测守门）
12. 写 `tests/gate/test_k14_ghost_labels.py`（幽灵 label 守门）
13. 回写 plan/00 里程碑状态
14. 写 HANDOFF-M4.md
15. commit + 双解释器验证

---

## 三、既定口径清单（K 编号，动了会打挂测试）

| K 编号 | 口径 | 改动影响 |
|---|---|---|
| K1 | 解析覆盖率如实报告（分母含未覆盖项） | 改覆盖率计算逻辑 → 测试红 |
| K2 | 未覆盖清单不得静默丢弃 | 改解析器丢弃行为 → 测试红 |
| K3 | 自定义宏需显式声明映射 | 改宏处理逻辑 → 测试红 |
| K4 | undecidable 与 invalid 必须分级 | 改 verdict 语义 → 测试红 |
| K5 | 每类断言登记能力覆盖度 | 改覆盖度统计 → 测试红 |
| K6 | 重放可复跑（同输入同结论） | 改算法引入随机 → 测试红 |
| K7 | 数值口径单一定义点 | 改容差硬编码 → 扫描测试红 |
| K8 | 数值断言不采信符号路径自证 | 改两条路径共享 → 测试红 |
| K9 | 容差一处定义 + 注记同源 | 改注记派生 → 测试红 |
| K10 | 未标单位不猜测 | 改单位猜测逻辑 → 测试红 |
| K11 | 量纲平衡 ≠ 公式正确 | 改报告模板 → 测试红 |
| K12 | 量纲代数确定性 | 改算法引入浮点 → 测试红 |
| K13 | 依赖图可复跑 | 改算法引入随机 → 测试红 |
| K14 | 幽灵 label 仅为提示 | 改报告分级 → 测试红 |
| K15 | 三态判定词汇三处同源 | 改 verdict 常量 → 测试红 |
| K16 | 降级路径全 undecidable + meta 声明 | 改降级逻辑 → 测试红 |
| K17 | 真值库只存输入与期望 | 真值库加 observed → 测试红 |
| K18 | 覆盖度分母反射自代码常量 | 改 MIN_COVERAGE 不联动 → 测试红 |
| K19 | 误报率 0 优先 | 改判定逻辑虚高 → 测试红 |
| K20 | 确定性生成（splitmix64） | 改用 stdlib random → 测试红 |
| K21 | zip 容器字节跨平台冻结 | 改 create_system → 测试红 |
| K22 | 探活打在消费处 | 探活失效 → 测试红 |
| K23 | 测试计数全仓一致 | 增测试不更新 README → 测试红 |
| K24 | 退出码三语义锁进测试 | 改退出码 → 测试红 |
| K25 | 形态失败与行失败分码 | 改退出码 → 测试红 |
| K26 | 双跑逐字节一致 | 改算法引入随机 → 测试红 |
| K27 | K 编号口径守门测试 | 改 K 口径不改测试 → 测试红 |
| K28 | 编码守卫覆盖所有入口 | 漏守入口 → 测试红 |
| K29 | 测试面 = 安装面 = README 指令面 | extras 缺依赖 → 测试红 |
| K30 | 单件异常不中断整批 | 改异常处理 → 测试红 |
| K31 | 守门必须证伪 | 守门无变异验证 → 测试红 |
| K32 | 双解释器复跑 | 3.8 不兼容语法 → 测试红 |
| K33 | extras 不进运行时必需面 | 改 extras 分层 → 测试红 |
| K34 | 测试期 import 的库进 dev extra | 缺测试依赖 → 测试红 |
| K35 | README 与 CI 同 extras | extras 不一致 → 测试红 |
| K36 | 白名单单一事实源 | 改 datas 生成 → 测试红 |
| K37 | 目录与文件条目分档 | 改打包逻辑 → 测试红 |
| K38 | 入包集合 == 白名单（双向） | 漏拷/多拷 → 测试红 |
| K39 | 双 exe hiddenimports/excludes 分档 | CLI 背 Qt → 测试红 |
| K40 | 冻结入口用薄模块 | 入口有相对导入 → AST 测试红 |
| K41 | 窗口版对未知参数 exit 2 | 静默忽略 → 测试红 |
| K42 | exe --selftest 内建参数 | 自检失效 → 测试红 |
| K43 | HANDOFF 库内写相对路径 | 写绝对路径 → 脱敏扫描红 |
| K44 | 留档只写类别与实算来源 | 留档复述词面 → 脱敏扫描红 |
| K45 | 姊妹项目用方向级描述 | 写具体领域词 → 脱敏扫描红 |
| K46 | 附件名一律 ASCII | 中文附件名 → gh CLI 剥名 |
| K47 | README 命令逐字可跑 | 命令不可跑 → 测试红 |
| K48 | 干净环境验证逐条留档 | 留档不实 → 测试红 |
| K49 | 所有入口 _ensure_utf8_stdio() | 漏守入口 → 测试红 |

---

## 四、本机环境坑（只写实测过的）

### 4.1 Python 版本

- 本机：`py -0p` 显示 3.8.8-64（主通道）+ 3.12（构建通道）
- 底线 3.8：所有一次性脚本/冒烟脚本只能用 3.8 语法
- 3.12 用于 PyInstaller 6.x 构建（3.8 上 PyInstaller 5.x 打 GUI 确定性崩）

### 4.2 编码

- 本机习惯 `py -X utf8`，但 CI 是 cp1252
- 所有入口 `_ensure_utf8_stdio()`
- 子进程解码显式 `encoding="utf-8"`
- CI 加 `env: PYTHONUTF8=1`

### 4.3 pip 代理污染

- pip 被注册表系统代理污染（`https://127.0.0.1:7897`）
- 解决：`NO_PROXY="*" no_proxy="*" py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <pkg>`

### 4.4 Git Bash 路径

- `/tmp` 与 Windows Python 路径不通
- 临时文件用工作区相对路径
- 以 `/` 开头的参数会被 MSYS 静默转写

### 4.5 pyc 偶发损坏

- 全程 `PYTHONDONTWRITEBYTECODE=1`（含 pip install）
- 出怪错先清 `__pycache__`

### 4.6 PySide6 3.8 上限

- 3.8.8 → PySide6 6.6.3.1 是最高可解析版本
- 6.7+ requires-python≥3.9，pip 自动回避

### 4.7 PyInstaller 版本

- 打 GUI 必须 ≥6.22.3（5.x 确定性崩在 `Instruction object is not iterable`）
- 打 CLI 可用 5.x，但本项目统一用 ≥6.22.3
- 发布构建固定用 3.12 通道

### 4.8 venv 通道

- `py -m venv` 的 ensurepip 子进程偶发 exit 1 → `--without-pip` 建壳 + 手动 ensurepip
- venv 解释器反复段错误 → 系统 Python + `PYTHONPATH=<目标>/src`

### 4.9 M1 实测新增

- **3.12 通道需显式装依赖**：`py -3.12` 的 venv 不含 sympy/mpmath/pydantic，需 `NO_PROXY="*" no_proxy="*" py -3.12 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple sympy mpmath pydantic pytest pytest-cov`
- **data/ 需 `__init__.py`**：`data.benchmark.generator` 才能被 import，否则 `from data.benchmark.generator import main` 报 `ModuleNotFoundError`
- **error_injector.py 多行字符串语法**：Python 3.8 不支持跨行字符串字面量（未转义换行），必须用 `\n` 转义或三引号
- **truth_builder.py 样本 ID 冲突**：同错误类型的多个样本共享相同 ID（如 `B001-dimension_mismatch`），导致 truth.json 重复条目。修复：加序号后缀 `B001-001-dimension_mismatch`
- **test_generator.py 路径问题**：原测试用 `subprocess.run` 调用 `auditor.benchmark.generator`，但生成器在 `data/` 不在 `src/`。修复：直接 `from data.benchmark.generator import main` 调用 Python API
- **K20 变异验证需路径归一化**：`input_card.paper_tex` 含临时目录路径，两次运行路径不同导致字节比较失败。修复：归一化路径为占位符

### 4.10 M2 实测新增

- **解析器 section 宏处理**：`\section` 是宏不是环境，需单独解析。修复：在 `_parse_sections()` 中用正则匹配 section 宏
- **table 环境嵌套 tabular**：`\begin{table}` 内含 `\begin{tabular}`，解析器会同时提取两个环境。这是正确行为（tabular 是 table 的内容）
- **注释剥离需保留 `\%`**：`%` 前有 `\` 时是转义百分号，不是注释。修复：注释剥离时检查前一个字符是否为 `\`
- **docstring 转义序列警告**：`"""剥离注释（% 到行尾，但保留 \%）。"""` 中 `\%` 是无效转义序列。修复：用原始字符串 `r"""..."""` 或双反斜杠 `\\%`

---

## 五、DoD 逐项 checklist

### M1 DoD

- [x] 生成器可复跑（固定 seed，两次运行逐字节一致）
- [x] 真值库只存输入+期望，无 observed 字段（K17）
- [x] 覆盖度口径落 manifest（五类错误各 ≥3 样本 + 3 篇干净论文）
- [x] 生成器 `--check` 位级一致守门测试（K20） ← **2026-10-21 更正**：此处勾选当时为空转（仓内无 `--check` 实现，手改 `truth.json` 的 `expect.location`/`generator_seed` 无门可发现）；本轮已补齐真实实现与门，见 `plan/RELEASE-M8.md` 与 `tests/gate/test_k20_regen_parity.py`
- [x] 确定性 RNG（splitmix64）落盘
- [x] 假数据白名单（whitelist.json）落盘（K36）
- [x] 真实论文回归集 registry.json 骨架
- [x] K31 变异验证（K17/K20/K22 守门证伪）
- [x] 双解释器（3.8 + 3.12）全量复跑全绿
- [x] 测试计数全仓一致（11 items，双解释器一致）

### M2 DoD

- [x] 解析器可消费生成器产出的 18 个样本
- [x] 结构树含 section / theorem / lemma / proof / equation / table / ref / label
- [x] 宏包清单如实报告
- [x] 未覆盖清单不得静默丢弃（K2）
- [x] 解析覆盖率如实报告（K1，分母含未覆盖项）
- [x] 自定义宏需显式声明映射（K3）
- [x] 编码守卫覆盖所有入口（K28）
- [x] 双解释器复跑全绿（K32）
- [x] 新增守门做变异验证（K31）

---

## 六、关键命令速查

```bash
# 查看当前状态
git log --oneline -5
git status

# 运行测试（3.8）
py -3.8 -m pytest tests/ -v --tb=short

# 运行测试（3.12）
PYTHONPATH=src py -3.12 -m pytest tests/ -v --tb=short

# 生成器确定性守门
py -3.8 -m pytest tests/unit/test_generator.py -v

# 探活测试
py -3.8 -m pytest tests/benchmark/test_probe.py -v

# K31 变异验证
py -3.8 -m pytest tests/gate/test_k31_mutation.py -v

# K17 守门
py -3.8 -m pytest tests/gate/test_k17_truth.py -v

# K1 守门
py -3.8 -m pytest tests/gate/test_k1_coverage.py -v

# K2 守门
py -3.8 -m pytest tests/gate/test_k2_uncovered.py -v

# K3 守门
py -3.8 -m pytest tests/gate/test_k3_macros.py -v

# K28 守门
py -3.8 -m pytest tests/gate/test_k28_encoding.py -v

# 收集数对账
py -3.8 -m pytest tests/ --collect-only -q | wc -l

# 运行生成器（手动）
py -3.8 -c "from data.benchmark.generator import main; main('data/benchmark', min_per_type=3, clean_count=3)"

# 解析器测试
py -3.8 -m pytest tests/unit/test_parser.py -v
```

---

## 七、启动提示词（新对话用）

```
/goal 读取 "plan/HANDOFF-M3.md" 继续完成任务
```

---

## 八、待定决策（需用户拍板）

| # | 决策项 | 选项 | 推荐默认 | 说明 |
|---|---|---|---|---|
| D1 | GitHub 仓库名 | `math-paper-replay-auditor`（纯净）/ `HWS-math-paper-replay-auditor`（带标签） | `math-paper-replay-auditor` | 题面已写明仓库纯净名 |
| D2 | 模型端点默认配置 | 空（用户手动填）/ 示例端点（http://localhost:8000/v1） | 空 | 不随仓分发端点信息 |
| D3 | 真实论文回归集初始规模 | 0 篇（仅骨架）/ 3 篇（1 干净 + 2 有勘误） | 3 篇 | 用于"不误报"验证 |
| D4 | 预置快照生成时机 | M1 生成器产出时 / M3 引擎就绪后 | M1 生成器产出时 | 快照与真值库联动 |
