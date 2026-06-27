# PDF Processing Policy

本文件定义 `more-paper-workflow-pro-skill` 在 Step 6/7/8 中处理 PDF 的统一口径。目标不是把本 skill 改造成全文解析平台，而是在保持 `JSON + Zotero` 主链的前提下，让 PDF 读取更稳定、可回查、可审计。

## 1. 总原则

- 默认不做全量 `PDF -> Markdown` 预处理。
- 默认先读 `文献-Zotero架构对照.json`、Zotero notes、annotations、metadata，再决定是否进入 PDF 全文层。
- PDF 是保真核验源；提取后的 `md/txt/chunks` 是模型工作输入，不得替代原 PDF 的最终真值地位。
- 提取脚本的目标是“稳定复用 + 可回查”，不是完美恢复所有公式、表格和版面结构。
- `prepare_pdf_for_llm.py` 默认使用轻量解析链路；MinerU 仅作为可选增强后端，不是默认依赖。
- Zotero/MinerU 不是 Step 7/8 的硬依赖；没有这些工具时，用户可指定本地证据包，所有材料先归一为 `evidence_pack.json` 再进入写作。
- PDF-only evidence_pack 是正式入口，不是降级补丁；只有 PDF 文件夹的用户也可以直接进入 Step 7。

## 1.0 证据读取优先级

Step 7/8 读取 PDF 与相关材料时，按应用场景选择入口：

1. `zotero_mineru`：同一 Zotero item 下存在 `LLM-for-Zotero-MinerU-cache-*.zip` 时，优先读取 ZIP 中的 `manifest.json`、`full.md`、`images/` 作为图文增强层。
2. `zotero_full`：有 Zotero 条目时，读取 `zotero_get_item_fulltext` 或按页读取，并结合 notes、annotations、metadata 做来源确认。
3. `evidence_pack`：无 Zotero/MinerU 时，读取用户指定的 PDF、BibTeX/CSL JSON、实验报告、数据文件、草稿、标准文件、图片目录；PDF-only evidence_pack 先生成或刷新 `evidence_pack.json`，再按需生成 `prepared_pdf_artifacts.json`、`*.clean.md`、`*.chunks.json`、`*.extraction_report.json`。
4. `pymupdf_fallback`：无法使用 Zotero fulltext/MinerU 且需要快速预读时，使用 PyMuPDF 轻量链路。

Step 7 `deep_read_refine` 的文本源优先级固定为：

```text
zotero_mineru > zotero_fulltext > zotero_note/annotation > PyMuPDF/pdfplumber > abstract_only
```

图片源优先级固定为：

```text
MinerU ZIP / Zotero 图文资产 > 主抽图 > preview fallback
```

场景只决定读取路径，证据等级决定能写多强。摘要、BibTeX、检索结果、展示层 Markdown 只能作为候选或背景；PDF、用户自有实验报告、可核验数据、原始标准文件可在完成核验后支撑强 claim。

PDF-only 入口下，扫描件、OCR 差、表格/公式密集、页码锚点缺失的 PDF 必须标记 `must_check_pdf=true` 或对应 `risk_flags`；这些材料可以用于定位和候选整理，但不得自动升级为强证据。

## 1.1 解析后端选择

`prepare_pdf_for_llm.py` 支持：

- `--parser auto`
  默认模式。先用现有 PyMuPDF 轻量链路；若检测到复杂 PDF，会主动提示“建议改用 MinerU”，但仍继续执行，不阻塞主流程。
- `--parser pymupdf`
  强制使用现有轻量链路，不尝试 MinerU。
- `--parser mineru-local`
  仅当用户本地已安装 MinerU CLI 时使用；不可用时自动回退到 PyMuPDF，并明确打印回退原因。
- `--parser mineru-api`
  仅当用户已提供 API endpoint 或环境变量时使用；不可用时自动回退到 PyMuPDF，并明确打印回退原因。

默认不要求用户额外设置；只有在复杂 PDF 场景下，才主动建议切换到 MinerU。

PyMuPDF 输出必须视为低保真全文工作层。`parser_used=pymupdf` 时，脚本应写入：

- `parser_confidence: low`
- `must_check_pdf: true`
- `risk_flags`: `line_fragmentation` / `reading_order_risk` / `table_damage_risk` / `figure_caption_loss` / `paragraph_reconstruction_needed`

PyMuPDF 可用于快速预读、关键词定位和临时线索；不得直接支撑图表解释、复杂表格、公式、精确数值比较、页码级引语或强 claim。

## 1.1.1 Zotero-MinerU ZIP 缓存

MinerU 回挂给 Zotero 的正式形态是 ZIP 附件，通常命名为：

```text
LLM-for-Zotero-MinerU-cache-*.zip
```

ZIP 内典型文件：

| 文件 | 用途 |
|------|------|
| `full.md` | 图文阅读层，保留 Markdown 图片引用 |
| `manifest.json` | 图文映射首选索引：sections、page、figures、caption、path、charStart/charEnd |
| `content_list.json` / `*_content_list_v2.json` | 版面块级索引：bbox、page_idx、text/image/table 块 |
| `images/` | 图片素材目录 |
| `_llm_source.json` | Zotero 回挂信息：`parentItemKey`、`attachmentKey`、`sourceFilename` |
| `_llm_sync.json` | 同步状态元数据 |

读取规则：

- 优先从 ZIP 直接读取 `manifest.json` 和 `full.md`，不要求用户手动解压。
- 只有被选入正文的图片才复制到项目 `figures/`，正文不得引用 Zotero storage 绝对路径。
- `manifest.json` 是图表候选索引，不是 claim 支撑结论；图是否支撑 claim 由 `figure_evidence_report.md/json` 决定。
- 若 ZIP 缺 `manifest.json`，降级读取 `full.md` 中的图片引用；再缺失时只扫描 `images/`，并标记 `visual_pending`。

## 1.2 首次使用 MinerU 时的提示要求

当脚本建议或尝试使用 MinerU 时，应向用户给出充分说明，至少覆盖：

- **当前默认不会阻塞主流程**：即使没有 MinerU，skill 仍会继续使用现有轻量链路。
- **为什么建议 MinerU**：明确指出检测到的风险信号，如多栏、扫描件、低文本密度、公式/表格密集。
- **本地 CLI 路线**：说明官方支持 CLI，本地常见调用形态是 `mineru -p <input_path> -o <output_path>`；纯 CPU 场景可参考 `-b pipeline`。
- **API 路线**：说明如果用户已有自部署或远端服务，可通过 `--parser mineru-api` + endpoint 接入。
- **长期 API 使用说明**：补一句“如果你计划长期使用 MinerU API，可按官方文档自建或使用官方服务，并准备 endpoint / token 后再启用 `mineru-api`”，但不得把它写成默认前提。
- **在线试用路线**：说明官方仓库提供在线体验入口，可先试用再决定是否本地部署。
- **官方说明来源**：提示用户参考 MinerU 官方仓库的 `Quick Start`、`Online Experience`、`Local Deployment` 章节。

提示语义必须避免两种误导：

- 不得让用户误以为本 skill 已经内置了完整 MinerU 运行时
- 不得让用户误以为“不安装 MinerU 就无法继续当前任务”

## 2. 三档读取模式

### Mode A: `metadata-first`

默认模式。只读取：

- `文献-Zotero架构对照.json`
- Zotero notes
- Zotero annotations
- Zotero metadata
- BibTeX / 中文增强元数据 / 摘要

适用：

- 章节规划
- 背景性综述
- 候选文献筛选
- 低风险概括

### Mode B: `selective-fulltext`

按需读取单篇 PDF 或局部页段。可使用 Zotero fulltext，或先提取为带锚点的 `clean.md/chunks.json` 再喂给模型。带图综述优先复用 Zotero 条目下的 MinerU ZIP；只有没有 ZIP 或 ZIP 不可读时，再考虑重新解析或 PyMuPDF fallback。

适用：

- 关键 claim 需要原文确认
- 方法细节、参数、实验设置需要核对
- notes / annotations / 摘要不足
- 写后引用审计

### Mode C: `batch-fulltext`

批量提取全文，仅用于综述批读、章节预研或大批量证据预处理。默认只在明确需要时启用，不作为所有任务的起点。

适用：

- 文献综述初筛后的批量预读
- 指定章节的大规模证据整理
- 用户明确要求批量全文处理
- 已读核心全文不足，且同一章节需要扩读多篇全文补齐证据链

## 3. 从 A 升级到 B/C 的触发条件

满足任一条件即可升级：

- 需要支撑关键结论、强 claim、机制判断
- 需要核对实验参数、方法步骤、训练细节
- 需要核对页码、原句、图注、表格、公式
- 当前证据层只有 metadata / abstract / notes，无法支撑判断
- 正在执行 Step 7.16 引用审计
- 用户明确要求全文预读、批量综述、章节级证据整理
- 已读核心 T1/T2 全文仍不能支撑当前章节的必要 claim，尤其是机制判断、参数句、图表解释、数值比较、反例或适用边界

若只是背景性概述、主题归类或候选定位，不应默认升级到全文层。

### 3.0.1 扩大全文读取范围的触发与边界

默认先读取当前章节最相关的核心 T1/T2 全文；这只是成本控制起点，不是读取上限。出现以下情况时，应主动扩大全文读取范围：

- 当前强 claim 只有摘要、元数据或候选定位支撑。
- 引用审计、段落审阅或机理论证计划给出 `supplement_pdf_or_fulltext`。
- 已读核心全文覆盖面过窄，只能支持单一材料、单一工艺或单一指标，不能覆盖当前章节要求的对比维度。
- 用户要求投稿级、学位论文定稿级、系统综述级或审稿回应级证据强度。

扩读顺序固定为：

1. 同一章节/集合内未读全文的 T1/T2。
2. 同章相邻小节中与当前 claim 直接匹配的 T1/T2。
3. 用作反例、边界、方法参照或工程约束的 T3。
4. 仍不足时，回退 Step 4/5/6 补检索、补下载或补 Zotero 附件。

扩读后必须记录扩读原因、`reading_depth`、`source_trace` 和可支撑范围。扩读不能把摘要级证据自动升级为全文证据；如果扩读后仍缺少锚点，应降级 claim 或输出证据缺口。

## 3.1 何时主动提示用户使用 MinerU

当轻量链路检测到以下高风险信号时，应主动给出 MinerU 建议：

- 文本密度异常低
- 疑似扫描件 / OCR 风险
- 多栏或碎片化阅读顺序
- 公式 / 表格 / 图注密集
- 轻量链路文本提取几乎失败

提示语义应满足：

- 明确说明“建议使用 MinerU”
- 明确当前仍会继续执行轻量链路
- 明确给出可重跑命令：`--parser mineru-local` 或 `--parser mineru-api`
- 不得把提示写成阻塞门槛

## 4. 高风险内容规则

以下内容不得仅凭提取文本直接进入最终引用或强结论：

- 公式
- 复杂表格
- 图注
- 页码级直接引语
- appendix 细节
- 数值结果的精确比较

这些内容应标记：

- `must_check_pdf: true`
- `risk_flags`: `equation` / `table` / `figure_caption` / `direct_quote` / `appendix_detail`

## 5. 提取后产物的最小要求

任何供 Step 7/8 消费的 PDF 提取结果都应尽量保留以下锚点：

- `paper_title`
- `citekey`
- `zotero_item_key`
- `source_pdf`
- `pages`
- `section`
- `chunk_id`
- `evidence_level`
- `must_check_pdf`
- `parser_used`
- `parser_confidence`

证据包入口还应记录：

- `source_path`
- `source_type`
- `claim_scope`
- `verification_action`

推荐证据层级：

- `metadata_only`
- `notes_or_abstract_supported`
- `pdf_fulltext_supported`

## 6. 清洗规则最低要求

进入全文提取后，至少执行：

- 删除页眉、页脚、页码
- 合并异常断行
- 修复常见连字符断词
- 标记双栏乱序风险
- 标记公式损坏风险
- 标记复杂表格风险
- 尽量保留图表标题或显式占位
- 参考文献区单独分段

若无法可靠修复，不要伪装成高保真结果，应在报告中写明风险。

## 7. 与现有资产链的关系

- 提取结果是 `文献-Zotero架构对照.json` / Zotero item / `pdf-附件池索引.json` 的延伸资产，不是旁路知识库。
- `retrieval_candidates.json` 只能作为候选定位层，不得因为全文提取而自动升级为已验证证据。
- Step 8 只能消费已确认的证据层，不得把候选提取文本当作新增外部证据。
