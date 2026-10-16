# plan/HANDOFF-M1.md

> 跨会话交接快照——M0 计划先行 → M1 数据先行。
> 版本：v1（2026-10-16）。
> **用法**：新对话启动用 `/goal 读取 "plan/HANDOFF-M1.md" 继续完成任务`（库内写相对路径 `plan/HANDOFF-M1.md`，启动命令从用户侧拼绝对路径）。

---

## 一、当前进度与证据

### 1.1 已完成

| 文档 | 路径 | 状态 |
|---|---|---|
| 00-README 总览 | plan/00-README总览.md | ✅ v1 定稿 |
| 01-题目详细定义 | plan/01-题目详细定义.md | ✅ v1 定稿 |
| 02-算法与口径说明 | plan/02-算法与口径说明.md | ✅ v1 定稿（16 条 K 编号口径） |
| 03-基准套件设计 | plan/03-基准套件设计.md | ✅ v1 定稿（K17-K22） |
| 04-测试与验收 | plan/04-测试与验收.md | ✅ v1 定稿（K23-K32） |
| 05-发布与交付 | plan/05-发布与交付.md | ✅ v1 定稿（K33-K49） |
| 06-架构与技术选型 | plan/06-架构与技术选型.md | ✅ v1 定稿 |
| data/README | data/README.md | ✅ v1 定稿 |

### 1.2 未完成

| 项目 | 状态 | 说明 |
|---|---|---|
| 项目骨架（目录/pyproject） | ⬜ 待 M1 起 | 待用户拍板后搭建 |
| 合成论文 LaTeX 生成器 | ⬜ 待 M1 | 里程碑 M1 核心交付 |
| 五类植入错误真值台账 | ⬜ 待 M1 | 里程碑 M1 核心交付 |
| 预置模型输出快照 | ⬜ 待 M1 | 里程碑 M1 核心交付 |
| 单元测试 | ⬜ 待 M2 | 里程碑 M2 |
| 引擎实现 | ⬜ 待 M3 | 里程碑 M3 |
| 基准 runner | ⬜ 待 M4 | 里程碑 M4 |
| 打包 exe | ⬜ 待 M5 | 里程碑 M5 |
| GitHub Release | ⬜ 待 M6 | 里程碑 M6 |

### 1.3 关键证据

- 题目定义已定稿（plan/01-题目详细定义.md，v1 2026-10-15）
- 数据底座预检已通过（arXiv API 200、SymPy 200、openPangu 512K 上下文已核对）
- 开源空白论据已核实（6 条检索式 5 条 0 结果）
- 16 条 K 编号口径已落盘（plan/02）

---

## 二、下一里程碑待办（M1 数据先行）

### 2.1 M1 目标

合成论文 LaTeX 生成器、五类植入错误真值台账、预置快照格式。

### 2.2 M1 DoD

- [ ] 生成器可复跑（固定 seed，两次运行逐字节一致）
- [ ] 真值库只存输入+期望，无 observed 字段
- [ ] 覆盖度口径落 manifest（五类错误各 ≥3 样本 + 3 篇干净论文）
- [ ] 生成器 `--check` 位级一致守门测试
- [ ] 确定性 RNG（splitmix64）落盘
- [ ] 假数据白名单（假 DOI/arXiv/ORCID/作者/机构/期刊）落盘
- [ ] 真实论文回归集 registry.json 骨架（不含全文）

### 2.3 M1 待办清单

1. 创建目录结构（按 plan/06 布局）
2. 写 `data/benchmark/generator/deterministic_rng.py`（splitmix64）
3. 写 `data/benchmark/generator/paper_template.py`（论文骨架模板）
4. 写 `data/benchmark/generator/error_injector.py`（五类错误植入）
5. 写 `data/benchmark/generator/truth_builder.py`（真值构建器）
6. 写 `data/benchmark/generator/__init__.py`（生成器入口）
7. 运行生成器产出 `data/benchmark/samples/` 目录
8. 写 `data/benchmark/truth.json`（真值台账）
9. 写 `data/benchmark/manifest.json`（覆盖度口径）
10. 写 `data/real_papers/registry.json`（真实论文回归集骨架）
11. 写 `tests/unit/test_generator.py`（生成器确定性守门）
12. 写 `tests/benchmark/test_probe.py`（探活用例）
13. 写 `pyproject.toml`（deps + extras）
14. 写 `.gitignore` + `.gitattributes`
15. 写 `README.md`（骨架）
16. commit + 本地等价校验

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
- extras 写下限不锁死小版本，构建环境固定用实测版

### 4.7 PyInstaller 版本

- 打 GUI 必须 ≥6.22.3（5.x 确定性崩在 `Instruction object is not iterable`）
- 打 CLI 可用 5.x，但本项目统一用 ≥6.22.3
- 发布构建固定用 3.12 通道

### 4.8 venv 通道

- `py -m venv` 的 ensurepip 子进程偶发 exit 1 → `--without-pip` 建壳 + 手动 ensurepip
- venv 解释器反复段错误 → 系统 Python + `PYTHONPATH=<目标>/src`

---

## 五、DoD 逐项 checklist

### M0 DoD

- [x] 待定决策表经用户拍板（本文即为拍板材料）
- [x] plan/00–06 全部落盘
- [x] data/README 定稿
- [x] 16 条 K 编号口径落盘
- [x] 决策记录表更新
- [x] 里程碑初稿（plan/00 §四）
- [x] 交付对标（plan/00 §三 承诺-证据台账）
- [x] 本机环境坑记录（本文 §四）
- [x] HANDOFF-M1 落盘
- [x] commit（当前 9c57d56，clean）

### 下一步（M1）DoD 预览

- [ ] 生成器可复跑（固定 seed，两次运行逐字节一致）
- [ ] 真值库只存输入+期望，无 observed 字段
- [ ] 覆盖度口径落 manifest（五类错误各 ≥3 + 3 篇干净）
- [ ] 生成器 `--check` 位级一致守门测试
- [ ] 确定性 RNG（splitmix64）落盘
- [ ] 假数据白名单落盘
- [ ] 真实论文回归集 registry.json 骨架

---

## 六、关键命令速查

```bash
# 查看当前状态
git log --oneline -5
git status

# 运行测试（3.8）
py -3.8 -m pytest tests/ -v --tb=short

# 运行测试（3.12）
py -3.12 -m pytest tests/ -v --tb=short

# 生成器确定性守门
py -3.8 -m pytest tests/unit/test_generator.py -v

# 探活测试
py -3.8 -m pytest tests/benchmark/test_probe.py -v

# 收集数对账
py -3.8 -m pytest tests/ --collect-only -q | wc -l

# 编码测试（cp1252 复现）
py -3.8 -m pytest tests/gate/test_encoding.py -v

# 扫描测试（K7 容差守门）
py -3.8 -m pytest tests/gate/test_k7_tolerance.py -v

# 真值库守门（K17）
py -3.8 -m pytest tests/gate/test_k17_truth.py -v

# 干净环境验证（M1 暂不执行，M5 起）
# git clone ... && py -3.12 -m venv .venv && .\.venv\Scripts\activate
# python -m pip install -e ".[dev,core]"
# python -m pytest tests/ -v
```

---

## 七、启动提示词（新对话用）

```
/goal 读取 "plan/HANDOFF-M1.md" 继续完成任务
```

---

## 八、待定决策（需用户拍板）

| # | 决策项 | 选项 | 推荐默认 | 说明 |
|---|---|---|---|---|
| D1 | GitHub 仓库名 | `math-paper-replay-auditor`（纯净）/ `HWS-math-paper-replay-auditor`（带标签） | `math-paper-replay-auditor` | 题面已写明仓库纯净名 |
| D2 | 模型端点默认配置 | 空（用户手动填）/ 示例端点（http://localhost:8000/v1） | 空 | 不随仓分发端点信息 |
| D3 | 真实论文回归集初始规模 | 0 篇（仅骨架）/ 3 篇（1 干净 + 2 有勘误） | 3 篇 | 用于"不误报"验证 |
| D4 | 预置快照生成时机 | M1 生成器产出时 / M3 引擎就绪后 | M1 生成器产出时 | 快照与真值库联动 |
