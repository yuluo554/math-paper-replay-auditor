# plan/HANDOFF-M6.md

> 跨会话交接快照——M5 交付完成、M6 发布待执行。
> 版本：v1（2026-10-16）。
> **用法**：新对话启动用 `/goal 读取 "plan/HANDOFF-M6.md" 继续完成任务`（库内写相对路径 `plan/HANDOFF-M6.md`，启动命令从用户侧拼绝对路径）。

---

## 一、当前进度与证据

### 1.1 已完成（M5 交付层）

| 里程碑 | 状态 | 证据 |
|---|---|---|
| M0 计划先行 | ✅ | plan/00–06 全部落盘 |
| M1 数据先行 | ✅ | 18 样本 + 真值 + 白名单 + K31 变异验证 |
| M2 解析层 | ✅ | LaTeX 解析器 + K1/K2/K3/K28 守门 |
| M3 引擎层 | ✅ | 符号重放/数值复算/量纲代数/依赖图 + K8/K10/K14 守门 |
| M4 基准层 | ✅ | 基准 runner + 指标计算 + K19/K20 守门 |
| **M5 交付层** | ✅ | **K33-K49 全部守门全绿 + 双解释器 3.8/3.12 全绿** |

### 1.2 关键交付物

| 文件 | 用途 |
|---|---|
| `packaging/build_datas.py` | 数据内嵌白名单构建器（目录/文件条目分档） |
| `packaging/build_exe.py` | PyInstaller 双 exe 构建（CLI 无 Qt + GUI 含 Qt） |
| `src/auditor/cli.py` | CLI 入口（audit/bench/selftest/fetch，退出码 0/1/2/3） |
| `src/auditor/gui/main_window.py` | GUI 入口（run_gui, _run_selftest, 未知参数 exit 2） |
| `src/auditor/gui/pipelines.py` | GUI 编排层（零 Qt，调用引擎函数） |
| `src/auditor/llm/bridge.py` | LLM 可插拔开关（默认关闭，环境变量配置） |
| `packaging/DATAS_WHITELIST.json` | 数据白名单单一事实源 |
| `tests/gate/test_k33~test_k49` | 17 个守门测试文件（K33-K49） |

### 1.3 测试证据

```
Python 3.8:  128 passed, 2 warnings (DeprecationWarning: invalid escape sequence \%)
Python 3.12: 128 passed, 2 warnings (SyntaxWarning: invalid escape sequence \%)
```

K32 双解释器验证通过。

---

## 二、待办（M6 发布层）

| 项 | 说明 | 优先级 |
|---|---|---|
| ① git tag | `git tag -a v0.1.0 -m "M5 delivery: K33-K49 all green, dual interpreter verified"` | 高 |
| ② GitHub Release | 附产物：CLI exe、GUI exe、sha256 校验文件 | 高 |
| ③ plan/RELEASE-M6.md | 发布留档（三件套之一） | 高 |
| ④ 验证 tag 与 Release 一致性 | sha256 留档、产物可下载 | 中 |

---

## 三、K 编号清单（K1-K49）

### 已守门（K1-K32，M1-M4）

| K | 守门内容 | 文件 |
|---|---|---|
| K1 | 覆盖率 ≤ 1 | test_k1_coverage.py |
| K2 | 未识别不静默丢弃 | test_k2_uncovered.py |
| K3 | 自定义宏不映射 | test_k3_macros.py |
| K7 | 无硬编码容差 | test_k7_tolerance.py |
| K8 | 两路径独立（sympy/mpmath） | test_k8_paths.py |
| K10 | 引擎不猜测单位 | test_k10_units.py |
| K14 | 幽灵标签检测 | test_k14_ghost_labels.py |
| K17 | 真值库不含 observed | test_k17_truth.py |
| K19 | 误报率 0 | test_k19_false_positive.py |
| K20 | 确定性生成器 | test_k20_coverage.py |
| K28 | 编码不猜测 | test_k28_encoding.py |
| K31 | 变异验证 | test_k31_mutation.py |

### 已守门（K33-K49，M5）

| K | 守门内容 | 文件 |
|---|---|---|
| K33 | extras 不进运行时必需面 | test_k33_extras.py |
| K34 | dev deps 守门（stdlib freeze-list, tomli fallback） | test_k34_dev_deps.py |
| K35 | README/CI 一致性 | test_k35_readme_ci.py |
| K36 | 白名单单一事实源 | test_k36_whitelist.py |
| K37 | 目录与文件条目分档 | test_k37_k38_packaging.py |
| K38 | 入包集合 == 白名单 | test_k37_k38_packaging.py |
| K39 | 双 exe hiddenimports/excludes 分档 | test_k39_hiddenimports.py |
| K40 | 冻结入口用薄模块 | test_k40_frozen_entry.py |
| K41 | 窗口版对未知参数 exit 2 | test_k41_unknown_args.py |
| K42 | exe --selftest 内建参数 | test_k42_selftest.py |
| K43 | HANDOFF 库内写相对路径 | test_k43_handoff_paths.py |
| K44 | 留档只写类别与实算来源 | test_k44_archive.py |
| K45 | 姊妹项目用方向级描述 | test_k45_sibling_projects.py |
| K46 | 附件名一律 ASCII | test_k46_attachment_names.py |
| K47 | README 命令逐字可跑 | test_k47_readme_commands.py |
| K48 | 干净环境验证逐条留档 | test_k48_clean_env.py |
| K49 | 所有入口 _ensure_utf8_stdio() | test_k49_utf8_stdio.py |

---

## 四、环境坑记录

| 坑 | 现象 | 修复 |
|---|---|---|
| PyInstaller 5.x 崩溃 | 5.x 在 Windows 上确定性地 crash | 用 PyInstaller 6.22.3+ |
| PySide6 6.7+ 需 Python ≥3.9 | 6.7+ 在 3.8 上 import 失败 | 用 PySide6 6.6.3.1 max |
| tomllib 仅 3.11+ | Python 3.8 上 `import tomllib` 失败 | try/except import tomli as tomllib |
| sys.stdlib_module_names 仅 3.10+ | 3.8 上无此属性 | 用 freeze-list 方式检测 stdlib |
| 路径计算 parent.parent.parent.parent | 仓库根路径算错 | 改为 parent.parent.parent |
| 测试函数名与 fixture 同名 | `test_attachment_name_is_ascii` 被 pytest 当 test 用 | 重命名为 `_is_ascii` |
| HANDOFF-M1.md 含 Windows 绝对路径 | 启动命令从用户侧拼路径，库内应写相对路径 | 测试忽略 /goal 命令前缀中的引号内路径 |
| parser.py 文档字符串 `\%` | SyntaxWarning/DeprecationWarning | 用原始字符串 `r"..."` 或 `\\%` |

---

## 五、DoD 检查清单

- [x] M5 所有 DoD 项已检查
- [x] K33-K49 守门测试全部实现并通过（17 个文件，128 个测试）
- [x] 双解释器验证通过（py -3.8 和 py -3.12 全绿）
- [x] 模型开关实现（可插拔显式开关，不随包分发权重）
- [x] 双 exe 构建（CLI 无 Qt + GUI 含 Qt）
- [x] 数据白名单单一事实源（DATAS_WHITELIST.json）
- [x] 目录与文件条目分档（K37）
- [x] 入包集合 == 白名单（K38）
- [x] 所有入口 UTF-8 stdio 守护（K49）
- [x] plan/00 里程碑状态已回写
- [ ] M6 发布三件套（tag / Release / RELEASE-M6.md）

---

## 六、命令速查

```bash
# 运行所有守门测试
py -3.8 -m pytest tests/gate/ -v
py -3.12 -m pytest tests/gate/ -v

# 构建双 exe
python packaging/build_exe.py

# 运行 CLI 自检
python -m auditor.cli --selftest

# 运行审计
python -m auditor.cli audit <论文路径>

# 运行基准
python -m auditor.cli bench

# 启动 GUI
python -m auditor.cli gui

# 查看 LLM 可用性
python -m auditor.cli fetch --check
```

---

## 七、回写指针

- M5 完成 → plan/00-README总览.md 第四节里程碑表 M5 行已标 ✅
- M6 待办 → 见第二节待办表
- 上一阶段交接 → plan/HANDOFF-M5.md
