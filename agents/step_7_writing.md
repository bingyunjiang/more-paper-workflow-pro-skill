# Step 7: 论文写作

> 利用 Step 1-6 的所有产出，以 Zotero 条目、PDF 附件池和 `文献-Zotero架构对照.json` 作为推荐证据底座，撰写正式学术论文。
> **核心原则：每处引用必须能追溯到 Zotero 条目、PDF 原文、笔记、标注或用户提供的可核验证据，抑制大模型幻觉。Zotero/MinerU 是推荐资产层，不是 Step 7 的硬依赖。**

---

## 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `研究主题.md` — Step 1 产出（研究方向 + 预审结论）
- [ ] `大纲关键词.md` — Step 2 产出（章节结构） + `.skill-state/term_aliases.md` 🆕
- [ ] `检索文献表.md` — Step 4 产出（参考文献 + 评分）
- [ ] `文献库.bib` — Step 4 产出（筛选后 BibTeX 文献库）
- [ ] `zotero-架构.md` — Step 6 产出（Zotero 集合结构）
- [ ] `文献-Zotero架构对照.json` — Step 6 产出（文献到集合、Zotero 条目、PDF 附件的完整机器映射；如直接基于 Zotero 写作，可由 Zotero MCP 动态生成最小映射）
- [ ] `文献-Zotero架构对照.md` — Step 6 产出（人工审阅版，可截断，不作为机器执行源；直接 Zotero 写作时可缺省）
- [ ] `pdf-附件池索引.json` — Step 6 产出（多来源 PDF 附件池、匹配状态、完整路径；直接 Zotero 写作时可缺省）
- [ ] `evidence_pack.json` — 本地证据包索引（可选；无 Zotero/MinerU 时推荐生成）
- [ ] `retrieval_index_manifest.json` — 🆕 RAG 候选定位索引说明（可缺省；仅内部加速层）
- [ ] `retrieval_candidates.json` — 🆕 章节级 claim 候选证据包（可缺省；不可直接当证据）
- [ ] `.skill-state/term_aliases.md` — 🆕 术语标准化映射（确保写作用词与检索一致）
- [ ] `references/literature-review-matrix-schema.md` — 综述矩阵 schema
- [ ] `references/journal-style-learning-guide.md` — 目标体裁/文档风格学习方法论（期刊、学位论文、会议论文、既有草稿均可适配）
- [ ] `references/gbt7714-2015-citation-format.md` — 引用格式规范
- [ ] `references/genre-style-axis.md` — 🆕 target_genre 轴：thesis / journal / review / report / proposal / conference
- [ ] `references/section-function-matrix.md` — 🆕 章节-功能-证据需求矩阵
- [ ] `references/section-blueprint-workflow.md` — 🆕 章节蓝图工作流
- [ ] `references/writing-antipatterns.md` — 🆕 写作反模式库
- [ ] `references/reviewer-protocol.md` — 🆕 reviewer-style 预审输出格式
- [ ] `references/citation-audit-contract.md` — 🆕 写作后引用审计契约
- [ ] `references/figure-writing-interface.md` — 图表与写作接口
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则

---

## 适用任务 (Applicable Tasks)

- 撰写完整学术论文（paper_type × language × target_genre）
- 写文献综述（review 类型专属 8 节骨架 + 7 条纪律）
- 写中英文双边摘要
- 撰写或续写学位论文、课程论文、会议论文、期刊论文的指定章节
- 基于已有草稿补写、改写、扩写其中一部分章节
- 解读审稿意见并生成修稿路线图、逐条回应骨架、证据缺口清单
- 实时引文支撑（7.9）
- 同行评审仿真 + Rebuttal 预演（7.11）
- 科研图表生成（7.14）
- 写后引用审计（7.15）

---

## 不适用任务 (Non-applicable Tasks)

- 大纲生成 → 路由到 `agents/step_2_outline.md`
- 文献检索 → 路由到 `agents/step_4_search_score.md`
- 成稿级精修、全文一致性、表达风险收口、修订后验证 → 路由到 `agents/step_8_polishing.md`

---

## 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 研究主题 | Step 1 | .md | ✅ |
| 大纲关键词 | Step 2 | .md | ✅ |
| 检索文献表 | Step 4 | .md | ✅ |
| BibTeX 文献库 | Step 4 | .bib | ✅ |
| Zotero 架构 | Step 6 | .md/.json | ✅ |
| 文献-Zotero架构对照 | Step 6 / Zotero MCP 动态生成 | .json + .md | 推荐 |
| PDF 附件池索引 | Step 6 / Zotero MCP 动态生成 | .json | 可选 |
| Prepared PDF artifacts | Step 6 / `prepare_pdf_for_llm.py` | `.json` + `.md` | 可选；全文提取后的带锚点工作层 |
| Zotero 条目/PDF 附件 | Zotero 文库 | Zotero MCP | 推荐；非硬依赖 |
| MinerU ZIP 缓存 | Zotero 附件 / 用户提供 | `LLM-for-Zotero-MinerU-cache-*.zip` | 可选；图文增强层 |
| 证据包 | 用户提供 / 项目目录 | PDF、BibTeX、CSL JSON、报告、数据、草稿、标准文件、图片目录 | 无 Zotero/MinerU 时推荐 |
| 已有草稿/指定章节 | 用户提供 | .md/.docx/章节文本 | 可选 |
| 综述矩阵 | Step 7.1 | .csv/.md | 写作前生成 |
| 目标体裁/文档风格画像 | Step 7.2 | `.md` / `.json` | 🆕 |
| 章节蓝图 | Step 7.2 | `.md` / `.json` | 🆕 |
| `section_blueprints` | Step 2 / Step 7.2 | `.md` / `.json` | 推荐；承载章节功能矩阵 + 章节蓝图 |
| MinerU 图文资产 | Zotero 附件 / 用户提供 | `LLM-for-Zotero-MinerU-cache-*.zip` 或等价图文资产包 | `auto_insert_figures=true` 时必选 |

> Step 7 不再直接把 `paper-temp/*.pdf` 当作唯一知识库。PDF 可以来自 Step 5、原有文件、后续补下载、手动整理目录、Zotero 条目附件或用户证据包。若 `pdf-附件池索引.json` 不存在，但 Zotero 条目已带 PDF 附件，则以 Zotero MCP 的 `zotero_get_item_children` / `zotero_get_attachment_path` / `zotero_get_item_fulltext` 为准，必要时再生成临时 `pdf-附件池索引.json` 供审计复用。

**多入口证据 intake：**

Step 7 先识别证据入口，再构造最小证据映射。场景只决定读取路径，证据等级决定能写多强。

| entry_mode | 适用场景 | 默认处理 |
|------------|----------|----------|
| `zotero_full` | 有 Zotero 条目、PDF、notes/annotations | 读取 Zotero 元数据、notes、annotations、fulltext，构造 claim 证据映射 |
| `zotero_mineru` | Zotero 条目下有 MinerU ZIP | 在 `zotero_full` 外读取 ZIP 的 `full.md`、`manifest.json`、`images/` 作为图文增强层 |
| `evidence_pack` | 无 Zotero/MinerU 或用户指定本地材料 | 读取 PDF、文献库、报告、数据、草稿、标准文件、图片目录，生成 `evidence_pack.json` |
| `draft_only` | 只有草稿或写作需求 | 只生成低风险结构稿、待补引用和 `evidence_gap_list.md`，不写强 claim |
| `mixed` | Zotero、证据包、草稿混合 | 以 claim 为中心合并证据，不以文件来源堆材料 |

**证据包最小字段：**

`evidence_pack.json` 中每个来源至少记录：

| 字段 | 说明 |
|------|------|
| `source_path` | PDF、报告、数据、草稿、标准文件、图片或 MinerU ZIP 路径 |
| `source_type` | `pdf / mineru_zip / bibliography / report / data / draft / standard / image / unknown` |
| `evidence_level` | `pdf_fulltext_supported / author_provided / source_document_supported / metadata_only / visual_candidate / candidate_only` |
| `claim_scope` | 可支撑范围，如 `strong_claim_if_traceable` 或 `background_or_candidate` |
| `risk_flags` | 候选层、需回 PDF、图文未确认、字段缺失等风险 |
| `verification_action` | 进入正文前的核验动作 |

无 Zotero/MinerU 时不阻塞 Step 7，但必须要求用户指定证据包或证据目录。没有 PDF、全文、实验报告、可核验数据或标准文件支撑时，只能写背景、结构和待补证据草稿。

**Zotero-MinerU ZIP 规则：**

- 若 Zotero 条目只有 PDF、没有 MinerU ZIP，Step 7 仍可继续读取 Zotero fulltext、notes、annotations 或 PDF 原文；只有当本轮需要图文综述、图表候选或 Word 图文稿时，才建议用户先用 `llm-for-zotero` + MinerU 解析核心 PDF。
- Zotero 中 MinerU 缓存的正式附件形态是 `.zip`，通常命名为 `LLM-for-Zotero-MinerU-cache-*.zip`。
- ZIP 内 `manifest.json` 是图文映射首选索引，`full.md` 是图文阅读层，`images/` 是图像素材，`_llm_source.json` 记录 `parentItemKey / attachmentKey / sourceFilename`。
- MinerU ZIP 是增强缓存，不替代 PDF 原文、Zotero notes 或 annotations 的最终核验地位。
- 如果发现同名已展开目录，只能作为临时缓存复用，不能作为契约前提。
- 若 `auto_insert_figures=true` 且 MinerU ZIP 缺失，应明确降级为 `figure_mode=post_write`；若连正文占位都不适合，则退回 `figure_mode=skip`，不得静默失败。

**独立入口规则：**
如果用户已有 Zotero 文库、已有草稿、已有参考文献、已有 PDF 目录或只要求撰写/续写指定章节，可直接从 Step 7 开始，不要求补跑 Step 1-6。Agent 应先构造最小证据映射：目标章节、大纲片段、可用 Zotero/PDF/笔记证据、引用风险；只有证据不足影响关键 claim 时，才触发 `CP-CITATION-WARN` 或建议回退补证据。

对已有草稿的 direct-entry，应优先判定为以下三类之一：
- `continue-existing`：已有草稿，继续写主体内容
- `chapter-only`：已有草稿或目录，只处理指定章节
- `revision-only`：已有草稿 + 审稿意见/修订目标，只做定向修订

existing-draft 可以跳过前链，但不能跳过证据确认。

**Direct-entry input contract：**

| 可接受输入 | 最小处理 | 降级规则 |
|------------|----------|----------|
| `文献-Zotero架构对照.json` | 作为机器主索引读取 tier、collection、item_key、pdf_path | 缺字段时动态查 Zotero |
| Zotero 集合/标签/条目 key | 只读生成最小映射 | 不要求先跑 Step 6 |
| PDF 目录 / `pdf-附件池索引.json` | 建立附件池和可读证据列表 | 无 Zotero key 时标为本地证据 |
| MinerU ZIP | 读取 `manifest.json`、`full.md`、`images/`，生成图文候选 | 只能作为增强工作层，强 claim 仍需回 PDF/笔记/标注核验 |
| 本地证据包 | 生成 `evidence_pack.json` 最小映射 | 无可核验证据时只写背景或结构稿 |
| `prepared_pdf_artifacts.json` / `*.chunks.json` | 作为全文工作层输入，保留 `chunk_id/pages/evidence_level/must_check_pdf` | 无锚点时只作辅助阅读，不能直接升级为强证据 |
| workflow search results JSON / BibTeX | 构造参考文献候选和证据等级 | 只能作为元数据/摘要级证据，除非补到 PDF/笔记 |
| `paper_card` / Zotero `More-Paper Evidence Card` child note | 恢复文献级证据角色、读取深度和内容贴合边界 | JSON 为主源；Zotero note 只作人类可读副本和 direct-entry 辅助线索 |
| 已有草稿/指定章节 | 识别写作模式和目标章节 | 缺引用审计时标记风险，不阻塞非关键改写 |

Step 7 的成功标准是完成当前写作任务的最小证据闭环，不是补齐 Step 1-6 全套产物。缺少上游产物时必须在输出中标注 evidence_level 和缺口，不得把摘要级证据升级为全文/PDF 证据。

**工件读取优先级：**

从本版开始，Step 7 对统一写作工件采用：

1. `style_profile.json`
2. `section_blueprints.json`
3. `writing_rationale_matrix.json`
4. `workflow_search_results.json` / `文献-Zotero架构对照.json` 中的 `paper_card`，以及 Zotero `More-Paper Evidence Card` child note 辅助线索

作为**机器优先输入**；对应的 `.md` 文件是人工审阅、展示和手工修订层。  
如果 JSON 缺失但 Markdown 存在，可以降级读取 Markdown；如果两者同时存在，以 JSON 为准。

---

## 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 综述矩阵 | CSV/Markdown | 13 列证据矩阵 |
| research_dossier/ | 目录 | 样本状态 + `style_profile` + `section_blueprints` + `writing_rationale_matrix` |
| `retrieval_index_manifest.json` | .json | 🆕 内部索引清单：记录轻量索引 / PDF chunk 索引的来源与规模 |
| `retrieval_candidates.json` | .json | 🆕 章节级 claim 候选证据包：按章节→claim 组织候选片段；仅候选，不是最终证据 |
| `figure_index.json` | .json | 🆕 图号/表号索引：页码、图注、正文引用位置、来源层级 |
| `figure_evidence_report.md/json` | `.md` / `.json` | 🆕 图表证据确认结果：该图/表是否真的支撑某条 claim |
| `evidence_pack.json` | .json | 无 Zotero/MinerU 或混合证据入口下的最小证据映射 |
| 论文初稿 | .md，完成后可导出 .docx | 含完整结构和参考文献；默认先写 Markdown |
| 指定章节草稿 | .md，完成后可导出 .docx | chapter-only / continue-existing 模式产出；默认先写 Markdown |
| 图文联合草稿 | .md/.docx | 写文后或同步插图后的版本，保留正文引出句、图后解释句和图表证据链 |
| 修稿路线图 | .md | `revision_roadmap.md`，逐条审稿意见的优先级、章节绑定、证据动作 |
| 回应骨架 | .md | `response_letter_skeleton.md`，Point-by-Point 回应框架 |
| 证据缺口清单 | .md | `evidence_gap_list.md`，需回退 Step 4/6/7.2 的证据问题 |
| 中→英术语对照表 | .md | zh-to-en 模式额外产出 |
| 写作风险摘要 | .md | `draft_risk_summary.md`，记录反模式、证据空洞与需回退问题 |
| 评审报告 + rebuttal-预演 | .md → .pdf | 7.11 质量门产出 |
| 图表 | SVG/PDF/TIFF/JPG/PNG | 7.14 产出或从 MinerU ZIP/证据包复制，保存到 `figures/` |
| 引用审计报告 | .md → .pdf | 7.16 产出 |
| 状态卡 | .md block / 对话块 | 当前 Step、entry_mode、输入依据、证据风险、下一步推荐 |

> 其中 `style_profile.json`、`section_blueprints.json`、`writing_rationale_matrix.json` 是机器工件；对应 `.md` 是展示层与审阅层。
> `retrieval_index_manifest.json`、`retrieval_candidates.json` 是内部加速层工件，只用于“找哪里可能有证据”，不直接进入正文、综述矩阵或审计结论。第一版 `retrieval_candidates.json` 只覆盖文字证据，不并入图表证据子链。
> `figure_index.json`、`figure_evidence_report.md/json` 是图表证据子链工件，用于“图表定位、图注绑定、图表 claim 确认”，不替代文字证据主链。
> 图文联合模式下，正文和图表必须共用同一份 `argument_plan`；没有 MinerU ZIP 时，只允许正文占位，不允许自动选图；`post_write` 与 `auto_insert` 只是执行顺序不同，证据链要求相同。

**DOCX 导出时机：**

Step 7 默认先完成 Markdown 主稿和配套证据工件；当前写作范围完成后，才提示用户是否导出 DOCX。除非用户明确要求“边写边给 Word”或“每章给导师看”，否则不得在每个写作增量后自动导出 DOCX。导出时使用 `scripts/md_to_docx.py`，并确保正文图片引用的是项目内 `figures/` 的相对路径。若开启 `auto_insert_figures=true`，则导出前必须完成图文绑定和 `figure_evidence_report` 生成。

---

## 执行流程 (Execution Flow)

### 前置输入

写作开始前，确认以上所有前置输入文件可访问。Step 7 支持两种入口：

| 入口 | 适用场景 | 必要条件 | 处理方式 |
|------|----------|----------|----------|
| Step 6 产物入口 | 已按本工作流完成 Zotero 架构、对照和附件池 | `文献-Zotero架构对照.json`、Zotero 条目、PDF 附件 | 直接按 JSON 映射读取证据 |
| Zotero 直接入口 | 用户已有 Zotero 文库，未生成本工作流的附件池索引 | Zotero 集合/条目可读，核心条目有 PDF/笔记/标注 | 通过 Zotero MCP 动态读取条目、附件、笔记和全文，并生成最小映射 |

**缺少 `pdf-附件池索引.json` 时：**
1. 不阻塞写作。
2. 先用 Zotero MCP 读取目标集合或用户指定条目的 children/attachments。
3. 能获取本地路径时，动态写入或刷新 `pdf-附件池索引.json`。
4. 不能获取本地路径但能通过 `zotero_get_item_fulltext` 读到全文时，仍可生成综述矩阵和写作证据，但审计报告中标记 `pdf_path_unavailable`。
5. 如果条目既无附件、又无笔记/标注/全文，但有完整摘要和可靠元数据，则可作为“摘要级证据”；如果连摘要也缺失，则只能作为“元数据候选”。

**Step 7 的功能边界：**

Step 7 是写作生产层。它可以在正文生成过程中完成基础可读性整形，但不承担成稿级润色。用户不需要感知内部拆层；对用户仍然只表现为“写作、续写、写综述、审稿前自检”等任务。

| 子步骤 | 核心功能 | 主要输入 | 主要输出 |
|--------|----------|----------|----------|
| 7.1 | 生成文献证据矩阵 | Zotero 条目/笔记/标注、PDF 附件、对照 JSON | `综述矩阵.csv/.md` |
| 7.2 | 学习目标体裁/文档风格并生成统一写作工件 | 目标样本文献/学位论文规范/已有草稿、Step 2 大纲、综述矩阵 | `style_profile.md/json` + `section_blueprints.md/json` + `writing_rationale_matrix.md/json` |
| 7.3 | 写作反模式闸门 | 已有草稿、写作蓝图、证据矩阵 | 反模式风险与回退要求 |
| 7.4 | 论文类型、目标体裁与语言识别 | 研究主题、大纲、投稿/毕业/课程目标 | paper_type + target_genre + language |
| 7.5 | 写作范围识别 | 写作范围、已有草稿、用户任务 | full-document / chapter-only / continue-existing / abstract-only / review-only / revision-only |
| 7.6 | 写作模式、语言规则与章节级论证计划 | `section_blueprints`、综述矩阵、已有草稿、章节范围 | `argument_plan.md/json` |
| 7.7 | 内部写作流水线 | `argument_plan`、章节蓝图、证据矩阵 | 可读性整形后的正文单元 |
| 7.8 | 章节级写作规则 | 大纲、矩阵、风格画像、已有草稿 | `论文初稿.md/.docx` 或指定章节草稿 |
| 7.9 | 实时引文支撑 | 已入库 Zotero 文献为主，新文献走回流闭环 | 段落引用匹配报告 |
| 7.10 | 防幻觉机制 | 引用、证据等级、JSON 追溯 | 引用安全规则 |
| 7.11 | 同行评审仿真与修稿闭环 | 初稿、矩阵、风格画像、审稿意见 | `评审报告.md` + `rebuttal-预演.md` + `revision_roadmap.md` |
| 7.12 | `revision-only` 修订执行 | 已有草稿、审稿意见、证据状态和写作蓝图 | 修订后正文 + 修订日志 |
| 7.13 | 复评 | `评审报告.md`、`revision_roadmap.md`、修订后正文、`引用审计报告.md` | `rereview_report.md` |
| 7.14 | 科研图表生成 | 初稿、数据文件、图表规范 | `figures/` + 图表清单 |
| 7.15 | 写后引用审计 | 初稿、Zotero 条目、PDF/笔记/标注证据 | `引用审计报告.md` |
| 7.16 | 引用风险 checkpoint | WARN/弱引用/摘要级证据进入关键 claim 前 | `CP-CITATION-WARN` |
| 7.17 | 图文联合插图 | 初稿、图文资产、图表意图、MinerU ZIP | `figure_index.json` + `figure_evidence_report.md/json` + 带引出句的正文段落 |

### 7.1. 入口判定：target_genre 与 writing_mode

Step 7 进入正文前，必须先明确两件事：

1. `target_genre` 是什么：
   - `thesis`
   - `journal`
   - `review`
   - `report`
   - `proposal`
   - `conference`
2. `writing_mode` 是什么：
   - `full-document`
   - `chapter-only`
   - `continue-existing`
   - `abstract-only`
   - `review-only`
   - `revision-only`
   - `pre-review`

默认原则：

- `target_genre` 决定默认结构深度和语气，不由期刊 prestige 反向主导。
- `writing_mode` 决定本轮输出范围，不因“能写更多”而擅自扩写。
- 未确认 `target_genre` 时，默认按用户当前任务选择最稳妥的通用体裁：
  - 学位任务 -> `thesis`
  - 投稿任务 -> `journal`
  - 综述任务 -> `review`
  - 工程交付 -> `report`
  - 开题/计划 -> `proposal`

### 7.2. 生成文献证据矩阵（写作前证据组织）

**13 列矩阵：** 作者年份 | 标题 | 研究问题 | 理论/概念 | 数据/样本 | 方法 | 核心发现 | 贡献 | 局限 | 与我的主题关系 | 可引用摘录 | 我的笔记 | DOI/URL

**图表证据可选扩展字段：**
- `figure_refs`
- `table_refs`
- `figure_evidence_level`

**输入优先级：**
```
0. 文献-Zotero架构对照.json / Zotero 动态映射     ← 机器主索引：tier/score/collection/zotero_item_key/pdf_path
1. retrieval_candidates.json（如存在）         ← retrieved_candidate 候选清单，必须二次确认
2. Zotero 笔记 (zotero_get_notes)              ← 最高质量人工证据
3. PDF 标注/高亮 (zotero_get_annotations)       ← 精读标注
4. Zotero 元数据 (zotero_get_item_metadata)     ← 标题/作者/DOI/摘要/URL/Extra/source_id
5. PDF 全文 (zotero_get_item_fulltext)          ← 完整原文
6. BibTeX/中文元数据 JSON/摘要                  ← 摘要级证据，只能支撑低风险概括
```

> 不要一上来就读 PDF 全文。优先用 `文献-Zotero架构对照.json` 确定 T1/T2/T3、集合归属、Zotero item key 和 PDF 状态；如存在 `retrieval_candidates.json`，只把它视为 `retrieved_candidate` 候选，不得直接写入正文或矩阵；必须再回到笔记、标注、元数据或 PDF 原文确认。`.md` 只用于人工审阅。

#### 7.2.0. 大纲-集合锁定取证

- Step 7 默认按“大纲片段 -> Zotero 子集合/条目映射”读取证据，不扫整个 Zotero 文库。
- 当本轮任务是 `chapter-only` 或用户明确指定 `1.1 / 1.1.1 / 2.3` 等节号时，只读取当前节号对应的集合、子集合、条目和附件。
- 若 `section_blueprints.json`、`argument_plan.json`、`文献-Zotero架构对照.json` 同时存在，应先用它们确定当前小节的 `collection / item_key / pdf_path` 范围，再开始读笔记、标注或 PDF。
- 仅当当前小节证据不足以支撑必要论点时，才允许向同章相邻小节映射的集合作有限扩展，并在输出中标记扩展依据。
- 不得因为“文库里还有很多相关文献”就提前读取后续小节集合，更不得把后续节的论证提前写入当前节。
- 如果用户已经给出等价的章节-集合映射，直接使用该映射，不要求回跑 Step 6。

#### 7.2.1. PDF 读取模式

Step 7 默认遵循 `references/pdf-processing-policy.md`，固定使用以下三档模式：

- `metadata-first`
  只读 `文献-Zotero架构对照.json`、Zotero notes、annotations、metadata、BibTeX/中文元数据/摘要。适用于章节规划、背景性综述、候选文献筛选和低风险概括。
- `selective-fulltext`
  当关键 claim、方法细节、参数、实验设置、页码、图注、表格或公式需要原文确认时，定点读取单篇 PDF、页段或小节；必要时可先提取为带锚点的 `clean.md/chunks.json`。
- `batch-fulltext`
  只用于综述批读、章节预研或用户明确要求的批量全文处理，不作为所有写作任务的默认起点。

#### 7.2.2. 从元数据层升级到全文层的触发条件

满足任一条件即可从 `metadata-first` 升级到 `selective-fulltext` 或 `batch-fulltext`：

- 需要支撑关键结论、强 claim、机制判断
- 需要核对实验参数、方法步骤、训练细节
- 需要核对页码、原句、图注、表格、公式
- 当前只有 metadata / abstract / notes，无法支撑判断
- 正在执行 7.16 引用审计
- 用户明确要求全文预读、批量综述或章节级证据整理

若只是主题归类、研究脉络说明、低风险综述句或候选定位，不应默认升级到全文层。

#### 7.2.3. 全文提取结果的使用约束

若使用 `scripts/prepare_pdf_for_llm.py` 或其他等价方式提取 PDF 文本，产物至少应保留：

- `paper_title`
- `citekey`
- `zotero_item_key`
- `source_pdf`
- `pages`
- `section`
- `chunk_id`
- `evidence_level`
- `must_check_pdf`

推荐 `evidence_level`：

- `metadata_only`
- `notes_or_abstract_supported`
- `pdf_fulltext_supported`

提取文本是模型工作输入，不替代原 PDF 的最终真值地位。

**纳入范围：**
- T1/T2/T3 均进入综述矩阵。T1/T2 是写作主证据，T3 作为背景、补充、反例或方法参照。
- T4 已在 Step 4 剔除，默认不进入 Step 7；如用户要求补充，只能作为“候选补查文献”，不得直接引用。
- 中文文献必须保留中文标题、作者、来源、年份、source/source_id、article_url；无真实 DOI 时不得用 `cnki.xxx` / `wanfang.xxx` 冒充 DOI。
- 写作优先使用 `VERIFIED` / `VERIFIED_LOCAL` 且 Tier 为 T1/T2 的文献；T3 主要作背景、补充、反例或方法参照。
- `WARN` 文献只能用于背景性描述、研究脉络或待补查线索，不能支撑关键结论、实验参数、性能提升、机制证明或强因果判断。
- `REJECT` 文献不得进入综述矩阵、正文引用或 Zotero 写入计划；若用户要求保留，只能放入“补查候选/异常清单”。
- `retrieved_candidate` 只是“可能相关”，不得直接升级为 `VERIFIED` / `VERIFIED_LOCAL`，也不得直接写入矩阵或正文。
- 若文献包含关键图表或表格，应把图号、页码、图注/表题先写入 `figure_index.json`，再决定是否进入图表证据子链。

**仅有元数据/完整摘要的条目用途：**

| 证据状态 | 可用于 | 不可用于 | 引用强度 |
|----------|--------|----------|----------|
| 完整元数据 + 完整摘要，无 PDF | 综述矩阵的研究问题/方法概述/主题归类/背景句/待精读优先级 | 具体数据、实验参数、模型细节、强结论、页码级原文摘录 | Weak/Background |
| 完整元数据，无摘要、无 PDF | 去重、集合归类、检索补全、参考文献候选 | 正文 claim 支撑 | Candidate only |
| 元数据 + Zotero 笔记/标注，无 PDF | 若笔记/标注明确记录原文依据，可支撑对应 claim；同时标记需补 PDF | 超出笔记/标注范围的细节 | Moderate，需补全文 |
| Step 4 `WARN` 文献 | 背景、研究脉络、待补查线索 | 关键结论、强 claim、实验数据、机制证明 | Weak/Background |

> 摘要可以派上用场，但不能被当作全文。它适合判断“这篇文献研究什么、用了什么大类方法、与主题是否相关”，不适合支撑“作者具体发现了多少、参数如何设置、机制如何证明”这类强断言。

#### 7.2.4. 高风险内容回 PDF 规则

以下内容不得仅凭提取文本直接进入最终引用或强结论，必须回到原 PDF 或可核验的 Zotero 原文层确认：

- 公式
- 复杂表格
- 图注
- 页码级直接引语
- appendix 细节
- 数值结果的精确比较

这类内容应显式标记：

- `must_check_pdf: true`
- `risk_flags`: `equation` / `table` / `figure_caption` / `direct_quote` / `appendix_detail`

**缺失值约定：** `未提及`（论文确实未讨论）/ `待补充`（计划后续补全）/ `推断：{内容}`（基于已有信息合理推断）

### 7.3. 目标体裁/文档风格学习与写作蓝图

**核心理念：** paper_type 轴告诉你"写什么类型的论文"，目标体裁/文档风格学习告诉你"这份文本应该按什么规范、结构深度和语言节奏来写"。目标可以是期刊，也可以是学位论文、会议论文、课程论文、开题报告，或用户已有草稿的既有风格。

> 从本版开始，Step 7 明确采用 `target_genre-driven`，而不是默认锁定某个高水平期刊风格。目标期刊仍可作为局部约束，但不应覆盖体裁本身。

**目标类型：**

| target_genre | 适用场景 | 风格/结构依据 |
|-------------|----------|---------------|
| `journal` | 目标期刊论文 | 目标期刊近期样文、author guidelines、投稿模板 |
| `thesis` | 硕士/博士学位论文 | 学校论文规范、学院模板、已有章节、大纲结构 |
| `conference` | 会议论文 | 会议模板、页数限制、领域样文 |
| `course-paper` | 课程论文/阶段报告 | 课程要求、教师给定格式、已有材料 |
| `existing-draft` | 已有部分内容，只续写/改写一部分 | 用户已有草稿的术语、语气、标题层级、引用格式 |

**写作范围：**
- `full-document`：从大纲开始撰写完整论文。
- `chapter-only`：只撰写一个或多个指定章节，如“绪论”“文献综述”“方法”“讨论”。
- `continue-existing`：在已有草稿基础上续写、补写或局部替换。
- `abstract-only`：只写中文摘要、英文摘要或双边摘要。
- `review-only`：只产出综述章节或综述主体，不扩展为完整论文。
- `revision-only`：不新增主体内容，只根据证据和风格规则修改已有章节，并生成修稿路线图与逐条回应骨架。

**工作流：**
```
Step 7.2-0: 样本盘点      → style_sample_status.md/json (样本来源、数量、缺口、回退策略；辅助元数据)
Step 7.2-1: 风格剖析      → style_profile.md/json         (统一风格画像 schema)
Step 7.2-2: 章节蓝图      → section_blueprints.md/json    (统一章节蓝图 schema，内含章节功能矩阵字段)
Step 7.2-3: 写作逻辑矩阵  → writing_rationale_matrix.md/json (统一单元级理由 schema)
Step 7.2-4: LaTeX 校验    → latex_check.md（可选）
```

**`style_profile` 最小统一字段：**

| 字段 | 说明 |
|------|------|
| schema_version | schema 版本 |
| target_genre | 目标体裁 |
| target_name | 目标期刊/学位类型/报告名称 |
| sample_source | 样本来源 |
| sample_count | 样本数量 |
| confidence | 画像置信度 |
| structure_rules | 结构规则 |
| language_rules | 语言规则 |
| citation_rules | 引用规则 |
| figure_rules | 图表规则 |
| constraints | 约束 |
| warnings | 风险提醒 |

**`section_blueprints` 最小统一字段：**

| 字段 | 说明 |
|------|------|
| schema_version | schema 版本 |
| section_id | 章节编号 |
| section_title | 章节标题 |
| section_function | 本章功能 |
| key_claims | 核心论点列表 |
| evidence_needed | 证据类型 |
| evidence_basis | 当前可用证据 |
| do_not_write | 本章不该承载的内容 |
| expected_length | 预期长度 |
| figure_needs | 图表/表格需求 |
| transition_from | 承上关系 |
| transition_to | 启下关系 |
| style_notes | 风格约束 |
| risk_flags | 风险标签 |

**`writing_rationale_matrix` 最小统一字段：**

| 字段 | 说明 |
|------|------|
| schema_version | schema 版本 |
| unit_id | 单元编号 |
| parent_section_id | 上级章节编号 |
| unit_name | 单元名称 |
| what_it_does | 该单元做什么 |
| motivation_link | 如何服务总论证 |
| claim_binding | 绑定的 claim |
| evidence_used | 使用的证据 |
| quality_check | 通过条件 |
| risk_notes | 风险备注 |

> `style_sample_status` 是 `style_profile` 的辅助元数据，不再与主 profile 并列成另一套半独立风格工件。`章节功能矩阵` 从本版开始视为 `section_blueprints` 的视图/最小版，不再形成第四套 schema。

### 7.4. 写作反模式闸门

在开始 7.8 正文生成前，必须用 `references/writing-antipatterns.md` 做一次轻量检查。至少排查以下问题：

- 文献堆砌，不形成论证
- 章节功能漂移
- 强 claim，弱证据
- 风格目标不明
- 直写正文，不做蓝图

若命中以上问题：

- 轻度问题：继续写，但写入 `draft_risk_summary.md`
- 中度问题：先补 `section_blueprints.md` 或 `章节功能矩阵`
- 重度问题：回退 Step 2、Step 4 或 Step 6 补结构/补证据

**两种分析深度：**

| 模式 | 范文数 | 时长 | 产出 | 适用场景 |
|------|:---:|------|------|------|
| **Flash** | 3 篇 | ~3 min | `style_profile.md/json` | 初次投稿该期刊 |
| **Pro** | 6 篇 | ~8 min | `style_profile.md/json` + `research_dossier.md` | 核心目标期刊/学位论文/既有草稿 |

```bash
python3 scripts/learn_journal_style.py --target-type journal --target-name "Applied Thermal Engineering" --sample-source zotero --collection "目标期刊样本" --mode flash
python3 scripts/learn_journal_style.py --target-type thesis --target-name "硕士学位论文" --sample-source draft --draft 论文已有草稿.md --mode flash
python3 scripts/generate_section_blueprints.py research_dossier/style_profile.md 大纲关键词.md --evidence 综述矩阵.csv --output research_dossier/
python3 scripts/generate_writing_rationale.py research_dossier/section_blueprints.md --style-profile research_dossier/style_profile.md --output research_dossier/writing_rationale_matrix.md
```

> 目标样本是“风格学习语料”，不等同于 Step 4 的主题文献库。样本可来自目标期刊近期代表作、学位论文模板、学校格式规范、用户指定 PDF 目录、Zotero 样本集合或已有草稿；不得默认使用 `paper-temp/` 中的全部研究文献作为目标风格样本。

**样本集合命名约定：**

| target_genre | 推荐 Zotero 集合名 | 说明 |
|-------------|--------------------|------|
| `journal` | `目标风格样本 / 期刊-{target_name}` | 目标期刊近期样文、投稿模板、author guidelines |
| `thesis` | `目标风格样本 / 学位论文-{学校或层级}` | 学校模板、学院规范、优秀学位论文、已有章节 |
| `conference` | `目标风格样本 / 会议-{target_name}` | 会议模板、页数限制、领域样文 |
| `course-paper` | `目标风格样本 / 课程论文-{课程名}` | 课程要求、评分 rubrics、已有材料 |
| `existing-draft` | `目标风格样本 / 已有草稿-{项目名}` | 用户草稿、已定稿章节、导师修改稿 |

> 集合名只是推荐约定，不是硬性要求；如果用户直接提供目录、文件或草稿，也可以作为样本源。但 7.2 必须把实际使用的样本写入 `style_sample_status.md/json`。

**样本来源规则：**
1. 优先使用用户指定的样本 PDF、Zotero 集合、学校模板、投稿模板或已有草稿。
2. `journal` 未指定样本时，可从 Step 4/6 中筛选 `publication_title` 与目标期刊一致的近期 T1/T2 文献。
3. `thesis` 未指定样本时，使用学校/学院格式规范和已有章节；没有规范时先生成通用学位论文蓝图并标记待确认。
4. 样本不足时，先报告缺口，再建议补充目标样本；不要把非目标体裁文本混入风格画像。
5. 风格学习只学习结构、语气、引用密度、图表呈现和章节节奏；不得复制句子或段落。

**样本数量与回退策略：**

| 状态 | 样本条件 | 处理方式 | confidence |
|------|----------|----------|------------|
| 充足 | `journal/conference` ≥ 3 篇；`thesis` ≥ 1 个模板/规范 + 1 篇样文或已有章节；`existing-draft` ≥ 1500 字 | 正常生成风格画像和章节蓝图 | high |
| 偏少 | `journal/conference` 1-2 篇；`thesis` 只有模板/规范或只有已有章节；`existing-draft` 500-1500 字 | 生成低样本风格画像，标记缺口，不阻塞写作 | medium |
| 缺失 | 无可用样本，仅有 target_genre / target_name | 使用通用体裁规则 + Step 2 大纲，必须提示用户补样本 | low |

**`style_sample_status.md` 推荐格式：**

```text
标题：目标风格样本状态

target_genre: thesis
target_name: 硕士学位论文
sample_source: existing_draft + university_template
sample_count: 2
confidence: medium

已使用样本
1. 论文已有草稿.md
2. 学校硕士论文模板.docx

缺口
- 缺少优秀学位论文样本
- 缺少学院具体格式细则

回退策略
使用学校模板 + 已有草稿风格 + 通用硕士论文结构规则。
```

**`style_sample_status.json` 最低字段：**

```json
{
  "target_genre": "thesis",
  "target_name": "硕士学位论文",
  "sample_source": ["existing_draft", "university_template"],
  "sample_count": 2,
  "confidence": "medium",
  "samples": [
    {"title": "论文已有草稿.md", "source_type": "draft", "path_or_zotero_key": "论文已有草稿.md"},
    {"title": "学校硕士论文模板.docx", "source_type": "template", "path_or_zotero_key": "学校硕士论文模板.docx"}
  ],
  "gaps": ["缺少优秀学位论文样本", "缺少学院具体格式细则"],
  "fallback_strategy": "使用学校模板 + 已有草稿风格 + 通用硕士论文结构规则"
}
```

### 7.5. 论文类型、目标体裁与语言识别

**轴一：论文类型（paper_type）**

| paper_type | 特征 | 典型章节骨架 |
|------------|------|-------------|
| **research** | 有明确的实验/仿真研究 | intro → related-work → method → experiments → discussion → conclusion |
| **methods** | 侧重方法/工具创新 | intro → problem-statement → design → implementation → validation → comparison |
| **hypothesis** | 先提假设再做实验检验 | background → hypothesis → test-design → results → implications |
| **algorithmic** | 算法/模型为核心贡献 | intro → preliminaries → algorithm → analysis → experiments → related-work |
| **review** | 系统综述/调研 | 8 节文献综述骨架 |

**轴二：语言 / 投稿目标（language）**

| language | 场景 | 引用格式 |
|----------|------|---------|
| **en** | 直接用英文撰写 | IEEE / APA / Nature |
| **zh** | 用中文撰写 | GB/T 7714 |
| **zh-to-en** | 中文草稿→英文成稿 | 按目标体裁/投稿目标 |

**轴三：目标体裁（target_genre）**

| target_genre | 写作重点 |
|-------------|----------|
| **journal** | 问题集中、贡献明确、篇幅紧凑、结果导向 |
| **thesis** | 结构完整、背景充分、方法细节完整、论证链清楚 |
| **conference** | 篇幅受限、贡献和实验结果前置 |
| **course-paper** | 符合课程要求，重视概念解释和规范表达 |
| **existing-draft** | 保持已有章节风格、术语、编号、引用格式一致 |

### 7.6. 写作范围识别

Step 7 在生成正文前，必须先明确本轮输出范围。默认原则：**先锁定写作边界，再决定如何写；不因“能写更多”而擅自扩写。**

| 模式 | 触发场景 | 主输出 |
|------|----------|--------|
| `full-document` | 已有清晰大纲和文献，直接逐章完整撰写 | 全文初稿 |
| `review-only` | 只产出综述章节或综述主体 | 综述章节 |
| `abstract-only` | 只写摘要 | 摘要 |
| `chapter-only` | 只写一个或多个指定章节 | 指定章节草稿 |
| `continue-existing` | 在已有草稿基础上补写、续写、局部改写 | 修订章节草稿 |
| `revision-only` | 已有审稿意见，只做针对性修订 | 修订后正文 + 修稿记录 |

**已有草稿处理规则：**
- 先识别已有草稿的标题层级、术语、引用格式、语气和章节编号。
- 新写内容必须与已有内容保持结构和语言一致，除非用户明确要求重构。
- 只写部分章节时，不擅自改动其他章节；只在必要处提出“需前后文同步”的提示。
- 如果已有草稿中的引用缺证据，标记为 `needs_evidence_audit`，不要默认删除。

### 7.7. 写作模式、语言规则与章节级论证计划

Step 7 在正文生成前，必须先确定本轮写作模式，并为目标章节生成最小论证计划。核心原则：**先锁定 claim、证据、图表与风险边界，再进入正文写作。**

#### 7.7.1. `abstract-only` 子类型

| 子类型 | 适用场景 | 约束 |
|--------|----------|------|
| `journal-abstract` | 投稿前摘要 | 更紧凑，更结果导向，背景压缩 |
| `thesis-abstract` | 学位论文摘要 | 背景更完整，方法与贡献展开更充分 |
| `bilingual-abstract` | 中英双语摘要 | 中英独立撰写，不做机械直译 |

若用户只说“写摘要”，默认按当前 `target_genre` 推断：`journal` → `journal-abstract`，`thesis` → `thesis-abstract`；若明确要求中英双语，则使用 `bilingual-abstract`。

#### 7.7.2. 语言差异化规则

**zh-to-en 特殊规则（中国研究者最常用场景）：**
1. 术语锁定：写作开始前先列出"中→英关键术语对照表"
2. 中文笔记→英文翻译四步法（提取论点→按英文逻辑重排序→英文撰写→检查翻译腔）
3. 识别中文写作特有的"英文不该有"的模式
4. 中文数字和单位的英文转换

#### 7.7.3. 章节级论证计划

**目的：** 在 `7.2` 风格工件与 `7.8` 正文生成之间，先锁定每个目标章节的核心 claim、所需证据、图表约束和弱点边界，避免写到一半才发现证据不够。

**适用范围：**
- `chapter-only`
- `continue-existing`
- `revision-only`
- `full-document` 中证据风险高的章节

**标准输出：**
- `argument_plan.md`
- `argument_plan.json`

**`argument_plan` 最小字段：**

| 字段 | 说明 |
|------|------|
| `section_id` | 目标章节编号 |
| `core_claim` | 本节主论点 |
| `required_evidence` | 本节必须具备的核心证据 |
| `allowed_evidence_level` | 允许使用的证据等级上限/下限 |
| `must_have_figure` | 是否必须包含图表 |
| `weak_points` | 当前最可能失守的论证点 |
| `rollback_if_missing` | 缺关键证据时回退到哪个 Step |

**`argument_plan` 证据确认区块（本版新增）：**

| 字段 | 说明 |
|------|------|
| `confirmed_evidence` | 已通过 note / annotation / 元数据 / PDF 原文确认的证据 |
| `unresolved_evidence` | 候选命中失败或原文确认失败的证据缺口 |
| `candidate_evidence_used` | 本轮候选定位曾触及的候选片段摘要 |
| `confirmation_status` | `confirmed / partially_confirmed / unconfirmed_requires_rollback` |
| `rollback_if_unconfirmed` | 仍未确认时的动作：`supplement_note_or_annotation / supplement_pdf_or_fulltext / downgrade_claim / rollback_to_step_4_or_6` |

**执行规则：**
1. `chapter-only` 和 `continue-existing` 默认先生成 `argument_plan`，再允许写正文。
2. 若关键证据缺失，不直接硬写正文；在 `argument_plan` 中输出 `rollback_if_missing`。
3. `revision-only` 需要把审稿意见中的问题映射到对应章节的 `argument_plan`，避免只改字面表达。
4. 若启用候选召回，必须把候选先写入 `retrieval_candidates.json`，再回到原文确认；不能把召回分数当作证据等级。
5. 对依赖图表支撑的章节，可新增：
   - `figure_role`
   - `figure_claim_binding`
   若缺少必要图/表，`rollback_if_missing` 可直接触发。

#### 7.7.4. 小节粒度与展开边界

- 每次只写一个当前请求的小节；未被请求的小节只允许作为边界提示存在，不得提前展开正文。
- 不提前展开后续小节；未被请求的小节只允许作为边界提示存在。
- 例如用户要求写 `1.1.1`，则本轮只回答 `1.1.1` 的核心问题，不提前写 `1.1.2`、`1.1.3` 的问题全貌、结论或技术价值。
- 当前小节内部应保持问题推进式叙述：围绕本节问题逐段推进，不使用模板化“先总后分再综上”的机械骨架充数。
- `chapter-only` 若一次包含多个相邻小节，也必须按小节顺序逐个完成，并在每个小节结束处停住，不把下一小节内容并段合写。
- 如果用户没有明确写作粒度，优先追随最小已命名单元：有节号按节号，有标题按标题，没有则按本轮最小章节任务生成一个小节。

#### 7.7.5. 学位论文深度下限

- `target_genre=thesis` 时，默认按博士论文深度组织当前小节，不得写成短综述、资料堆叠或提纲式背景。
- 每个背景/综述型小节通常应完成至少以下递进中的大部分：`工程场景 -> 需求来源 -> 机理约束 -> 制造约束 -> 研究必要性`。
- 若当前小节属于方法、实验或结果章节，则应替换为同等深度的论证链，而不是简单照搬背景型骨架。
- 篇幅由论证充分度决定，不追求机械字数；但只要用户要求的是博士论文章节，就不能用 1-2 段浅层概述草率收束。
- 若现有证据只够写“概况”，必须显式输出证据缺口，而不是用空泛套话把深度伪装出来。

#### 7.7.6. 章节级候选证据层（弱 RAG，按章节确认）

本层放在 `argument_plan` 之后、正文生成之前；它不是独立 Step，而是 Step 7 的内部证据前移层。

**定位：**
- 只负责“找哪里可能有证据”
- 不负责确认是否构成正文证据
- 候选召回粒度按 claim 生成，确认粒度按章节推进

**固定流程：**
1. 从 `argument_plan` 读取章节 claim 与 `required_evidence`
2. 针对每个 claim 生成候选片段，写入 `retrieval_candidates.json`
3. 按章节统一回到 Zotero note / annotation / 元数据 / PDF 原文确认
4. 将确认结果直接回写 `argument_plan`
5. 只有 `confirmation_status` 满足要求的 claim，才允许进入正文生成或 `revision-only` 正文修改

**`retrieval_candidates.json` 第一版组织方式：**
- `chapter_id`
- `chapter_title`
- `claim_id`
- `claim_text`
- `evidence_question_id`
- `query_variant`
- `candidate_item_key`
- `candidate_chunk_id`
- `page`
- `source_page_hint`
- `source_type`
- `retrieval_score`
- `match_reason`
- `negative_or_conflicting_evidence`
- `requires_direct_verification`
- `post_verify_status`

**章节级确认规则：**
- 同一章节中，多个 claim 可以共享同一篇文献或相邻 chunk 的确认结果
- 但每条 claim 必须保留独立 `claim_id` 和独立确认状态
- 每个候选问题必须保留 `evidence_question_id`，便于同一 claim 下多轮候选、反证候选和页码线索追踪
- `query_variant` 只记录候选生成的不同提问方式，不代表多版本写作方案
- `negative_or_conflicting_evidence` 用于提示可能反驳或削弱 claim 的材料；它不能被静默忽略，也不能未经确认直接写成反方结论
- `source_page_hint` 只作为回到 note / annotation / PDF 的定位线索，不等同于页码级证据确认
- 候选命中失败或原文确认失败时，必须回写 `unresolved_evidence`，不得静默消失
- `retrieved_candidate` 只能表示“可能相关”，不得直接升级为正文证据

### 7.8. 内部写作流水线（用户不可见）

Step 7 的正文生产按以下内部顺序执行；这是 agent 执行纪律，不是用户可见模式，也不新增入口词。

| 内部阶段 | 职责 | 允许修改 | 禁止越界 |
|----------|------|----------|----------|
| 生成 | 按 `argument_plan`、章节蓝图和证据矩阵写出正文单元 | 生成段落、句子、引用占位、章节过渡 | 不凭空补证据，不扩写未请求章节 |
| 整合 | 把多篇文献、图表、方法和 claim 合成为论证链 | 合并重复论点，调整段内信息顺序，补承上启下句 | 不把文献堆砌伪装成综述，不提高证据等级 |
| 审阅 | 对刚生成的段落做基础可读性整形 | 连贯性、术语统一、过渡句、重复句压缩、轻度机械句清理 | 不做全文终稿 polish，不重排整章结构 |
| 校验 | 检查 claim、引用、证据等级和风险边界 | 标记 `[待补引用]`、`needs_evidence_audit`、`rollback_if_missing` | 不把 WARN/摘要级证据升级为强证据 |

执行要求：

- 每个正文单元完成后，先经过“审阅”和“校验”，再进入下一个单元。
- 内部阶段名不得作为用户选项、命令、按钮或对话模式暴露；对用户只汇报当前写作结果、证据风险和下一步建议。
- 如果校验发现关键证据缺失，优先输出风险和回退目标，而不是用润色语气掩盖证据问题。

#### 7.8.1. 轻量可读性整理

Step 7 可以在正文生成过程中做基础可读性整理，但这类整理只服务“让初稿可继续阅读与修订”，不应预设用户的写作策略、论证风格或表达审美。

允许的整理边界：

- 保持段落基本连贯
- 按 `.skill-state/term_aliases.md` 做最小术语统一
- 删除明显重复或空泛的句子
- 标记需要后续补证据、补引用或回退的问题

不应在本层写成硬规则的内容：

- 段落必须采用何种组织方式
- 某类章节必须遵循何种固定写法
- 具体句式、修辞、语气或“人味”策略

Step 7 的职责是维持 workflow 与证据边界，不替用户决定“正确写法”。成稿级精修、风格收口和终稿修订仍留给 Step 8。

### 7.9. 章节级写作提示

Step 7 可以根据 `section_blueprints`、`argument_plan`、`target_genre` 和现有草稿，为当前章节提供写作提示，但这些提示不构成硬性模板，也不应限制用户的创造性组织方式。

推荐保留的只有两类约束：

- **证据约束**：当前章节的 claim 需要哪些证据、哪些证据仍不足
- **边界约束**：当前章节不应擅自承载哪些未确认内容、未请求扩写内容或高风险强 claim

其余关于章节结构、段落组织、语气偏好、修辞策略的内容，只能作为可选提示，不应写成质量门或完成条件。

#### 7.9.1. 术语对齐检查

- 每章写作前，确认本章核心术语与 `.skill-state/term_aliases.md` 中的推荐用法基本一致
- 若用户、学科或既有草稿已形成稳定写法，应优先尊重既有写法，再做最小统一

> 具体的章节组织方式、常见写法、文体提示与反模式示例，不再留在主协议中，统一放到 `references/writing-modes.md`、`references/writing-antipatterns.md` 与相关参考文档中，按需查阅。

### 7.10. 实时引文支撑

本层只约束“引用必须可追溯到 Zotero / note / annotation / PDF 原文或允许的摘要级证据”，不规定用户必须采用哪种段落级写法、引用密度或叙述节奏。

**`paper_card` claim-source fit 预判：**
- 写作前按章节优先筛选 `evidence_role` 合适、`content_fit` 不为 `mismatch` 的文献；完整字段见 `references/paper-card-contract.md`。
- `paper_card` 只做文献级用途边界，不替代 PDF、Zotero note、annotation 或全文证据确认。
- `content_fit=direct` 可进入关键 claim 候选，但仍需原文/笔记/标注确认。
- `content_fit=adjacent` 只能支撑保守表述，若正文使用“证明/显著优于/最佳”等强动词，需降级为 `weak-support` 或补全文证据。
- `content_fit=background_only` 只能用于背景、领域现状或综述性句子，不得支撑方法细节、实验数值、强因果结论。
- `content_fit=mismatch` 不得作为正文 claim 支撑；只能进入排除说明、反例或待补查清单。
- 正文 claim 超出 `primary_claim` 或 `content_fit_note` 时，引用审计应标记为 `weak-support` 或 `not-supported`。
- 缺少 `paper_card` 不阻塞 Step 7；按现有 Zotero/PDF/证据包规则降级运行，并记录 `paper_card_missing` 风险。

**摘要级引用规则：**
- 只有完整摘要、无 PDF 的条目，可以用于背景性、领域概况性、研究主题归类性引用。
- 引用标记必须记录为 `evidence_level=abstract_only`，7.16 审计时单独列出。
- 不得用摘要级证据支撑具体实验数据、参数、机制解释、效果提升百分比或“证明/证实”类强动词。
- 写作主证据不足时，应回到 Step 5/6 补 PDF 或补全文，而不是提高摘要级证据的强度。

**已读深度标注规则：**
- Step 7 正文中，每个文献引用在作者-年份或编号标记后，必须显式追加已读深度标签：`（已读全文）` / `（已读摘要）` / `（仅元数据）`。
- 推荐写法：`……并通过轴向力和内压辅助弯曲研究其改善路径 [Wang and Agarwal, 2006, （已读全文）]。`
- 标签映射固定如下：
  - `reading_depth=full_text / pdf_verified / zotero_note` -> `（已读全文）`
  - `reading_depth=abstract_only` -> `（已读摘要）`
  - `reading_depth=metadata_only` -> `（仅元数据）`
- 若同一条引文同时依赖多篇文献，每篇文献都应各自标注已读深度，不得合并成一个笼统标签。
- 只允许对“本轮确实已读到的层级”打标，不得把摘要级或元数据级文献冒充为已读全文。
- `（仅元数据）` 文献只能承担题录定位、研究对象归类、候选线索或极弱背景提示，不得承载具体结论。
- `（已读摘要）` 文献只能承担背景概括、研究主题归类、方向性描述；不得承载具体实验结果、参数、机制、图表解释、效果百分比、强因果或“证明/证实/显著优于”等强结论。
- 具体结论、方法细节、实验设置、结果比较、机制判断和强 claim，只能引用 `（已读全文）` 文献；若当前只有摘要或元数据，必须改写为保守表述，或输出 `[待补证据: claim]`。

**新增引用回流规则：**
- 如果现有 Zotero 文库无法支撑某个 claim，不允许现场编造或只凭网页摘要引用。
- 新引用必须走 Step 4/6 小闭环：检索/评分 → 加入 `文献库.bib` 或增量 bib → 补充中文元数据 → PDF 下载/附件池匹配 → Zotero 入库 → 更新 `文献-Zotero架构对照.json` → 再进入 7.9。
- 紧急写作时可在段落中保留 `[待补引用: claim]`，但不得进入最终稿。
- 候选召回命中的片段只能标记为 `retrieved_candidate`；若原文确认失败，必须继续保持回退状态，不得因召回分数高而强行引用。
- `retrieval_candidates.json` 应按章节→claim 组织，便于章节级确认和 `argument_plan` 回写。

**当前试写阶段的引用格式：**
- Step 7 试写阶段默认保持作者-年份格式，并显式标注阅读深度。
- 在单条引文中，推荐形式为：`作者, 年份, （已读全文）`；若有多篇并列支撑，则逐篇并列标注，不合并阅读深度。
- 只有进入整章或全稿定稿阶段，才统一转换为 GB/T 7714 编号格式。

**英文文献与中文场景的联合支撑：**
- 关键论点优先采用“英文基础/国际研究 + 中文工程场景文献”共同支撑。
- 不得长期只依赖中文文献完成关键技术判断；也不得只靠英文通用研究而完全脱离具体航空/工程应用场景。
- 当中文场景文献缺失时，可以先用英文文献搭骨架，但必须把中文场景证据缺口显式写出。

**重要论点的并列支撑：**
- 重要判断默认不只挂 1 篇文献；优先用 2-3 篇文献并列支撑同一关键论点。
- 对承载章节核心判断或高强度结论的论点，若当前只找到单篇支撑文献，应标记为支撑不足或待补证据。
- 多文献并列时，应避免重复复述同一句结论，而是让各文献分别支撑需求、现象、约束或场景中的不同侧面。

两类 claim 仍区分为 `text_claim` 与 `figure_claim`，但具体评估细节和图表证据流程转交 `references/figure-writing-interface.md` 与图表证据子链文档。

### 7.11. 防幻觉机制（核心）

本层的硬边界只有三条：

- 引用必须可追溯
- 摘要级证据不能支撑强 claim
- 候选召回层不能直接进入正文或审计结论
- `paper_card` 的 `background_only`、`mismatch` 或 `abstract_only` 不能被提升为关键 claim 的强支撑

更细的写作与引用方法学说明，统一放到 `references/citation-audit-guide.md`、`references/evidence-tier-policy.md` 与相关参考文档。

### 7.12. 评审与修稿路线图

本层只定义修稿闭环的输入、输出、证据状态和回退边界；具体评审方法、review 话术、反驳思路和评分细则转交 `references/reviewer-protocol.md` 与相关参考文档。

#### 7.12.1. 修稿教练（审稿意见 → 路线图）

**适用场景：**
- 已收到真实审稿意见，需要先分解任务再执行修改
- 用户已有草稿，想知道哪些意见只改措辞、哪些必须回退补证据
- 需要先出 Point-by-Point 回应骨架，再进入 `revision-only`

**标准输出：**
- `revision_roadmap.md`
- `response_letter_skeleton.md`
- `evidence_gap_list.md`

**`revision_roadmap.md` 必备字段：**

| 字段 | 说明 |
|------|------|
| reviewer_comment_id | 审稿意见唯一编号 |
| priority | P0 / P1 / P2 |
| chapter_binding | 涉及章节、段落或图表 |
| claim_binding | 对应 claim / 论点 / 结果 |
| evidence_status | VERIFIED / VERIFIED_LOCAL / WARN / REJECT / abstract_only / candidate_only |
| action_type | 直接改写 / 补文献 / 补 PDF / 补 Zotero / 重做风格蓝图 / 回退上游 Step |
| rollback_target | Step 4 / Step 6 / Step 7.2 / 无需回退 |
| success_condition | 该条意见何时算处理完成 |

> 从本版开始，`revision_roadmap`、`claim_delta_report`、`evidence_gap_list` 与 Step 8 `revision_ledger` 共用同一套闭环语义：问题识别、修订动作、证据状态、验证结果、下一步动作。该语义只约束问题生命周期，不规定具体写作策略、修辞路径或段落组织方式。

**修订闭环最小字段族（Step 7 / Step 8 统一）：**

| 字段 | 说明 |
|------|------|
| `issue_id` | 问题唯一标识；跨 `revision_roadmap / claim_delta_report / revision_ledger` 复用 |
| `chapter_binding` | 涉及章节、段落或图表 |
| `claim_binding` | 对应 claim / 论点 / 结果 |
| `problem_summary` | 问题描述或修订目标 |
| `action_type` | 本轮修订动作 |
| `evidence_status` | 当前证据状态 |
| `verification_result` | 当前验证结果 |
| `next_action` | 下一步动作：继续保留 / 人工复核 / 回退补证据 / 回退上游 Step |
| `issue_state` | `identified / routed / in_revision / verification_pending / closed / blocked_author_decision / blocked_evidence / invalid_or_not_applied` |
| `state_reason` | 当前状态原因，说明为什么关闭、阻塞、回退或不采纳 |

约束：
- `revision_roadmap` 偏向“问题识别 + 动作分派”
- `claim_delta_report` 偏向“claim 变化 + 证据变化”
- `evidence_gap_list` 偏向“证据阻塞 + 回退目标”
- `revision_ledger` 偏向“最终修订验证 + 状态收口”
- 三者字段不要求完全同名同量，但必须能一一映射到上面这组最小闭环字段
- `closed` 只能表示问题已通过证据和验证条件关闭；不能因为文字被改顺就关闭
- `invalid_or_not_applied` 用于记录误读、无依据建议或用户决定不采纳的问题，不能从工件中删除

**执行规则：**
1. 不允许只做“文字总结”；每条意见都必须绑定章节和 claim。
2. 发现证据不足时，优先输出回退动作，而不是建议“弱化语气”来掩盖问题。
3. `WARN`、摘要级证据或无 PDF 条目支撑关键 claim 时，必须写入 `evidence_gap_list.md`。
4. `response_letter_skeleton.md` 只提供标准回应骨架，不冒充已经完成修改。
5. 若使用候选召回，必须把召回片段视为待确认材料；只有原文确认成功后，才能计入 `evidence_added`。

### 7.13. `revision-only` 修订执行

**定位：** `revision-only` 不是“重新写论文”，而是基于已有草稿、审稿意见、证据状态和写作蓝图，对指定章节、指定 claim、指定引用进行可追踪修订。

**标准输出：**
- 修订后正文
- `revision_change_log.md`
- `claim_delta_report.md`
- 更新后的 `response_letter_skeleton.md`
- 更新后的 `evidence_gap_list.md`
- `revision_execution_status.md`

**`revision_change_log.md` 最小字段：**

| 字段 | 说明 |
|------|------|
| `comment_id` | 对应审稿意见 |
| `chapter_binding` | 所属章节 |
| `location_before` | 修订前位置 |
| `location_after` | 修订后位置 |
| `change_type` | 修改类型 |
| `summary_of_edit` | 修改摘要 |
| `evidence_touched` | 触及的证据 |
| `status` | `applied / partially_applied / blocked_requires_rollback` |

**`claim_delta_report.md` 最小字段：**

| 字段 | 说明 |
|------|------|
| `issue_id` | 对应修订问题编号 |
| `claim_id` | claim 编号 |
| `before_claim` | 修改前 claim |
| `after_claim` | 修改后 claim |
| `delta_type` | `unchanged / softened / strengthened_with_new_evidence / reframed / removed` |
| `evidence_status_before` | 修改前证据状态 |
| `evidence_status_after` | 修改后证据状态 |
| `risk_after_revision` | 修订后风险 |
| `verification_result` | `PASS / WARN / FAIL` 或等价结果 |
| `next_action` | 下一步动作：保留 / 人工复核 / 回退补证据 / 回退上游 Step |

**硬规则：**
1. 不得用“降级措辞”替代补证据。
2. 不得绕开 `section_blueprints` / `argument_plan` 重写章节功能。
3. 回应信、正文、证据三者必须同步。
4. 被阻塞的问题必须留在 `evidence_gap_list.md`，不得静默消失。
5. `retrieved_candidate` 命中不能直接记作 `evidence_added`；必须有 note / annotation / PDF 原文确认。
6. claim 问题只有在 `claim_delta_report` 与证据状态同时更新后，才可视为进入关闭判定。

### 7.14. 复评（验证修稿是否真的解决问题）

**输入：**
- `评审报告.md`
- `revision_roadmap.md`
- 修订后正文
- `引用审计报告.md`

**输出：**
- `rereview_report.md`

**固定判断维度：**
1. 上轮问题是否关闭
2. 是否引入新问题
3. 引用风险是否下降
4. 是否仍需回退到 Step 4 / Step 6 / Step 7.3 / Step 7.7 / Step 7.16

**执行规则：**
1. 复评不是新一轮大评审，不扩展 reviewer persona。
2. 每条上轮问题必须标记为：`closed` / `partially_closed` / `open`。
3. 若修稿引入新问题，必须单列为 `new_issue`，不得混进“旧问题未解决”。
4. 引用风险未下降时，优先建议回退到 Step 7.16 或 Step 4/6，而不是继续润色。

如需更细的反方挑战、review 话术或 rebuttal 提示，应查 `references/reviewer-protocol.md`，而不在主协议中强行预设用户的论证路线。

### 7.15. 图表意图与证据约束

Step 7.14 的主目标不是追求某种固定图表风格，而是把“为什么需要这张图、它支撑哪个 claim、哪些证据可用、哪些风险必须标记”记录清楚。生成脚本可以作为可选执行工具，但图表是否进入正文由 claim 绑定和证据状态决定。

```bash
python3 scripts/generate_figures.py 论文初稿.md --data data/ --output figures/
```

**图表链最小流程：**
1. `figure_intent`：说明这张图要回答什么问题、服务哪个章节或 claim。
2. `evidence_basis`：列出数据文件、已有图/表、PDF 原文、note / annotation 或作者输入等依据。
3. `candidate_specs`：给出 1-3 个候选图表规格，只记录可选方案，不替用户决定最终表达。
4. `human_selected_candidate`：记录作者选择或确认的候选规格。
5. `figure_risk_note`：记录数据不足、图文不一致、过度解释、视觉确认缺失等风险。

**图表与论证绑定要求：**
- 新生成图表应可回写到 `figure_index.json`
- 每个图表至少应绑定：
  - `figure_id`
  - `caption`
  - `claim_binding`
  - `section_id`
- 图表证据确认还应记录：
  - `figure_intent`
  - `evidence_basis`
  - `candidate_specs`
  - `human_selected_candidate`
  - `figure_risk_note`
- 图表清单只记录“生成了什么”；图表是否支撑 claim 由 `figure_evidence_report.md/json` 决定

### 7.16. 写后引用审计

> 核心目的：抓"LLM 把标题相关的论文当成支撑某个具体声明的论文"这种张冠李戴。

```
稿件 → 提取所有引用标记 [1][2]...[N] → 逐条：
① 通过 citekey / zotero_item_key 定位 Zotero 条目与对照 JSON 记录
  ② 读取 `paper_card`、Zotero child note、PDF 标注、元数据、PDF 全文证据
  ③ 定位稿件中引用该论文的具体声明（claim sentence）
  ④ 判断：`paper_card` + 原文/笔记/标注是否支撑这个 claim？
     ✅ 支撑 / 🟡 弱支撑 / ❌ 不支撑
  ⑤ 输出审计报告
```

```bash
python3 scripts/citation_audit.py 论文初稿.md \
  --mapping 文献-Zotero架构对照.json \
  --pdf-index pdf-附件池索引.json \
  --prepared-chunks paper.clean.chunks.json \
  --output 引用审计报告.md

# fallback: no prepared chunks, but citations can still map to Zotero items
python3 scripts/citation_audit.py 论文初稿.md \
  --mapping 文献-Zotero架构对照.json \
  --output 引用审计报告.md
```

**三层审计结构：**

| 审计层 | 核心问题 | 输出字段 |
|--------|----------|----------|
| 格式层 | GB/T 7714、作者、年份、条目字段是否合规 | `format_status` |
| 对应层 | 正文引用能否映射回 BibTeX / Zotero / 对照 JSON | `mapping_status` |
| 证据层 | claim 是否被 `VERIFIED` / `VERIFIED_LOCAL` / `WARN` / `REJECT` 或摘要级证据正确支撑 | `evidence_status` |

**动作化输出：**

在三层状态之外，每条引用必须追加 `recommended_action`，固定值域为：
- `retain`
- `downgrade_claim`
- `supplement_pdf_or_fulltext`
- `repair_mapping`
- `replace_or_remove`

四种误引模式：标题-摘要张冠李戴 / 综述当实证 / 贡献过度归因 / 数据编造

**`paper_card` 驱动的审计规则：**
- `content_fit=direct` 且 `reading_depth` 不低于 `full_text` / `pdf_verified` 时，才可进入关键 claim 的正常支撑候选。
- `content_fit=adjacent` 或 `reading_depth=abstract_only` 时，若正文使用强结论语气，优先给出 `downgrade_claim` 或 `supplement_pdf_or_fulltext`。
- `content_fit=background_only` 只能保留为背景支撑；不得用于验证具体实验结果、方法优势或因果结论。
- `content_fit=mismatch` 或 `paper_card` 缺失时，不得仅凭题目相关性保留为关键支撑，优先 `replace_or_remove` 或 `repair_mapping`。
- 若 Zotero child note 与 `paper_card` 不一致，以 `文献-Zotero架构对照.json` 为主；note 仅作辅助线索。

**审计结论分级：**
- `retain`：可保留
- `downgrade`：需降级表述
- `supplement`：需补证据
- `replace_or_remove`：必须删除或替换

**推荐动作映射：**
- 摘要级证据用于强 claim → `downgrade_claim` 或 `supplement_pdf_or_fulltext`
- BibTeX / Zotero / JSON 映射缺失 → `repair_mapping`
- `REJECT` 支撑关键 claim → `replace_or_remove`
- `retrieved_candidate` 本身不得决定 `recommended_action`；动作必须基于原文确认后结果。

**图表证据子路径：**

当某条 claim 主要依赖图/表时，除文字审计外，额外记录：
- `figure_id`
- `caption_support`
- `text_support`
- `visual_support`
- `evidence_status`
- `recommended_action`

**图表证据状态值域：**
- `caption_only`
- `text_caption_aligned`
- `visual_confirmed`
- `figure_not_supported`

**图表误引风险：**
- `figure_overinterpretation`

**图表动作建议值域：**
- `retain`
- `downgrade_claim`
- `need_visual_check`
- `supplement_text_evidence`
- `replace_or_remove`

> Crossref / Semantic Scholar 摘要只能作为补充核验，不能替代 Zotero 条目和 PDF 原文。CNKI/万方中文文献尤其必须以本地元数据、详情页 URL、PDF 原文和 Zotero Extra/source_id 为审计依据。

### 7.17. CHECKPOINT W — CP-CITATION-WARN

当 `WARN` 文献、弱引用、摘要级证据、无 PDF 条目或审计中的“不支撑/弱支撑”将被用于关键 claim 时，必须输出 checkpoint 块并等待用户明确确认。普通背景性描述、研究脉络说明、综述矩阵候选记录和待补查清单不触发 checkpoint。`REJECT` 仍禁止进入正文关键引用和 Zotero 写入计划。

```md
CHECKPOINT W — CP-CITATION-WARN

entry_mode: normal_chain|direct_entry|resume|repair|partial_artifact
status: blocked
blocks_next: using risky evidence in key claims
must_confirm: true

summary:
- 列出异常文献/引用、风险类型和受影响 claim。

user_options:
1. 删除或替换异常引用
2. 保留但标注为背景/待补证据
3. 回退 Step 4/5/6 小闭环补证据
4. 逐条人工审查

does_not_block:
- WARN 文献用于背景性描述、研究脉络或待补查线索
- 摘要级证据用于领域概况、主题归类或精读优先级判断
- 综述矩阵中的候选记录、异常清单和低风险描述性整理

required_confirmation:
- “确认 CP-CITATION-WARN”
```

---

## 质量门槛 (Quality Gates)

- [ ] paper_type 和 language 已识别
- [ ] 7.1 文献证据矩阵：13 列完整，证据优先级规则已遵循
- [ ] 7.2 目标体裁/文档风格：`style_sample_status.md/json` 已生成，Flash 或 Pro 模式已完成，style_profile.md 已生成
- [ ] 7.6.3 章节级论证计划：`argument_plan.md/json` 已生成（适用时）
- [ ] 防幻觉机制：每处引用均来自 Zotero 条目和实际 PDF/笔记/标注证据
- [ ] T1/T2/T3 覆盖：矩阵覆盖 Step 6 中所有 T1/T2/T3，写作引用优先使用 T1/T2，T3 用途已标明
- [ ] Step 4 可信度约束：关键 claim 均由 `VERIFIED` / `VERIFIED_LOCAL` 文献支撑；WARN 仅作背景；REJECT 未进入正文
- [ ] 7.8.1 段落自查：每段一个工作 / 从证据向外写 / 动词校准 / 无虚假新颖性 / 段落流
- [ ] 🆕 术语对齐：核心术语与 `.skill-state/term_aliases.md` 一致
- [ ] 7.11 同行评审：五维评分全部 ≥ 5 分（<5 分已回退修复）
- [ ] 7.12.1 修稿教练：如存在外部审稿意见，`revision_roadmap.md`、`response_letter_skeleton.md`、`evidence_gap_list.md` 已生成
- [ ] 7.13 复评：如完成修稿，`rereview_report.md` 已生成，且旧问题关闭状态明确
- [ ] 7.16 引用审计：❌ 不支撑引用已移除或替换

---

## 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `论文初稿.md` 已生成
- [ ] `论文初稿.docx` 已自动生成
- [ ] `综述矩阵.csv` + `综述矩阵.md` 已生成
- [ ] 目标体裁/文档风格产出：`research_dossier/` 目录完整，含 `style_sample_status.md/json`
- [ ] `评审报告.md` + `rebuttal-预演.md` 已生成
- [ ] 如完成修稿复评：`rereview_report.md` 已生成
- [ ] `引用审计报告.md` 已生成
- [ ] 如走 `revision-only`：`revision_roadmap.md`、`response_letter_skeleton.md`、`evidence_gap_list.md` 已生成
- [ ] figures/ 目录图表完整

### 术语对齐检查 🆕
- [ ] 逐章扫描核心术语，确认与 `.skill-state/term_aliases.md` 一致
- [ ] 发现术语不一致 → 修正为 Main Term → 如 Main Term 不当 → 更新 term_aliases.md → 记录到 decision_log.md

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 引用编造 → 追加到 `.skill-state/error_log.md`
  - 综述矩阵证据填充错误 → 追加到 `.skill-state/error_log.md`
  - 目标体裁/文档风格分析偏差 → 追加到 `.skill-state/error_log.md`
  - 术语混用 → 追加到 `.skill-state/error_log.md`
  - 7.16 审计发现系统性误引 → 追加到 `.skill-state/error_log.md`

### 决策日志更新 🆕
- [ ] 是否调整了章节结构？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否修改了 paper_type 判定？→ 记录到 `.skill-state/decision_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：论文润色（Step 8）
  > **下一步 → Step 8：** 同行评审通过 + rebuttal 预演无遗漏 + 引用审计无重大问题后，进入润色、保守修订与修订后验证。

### 成功判据
- [ ] 当前输出已说明证据基础来自 Zotero/PDF/笔记/摘要中的哪一层
- [ ] 当前输出已说明引用风险状态
- [ ] 用户能区分“正文已形成”和“证据仍弱但可继续修”

### 完成前必须确认
- [ ] 只有在 evidence basis 和 citation risk 都已说明时，才能声称“章节写完”
- [ ] 若关键 claim 仍为摘要级或候选级证据，只能表述为草稿可继续，不能表述为证据闭环已完成

### 失败分流
- 写不出来：先按 `references/failure-triage.md` 判定是证据层问题还是蓝图层问题
- 引用支撑弱：优先回 7.1/7.2 或 Step 4/6 小闭环，不让模型硬写
- 体裁不稳：先修 style profile / section blueprint，再改正文

---

## 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **引用不足**：运行 7.9 扩展搜索补充引用；检查引用密度指南
- **现有 Zotero 文库不能支撑 claim**：回到 Step 4/6 小闭环补文献、补 PDF、补入库，再继续写作
- **表达明显机械或重复**：7.8.1 做轻量可读性整理；Step 8 Level 3 做表达风险清理
- **引用审计大量不支撑**：7.16 逐条处理，❌ 级别优先替换或移除
- **术语不一致**：回查 `.skill-state/term_aliases.md`，全篇统一为 Main Term
