# data/README.md — 依据查证与数据纪律

仓库 `HWS-math-paper-replay-auditor`（数学论文可验证重放审计器）。基准日：**2026-10-15**。

## 一、依据查证记录（三态）

| # | 依据 | 三态 | 渠道与说明 |
|---|---|---|---|
| 1 | openPangu-2.0-Flash 模型规格 | ✅已核对 | 官方模型卡（hf-mirror 镜像直连）：MoE，92B 总参数 / ~6B 每 token 激活，**原生 512K（524,288）上下文**，~34T tokens 训练 |
| 2 | **512K 上下文 + 满上下文压缩 MLA KV 仅约 12GB** | ✅已核对 | 官方模型卡 + `mrexodia/llama.cpp-openPangu-2.0-Flash` README（GitHub API 直连）——**本题"整篇论文不切块"的工程可行性前提** |
| 3 | openPangu-2.0-Flash 官方基准 | ✅已核对 | 官方模型卡：AIME 2026 93.3（**挂 Python 后 98.1**）；HMMT Feb 2025 91.5（w/Python 96.9）；IMO-AnswerBench 76.5（w/Python 80.8）；GPQA-Diamond 83.7；LiveCodeBench V6 85.1 |
| 4 | **arXiv e-print LaTeX 源码**（核心底座） | ✅已获取 | `https://arxiv.org/e-print/2401.00001` HTTP 200，`content-type: application/gzip`，实测 8.4MB 整包可下（基准日 2026-10-15） |
| 5 | **arXiv API**（元数据） | ✅已获取 | `http://export.arxiv.org/api/query?search_query=all:math.NT&max_results=1` HTTP 200，Atom XML |
| 6 | **SymPy**（符号重放引擎，核心底座） | ✅已获取 | `https://api.github.com/repos/sympy/sympy` 直连 200；纯 Python 可随 exe 内嵌 |
| 7 | **OEIS JSON API / b-file** | ✅已获取 | `https://oeis.org/search?q=...&fmt=json` HTTP 200；b-file `https://oeis.org/A000045/b000045.txt` HTTP 200，纯文本两列 |
| 8 | **Crossref REST API**（DOI 元数据交叉核对） | ✅已获取 | `https://api.crossref.org/works?query=riemann&rows=1` HTTP 200，免密钥 |
| 9 | openPangu 部署路径 | ✅/⬜ | llama.cpp fork ✅；CUDA/ROCm 引擎 ✅；omni-infer（昇腾，gitcode）⬜ 待核对 |
| 10 | **arXiv 使用条款 / 论文再分发边界** | ⬜待核对 | 入库时核对条款；题面已写死"**不随仓分发论文全文**，只存元数据与本地解析结果"。真实论文回归集仅登记 arXiv id 与本地解析产物 |
| 11 | 模型许可 | ⬜待核对 | OPENPANGU MODEL LICENSE AGREEMENT VERSION 2.0；入库时核对"不随仓分发权重"措辞 |
| 12 | 开源空白论据（硬） | ✅已核对 | GitHub repo 检索（基准日 2026-10-15）：`arxiv latex math extraction verification` **0**；`arxiv paper numerical consistency check` **0**；`latex paper proof step checker` **0**；`math paper replication tool` **0**；`paper claim verification math` **0**；`paper equation consistency` **1**（无关）；`openpangu-2.0` **4**（零应用层） |
| 13 | 开源空白论据（软，辅助） | ⬜软论据 | `arxiv-bbox-pipeline` 0★（仅抽 bbox）、`unitgate` 9★（量纲）、`dimensional-consistency-checker` 0★、`arbiter` 0★（多智能体+Z3）；**均非"论文数学断言重放+逐条证据+公开基准"闭环** |

## 二、数据源可获取性记录

| 源 | 可获取性 | 获取方式 | 用途 |
|---|---|---|---|
| arXiv e-print LaTeX 源码 | ✅ 已获取 | HTTP GET（`/e-print/<id>`），无密钥 | 论文结构解析与断言重放（核心输入） |
| arXiv API | ✅ 已获取 | HTTP GET，无密钥 | 论文元数据（标题/作者/版本/分类） |
| SymPy | ✅ 已获取 | pip 包（离线内嵌） | 符号断言重放（核心引擎） |
| OEIS JSON / b-file | ✅ 已获取 | HTTP GET，无密钥 | 数列类断言核验（扩展项） |
| Crossref REST API | ✅ 已获取 | HTTP GET，无密钥 | DOI 元数据交叉核对（扩展项） |
| openPangu-2.0-Flash 端点 | ✅ 可达（用户自备） | OpenAI 兼容端点 / llama.cpp server | 模型在环（显式开关，默认关） |
| 模型权重 | ⛔ 不分发 | — | **不随包分发** |
| 论文全文（真实） | ⛔ 不分发 | — | **不随仓分发**，只存元数据与本地解析结果 |

## 三、合成数据纪律

本仓库**主力数据为合成数据**（自产论文 LaTeX 生成器），非外部抓取。

1. **合成论文 LaTeX 生成器**：程序化生成完整论文骨架（section / equation / theorem / lemma / proof / table / ref / label），并**植入已知错误**。
2. **植入错误五类白名单**（真值台账登记，覆盖度口径即按此列）：
   - `dimension_mismatch`（量纲不一致）
   - `illegal_derivation`（符号推导非法步）
   - `numeric_mismatch`（数值断言算错）
   - `dangling_ref`（label·ref 悬空）
   - `dep_chain_break`（定理依赖断链）
3. **真值台账**：每条样本登记 `input`（论文 .tex）与 `expect`（错误所在公式/行号 + 类型 + 是否干净），**不存 `observed`**（观测运行时实算）。
4. **假数据白名单**（生成器占位标识，防与真实数据混淆）：
   - 假 DOI 前缀：`10.9999/`（保留段，不指向真实 DOI）
   - 假 arXiv 号段：`9999.99999` / `arXiv:9999.99999`
   - 假 ORCID：`0000-0000-0000-0000`
   - 假作者：`A. Example` / `B. Sample` / `Test Author`；假机构：`Example University` / `样例大学`
   - 假期刊：`Journal of Sample Results`（明确标注为合成）
5. **真实论文回归集**：只登记 **arXiv id + 版本 + 本地解析产物 sha256**，**不随仓存全文**；正样本限"有公开勘误/撤回说明"的论文（勘误说明作为外部真值引用来源，标 ⬜ 待核对具体条目），负样本为干净论文（用于"不误报"验证）。
   > **⚠️ 当前交付状态（2026-10-21 实测）**：本目录 `data/real_papers/registry.json` 里
   > **只有一条占位记录**（`paper_id = "arXiv:XXXX.XXXXX"`、`local_parse_sha256 = null`），
   > **真实论文回归集是扩展项、尚未交付**。
   > 因此本仓的"误报率 0"只来自 `data/benchmark/` 里的 **3 份合成干净样本**，
   > **不代表在真实论文上验证过**。
6. **预置模型输出快照**：含模型名、版本、生成参数、原始输出、sha256；随仓只存快照与真值台账。
7. **只增不改**：`data/snapshots/**` 入仓后标 `.gitattributes` `-text` 防 EOL 改写字节。

## 四、编码纪律

LaTeX 源码与快照一律按 **UTF-8** 读写，**不做编码猜测**（静默把非 UTF-8 解成乱码会产出"自洽但错"的重放结果）。非 UTF-8 一律报错并提示转换。
