# Changelog

版本号格式：`v<major>.<minor>.<patch>-<YYYYMMDD>`

- **major**：工作流步骤增减或架构重设计
- **minor**：单个步骤重大更新（新脚本、新策略、新产出）
- **patch**：Bug 修复、文档更新、小优化

---

## v1.0.12-20260614 (2026-06-14)

### Step 1 / Step 2：研究问题收敛器 + 大纲唯一生成层 🆕

- **Step 1 借鉴 `deep-research` 的 Socratic 协议**：从“研究方向确认”升级为“研究问题收敛 + 方法偏好成形 + 检索意图判定 + 反方挑战暴露”
- **Step 1 新增结构化输出字段**：`research_intent_type`、`research_question_candidates`、`primary_rq`、`secondary_rqs`、`scope_boundaries`、`sub_questions`、`methodology_blueprint`、`devils_advocate_challenge`、`fatal_risks`、`what_would_fail_this_topic`
- **Step 1 边界钉死**：文档明确写入“Step 1 只生成问题结构，不生成章节结构”
- **Step 2 强化为大纲唯一生成层**：新增 Step 1 → Step 2 字段映射，明确 `primary_rq / secondary_rqs / scope_boundaries / methodology_blueprint / research_intent_type` 如何影响大纲结构、章节任务和证据需求
- **Step 2 的 2c 既有大纲分支增强**：当同时存在 Step 1 输出和已有大纲时，默认仍进入 `2c`；Step 1 只作为约束源，不作为重写主轴
- **Step 2 新增对齐检查**：已有大纲是否承接 `primary_rq`、覆盖 `secondary_rqs`、违反 `scope_boundaries`、与 `methodology_blueprint` 冲突、是否需要补章节承接 `fatal_risks`

### Step 7 / Step 8：RAG 候选层与图表证据子链 🆕

- **RAG MVP 定位明确**：不是替代 PDF 直读，而是候选定位加速层。RAG 负责“找哪里可能有证据”，Zotero note / annotation / PDF 原文直读负责“确认这里是不是真证据”
- **新增 RAG 内部工件**：`retrieval_index_manifest.json`、`retrieval_candidates.json`
- **新增中间状态**：`retrieved_candidate`，只能表示“可能相关”，不得直接升级为 `VERIFIED / VERIFIED_LOCAL`
- **Step 7 契约接入 RAG 候选层**：
  - `7.1` 证据矩阵允许先读候选，再回到原文确认
  - `7.7` 引文支撑新增 `Retrieve` 候选召回步骤，但不得跳过 `Read`
  - `7.9.2 revision-only` 中，候选召回只能帮助找潜在补证据材料；原文确认失败仍是 `blocked_requires_rollback`
  - `7.11` 中 `recommended_action` 明确不得由相似度直接决定
- **新增图表证据链工件**：`figure_index.json`、`figure_evidence_report.md/json`
- **图表证据链接入 Step 7**：
  - `7.1` 可选扩展 `figure_refs`、`table_refs`、`figure_evidence_level`
  - `7.5` 可新增 `figure_role`、`figure_claim_binding`
  - `7.7` 显式区分 `text_claim` 与 `figure_claim`
  - `7.11` 新增图表误引风险 `figure_overinterpretation`
- **图表证据状态与动作**：
  - 状态：`caption_only`、`text_caption_aligned`、`visual_confirmed`、`figure_not_supported`
  - 动作：`retain`、`downgrade_claim`、`need_visual_check`、`supplement_text_evidence`、`replace_or_remove`
- **Step 8 边界强化**：文档明确 Step 8 不直接读取 `retrieval_candidates.json`，也不直接依赖图表证据工件；只消费 Step 7 已确认后的审计结论与诊断摘要

### README / 质量防线更新 🆕

- **中文与英文 README 顶部版本同步到 `v1.0.12-20260614`**
- **“直接读 PDF vs RAG 分块”段落修正**：不再写成 “RAG 直接读 PDF 原文”，而是明确“当前以直接读 PDF 原文为主链；若后续引入 RAG，也只作为候选定位加速层”
- **论文质量防线 / Quality Defense Line 重写**：
  - 从旧的“6 道评审节点”升级为“前中后段联动的质量防线”
  - 新总图和表格覆盖：
    - `Step 7.5 章节论证计划`
    - `Step 7.9 修稿与复评`
    - `Step 7.11 写后引用审计`
    - `Step 8 诊断优先润色`
- **Step 7 概述同步增强**：README 中已反映图表证据子链、修稿/复评闭环、Step 8 诊断优先润色

### 测试与契约回归

- **新增 `tests/test_step1_step2_contracts.py`**：钉死 Step 1 只生成问题结构、Step 2 是大纲唯一生成层、2c 以已有大纲为主体且 Step 1 只作约束源
- **增强 `tests/test_step7_step8_contracts.py`**：覆盖
  - Step 1/2 借鉴 `deep-research` 的字段
  - RAG 候选层是非权威中间层
  - 图表证据子链的工件、状态和值域
  - Step 8 不直接读取候选层
- **增强 `tests/test_workflow_contracts.py`**：补 `retrieval_*` 与 `figure_*` payload 的稳定 JSON 合同

## v1.0.11-20260613-1 (2026-06-12 至 2026-06-13)

### Step 7/8 写作与润色工作台收紧 🆕

- **Step 7 写作模式收敛**：公开写作模式统一为 6 个稳定模式：`full-document`、`review-only`、`abstract-only`、`chapter-only`、`continue-existing`、`revision-only`，并同步 README / SKILL / Step 7 运行时契约
- **摘要模式细分**：`abstract-only` 内部明确区分 `journal-abstract`、`thesis-abstract`、`bilingual-abstract`，分别约束紧凑度、背景展开度和中英独立撰写要求
- **风格工件统一为三件套**：Step 7.2 的机器工件固定为 `style_profile.md/json`、`section_blueprints.md/json`、`writing_rationale_matrix.md/json`；`style_sample_status` 作为辅助元数据，不再与主风格工件并列
- **新增章节级论证计划**：在风格蓝图与正文写作之间补入 `argument_plan.md/json`，先锁定章节 claim、所需证据、图表约束和 `rollback_if_missing`
- **修稿闭环成形**：Step 7 新增修稿教练与 `revision-only` 契约，标准输出包括 `revision_roadmap.md`、`response_letter_skeleton.md`、`evidence_gap_list.md`、`revision_change_log.md`、`claim_delta_report.md`、`revision_execution_status.md`
- **新增复评层**：Step 7 增加 `rereview_report.md` 作为修订验证层，固定检查“旧问题是否关闭 / 是否引入新问题 / 引用风险是否下降 / 是否仍需回退”
- **三层引用审计动作化**：在 `format_status / mapping_status / evidence_status` 之外，增加 `recommended_action`，固定值域为 `retain`、`downgrade_claim`、`supplement_pdf_or_fulltext`、`repair_mapping`、`replace_or_remove`
- **Step 8 绑定 Step 7 三工件**：`style_profile.json`、`section_blueprints.json`、`writing_rationale_matrix.json` 从“优先读取”升级为“默认约束源”；缺失时只能降级运行并显式记录
- **Step 8 非阻塞规则保留**：缺评审报告继续标记“评审依据不足”，缺引用审计继续标记“引用安全提醒”，不冒充审计通过，也不要求回跑 Step 7

### 用户入口、文档分发与示例层 🆕

- **新增 `commands/` 层**：补入 `topic`、`search`、`download`、`zotero`、`write`、`polish`、`citation-audit`、`revision-roadmap` 八个短文档，专门回答何时使用、最小输入、主要产出、常见阻塞点
- **新增 `examples/showcase/`**：加入 `revision_roadmap`、`citation_audit`、`polish_quality_report` 示例，帮助用户理解中间工件而不是只看流程描述
- **README 场景入口增强**：补入“导师给了目录”“已有 DOI/BibTeX”“已有 Zotero 文库”“已有草稿”“收到审稿意见”等直达 Step 入口说明

### Step 7 内部编号整理 🆕

- **减少补丁式编号**：把 `7.5b` 合并进 `7.5 写作模式与章节级论证计划`
- **把修稿与复评收回到 `7.9` 主闭环**：`7.9` 下统一组织为评审仿真、修稿教练、`revision-only`、复评四个连续环节，避免 `7.9b / 7.9c` 孤立生长
- **明确主线顺序**：Step 7 内部现在更接近“风格蓝图 → 论证计划 → 正文生成 → 引文支撑 → 防幻觉 → 评审/修稿/复评 → 图表 → 引用审计”的稳定结构

### 测试与契约回归

- **新增 `tests/test_step7_step8_contracts.py`**：覆盖 Step 7 公开写作模式、修稿教练、三层引用审计、Step 8 降级规则、`commands/` 和 `examples/showcase/` 的存在性
- **补 Step 7/8 fixtures**：新增 `step7_chapter_only`、`step7_revision_only`、`step8_degraded` 三个契约样例目录
- **修正旧测试假设**：`test_direct_entry_contracts.py` 过去默认每个 Step 只有一个 agent 文件；现改为跳过 `*_entry.md`，适配入口层 + 主执行层的双文件结构

## v1.0.9-20260609 (2026-06-08 至 2026-06-09)

### Step 2-5 流程接口收口 🆕

- **Step 2 新增已有大纲模式**：用户直接提交目录/大纲/草稿目录时，进入 `2c`，先反向抽取研究主题，再做五维评审、修订建议、关键词清单和章节证据需求表
- **Step 2 路由判定补齐**：新增 `2-0` 入口判定，明确 `2a` 标准生成与 `2c` 已有大纲优化的边界；同时统一术语为“章节大纲 / 关键词清单 / 章节证据需求表”
- **Step 3/4 结构化交接强化**：Step 3 以 `search_tasks` 承接 Step 2 的章节证据需求；Step 4 保留 `search_task_id`、`chapter_id`、`chapter_title`、`evidence_type`，供后续 Zotero 架构和写作回溯
- **Step 4 交付物统一为 7 件套**：`检索文献表.md/.xlsx`、`检索报告.md/.pdf`、`文献库.bib`、`saturation_snapshot.json`、`中文论文元数据.json`
- **Step 5 新增直达下载模式**：用户可不经过 Step 1-4，直接提供 DOI、标题、URL、BibTeX 或参考文献列表；标题先归一化为 DOI/URL/中文 `article_url`，无法唯一解析的条目写入 `unresolved_download_items.md`
- **Step 5 编号重排**：执行流程统一为 `6a-6i`，收尾检查统一为 `8a-8d`，避免 `5a` 挂在 `## 6` 下或旧 `6.0` 编号混用

### Step 6 Zotero 文库管理升级 🆕

- **新增 `scripts/build_zotero_plan.py`**：在真正写入 Zotero 前，先生成可审阅、可恢复、可追溯的 Step 6 计划产物
  - `文献-Zotero架构对照.json`：机器执行源，完整保留集合、标签、导入方式、PDF 匹配和状态字段
  - `文献-Zotero架构对照.md`：人类审阅版，用于快速检查文献归属、导入状态和附件状态
  - `pdf-附件池索引.json`：扫描 Step 5 下载目录、原有 PDF、补下载目录和手动整理目录
- **中文文献 Zotero 入库规则补齐**：CNKI/万方条目不再依赖 DOI，改用 `source_id` + `article_url` + 中文元数据生成 CSL JSON 条目
- **附件策略更保守**：当前 Zotero MCP 不能直接向已有 item 挂载本地 PDF 时，默认只生成状态和建议动作，避免高风险重复挂载
- **一致性检查强化**：要求 Zotero 集合、BibTeX/中文元数据、PDF 附件池和对照 JSON 四者互相可追溯
- **本次补充修复**：
  - `build_zotero_plan.py` 写入审阅版时自动创建父目录
  - `organize_zotero.py` 支持 Step 2 标准格式中的 `章节大纲` 编号列表和 `关键词清单` 表格，避免把元信息标题误建成 Zotero 集合

### 中文检索批处理与 CDP 会话稳定性 🆕

- **新增 `scripts/batch_chinese_search.sh`**：交互式批量 CNKI/万方检索入口
  - 同一条命令内完成 CDP Chrome 启动/复用、目标网站打开、CARSI 登录等待、批量检索和 `.bib` 输出
  - 支持 `--login-only` 模式，专门用于 Step 5 下载前的登录门控
  - 解决跨命令 `require_escalated` 场景下 CDP 会话断连的问题
- `SKILL.md` 脚本索引与 Step 4/5 运行说明同步加入中文批量检索入口。

### 运行时状态模板与跨平台清理

- `references/decision_log.md`、`error_log.md`、`term_aliases.md` 移入 `references/templates/`
- `SKILL.md` 新增运行时初始化规则：首次使用时复制模板到项目 `.skill-state/`，后续只修改 `.skill-state/` 副本
- `.gitignore` 改为忽略整个 `.claude/` 目录，移除仓库内的 `.claude/settings.example.json`，避免本地 Agent 配置混入 skill 内容
- 删除无用根目录 `image.png`，减少仓库噪声
- 已知陷阱补充 Python 3.14 单行 `try/except` 语法限制、CDP WebSocket 层级、ScienceDirect 页面渲染等待等问题。

### README 与运行时文档重整

- README 更新为 `v1.0.9-20260609`，补充 Codex badge，并把 Claude Code / Codex / Hermes / OpenClaw 作为等价智能调度层展示
- README 大幅压缩执行细节，明确 `README.md` 只做 GitHub 概览，`agents/step_*.md` 才是运行时规则 Source of Truth
- Step 1-8 文档同步清理触发词、输入输出、质量门和故障处理，尤其强化 Step 2-5 的跨步骤接口和 Step 6 的 6a/6b/6c/6d 分工
- `agents/known_pitfalls.md` 扩展常见坑，便于后续 Agent 跨会话复用修复经验。

### 自动升级提醒

- 新增 `scripts/check_skill_update.py`：每个 agent 启动时可做 best-effort 更新检查，比较本地版本元数据和远程 git `HEAD`
- 默认 24 小时最多提醒一次，状态写入用户缓存目录；只输出更新建议，不自动执行 `git pull`
- 支持 `--force`、`--no-network`、`--quiet` 和 `MORE_PAPER_SKILL_UPDATE_CHECK=0` 关闭开关
- 同步 `SKILL.md` frontmatter 版本到 `v1.0.9-20260609`，避免 README/CHANGELOG 与运行时元数据不一致

### 修改文件

| 文件 | 改动 |
|------|------|
| `scripts/build_zotero_plan.py` | 新增 Step 6 对照计划生成器；支持 BibTeX/中文元数据/PDF 附件池匹配 |
| `scripts/organize_zotero.py` | 支持 Step 2 标准章节大纲和关键词清单解析，修正集合层级截取 |
| `scripts/batch_chinese_search.sh` | 新增 CNKI/万方批量 CDP 检索与登录等待入口 |
| `scripts/generate_retrieval_report.py` | 兼容 `search_tasks` 字段，保留章节和证据类型信息；中文合成 ID 写入 `source_id` 而非 DOI |
| `scripts/generate_search_report.py` | 检索报告兼容章节字段和 `source_id`，保持 Step 4/6/7 可追溯 |
| `scripts/unified_download_router.py` | 中文论文解析兼容 `source_id` fallback，配合 `中文论文元数据.json` 下载 |
| `agents/step_2_outline.md` | 新增已有大纲模式、2a/2c 路由判定、章节证据需求表和 Step 3/6/7 handoff |
| `agents/step_3_search_plan.md` | 新增 `search_tasks` 作为结构化检索任务接口 |
| `agents/step_4_search_score.md` | 强化 7 件套交付物、中文论文元数据和 search_tasks 字段保留规则 |
| `agents/step_5_download.md` | 新增直达下载模式，整理执行流程编号为 6a-6i |
| `agents/step_6_zotero.md` | 重写 Step 6 为架构、对照、集合创建、入库/附件状态四段式流程 |
| `scripts/check_skill_update.py` | 新增自动升级提醒脚本 |
| `SKILL.md` | 更新触发词、路由表、脚本索引、运行态模板复制规则、自动升级提醒和 Step 6 概览 |
| `README.md` | 更新 v1.0.9 展示、版本历史、Step 6 能力、自动升级提醒、英文区版本号 |
| `references/templates/*.md` | 将错误日志、决策日志、术语别名改为运行时模板 |
| `.gitignore` | 忽略 `.claude/` 和运行时状态目录 |

---

## v1.0.7 (2026-06-07)

### CDP 登录门控 — 文档规则 + 脚本机制双层防护 🆕

- **问题**：Agent 在执行 CDP 下载时直接调用路由器，未提示用户完成机构登录，导致批量失败
- **文档层** `agents/step_5_download.md`：新增 Section 6.0 硬性规则
  - Agent 必须先 `--dry-run` 查看需要登录的出版社
  - Agent 必须打开浏览器并暂停，提示用户完成机构登录
  - 仅收到"已登录"确认后才能执行下载
  - 质量门槛新增 2 项登录检查点
- **脚本层** `scripts/unified_download_router.py`：
  - 新增 `show_login_gate()` — 扫描分类结果，列出需登录的出版社及域名
  - 新增 `--require-login-confirm` 参数
  - 支持 `已登录/y/yes/done/继续` 确认，`q/quit/abort` 中止
  - OA 出版社（direct_http）和 Sci-Hub 自动跳过门控

### 中文文献下载路由 — CNKI + Wanfang CDP 🆕

- **问题**：v1.0.6 已支持 CNKI/Wanfang 检索，但下载管线仅覆盖英文出版社，中文文献无法下载
- **核心设计**：中文文献多数无真实 DOI，无法走英文前缀路由。新增 Round 5 Chinese CDP，通过 `source` 字段识别，直接按文章页 URL 下载
- **`config/publishers.toml`**：新增 CNKI + Wanfang 条目，`strategy = "chinese_cdp"`
- **`scripts/generic_publisher_downloader.py`**：
  - `download_one()` 新增 `article_url` 参数
  - 新增 `chinese_cdp` 策略路由：导航文章页 → CSS 选择器提取 PDF → CDP Fetch 捕获
- **`scripts/unified_download_router.py`**：
  - 新增 `parse_chinese_papers()` / `run_chinese_round()`（Round 5 Chinese CDP）
  - 新增 `--chinese-input`、`--skip-chinese`、`--test-cnki`、`--test-wanfang` 参数
  - `show_login_gate()` 扩展为包含 CNKI/Wanfang 登录提示
- **`agents/step_5_download.md`**：路由矩阵新增 Round 5 Chinese CDP，命令参考 +4 条中文下载命令
- **`agents/step_4_search_score.md`**：新增中文论文文章 URL 保留规则

### SKILL.md frontmatter 压缩

- `description` 压缩为单行中英混合（~300 字），末尾保留中文链条保证语义路由跨语言匹配
- 适配 Codex 只读 `name` + `description` 的解析器行为

### 检索报告元数据化

**`scripts/generate_search_report.py`：**
- metadata 优先级改为 `meta → summary → default` 三级回退
- `source_breakdown` 支持嵌套 dict
- 无 metadata 时显示 `—` 而非错误数字
- PRISMA 流程图支持 `initial_tier_counts` / `expansion_tier_counts` 分阶段展示
- 路由表改为 `_build_source_routing_table()` 动态生成
- 记录管理改为 `.md + .xlsx + .bib` 导出，不再默认声称已进 Zotero

**`scripts/search_by_topic.py`：** OpenAlex venue 提取容错

### 检索执行规则修正

- **Step 3**：英文路由新增 L2 Crossref（必选源），Deep tier 下不得仅用 OpenAlex 完成检索
- **Step 4**：新增 CNKI/万方 preflight + CDP/CARSI 登录流程；英文源和中文源拆分独立决策表；新增「用户无机构账号」分支

### Step 6d 独立触发词 + 路由表

- 新增 11 条触发词（文库大纲对照表、覆盖热力图等中英文）
- 路由表新增独立 6d 路由行，概览图新增 `├─ 6d 对照表 PDF` 节点
- **设计意图**：此前 6d 仅作为 6c 隐式产出，现在可独立触发重新生成

### 其他修复

- `auto_sd_downloader.py` 重构内部逻辑（+19/-11）
- 新增 3 个中文论文测试 PDF（约 16 MB 合计），验证 CNKI/Wanfang 下载管线

### 修改文件

| 文件 | 改动 |
|------|------|
| `agents/step_5_download.md` | +Section 6.0 登录门控、+Round 5、+4 命令示例、+2 质量门槛项 |
| `scripts/unified_download_router.py` | +`show_login_gate()`、+`parse_chinese_papers()`、+`run_chinese_round()`、+5 CLI 参数 |
| `scripts/generic_publisher_downloader.py` | +`chinese_cdp` 路由、+`article_url` 参数、+110 行 |
| `scripts/generate_search_report.py` | PRISMA 分阶段 + 动态路由表 + 元数据驱动 |
| `scripts/search_by_topic.py` | +OpenAlex 容错、+中文检索增强 |
| `scripts/auto_sd_downloader.py` | 重构内部逻辑 |
| `config/publishers.toml` | +2 条目（CNKI、Wanfang） |
| `agents/step_4_search_score.md` | +登录流程、+决策表拆分、+文章 URL 规则 |
| `agents/step_3_search_plan.md` | +L2 Crossref 路由 |
| `SKILL.md` | +11 触发词、+1 路由行、概览图 +1 节点、description 压缩 |
| `references/literature-table-template.md` | +中文论文备注 |

---

## v1.0.6 (2026-06-06)

### 中文检索新增 — CNKI + Wanfang 双源并行

- **新增 CNKI 检索**：通过 CDP Chrome 操作旧版 `kns.cnki.net/kns/AdvSearch` 接口，含摘要提取（详情页）、请求间隔（3s）防反爬
- **新增 Wanfang 检索**：支持校园网 IP 直连 + 校外 CARSI CDP 双模式，搜索页直接解析摘要（结果页自带）
- **双源并行路由**：新增 `--parallel` 参数，中文查询 CNKI + Wanfang 同时跑，Step 4b DOI 去重合并
- **CDP 端口可配**：`_CDP_PORT` 通过 `CDP_PORT` 环境变量或 `--cdp-port` CLI 参数覆盖，默认 9222

### 英文源增强

- **OpenAlex**：新增 `_reconstruct_abstract()` 解析 `abstract_inverted_index` 倒排索引 → 明文摘要
- **Semantic Scholar + Crossref**：API 已返回 `abstract` 之前丢弃，现在保留
- **Semantic Scholar**：新增指数退避重试（429/SSL），限流后主动提示免费申请 API Key

### 评分升级 — 摘要驱动

- 维度① 主题匹配度：从仅标题 → **标题×2 + 摘要×1**
- 维度② 方法学严谨性：从固定 3/5 → 从摘要检测实验/仿真信号（中英文关键词）→ 5/3/2

### 输出贯通

| 产出 | 摘要 |
|------|:---:|
| CLI 表格 | `Abs` 列 + 统计 `X with abstracts` |
| `.bib` | `abstract = {...}` |
| `.xlsx` | 摘要列（第 3 列，自动换行） |
| `.md` 模板 | 摘要列 |

### 清理

- 删除 `step_3_search_plan.md` 中硬编码学校账号
- 删除废弃的 `CNKI_LOGIN_URL`、`CNKI_KNS8S_URL` 常量
- 移除摘要截断（之前 .bib 500 字 / .md 200 字限制）

### 修改文件

| 文件 | 改动 |
|------|------|
| `scripts/search_by_topic.py` | +280/-42 |
| `scripts/generate_retrieval_report.py` | +14 |
| `agents/step_3_search_plan.md` | 路由文档 |
| `agents/step_4_search_score.md` | 表格模板 + 命令 |

### 实测

- Zotero 个人论文 4 中文 + 10 英文测试
- CNKI 3/4 + Wanfang 4/4 → 合并 4/4（100%）
- OpenAlex 10/10（100%），摘要覆盖 76%

### CDP 登录门控 — 文档规则 + 脚本机制双层防护

- **问题**：Agent 在执行 CDP 下载时直接调用路由器，未提示用户完成机构登录，导致批量失败
- **文档层** `agents/step_5_download.md`：新增 Section 6.0 硬性规则
  - Agent 必须先 `--dry-run` 查看需要登录的出版社
  - Agent 必须打开浏览器并暂停，提示用户完成机构登录
  - 仅收到"已登录"确认后才能执行下载
  - 质量门槛新增 2 项登录检查点
- **脚本层** `scripts/unified_download_router.py`：
  - 新增 `show_login_gate()` — 扫描分类结果，列出需登录的出版社及域名
  - 新增 `--require-login-confirm` 参数
  - 支持 `已登录/y/yes/done/继续` 确认，`q/quit/abort` 中止
  - OA 出版社（direct_http）和 Sci-Hub 自动跳过门控

### 中文文献下载路由 — CNKI + Wanfang CDP

- **问题**：v1.0.6 已支持 CNKI/Wanfang 检索，但下载管线仅覆盖英文出版社，中文文献无法下载
- **核心设计**：中文文献多数无真实 DOI，无法走英文前缀路由。新增 Round 5 Chinese CDP，通过 `source` 字段识别，直接按文章页 URL 下载
- **`config/publishers.toml`**：新增 CNKI + Wanfang 条目，`strategy = "chinese_cdp"`
- **`scripts/generic_publisher_downloader.py`**：
  - `download_one()` 新增 `article_url` 参数
  - 新增 `chinese_cdp` 策略路由：导航文章页 → CSS 选择器提取 PDF → CDP Fetch 捕获
- **`scripts/unified_download_router.py`**：
  - 新增 `parse_chinese_papers()` / `run_chinese_round()`（Round 5 Chinese CDP）
  - 新增 `--chinese-input`、`--skip-chinese`、`--test-cnki`、`--test-wanfang` 参数
  - `show_login_gate()` 扩展为包含 CNKI/Wanfang 登录提示
- **`agents/step_5_download.md`**：路由矩阵新增 Round 5 Chinese CDP，命令参考 +4 条中文下载命令
- **`agents/step_4_search_score.md`**：新增中文论文文章 URL 保留规则

### SKILL.md frontmatter 压缩

- `description` 压缩为单行中英混合（~300 字），末尾保留中文链条保证语义路由跨语言匹配
- 适配 Codex 只读 `name` + `description` 的解析器行为

### 检索报告元数据化

**`scripts/generate_search_report.py`：**
- metadata 优先级改为 `meta → summary → default` 三级回退
- `source_breakdown` 支持嵌套 dict
- 无 metadata 时显示 `—` 而非错误数字
- PRISMA 流程图支持 `initial_tier_counts` / `expansion_tier_counts` 分阶段展示
- 路由表改为 `_build_source_routing_table()` 动态生成
- 记录管理改为 `.md + .xlsx + .bib` 导出，不再默认声称已进 Zotero

**`scripts/search_by_topic.py`：** OpenAlex venue 提取容错

### 检索执行规则修正

- **Step 3**：英文路由新增 L2 Crossref（必选源），Deep tier 下不得仅用 OpenAlex 完成检索
- **Step 4**：新增 CNKI/万方 preflight + CDP/CARSI 登录流程；英文源和中文源拆分独立决策表；新增「用户无机构账号」分支

### Step 6d 独立触发词 + 路由表

- 新增 11 条触发词（文库大纲对照表、覆盖热力图等中英文）
- 路由表新增独立 6d 路由行，概览图新增 `├─ 6d 对照表 PDF` 节点
- **设计意图**：此前 6d 仅作为 6c 隐式产出，现在可独立触发重新生成

### 其他修复

- `auto_sd_downloader.py` 重构内部逻辑（+19/-11）
- 新增 3 个中文论文测试 PDF（约 16 MB 合计），验证 CNKI/Wanfang 下载管线

### 修改文件

| 文件 | 改动 |
|------|------|
| `agents/step_5_download.md` | +Section 6.0 登录门控、+Round 5、+4 命令示例、+2 质量门槛项 |
| `scripts/unified_download_router.py` | +`show_login_gate()`、+`parse_chinese_papers()`、+`run_chinese_round()`、+5 CLI 参数 |
| `scripts/generic_publisher_downloader.py` | +`chinese_cdp` 路由、+`article_url` 参数、+110 行 |
| `scripts/generate_search_report.py` | PRISMA 分阶段 + 动态路由表 + 元数据驱动 |
| `scripts/search_by_topic.py` | +OpenAlex 容错、+中文检索增强 |
| `scripts/auto_sd_downloader.py` | 重构内部逻辑 |
| `config/publishers.toml` | +2 条目（CNKI、Wanfang） |
| `agents/step_4_search_score.md` | +登录流程、+决策表拆分、+文章 URL 规则 |
| `agents/step_3_search_plan.md` | +L2 Crossref 路由 |
| `SKILL.md` | +11 触发词、+1 路由行、概览图 +1 节点、description 压缩 |
| `references/literature-table-template.md` | +中文论文备注 |

---
## v1.0.5 (2026-06-05)

### 检索融合更新

借鉴 paper-search-pro，为 Step 3/4 增加 7 项检索增强能力，重构 Step 4 子步骤编号为 4a→4h。

**新增 3 文件：**
- `references/rcs-rubric.md` — 主题匹配度评鉴指南（RCS 启发，4 级锚定 + 5 种旗标）
- `scripts/discovery_curve.py` — 饱和度曲线分析（指数拟合估算文献覆盖率）
- `scripts/arxiv_helper.py` — arXiv L2 条件检索（CS/AI 信号触发）

**修改 5 文件：**
- `scripts/search_by_topic.py` — +引文网络 `--citation-network`、+语义缓存、+influentialCitationCount
- `agents/step_4_search_score.md` — 子步骤重编号 4a→4h；评分(4c)/筛选(4d)获正式编号；.bib 升级为检索报告(4g)输出 .md+.xlsx+.pdf+.bib；4e 引文扩展含评分闭环；T4 显式剔除
- `agents/step_3_search_plan.md` — +arXiv 路由 + Tier 参数表
- `agents/step_1_topic.md` — +Step 1e 检索深度自动推断
- `SKILL.md` — +触发词 + 路由/脚本/依赖表同步

**核心变化：**
```
4a 引文验证 → 4b 去重 → 4c 评分 → 4d 分级(T4剔除)
→ 4e 引文扩展(评分闭环) → 4f 饱和度 → 4g 检索报告(.md+.xlsx+.pdf+.bib) → 4h 完成
```

### 统一下载路由架构

- **新增 `unified_download_router.py`**：单一入口自动路由，三轮顺序执行（Sci-Hub → SD CDP → Generic CDP），覆盖 23 家出版社，产出 `download_log.md`
- **新增 `generic_publisher_downloader.py`**：CDP 通用下载引擎，策略 A（直连 PDF URL）→ 策略 B（文章页 CSS 选择器提取），支持补充材料下载（`--include-si`）
- **新增 `config/publishers.toml`**：24 家出版社集中式知识库（DOI 前缀 + URL 模板 + CSS 选择器 + 屏障检测规则）
- **增强 `cdp_utils.py`**：新增 15 个反检测 Chrome flag + `warmup_profile()` 预热函数，借鉴 ref-downloader 反机器人验证策略
- **IEEE 切换为 Generic CDP 引擎**，`download_via_ieee.py` 保留作为 SSO 交互备用
- 可自动下载 **23 家出版社**文献；MDPI（Akamai Bot Manager 封锁）暂无自动化方案
- 用户 Zotero 文库 9 篇真实论文实测全部通过（Sci-Hub 2 篇 + Generic CDP 7 篇）

### 检索方案全面升级 — T1→T2→T3 路由 + 检索后验证

**Step 3 检索方案设计：从平面映射到三级回退链**

- **旧版：** 每个子课题挂一个来源（如 `Semantic, Crossref`），源不可用即失败
- **新版：** 每个子课题挂一条 T1→T2→T3 回退链，T1 不足 30 条自动触发 T2，再不足到 T3，每次 fallback 记录原因
- **6 领域路由规则：** 医学(PubMed→Semantic→Google)、工程(CrossRef→Semantic→Scopus)、CS(arXiv→bioRxiv)、综述(PubMed+CrossRef+arXiv)、中文(CNKI/万方)
- **检索源能力速查：** 6 个数据源的覆盖范围、API 限制、费用一览

**Step 4 检索后新增三道工序：**

| 工序 | 做什么 | 产出 |
|------|--------|------|
| **4a 引文验证** | DOI 格式校验 + 元数据完整性检查（title/authors/year），剔除无效条目 | 干净 DOI 列表 |
| **4b DOI 去重** | 多源检索合并去重（DOI 主键 + title+author+year 回退键），冲突时保留元数据最完整的条目 | 去重文献表 |
| **4c .bib 导出** | 统一导出为 BibTeX 格式，含 Tier/Score 标签 + 子课题归属（`note` 字段），Zotero 直接导入 | `文献库.bib` |

**脚本侧：`search_by_topic.py` v3.0**

- **T1→T2→T3 路由：** `--t1 crossref --t2 openalex --t3 semantic_scholar --min-results 30`
- **Pre-flight 检查：** `--preflight` 测试全部 API 端点可达性
- **格式导出：** `--export-bib` (.bib)、`--convert` (.ris/.nbib)
- **DOI 验证：** `--verify-dois` 批量校验 DOI 有效性 + 元数据完整性
- **布尔查询：** `--bool query_plan.json` 支持 AND/OR/NOT 概念块组合
- **多策略检索：** `--strategy relevance|cited|recent|all`

### 综述矩阵 + 文献综述写作 + 写作润色

- **新增 Step 6e：文献综述矩阵** — 13 列结构化证据提取（作者年份→DOI），按证据优先级逐级回退填充（Zotero 笔记→标注/高亮→元数据→PDF 全文→摘要），产出 `综述矩阵.csv` + `综述矩阵.md`
- **增强 Step 7 review 论文类型** — 8 节文献综述专属骨架（标题→引言→主题脉络→分主题综述→方法证据→不足未来→小结→参考文献）+ 7 条写作纪律（观点分组/观点-作者格式/合并引用/对比表达/保留不确定性/不编造/缺失标注）
- **扩展 GB/T 7714-2015 规范** — 完整排序规则（中文在前/拼音序/英文字母序）+ 作者姓名处理 + 7 种文献类型代码 [J/M/C/D/R/EB/OL] + 缺失元数据处理方案
- **新增 3 个参考文件**：`references/literature-review-matrix-schema.md`、`references/literature-review-docx-guide.md`、`references/gbt7714-2015-citation-format.md`
- **新增 `scripts/generate_academic_reference_docx.py`** — 生成中文论文样式模板（A4/宋体+Times New Roman/黑体标题/1.5 倍行距），`md_to_docx.py` 自动检测使用
- **新增 `references/academic-reference.docx`** — pandoc 参考样式文档（解决 md_to_docx.py 长期缺失模板的问题）
- **新增 3 个步骤** — Step 6f 期刊风格学习+蓝图（`learn_journal_style.py`, `generate_section_blueprints.py`, `generate_writing_rationale.py`, `latex_guard.py`）、Step 7g 科研图表生成（`generate_figures.py`, `figure_utils.py`）、Step 7h 写后引用审计（`citation_audit.py`），借鉴 nature-figure、CiteCheck、PaperSpine
- **新增 5 个参考文件** — `journal-style-learning-guide.md`, `section-blueprint-template.md`, `nature-figure-style-guide.md`, `nature-color-schemes.md`, `citation-audit-guide.md`

### SKILL.md Agent 模块化 + Error Log + 术语标准化

对 3284 行 SKILL.md 单体文件进行系统性架构重构，借鉴 [ResearchWiki](https://github.com/jiawei601/ResearchWiki) 的 Agent 模块化、错误日志和术语别名三项核心模式。

**SKILL.md 拆分为 Agent 模块：**

- **SKILL.md 从 3284 行精简为 377 行**：保留完整 YAML trigger 短语 + 流水线图 + **新增 Agent 路由表** + 共享记忆文件表
- **新增 `agents/` 目录**：9 个独立 Agent 文件，每个遵循标准化 9 段模板（启动前读取 → 适用/不适用任务 → 输入要求 → 标准输出 → 执行流程 → 质量门槛 → 收尾检查 → 故障排除），路由规则按触发词精确匹配

| Agent 文件 | 对应 Step | 行数 |
|-----------|:--:|:--:|
| `agents/step_1_topic.md` | Step 1: 交互式定题（v2.0 增强版） | 180 |
| `agents/step_2_outline.md` | Step 2: 大纲 + 五维评审 + 术语映射 | 158 |
| `agents/step_3_search_plan.md` | Step 3: L1→L2→L3 分层路由检索方案 | 185 |
| `agents/step_4_search_score.md` | Step 4: 多渠道检索 + 5 维评分 + 引文验证 | 194 |
| `agents/step_5_download.md` | Step 5: 统一下载路由（24 家出版社） | 196 |
| `agents/step_6_zotero.md` | Step 6: Zotero + 综述矩阵 + 期刊风格 | 187 |
| `agents/step_7_writing.md` | Step 7: 写作 + 图表生成 + 引用审计 | 263 |
| `agents/step_8_polishing.md` | Step 8: 四合一润色引擎 + 术语标准化 | 178 |
| `agents/known_pitfalls.md` | 跨 Step 通用：已知陷阱与故障排除 | 95 |

**新增错误日志与决策日志：**

- **`references/error_log.md`** — 跨会话 AI 错误积累与修正规则。所有 8 个 Step Agent 收尾检查均包含"错误日志更新"条目，确保 AI 从错误中学习、不重复踩坑
- **`references/decision_log.md`** — 跨会话结构性决策记录（含 3 条初始决策：SKILL.md 拆分、Step 7 合并策略、术语标准化机制）

**新增术语标准化跨步骤贯穿：**

- **`references/term_aliases.md`** — 术语别名映射表（Main Term / Aliases / Recommended page / Note 四字段）
- Step 2 新增 2d: 术语映射表生成（从大纲关键词提取术语 → 填充映射表）
- Step 3 概念块构建时强制术语一致性（核心词与 Main Term 对齐，同义词从 Aliases 展开）
- Step 7 章节写作前术语对齐检查（每章术语与 Recommended page 匹配）
- Step 8 润色终验以 term_aliases 为基准校验全文术语一致性（不一致 → 修正 → 更新映射表 → 记录 decision_log）

**Trigger 短语优化：**

- 删除冗余变体和无效长句触发词（-7 条）
- 新增导航控制触发词（"继续下一步"、"回到上一步"、"当前进度" 等 +10 条）
- 新增共享记忆+健康检查触发词（"错误日志"、"决策日志"、"术语映射表"、"知识库审计" 等 +13 条）
- 新增口语化中文触发词（"帮我确定研究方向"、"帮我找几篇关于"、"这段太AI了" 等 +4 条）
- **164 → 184 条**（净增 20 条）

---

## v1.0.4 (2026-06-04)

### 质量防线体系 — 6 道评审节点

将散落在各步骤的评审能力整合为统一的 **论文质量防线**：
- 防线上图 + 各节点把控表，选题→大纲→检索→写作→成稿 5 阶段全覆盖
- Step 2b 新增**导师视角检查**：工作量达标 / 风险识别 / Plan B / 时间线与里程碑 / 发表拆分策略
- Step 7d.1 新增**段落与句子级自查**（借鉴 nature-writing）：每段一个工作 / 证据向外写 / 动词校准 / 清除虚假新颖性 / 段落流
- Step 7f 新增**三审稿人视角** + **Rebuttal Letter 预演**（借鉴 nature-reviewer + nature-response）

### SKILL.md 架构重整

- Step 7 物理顺序修正为 7a→7b→7c→7d→7e→7f
- Step 7 重构为 paper_type(5种) × language(en/zh/zh-to-en) 双轴写作引擎
- 新增 zh-to-en 四步转换法 + 中文期刊特有规范（GB/T 7714）
- 新增 7e 实时引文支撑（借鉴 nature-citation）：分段→搜索→评估→导出
- 新增 7f.2 三审稿人视角 + 7f.4 Rebuttal 预演
- 新增 7c 语言差异化规则（zh/en/zh-to-en 写作规范差异 + 章节命名对照）
- 清理 17 个 🆕 emoji + 5 条 v1.0.3 changelog 注记
- 删除 `实测性能基线` 节（开发者 benchmark，非用户面内容）

### 脚本增强

- `search_by_topic.py` v2.0：新增 T1→T2→T3 路由、`--preflight`、`--export-bib`、`--convert` (.ris/.nbib)、`--score`、`--verify-dois`（151→450 行）
- `batch_resolve_pii.py` 重构：提取 5 个单一职责函数，认知复杂度 38→12

### 文档

- README 新增 `## 🛡️ 质量防线` 章节
- 删除 `scripts/generate_proposal.py`（不具有通用性）

---

## v1.0.3 (2026-06-03)

### Zotero MCP 多环境兼容

- **`scripts/setup_zotero.py`** 全面增强：
  - `--target` 参数：Claude Code / Hermes / Cursor / Claude Desktop / auto
  - 优先 `claude mcp add` CLI 注册（VS Code 扩展版官方方式），回退 `mcp.json`
  - `--non-interactive` 模式（CI/CD）、`--smoke-test` 8 项验证
  - `detect_target()` 自动检测、`--check` 多目标状态字段
- **`docs/ZOTERO_MCP_SETUP.md`**：多平台配置指南 + FAQ
- **`scripts/packages/README.md`**：wheel 兼容性说明
- **`.claude/settings.json`** 从 Git 移除，加入 `.gitignore`
- 实测：VS Code Claude Code 成功注册连接，948 篇文献正常访问

### README 结构重整

- 合并「工程品质」入「核心优势」，消除内容重复
- Zotero MCP 配置从独立章节移入 Step 6b
- Step 5 精简 70%（细节移至 `references/`）
- 新增**设计哲学对比表**（AI 辅助 ≠ AI 替代）
- 新增**「适合谁 / 不适合谁」**章节
- 强化「为什么需要这个工具」—— AI 编造参考文献问题
- 项目结构扩展（docs/、全部 9 个 references、packages/）
- 脚本速查新增 3 个条目（sd_download CLI 模式、generate_posters、start_cdp_chrome）

### 对话触发短语

- README 每个 Step 添加 `💬` 触发短语（8 中文 + 8 英文）
- SKILL.md `triggers` 同步添加完整短语

### SKILL.md 能力增强

| 步骤 | 借鉴来源 | 增强内容 |
|------|---------|----------|
| **Step 1a** 阶段诊断 | 确认用户画像（硕士/博士/青年教师），推荐最佳入口 |
| **Step 1b** 预检索 | 发散子方向 → 文献量/趋势/gap 初判，用外部数据替代用户猜测 |
| **Step 1c** 深度聚焦 | 方法论深化 + 创新点预判 |
| **Step 1d** 选题预审 | originality/importance/feasibility 三问，绿灯/黄灯/红灯 |
| **Step 3-4** 检索路由 | T1→T2→T3 分级检索 + 引文验证 + DOI 去重 + `.bib` 导出 |
| **Step 7** 写作引擎 | paper_type（5 种）× language（en/zh/zh-to-en）双轴写作 + 章节级规则 + 实时引文支撑 |
| **Step 7f** 评审仿真 | 三审稿人视角 + Rebuttal 预演 |

### 安全审计

- 全量代码扫描：无 API Key、密码、个人路径泄露

---

## v1.0.2 (2026-06-02)

### Zotero MCP Server 安装与连接全面升级

| 项目 | 修改前 | 修改后 |
|------|--------|--------|
| **SKILL.md 描述** | "已随本 skill 封装"（虚） | "脚本一键安装，含本地 wheel 优先离线安装"（实） |
| **安装方式** | 用户自行 `pip install` | `python3 scripts/setup_zotero.py --install` 全自动安装 |
| **连接模式** | 仅 Web API（硬编码） | Web API + 本地 API 二选一，通过 `--mode` 参数切换 |
| **离线能力** | 无 | 74 个纯 Python wheel（~15 MB）本地缓存于 `scripts/zotero_wheels/`，平台编译包自动补全 |
| **状态检测** | 仅显示环境变量 | 显示连接模式、后台进程、API Key 配置、wheel 完整性 |

**详情：**

- **`scripts/setup_zotero.py`** 重写为全自动安装器：
  - `--install` 一键安装：优先使用本地 wheel 离线安装（`scripts/zotero_wheels/`），缺失时自动从 PyPI 下载
  - `--check` 全面状态检测：模式 / 进程 / 配置 / API Key 完整性
  - `--mode web` / `--mode local` 切换连接模式
  - 支持 macOS / Linux / Windows 三平台 wheel 分发
- **本地 API 模式**：通过 Zotero 桌面端内置 API（`http://127.0.0.1:23119`）直连，仅读取文库，无需 API Key，零网络依赖
- **Web API 模式**：通过 Zotero Web API（`api.zotero.org`）远程连接，支持读写，需 API Key
- 依赖清单表格同步更新，安装方式从 "手动 pip install" 改为 "脚本一键安装+模式选择"

---

## v1.0.1 (2026-06-02)

### IEEE 论文下载（重大更新）

- 新增 **IEEE CDP 两步走策略**（`scripts/download_via_ieee.py`）：
  - Step A（首选）：导航文章页 → 提取 stamp URL → 新标签页 Fetch 预启用捕获（Referrer 校验通过）
  - Step B（回退）：直连 `stamp/stamp.jsp` / `getPDF/getPDF.jsp`
  - 交互式登录：`--login` 打开 IEEE SSO 登录页；`--check-session` 检查机构会话
- **10.1109/ DOI 前缀自动路由**：检测到 IEEE DOI 时自动触发 IEEE 下载脚本，不尝试其他方式
- **`scripts/batch_resolve_pii.py`**：支持 BibTeX / Markdown 表格 / 纯文本引用三种输入格式，DOI → PII 解析

### CDP 下载模块重写

- **`scripts/cdp_utils.py`** 抽取共享 CDP 模块（浏览器管理 / Fetch 捕获 / 依赖检查）
- **`scripts/sd_download.py`** 混合下载核心：策略 A（直连 8s → PDF 标签页 → Fetch 捕获） + 策略 B（文章页 25s 渲染 → 提取 `?md5=` → PDF 标签页 → Fetch 捕获）
- **`scripts/auto_sd_downloader.py`** 全自动版：启停浏览器 + 断点续跑 + `skip_set` 永久跳过无权限论文（防止重启死循环）
- **`scripts/parallel_sd_download.py`** 双浏览器并行版（Chrome + Edge 各自独立标签页上下文）
- Chrome Profile 从 `/tmp/` 迁移到 `~/.hermes/chrome_sd_profile`（持久化，重启保留 Cookie）
- **PDF 标签页残留修复**：每篇下载后关闭 PDF 标签页，防止下篇误捕获
- **Python buffer 修复**：`PYTHONUNBUFFERED=1` / `python3 -u` 确保后台进程实时输出

### Step 7-8 增强

- **Step 7d 同行评审仿真**（质量门）：5 维度评分 + 限 2 轮修改 + Acknowledged Limitations
- **Step 8 论文润色**（四合一精修引擎）：
  - Level 1 表面清理 + Level 2 结构优化 + Level 3 去 AI 痕迹（29 种模式）+ Level 4 注入人味
  - 句长波动检测（burstiness）+ 章节风格指南（不同章节不同波动度目标）
  - Before/After/Reason 三列修改对照表

### 其他

- 已知陷阱大幅扩展：Python 3.14 语法 / CDP WebSocket 层级 / SD 文章页渲染时长 / 真实 Profile CDP 端口不绑定
- `references/publisher-access-matrix.md` / `references/sd-cdp-architecture.md` / `references/cdp-pdf-capture-limitations.md`

---

## v1.0.0 (2026-06-01)

### Initial Release

- **8 步完整学术工作流**：确定主题 → 大纲关键词 → 检索方案 → 多渠道检索 → 批量下载 → Zotero 管理 → 论文写作 → 论文润色
- **Step 4 多渠道检索**：Semantic Scholar / Crossref / OpenAlex，相关性 5 维评分（Tier 1-4）
- **Step 5 批量下载**：Sci-Hub CDP / ScienceDirect CDP 混合策略
- **Step 6 Zotero 管理**：`organize_zotero.py` 生成集合架构 + PDF 导入
- **Step 7 论文写作**：4 种模式（full / outline-only / plan / abstract-only）+ 防幻觉机制
- **Step 8 论文润色**：4 层润色架构 + 中英文通用
