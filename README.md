# auditor — 数学论文可验证重放审计器

> 首个面向 openPangu-2.0-Flash 的论文数学断言审计工具。审计核心零模型依赖、可离线复跑；模型接入为可插拔显式开关。

## 特性

- **LaTeX 源码摄入**：整篇论文不切块，结构树 + 宏包清单 + 未覆盖清单如实报告
- **符号断言重放**：SymPy 逐步推导链验证，三级判定（ok / invalid / undecidable）
- **数值独立复算**：mpmath 高精度路径，与符号路径实现独立，防"同源错误互相印证"
- **量纲一致性审计**：确定性量纲代数，未标单位不猜测
- **定理依赖图完整性**：悬空引用 / 幽灵 label / 依赖断链检测
- **内置评测基准**：合成论文植入真值，误报率 0 优先

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/yuluo554/math-paper-replay-auditor.git
cd math-paper-replay-auditor

# 2. 创建虚拟环境
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# 3. 安装
python -m pip install -U pip setuptools wheel
python -m pip install -e ".[dev,core]"

# 4. 自检（内嵌数据定位 + 四引擎全链路 + 基准达标）
python -m auditor selftest

# 5. 运行基准（18 个合成样本：检出率 / 误报率 / 逐类覆盖）
python -m auditor bench

# 6. 审计一篇论文（人读报告；加 --format json 出机读报告）
python -m auditor audit --input data/benchmark/C001-clean/paper.tex

# 7. 只跑一类错误
python -m auditor bench --only numeric_mismatch
```

## 退出码语义

| 退出码 | 含义 |
|---|---|
| 0 | 无确证问题 / 基准全绿（`bench`） |
| 1 | 检出确证问题 / 基准未达标 |
| 2 | 用法错误（缺文件、未知命令、参数错误） |
| 3 | 缺依赖（可选组件未安装，如 GUI 的 PySide6） |

> 非 0 退出码不等于"跑挂了"：`audit` 对含问题的论文返回 1 是**既定语义**。

## 项目结构

```
src/auditor/          # 包源码
  core/               # 引擎层（零模型、确定性）
    parser.py         # LaTeX 解析器
    replay.py         # 符号重放
    numerical.py      # 数值复算
    dimensional.py    # 量纲代数
    graph.py          # 依赖图
    types.py          # 类型定义
  llm/                # LLM 桥接（可插拔、默认关）
  report/             # 报告渲染
  gui/                # GUI（PySide6）
tests/                # 测试
data/                 # 数据（合成基准 + 真实论文元数据）
tools/                # 构建/发布工具
packaging/            # 打包辅助
```

## 评测指标

| 指标 | 目标 |
|---|---|
| 检出率 | ≥ 95% |
| 误报率 | **0** |
| 解析覆盖率 | 如实报告 |
| 复算一致率 | 如实报告 |

## 限制

- **不随仓分发论文全文**：只存元数据与本地解析结果
- **模型开关默认关闭**：审计核心零模型依赖
- **LaTeX 解析覆盖度如实报告**：未覆盖清单不得静默丢弃

## 免责声明

审计结论为提示，不构成对论文正确性、作者或期刊的评判。最终以原文与正式勘误为准。

## 已知环境问题

- Windows 上 `py` 启动器会无视 venv，venv 段落一律用 `python -m pip ...`（激活后 `python` 才指向 venv）
- PyInstaller 打包 GUI 必须 ≥6.22.3（5.x 确定性崩）
- PySide6 在 3.8 上上限为 6.6.3.1

## License

MIT
