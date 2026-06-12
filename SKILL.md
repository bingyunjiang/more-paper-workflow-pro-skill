---
name: more-paper-workflow-pro-skill
version: v1.0.11-20260613-1
description: Use when the user asks for the more-paper academic workflow: research topic clarification, outline and keyword generation, structured literature search plans, multi-source literature search and scoring, paper PDF download routing (Sci-Hub/IEEE/ScienceDirect), Zotero library organization, review matrices, paper writing, citation audit, or polishing. Especially useful for Chinese or English thesis, dissertation, literature review, PRISMA-style search logs, and GB/T 7714 references. 学术论文全流程：确定研究主题，生成大纲，文献检索，下载，Zotero，综述矩阵，论文写作，润色。
author: Dr. Jiang Bingyun（江博士）
wechat: Bingyunjiang
category: research
license: CC BY-NC-SA 4.0
related_skills:
  - science-direct-cdp-pipeline: "Overlaps on CDP ScienceDirect download; this skill adds the full 8-step workflow from topic definition to paper polishing."
  - zotero-review-matrix-skill: "Source of literature-review-matrix-schema, literature-review-docx-guide, and gbt7714-2015-citation-format references. Integrated into Step 7 writing preparation and writing."
triggers:
  # Step 1: 确定研究主题（v2.0 增强版）
  - "确定研究主题"
  - "厘清研究方向"
  - "帮我确定研究方向"
  - "我想研究某个方向"
  # Step 1a: 研究阶段诊断
  - "研究阶段诊断"
  - "研究可行性评估"
  - "研究选题评估"
  # Step 1b: 广度探索 + 预检索
  - "选题预检索"
  - "研究趋势分析"
  - "文献量扫描"
  - "研究方向可行性"
  # Step 1c: 深度聚焦
  - "研究方向聚焦"
  - "创新点预判"
  # Step 1d: 选题预审
  - "选题预审"
  - "选题创新性评估"
  - "审稿人视角评估选题"
  # Step 1e: 检索深度
  - "深度检索"
  - "快速检索"
  - "标准检索"
  - "深度文献检索"
  - "快速文献扫描"
  - "comprehensive search"
  - "quick literature scan"
  # Step 2: 大纲
  - "生成论文大纲"
  - "论文关键词"
  - "大纲评审"
  - "评审大纲"
  - "评估我的大纲"
  - "优化已有大纲"
  - "根据这个大纲生成检索计划"
  - "根据已有目录做文献检索方案"
  - "导师给了一个目录"
  - "Outline review"
  - "optimize existing outline"
  - "generate search plan from outline"
  - "基于确定的研究主题，生成论文大纲和关键词清单"
  - "Based on the confirmed research topic, generate a paper outline and keyword list"
  # Step 3: 检索方案
  - "制定检索方案"
  - "文献检索策略"
  - "根据大纲和关键词，制定结构化文献检索方案"
  - "Based on the outline and keywords, design a structured literature search strategy"
  # Step 4: 检索与评分
  - "检索论文"
  - "文献检索"
  - "帮我找几篇关于"
  - "帮我找文献"
  - "搜索论文并下载"
  - "按检索方案执行多渠道文献检索，并进行相关性评分和分级"
  - "Execute the multi-source literature search and perform relevance scoring and grading"
  # Step 4d: 饱和度曲线
  - "饱和度曲线"
  - "文献覆盖率"
  - "文献饱和度"
  - "discovery curve"
  - "saturation analysis"
  - "检索覆盖率"
  # Step 4e: 引文扩展
  - "引文扩展"
  - "引文网络"
  - "citation expansion"
  - "citation network"
  - "向前向后引用"
  - "追溯引用"
  - "参考文献扩展"
  # Step 4f: PRISMA-S 日志
  - "PRISMA"
  - "PRISMA-S"
  - "检索合规"
  - "检索透明度"
  - "search compliance"
  # Step 5: 统一批量下载
  - "批量下载"
  - "批量下载论文 PDF"
  - "下论文"
  - "下载 DOI 列表"
  - "直接下载这些 DOI"
  - "按论文标题下载"
  - "根据论文标题下载 PDF"
  - "下载这些论文标题"
  - "从参考文献列表中下载 PDF"
  - "BibTeX 批量下载 PDF"
  - "Sci-Hub 下载论文"
  - "Start batch downloading paper PDFs"
  - "Download all papers"
  - "download by paper title"
  - "download these DOIs"
  # Step 5 单篇测试与会话检查
  - "测试下载这篇论文"
  - "检查下载会话"
  - "check download session"
  - "下载路由预览"
  # IEEE（自动走 Generic CDP，download_via_ieee.py 作为备用）
  - "IEEE 下载"
  - "10.1109/*"
  - "doi:10.1109/*"
  # Zotero 附件管理
  - "Zotero 检查遗漏附件"
  - "Zotero 查找无附件条目"
  - "补下 Zotero 缺少的 PDF"
  # Step 6: Zotero 管理
  - "Zotero 文库整理"
  - "Zotero 架构生成"
  - "PDF 导入 Zotero"
  - "整理 Zotero 文库"
  - "Import the downloaded PDFs into Zotero and generate a collection architecture"
  # Step 6c: 文库一致性调整
  - "文库一致性"
  - "大纲对齐文库"
  - "文库结构调整"
  - "Zotero 大纲对齐"
  - "文库关联性"
  - "文献缺口"
  # Step 6b/6c/6d: BibTeX-Zotero 架构对照 + 集合/PDF 一致性
  - "文献-Zotero架构对照"
  - "生成文献-Zotero架构对照"
  - "BibTeX 导入 Zotero"
  - "Zotero 条目附件关联"
  - "文库大纲对照表"
  - "生成文库对照表"
  - "文献覆盖热力图"
  - "大纲对应关系 PDF"
  - "Zotero 大纲对应"
  - "文库覆盖图"
  - "大纲覆盖报告"
  - "文库覆盖热力图"
  - "collection coverage heatmap"
  - "outline mapping report"
  - "Zotero coverage PDF"
  # Step 7.1: 文献证据矩阵
  - "综述矩阵"
  - "文献综述矩阵"
  - "生成综述矩阵"
  - "Review matrix"
  - "文献矩阵"
  - "文献审阅矩阵"
  - "论文审阅表"
  # Step 7.2: 目标体裁/文档风格学习+蓝图 🆕
  - "学习目标期刊风格"
  - "期刊风格分析"
  - "目标期刊蓝图"
  - "论文风格学习"
  - "期刊格式分析"
  - "学位论文写作风格"
  - "目标体裁风格"
  - "文档风格分析"
  - "已有草稿续写"
  - "只写部分章节"
  - "撰写指定章节"
  - "续写论文"
  - "Journal style learning"
  - "Target journal blueprint"
  - "Learn journal style"
  - "Analyze target journal"
  - "Thesis style"
  - "Target genre"
  - "Document style"
  - "Continue existing draft"
  - "Write selected chapter"
  - "Chapter-only writing"
  - "Section blueprints"
  - "Writing rationale matrix"
  - "风格剖析"
  - "章节蓝图"
  - "写作逻辑矩阵"
  # Step 7: 论文写作（含文献综述 + GB/T 7714）
  - "写文献综述"
  - "Literature review writing"
  - "生成文献综述docx"
  - "文献综述docx"
  - "GB/T 7714格式"
  - "参考文献格式GB"
  - "GBT7714"
  # Step 7: 论文写作
  - "写论文"
  - "撰写论文"
  - "帮我写论文"
  - "基于文献写论文"
  - "基于 Zotero 文库中的文献，开始撰写论文"
  - "Based on the literature in Zotero, let's start writing the paper"
  # Step 7.10: 科研图表生成 🆕
  - "生成图表"
  - "科研绘图"
  - "论文图表"
  - "生成论文图表"
  - "Nature风格图表"
  - "数据可视化"
  - "科研数据图"
  - "论文配图"
  - "Generate figures"
  - "Create publication figures"
  - "Make charts for paper"
  # Step 7.11: 引用审计 🆕
  - "引用审计"
  - "参考文献审计"
  - "检查引用是否准确"
  - "审计论文引用"
  - "Citation audit"
  - "Audit references"
  - "验证引用准确性"
  # Step 8: 论文润色（四合一精修引擎）
  - "论文润色"
  - "去 AI 痕迹"
  - "去 AI 化"
  - "注入人味"
  - "润色分层"
  - "四合一精修"
  - "这段太AI了，帮我改改"
  - "Polish the draft: remove AI traces, inject a human voice, and optimize sentence rhythm"
  # 全流程 + 导航
  - "论文相关工作流"
  - "学术文献全流程"
  # 导航控制 🆕
  - "继续下一步"
  - "下一步"
  - "next step"
  - "continue"
  - "回到上一步"
  - "跳转到 Step"
  - "跳到第"
  - "当前进度"
  - "到哪一步了"
  - "check progress"
  # 共享记忆 + 健康检查 🆕
  - "错误日志"
  - "查看错误日志"
  - "error log"
  - "决策日志"
  - "决策记录"
  - "decision log"
  - "术语标准化"
  - "术语映射表"
  - "term aliases"
  - "健康检查"
  - "知识库审计"
  - "检查知识库"
  - "lint"
  # 工程文档组合分析（非学术论文场景）
  - "文档组合分析"
  - "技术文档分析"
  - "工程文档分析"
  - "技术文档批量提取"
  - "分析现有技术文档报告"
  # 工程文档→大纲优化（Step 2d）
  - "大纲优化"
  - "工程文档优化大纲"
  - "结合工程文档优化大纲"
  - "基于技术报告优化大纲"
  - "用现有工程文档优化论文大纲"
  # 生成优化版大纲文档（Step 2b→2c 输出）
  - "生成优化版大纲"
  - "输出优化版大纲"
  - "导出优化大纲"
  - "优化版大纲PDF"
  - "优化版大纲docx"
  - "大纲PDF输出"
  - "大纲Word输出"
  - "生成大纲PDF"
  - "生成大纲Word"
  - "大纲修改对照表"
  - "根据评审意见生成大纲"
  - "按评审报告修改大纲"
  - "把评审写入大纲"
  - "根据检索结果优化大纲"
  - "应用修改建议生成大纲"
  - "大纲定稿"
  - "输出大纲定稿"
  - "大纲修订版"
  - "修订大纲"
  - "更新大纲"
  - "优化大纲文档"
  - "outline review to optimization"
  - "Outline optimization PDF"
  - "generate optimized outline"
  - "export refined outline"
---

# 完整学术文献检索和写作工作流（8 步法）

## 概述

```
Step 1: 交互式确定研究主题（v2.0 增强版） → 研究主题.md
  ├─ 1a 研究阶段诊断    确认用户画像 + 推荐入口
  ├─ 1b 广度探索+预检索  3-5子方向 → 文献量/趋势/代表文献/gap初判
  ├─ 1c 深度聚焦        方法论深化 + 三视角检查 + 创新点预判
  ├─ 1d 选题预审        五维0-25分 + 绿/黄/红灯决策
  └─ 1e 检索深度推断 🆕  auto tier: quick|standard|deep + Step2/3 handoff
Step 2: 生成研究大纲与关键词        → 大纲关键词.md → 大纲关键词.pdf
  ├─ 2a 标准大纲生成    类型判断 + 章节大纲生成协议
  ├─ 2b 大纲评审        五维0-25分 + P0-P3问题 + 修订建议 + 导师视角
  ├─ 2c 已有大纲优化    反推研究主题 + 评估修订 + 检索交接
  ├─ 2d 工程文档优化    文档组合分析→交叉映射→逐章注入
  └─ 2e/2f 术语与交接  term_aliases + Step3/6/7 handoff
Step 3: 生成文献检索方案（search_tasks+L1→L2→L3分层路由+概念块布尔+arXiv条件触发）→ 检索方案.md → 检索方案.pdf
Step 4: 多渠道检索+评分+报告（4a-4h） → 检索文献表.md/.xlsx + 检索报告.md/.pdf + 文献库.bib + saturation_snapshot.json + 中文论文元数据.json
  ├─ 4a 文献可信度   VERIFIED/WARN/REJECT 三态 + DOI/source_id/元数据可追溯
  ├─ 4b DOI去重     多源合并去重
  ├─ 4c 相关性评分   五维度 0-25 + rcs-rubric 启发
  ├─ 4d 筛选标准     Tier 1-4 分级，T4 剔除
  ├─ 4e 引文扩展 🆕  单轮1-hop/T1种子/内部评分闭环
  ├─ 4f 饱和度曲线 🆕 全量 T1-T3 覆盖率估算 + 解释 + 建议
  ├─ 4g 检索报告 🆕  统一交付物 .md+.xlsx+.bib +检索报告(.md+.pdf)+饱和度+PRISMA
  └─ 4h 完成 🆕      汇报 + 决策记录 + 转交 Step 5
Step 5: 统一路由下载               → paper-temp/ PDFs
Step 6: Zotero 文库管理              → zotero-架构.md + 文献-Zotero架构对照.md/json + pdf-附件池索引.json + Zotero 条目/PDF 附件
  ├─ 6a 生成架构    根据 Step 2 大纲生成 zotero-架构.md/json
  ├─ 6b 生成对照    结合 Step 4 文献库.bib/中文元数据 与 zotero-架构生成文献-Zotero架构对照.md/json
  ├─ 6c 创建集合    通过 Zotero MCP 创建集合并检查架构一致性
  └─ 6d 导入附件    英文按 DOI/BibTeX，中文按 source_id+CSL JSON 入库，并从 PDF 附件池关联文件
Step 7: 论文写作（paper_type×language×target_genre） → style_profile.md/json → section_blueprints.md/json → writing_rationale_matrix.md/json → argument_plan.md/json → 论文初稿.md / 指定章节.md / .docx
  ├─ 7.1 文献证据矩阵   13 列证据矩阵，按证据优先级填充 🆕
  ├─ 7.2 风格学习+蓝图 目标体裁/文档风格画像+章节蓝图+写作逻辑矩阵 🆕 v1.1.0
  ├─ 7.3 类型+语言+体裁识别 research/en/zh/zh-to-en + journal/thesis/conference/existing-draft
  ├─ 7.4 写作模式       full-document/review-only/abstract-only/chapter-only/continue-existing/revision-only
  ├─ 7.5 语言差异化     zh/en/zh-to-en 写作规范+章节命名
  ├─ 7.5b 章节级论证计划 先锁定 claim/证据/图表/弱点边界
  ├─ 7.6 章节写作规则   摘要/引言/相关工作/方法/实验/结论
  ├─ 7.7 实时引文支撑   Zotero优先匹配→证据读取→评估→引用确认；新文献回流 Step 4/6
  ├─ 7.8 防幻觉机制     evidence_level + JSON追溯 + 中文元数据完整
  ├─ 7.9 同行评审仿真   评审报告.md + rebuttal-预演.md → PDF
  ├─ 7.9b 修稿教练      revision_roadmap.md + response_letter_skeleton.md + evidence_gap_list.md
  ├─ 7.9c 复评          rereview_report.md（验证问题是否真的解决）
  ├─ 7.10 科研图表生成  figures/ + 图表清单.md
  └─ 7.11 写后引用审计  三层审计：format_status / mapping_status / evidence_status + recommended_action
Step 8: 论文润色（含句长波动检测）   → 论文润色稿.md → 论文润色稿.docx
```

---

## Agent 路由规则

> 本文件是工作流的入口路由。每个 Step 的详细执行规则在 `agents/` 目录下。
> 架构借鉴自 ResearchWiki 的 Agent 模块化模式。
> `README.md` 仅作为 GitHub 展示与快速开始说明；运行时规则以本文件和 `agents/step_*.md` 为准。
> **总原则：所有 Step 都支持 direct-entry。** 前序产物是高质量输入，不是硬入口门槛；若缺失，优先在当前 Step 内重建最小依据、输出 plan-only 工件或记录风险边界，而不是默认要求用户回到上一步。

### 路由表

| 触发条件 | Agent 文件 | 说明 |
|----------|-----------|------|
| "确定研究主题" / "厘清研究方向" / Step 1 相关触发词 | `agents/step_1_entry.md` | 新入口层：先判定 `user_stage / goal_type / search_depth / evidence_risk`，再加载 Step 1 主协议 |
| "生成论文大纲" / "大纲评审" / "优化已有大纲" / Step 2 相关触发词 | `agents/step_2_outline.md` | 章节大纲 + 关键词清单 + 章节证据需求表 + 2c 已有大纲评估优化 + 五维评审 + 术语映射 |
| "制定检索方案" / Step 3 相关触发词 | `agents/step_3_entry.md` | 新入口层：先判定 `standard / citation-expansion / prisma-s / chinese-sources`，再加载 Step 3 主协议 |
| "检索论文" / Step 4 相关触发词 | `agents/step_4_search_score.md` | search_tasks 执行 + 5 维评分 + 引文验证 + 🆕 引文扩展/饱和度/7 件套检索报告 |
| "饱和度曲线" / "discovery curve" | `agents/step_4_search_score.md` | 🆕 子步骤 4f：文献覆盖率估算 |
| "引文扩展" / "citation network" | `agents/step_4_search_score.md` | 🆕 子步骤 4e：单轮 1-hop 引文网络扩展 |
| "下载论文" / Step 5 相关触发词 | `agents/step_5_download.md` | 统一下载路由（Sci-Hub→SD→IEEE→Generic） |
| "Zotero 文库整理" / Step 6 相关触发词 | `agents/step_6_entry.md` | 新入口层：先判定 `plan-from-bib / plan-from-zotero / consistency-adjustment`，再加载 Step 6 主协议 |
| "文献-Zotero架构对照" / "PDF 导入 Zotero" | `agents/step_6_entry.md` | 子步骤 6b/6d：`.json` 为完整执行源，`.md` 为审阅版；英文 DOI/BibTeX，中文 source_id/CSL JSON，多来源 PDF 附件池关联 |
| "综述矩阵" / "期刊风格学习" / "学位论文风格" | `agents/step_7_entry.md` | Step 7 入口层：按 `mode + target_genre` 判定，按需加载风格学习、章节蓝图、审稿协议、引用审计契约 |
| "写论文" / "只写部分章节" / "续写已有草稿" / "审稿意见解读" / "修稿路线图" / Step 7 相关触发词 | `agents/step_7_entry.md` | 风格画像 + 章节蓝图 + 写作逻辑矩阵 + 文献证据矩阵 + target_genre 驱动写作 + 反模式闸门 + 修稿教练 + 三层引用审计 + 图表生成 |
| "论文润色" / Step 8 相关触发词 | `agents/step_8_entry.md` | 新入口层：先判定 `revision_scope + language + target_genre`，默认保守改写，不替代 Step 7 重写 |
| 技术问题 / 报错排查 | `agents/known_pitfalls.md` | Python/CDP/Zotero 已知陷阱 |

### 路由规则

1. **精确匹配优先** — 根据触发词精确匹配对应的 agent 文件
2. **上下文推断** — 如果用户只说"继续下一步"，根据上一轮的 Step 编号自动加载下一个 agent
3. **跨 Step 跳转** — 用户可以直接跳到任意 Step（如"直接下载论文"→ Step 5）
4. **多文件加载** — 某些场景需要同时加载多个 agent（如 Step 3 执行前需加载 Step 2 的术语映射表）

### 共享记忆文件 (Shared Memory)

每个 agent 启动时必须检查以下文件是否存在/最新：

| 文件 | 用途 | 写入者 | 读取者 |
|------|------|--------|--------|
| `.skill-state/error_log.md` | AI 错误积累 | 所有 agent | 所有 agent |
| `.skill-state/decision_log.md` | 结构性决策记录 | 所有 agent | 所有 agent |
| `.skill-state/term_aliases.md` | 术语标准化映射 | Step 2, Step 8 | Step 3, Step 7, Step 8 |

### 统一 Checkpoint 协议

> Checkpoint 是“当前 Step 的输入与风险确认协议”，不是线性流程锁。用户可以从任意 Step 开始；只要已有材料满足当前 Step 的输入契约，就在当前 Step 内完成 checkpoint，不要求回跑前序步骤。

**Checkpoint 状态：**

| status | 含义 |
|--------|------|
| `confirmed_by_workflow` | 前序 Step 刚生成产物并已由用户确认 |
| `satisfied_by_user_artifact` | 用户已有大纲、检索方案、文献表、Zotero 文库等，可直接作为当前 Step 输入 |
| `satisfied_by_agent_reconstruction` | Agent 从用户材料中反推/补齐最小 handoff 后确认 |
| `blocked` | 当前输入不足，且无法安全继续当前 Step 的下一项动作 |

**entry_mode：** `normal_chain` / `direct_entry` / `resume` / `repair` / `partial_artifact`

**软确认 / 高风险动作确认：**
- `CP-TOPIC` 和 `CP-OUTLINE` 默认是 soft checkpoint：只确认当前输入依据，不能阻拦任意 Step 启动；只有主题/大纲不足以支撑当前动作时才设为 `status: blocked`。
- `CP-SEARCH`、`CP-DOWNLOAD-LOGIN`、`CP-CITATION-WARN` 是高风险动作确认：只阻塞真实检索执行、已判定需要登录的下载、异常证据进入关键结论；不得阻拦任意 Step 启动、计划生成、只读检查或低风险整理。
- `CP-ZOTERO-WRITE` 是外部状态写入确认：不限制 Step 6/7 直接入口，也不限制读取 Zotero、生成计划、查重或 dry-run；只在即将实际修改 Zotero 文库前要求用户确认写入范围。

**标准 checkpoint 块：**

```md
## CHECKPOINT 2 — CP-OUTLINE

entry_mode: direct_entry
status: satisfied_by_user_artifact
blocks_next: none unless outline is structurally insufficient
must_confirm: false

summary:
- 用户已提供大纲，可作为检索结构使用。
- 缺少正式 Step 2 产物，但当前 Step 不要求回跑 Step 2；Agent 可基于该大纲继续生成 search_tasks。

user_options:
1. 确认按此大纲进入 Step 3
2. 先轻量修订大纲再进入 Step 3
3. 暂停，用户补充大纲细节

optional_confirmation:
- “确认 CP-OUTLINE”
```

**Checkpoint 映射：**

| checkpoint | 触发点 | 阻塞动作 |
|------------|--------|----------|
| `CHECKPOINT 1 — CP-TOPIC` | 记录当前主题依据 | 默认不阻塞；仅主题不足时 blocked |
| `CHECKPOINT 2 — CP-OUTLINE` | 记录当前大纲依据 | 默认不阻塞；仅大纲不足时 blocked |
| `CHECKPOINT 3 — CP-SEARCH` | 即将执行多源检索命令前 | Step 4 实际检索命令；不拦检索方案生成 |
| `CHECKPOINT W — CP-DOWNLOAD-LOGIN` | `access_probe` 判定需要登录后 | 需要登录态的中文源/出版社下载；不拦 Sci-Hub/OA/IP 已授权 |
| `CHECKPOINT W — CP-ZOTERO-WRITE` | 即将实际修改 Zotero 文库前 | 外部状态写入确认：集合创建、条目导入、移动集合、附件动作；不拦只读规划 |
| `CHECKPOINT W — CP-CITATION-WARN` | 异常证据将支撑关键 claim 前 | 将 WARN/弱证据/摘要级证据用于正文关键结论 |

确认结果写入 `.skill-state/decision_log.md`；如需要状态恢复，可额外写入运行时文件 `.skill-state/checkpoints.json`，但不要把该 JSON 作为 skill 仓库模板文件创建。

### 自动升级提醒

每个 agent 启动时，在 Pre-read Checklist 阶段先执行一次轻量更新检查：

```
python3 "$SKILL_DIR/scripts/check_skill_update.py" --quiet
```

- 该检查为 **best-effort**：网络不可用、远程仓库不可访问或 git 不可用时不得阻塞主流程
- 默认 24 小时最多提醒一次，状态写入用户缓存目录，不写入项目 `.skill-state/`
- 只打印提醒和更新命令，不自动执行 `git pull`
- 手动强制检查：`python3 "$SKILL_DIR/scripts/check_skill_update.py" --force`
- 关闭自动检查：设置环境变量 `MORE_PAPER_SKILL_UPDATE_CHECK=0`
- 调整检查间隔：设置 `MORE_PAPER_SKILL_UPDATE_INTERVAL_HOURS=6`

### 🆕 .skill-state/ 初始化规则

运行态的状态文件存放在项目工作目录下的 `.skill-state/` 中（与 skill 目录隔离）。

**初始化时机：** 每个 agent 启动时，在 Pre-read Checklist 阶段检查：

```
if [ ! -d "$CWD/.skill-state/" ]; then
  mkdir -p "$CWD/.skill-state/"
  cp "$SKILL_DIR/references/templates/"*.md "$CWD/.skill-state/"
fi
```

- `$CWD` = 当前项目工作目录（即用户运行 agent 的目录）
- `$SKILL_DIR` = skill 安装目录（即本 SKILL.md 所在目录）
- 三个文件（`term_aliases.md`、`error_log.md`、`decision_log.md`）通过模板复制获得初始内容
- **注意：** 不要直接修改 `references/templates/` 下的文件——修改应写入 `.skill-state/` 中的副本
- **多项目隔离：** 每个项目目录下的 `.skill-state/` 独立维护，互不干扰
- **git 隔离：** `.skill-state/` 已在 `.gitignore` 中，不会污染技能仓库


---

## ⚙️ 依赖清单与配置提示

> **一键安装：** `pip install -r requirements.txt`
> 详细说明见 [`requirements.txt`](requirements.txt) — 必选依赖已解注，可选依赖按需安装。

| 依赖 | 用途 | 步骤 | 必选 |
|------|------|------|:--:|
| **Python 3.9+** | 运行所有脚本 | 全部 | ✅ 必选 |
| **websocket-client** | CDP 协议连接 Chrome/Edge | Step 5 | ✅ 必选 |
| **openpyxl** | 检索文献表 .xlsx 生成 | Step 4g | ✅ 必选 |
| **arxiv (>=2.1)** | arXiv API 检索 | Step 4 | ⬜ 可选 |
| **beautifulsoup4** | 万方数据 HTML 解析 | Step 4 | ⬜ 可选 |
| **PyMuPDF (fitz)** | 提取 PDF 全文文本 | Step 8 | ⬜ 可选 |
| **python-docx** | 提取/生成 .docx | Step 2b/2c | ⬜ 可选 |
| **fpdf2 (>=2.5.1)** | 生成中文 PDF 报告 | Step 2b/6d | ⬜ 可选 |
| **numpy** | 图表数据处理 | Step 7.10 | ⬜ 可选 |
| **matplotlib** | 科研图表生成 | Step 7.10 | ⬜ 可选 |
| **Pillow** | 图片生成/海报 | Step 7.10 | ⬜ 可选 |
| **Zotero MCP Server** | 对话读写 Zotero 文库 | Step 6-7 | ⬜ 可选 |

---

## 脚本速查表

| 脚本 | 步骤 | 用途 |
|------|------|------|
| `scripts/search_by_topic.py` | 4 | 多渠道检索（Semantic Scholar / Crossref / OpenAlex / 🆕 CNKI / 🆕 Wanfang Data）+ 引文网络 + 语义缓存。CNKI 中文文献：校园 IP 直连零配置；校外 CDP Chrome（🚀 配合 batch_chinese_search.sh 交互式批量检索，防止跨命令 CDP 断连）。Wanfang：校内 IP；校外 CARSI SSO（同上）。
| `scripts/batch_chinese_search.sh` 🆕 | 4/5 | 🆕 交互式批量 CDP 检索脚本。同一条命令内完成：启动/复用 CDP Chrome → 导航到目标网站 → 等待 CARSI 登录确认 → 批量执行所有 CNKI/万方检索 → 输出 .bib 文件。支持 `--login-only` 模式（仅启动 Chrome + 等待登录，用于 Step 5 下载门控）。解决 `require_escalated` 跨命令 CDP 断连问题。 ||
| `scripts/generate_retrieval_report.py` | 4g | 🆕 检索文献表一键交付（.xlsx + .bib）— 🔴 Step 4 强制 |
| `scripts/generate_search_report.py` | 4g | 🆕 检索方法论报告（8 章节：范围→流水线→评分→分布→饱和度→建议） |
| `scripts/discovery_curve.py` | 4d | 🆕 饱和度曲线估算 |
| `scripts/arxiv_helper.py` | 4a | 🆕 arXiv 新鲜度检索（L2 条件触发） |
| `scripts/unified_download_router.py` | 5 | 统一下载路由入口 |
| `scripts/generic_publisher_downloader.py` | 5 | 通用 CDP 下载引擎 |
| `scripts/download_via_scihub.py` | 5 | Sci-Hub CDP 下载 |
| `scripts/download_via_ieee.py` | 5 | IEEE CDP 两步走下载 |
| `scripts/auto_sd_downloader.py` | 5 | SD 全自动下载（断点续跑） |
| `scripts/organize_zotero.py` | 6 | 生成 Zotero 文库架构 |
| `scripts/setup_zotero.py` | 6 | Zotero MCP 一键安装+配置 |
| `scripts/check_skill_update.py` | 全部 | 自动升级提醒：检查本地版本元数据和远程 git HEAD，默认每日最多提醒一次 |
| `scripts/learn_journal_style.py` | 7.2 | 目标体裁/文档风格学习 🆕 |
| `scripts/learn_journal_style.py` | 7.2 | 风格画像生成（输出 `style_profile.md/json`）🆕 |
| `scripts/generate_section_blueprints.py` | 7.2 | 章节蓝图生成（输出 `section_blueprints.md/json`）🆕 |
| `scripts/generate_writing_rationale.py` | 7.2 | 写作逻辑矩阵生成（输出 `writing_rationale_matrix.md/json`）🆕 |
| `scripts/batch_read_pdfs.py` | 7 | 批量提取 PDF 全文文本 |
| `scripts/citation_audit.py` | 7.11 | 写后引用审计 🆕 |
| `scripts/generate_figures.py` | 7.10 | 科研图表生成 🆕 |
| `scripts/md_to_pdf.py` | 2/3/4/7.9 | Markdown → PDF 转换器 |
| `scripts/md_to_docx.py` | 7/8 | Markdown → DOCX 转换器 |
| `config/publishers.toml` | 5 | 集中式出版社知识库 |

---

## 参考文件

| 文件 | 关联步骤 |
|------|---------|
| `.skill-state/error_log.md` 🆕 | 全部 — AI 错误积累与修正规则 |
| `.skill-state/decision_log.md` 🆕 | 全部 — 结构性决策记录 |
| `.skill-state/term_aliases.md` 🆕 | Step 2/3/7/8 — 术语标准化映射 |

### 🆕 .skill-state/ 初始化规则

运行态的状态文件存放在项目工作目录下的 `.skill-state/` 中（与 skill 目录隔离）。

**初始化时机：** 每个 agent 启动时，在 Pre-read Checklist 阶段检查：

```
if [ ! -d "$CWD/.skill-state/" ]; then
  mkdir -p "$CWD/.skill-state/"
  cp "$SKILL_DIR/references/templates/"*.md "$CWD/.skill-state/"
fi
```

- `$CWD` = 当前项目工作目录（即用户运行 agent 的目录）
- `$SKILL_DIR` = skill 安装目录（即本 SKILL.md 所在目录）
- 三个文件（`term_aliases.md`、`error_log.md`、`decision_log.md`）通过模板复制获得初始内容
- **注意：** 不要直接修改 `references/templates/` 下的文件——修改应写入 `.skill-state/` 中的副本
- **多项目隔离：** 每个项目目录下的 `.skill-state/` 独立维护，互不干扰
- **git 隔离：** `.skill-state/` 已在 `.gitignore` 中，不会污染技能仓库

| `references/search-query-frameworks.md` | Step 3 — 检索查询框架参考 |
| `references/rcs-rubric.md` 🆕 | Step 4 — 主题匹配度评鉴启发指南（RCS 启发） |
| `references/literature-review-matrix-schema.md` | Step 7.1 — 13 列文献证据矩阵定义 |
| `references/literature-review-docx-guide.md` | Step 7 — 综述 DOCX 写作结构 |
| `references/gbt7714-2015-citation-format.md` | Step 7 — GB/T 7714 引用格式 |
| `references/citation-audit-guide.md` | Step 7.11 — 引用审计方法论 |
| `references/direct-api-search-fallback.md` | Step 4 — search_by_topic.py 不可用时的直接 API 检索方案 |
| `references/nature-figure-style-guide.md` | Step 7.10 — 科研图表设计规则 |
| `references/publisher-access-matrix.md` | Step 5 — 出版商下载可行性对照表 |
| `agents/known_pitfalls.md` 🆕 | 全部 — 已知陷阱与故障排除 |

---

## 目录结构

```
More-Paper-Workflow-Pro-Skill/
├── SKILL.md                          ← 本文件（轻量路由器 ~200 行）
├── README.md
├── agents/                           ← 🆕 Agent 模块目录
│   ├── step_1_topic.md               ← Step 1: 交互式定题（v2.0 增强版）
│   ├── step_2_outline.md             ← Step 2: 大纲生成 + 术语映射
│   ├── step_3_search_plan.md         ← Step 3: 检索方案
│   ├── step_4_search_score.md        ← Step 4: 检索与评分
│   ├── step_5_download.md            ← Step 5: 统一下载
│   ├── step_6_zotero.md              ← Step 6: Zotero 文库管理
│   ├── step_7_writing.md             ← Step 7: 论文写作
│   ├── step_8_polishing.md           ← Step 8: 论文润色
│   └── known_pitfalls.md             ← 已知陷阱
├── config/
│   └── publishers.toml
├── scripts/                          ← Python 可执行脚本
├── references/                       ← 参考文档 references/                       ← 模板与参考文档（含 🆕 error_log/decision_log/term_aliases） templates/（空模板，运行态复制到 .skill-state/）
└── docs/
```

---

## 版权

© 2026 Dr. Jiang Bingyun (江博士). All rights reserved.

本技能及其全部脚本、文档、参考文件均以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可发布。

- **BY（署名）**：使用或演绎必须保留原作者署名
- **NC（非商业）**：禁止用于商业用途
- **SA（相同方式共享）**：演绎作品必须以相同许可发布
