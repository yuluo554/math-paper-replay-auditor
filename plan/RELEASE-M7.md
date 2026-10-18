# plan/RELEASE-M7.md — v0.1.1 发布留档

> 仓库：`yuluo554/math-paper-replay-auditor`
> 里程碑：M7（回访修复 + 补丁版本发布）
> 留档日期：2026-10-18

本文件在 **tag 之前**写好并进 tag 树；发布后才产生的事实列在 §五「tag 后追加事实」。

---

## 一、tag 时点事实

| 项 | 值 |
|---|---|
| 版本 | `v0.1.1` |
| 发布形态 | 源码仓库 + 双 exe 数据 zip + sha256 台账 + demo HTML/GIF + 源码包 |
| 变更范围 | 桌面应用实现、附件清单对齐、LICENSE、台账回填；**不动四引擎判定逻辑** |
| 测试 | 291 passed（v0.1.0 为 278，新增 13 条桌面形态测试） |

---

## 二、修复清单（回访缺陷 → 处置）

| # | 缺陷（v0.1.0 实况） | 级别 | 处置 |
|---|---|---|---|
| D1 | **`auditor.exe` 是占位空窗口**：`QMainWindow()` + 标题 + 尺寸，无 central widget；`gui/pipelines.py` 全仓**无调用方**（孤岛） | 出题级（㉕） | 新增 `gui/window.py`（真窗口：路径/审计/断言表/报告预览/导出）；`main_window.py` 改为真入口；`--selftest` 走同一条零 Qt 链路 |
| D2 | **声明 5 个附件、只上传 2 个**（zip / sha256 / GIF / 2 份 demo HTML 全缺） | 出题级（㉖） | `tools/make_release_zip.py` 按 plan/05 逐名产出；`tools/make_demo_assets.py` 真生成 demo HTML/GIF |
| D3 | **`make_demo_assets.py` 是 `pass`**（TODO M5 未实现） | 出题级（㉔） | 真实现：两份 demo HTML + offscreen 渲染 GIF |
| D4 | **无 LICENSE 文件**，README/pyproject 写 MIT | 写题级 | 补 `LICENSE`（MIT） |
| D5 | **`=6.22.3` 误入库**（pip 重定向产物），且进了 tag 树 | 写题级 | `git rm` + 删除 |
| D6 | **plan/00 索引表 `RELEASE-M6.md ⬜` 与同文件 M6 ✅ 矛盾** | 写题级 | 索引表回填 + 补 RELEASE-M7 行 |
| D7 | **台账 3 行"待 M1/M3/M4"残留** | 写题级（㉒） | 已实现项翻 ✅；扩展项标"首期不交付、不进判定路径" |
| D8 | **§三 承诺的技术报告 / 演示样例不存在**，模型快照写成交付项但从未产出 | 出题级（㉔） | `docs/技术报告.md` + demo HTML/GIF；快照降级为扩展项并在题面写明 |
| D9 | **缺招牌动词表 / 逐形态验收** | 出题级（⑳/⑩） | plan/00 §三之二 + plan/04 §二之二 |

---

## 三、验证（tag 时点）

```bash
python -m pytest tests/ -q                                  # 291 passed
python -m auditor selftest                                  # 通过
python -m auditor bench                                     # 18 样本，误报率 0
dist/auditor-cli.exe selftest                               # 0
dist/auditor.exe --selftest                                 # 0（审计 12 条断言 + 三格式导出）
python tools/make_demo_assets.py                            # demo HTML ×2 + GIF
python tools/make_release_zip.py --tag v0.1.1               # 6 个附件
```

**附件清单（tag 时点，`release/` 下）**：

| 附件 | 说明 |
|---|---|
| `auditor-v0.1.1-win64.zip` | 双 exe 数据包 |
| `auditor-v0.1.1-win64-sha256.txt` | sha256 台账 |
| `demo-clean-vs-error.gif` | 窗口三步演示 |
| `demo-clean-report.html` | 干净论文报告（0 外链） |
| `demo-error-report.html` | 含错论文报告（0 外链） |
| `auditor-source-v0.1.1.zip` | 源码包（from tag 树） |

> exe 不承诺跨机字节一致（PyInstaller + onefile）；可复跑的是**打包这一步**
> （`ZIP_STORED` + 条目排序 + 固定时间戳）。

---

## 四、已知边界（未变）

- 解析覆盖度受限，未覆盖项如实登记；
- `undecidable` ≠ 正确；量纲平衡非充分条件；幽灵 label 非确证错误；
- 模型开关默认关，且从不参与数值结论；
- 预置模型输出快照为扩展项，首期不交付；
- 真实论文回归集只存元数据与本地解析产物。

---

## 五、tag 后追加事实

> 本节内容产生于 tag 之后，与 §一「tag 时点事实」分开记录（preflight ㉒）。

**Release 附件**（`gh release view v0.1.1 --json assets` 回读）：

| 附件 | 大小 | sha256 |
|---|---|---|
| `auditor-v0.1.1-win64.zip` | 176,809,267 B | `74e77a0abe4b7d02e6106c124b5b33b8034b35482174c6b6855cc5eccd4df3c8` |
| `auditor-v0.1.1-win64-sha256.txt` | 456 B | —（台账本身） |
| `demo-clean-vs-error.gif` | 100,622 B | `84dffc4a45e09a45e6a0379ce525d23fe40b446ee2576cc1da5f763c277f8af2` |
| `demo-clean-report.html` | 3,313 B | `a08399765f14f663e1a63d5e2349e95306ab5786e9ceec3870abd6b123c20048` |
| `demo-error-report.html` | 3,335 B | `e41900f69206e59ee8c875e107e854f4f318365e8968cfda15a0aa615d30bdd8` |
| `auditor-source-v0.1.1.zip` | 385,557 B | `4549455d8bea81dcb9058beebd0a948a7627561adaa578de34b7a9ee6858f52e` |

**真下载复核**（`gh release download v0.1.1`，中立目录，`env -u PYTHONPATH -u PYTHONHOME`）：

| 命令 | 结果 |
|---|---|
| 解压 `auditor-v0.1.1-win64.zip` | 含 `auditor/auditor-cli.exe` 与 `auditor/auditor.exe` |
| `auditor-cli.exe selftest` | exit 0 |
| `auditor.exe --selftest` | exit 0（审计 12 条断言 + 三格式导出） |
| 下载件 sha256 vs 台账 | 逐位一致 |
| demo HTML 外链扫描 | 两份均 **0 处** http/https |

**已知形态差异**：zip 内为 onedir 双 exe（不是 onefile 单文件），
与 plan/05 §5.2 的 `auditor-v<tag>-win64.zip`（"双 exe + 数据"）口径一致。

**CI**：tag `v0.1.1` 推送触发（见 GitHub Actions）。
