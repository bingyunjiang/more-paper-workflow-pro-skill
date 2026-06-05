---
name: more-paper-workflow-pro-skill
version: v1.0.5-20260605
description: 完整学术文献检索和写作工作流（8 步法 + 3 个 v1.1.0 新功能：科研图表生成、写后引用审计、目标期刊风格学习+蓝图）： 完整学术文献检索和写作工作流（8 步法）：①交互式确定研究主题（v2.0 增强版：阶段诊断→广度探索+预检索→深度聚焦→选题预审，借鉴 academic-mentor/nature-academic-search/deep-research/nature-reviewer 等 10 个 skill） ②生成大纲/关键词 ③制定检索方案 ④多渠道检索+评分 ⑤统一路由下载（Sci-Hub→SD CDP→IEEE CDP→Generic CDP） ⑥Zotero 文库管理（架构生成+PDF 导入+大纲对齐一致性调整+综述矩阵） ⑦论文写作（5 种模式含文献综述 + 中英文双边摘要 + 仿真评审质量门 + GB/T 7714 完整规范） ⑧论文润色（句长波动检测 + 四合一精修引擎：去 AI 痕迹 29 种模式 + 注入人味 + 章节风格指南 + before/after 对照表）
author: Dr. Jiang Bingyun（江博士）
wechat: Bingyunjiang
category: research
related_skills:
  - science-direct-cdp-pipeline: "Overlaps on CDP ScienceDirect download; this skill adds the full 8-step workflow from topic definition to paper polishing."
  - zotero-review-matrix-skill: "Source of literature-review-matrix-schema, literature-review-docx-guide, and gbt7714-2015-citation-format references. Integrated into Steps 6e and 7."
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
  - "Outline review"
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
  - "从参考文献列表中下载 PDF"
  - "BibTeX 批量下载 PDF"
  - "Sci-Hub 下载论文"
  - "Start batch downloading paper PDFs"
  - "Download all papers"
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
  # Step 6e: 综述矩阵
  - "综述矩阵"
  - "文献综述矩阵"
  - "生成综述矩阵"
  - "Review matrix"
  - "文献矩阵"
  - "文献审阅矩阵"
  - "论文审阅表"
  # Step 6f: 目标期刊风格学习+蓝图 🆕
  - "学习目标期刊风格"
  - "期刊风格分析"
  - "目标期刊蓝图"
  - "论文风格学习"
  - "期刊格式分析"
  - "Journal style learning"
  - "Target journal blueprint"
  - "Learn journal style"
  - "Analyze target journal"
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
  # Step 7g: 科研图表生成 🆕
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
  # Step 7h: 引用审计 🆕
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
  # 工程文档→大纲优化（Step 2c）
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
  ├─ 1b 广度探索+预检索  发散子方向 → 文献量/趋势/gap初判
  ├─ 1c 深度聚焦        方法论深化 + 创新点预判
  ├─ 1d 选题预审        originality/importance/feasibility 三问
  └─ 1e 检索深度推断 🆕  auto tier: quick|standard|deep
Step 2: 生成研究大纲与关键词        → 大纲关键词.md → 大纲关键词.pdf
Step 3: 生成文献检索方案（L1→L2→L3分层路由+概念块布尔+arXiv条件触发）→ 检索方案.md → 检索方案.pdf
Step 4: 多渠道检索+评分+报告（4a-4h） → 检索文献表.md / .xlsx / .bib + 检索报告.md / .pdf
  ├─ 4a 引文验证    DOI有效性+元数据完整性
  ├─ 4b DOI去重     多源合并去重
  ├─ 4c 相关性评分   五维度 0-25 + rcs-rubric 启发
  ├─ 4d 筛选标准     Tier 1-4 分级，T4 剔除
  ├─ 4e 引文扩展 🆕  单轮1-hop/T1种子/内部评分闭环
  ├─ 4f 饱和度曲线 🆕 全量 T1-T3 覆盖率估算 + 解释 + 建议
  ├─ 4g 检索报告 🆕  统一交付物 .md+.xlsx+.bib +检索报告(.md+.pdf)+饱和度+PRISMA
  └─ 4h 完成 🆕      汇报 + 决策记录 + 转交 Step 5
Step 5: 统一路由下载               → paper-temp/ PDFs
Step 6: Zotero 文库管理              → zotero-架构.md + Zotero 桌面端 + 综述矩阵.csv
  ├─ 6a 生成架构    首次按大纲生成
  ├─ 6b 导入 PDF    将 PDF 拖入对应集合
  ├─ 6c 一致性调整  大纲修订后重对齐文库 🌟
  └─ 6e 综述矩阵    13 列证据矩阵，按证据优先级填充 🆕
Step 7: 论文写作（paper_type×language双轴）  → 论文初稿.md / .docx
  └─ 6f 风格学习+蓝图 目标期刊风格画像+章节蓝图+写作逻辑矩阵 🆕 v1.1.0
  ├─ 7a 类型+语言识别  research/en/zh/zh-to-en
  ├─ 7b 写作模式       full/outline-only/plan/abstract-only/argument-first
  ├─ 7c 语言差异化     zh/en/zh-to-en 写作规范+章节命名
  ├─ 7d 章节写作规则   摘要/引言/相关工作/方法/实验/结论
  ├─ 7e 实时引文支撑   分段→搜索→评估→导出
  └─ 7f 中英文双边摘要
Step 7f: 同行评审仿真（质量门）      → 评审报告.md + rebuttal-预演.md → 评审报告.pdf + rebuttal-预演.pdf
Step 7g: 科研图表生成 🆕 v1.1.0       → figures/ + 图表清单.md
Step 7h: 写后引用审计 🆕 v1.1.0       → 引用审计报告.md
Step 8: 论文润色（含句长波动检测）   → 论文润色稿.md → 论文润色稿.docx
```

---

## Agent 路由规则

> 本文件是工作流的入口路由。每个 Step 的详细执行规则在 `agents/` 目录下。
> 架构借鉴自 ResearchWiki 的 Agent 模块化模式。

### 路由表

| 触发条件 | Agent 文件 | 说明 |
|----------|-----------|------|
| "确定研究主题" / "厘清研究方向" / Step 1 相关触发词 | `agents/step_1_topic.md` | v2.0 增强版：阶段诊断→广度探索→深度聚焦→选题预审 |
| "生成论文大纲" / "大纲评审" / Step 2 相关触发词 | `agents/step_2_outline.md` | 大纲生成 + 五维评审 + 导师视角 + 术语映射表 |
| "制定检索方案" / Step 3 相关触发词 | `agents/step_3_search_plan.md` | L1→L2→L3 分层路由 + 概念块布尔 |
| "检索论文" / Step 4 相关触发词 | `agents/step_4_search_score.md` | 多渠道检索 + 5 维评分 + 引文验证 + 🆕 引文扩展/饱和度/检索报告 |
| "饱和度曲线" / "discovery curve" | `agents/step_4_search_score.md` | 🆕 子步骤 4f：文献覆盖率估算 |
| "引文扩展" / "citation network" | `agents/step_4_search_score.md` | 🆕 子步骤 4e：单轮 1-hop 引文网络扩展 |
| "下载论文" / Step 5 相关触发词 | `agents/step_5_download.md` | 统一下载路由（Sci-Hub→SD→IEEE→Generic） |
| "Zotero 文库整理" / Step 6 相关触发词 | `agents/step_6_zotero.md` | 架构生成 + PDF 导入 + 一致性调整 + 综述矩阵 + 期刊风格 |
| "写论文" / Step 7 相关触发词 | `agents/step_7_writing.md` | 5 种写作模式 + 引用审计 + 图表生成 |
| "论文润色" / Step 8 相关触发词 | `agents/step_8_polishing.md` | 四合一精修引擎 + 术语标准化 |
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
| `references/error_log.md` | AI 错误积累 | 所有 agent | 所有 agent |
| `references/decision_log.md` | 结构性决策记录 | 所有 agent | 所有 agent |
| `references/term_aliases.md` | 术语标准化映射 | Step 2, Step 8 | Step 3, Step 7, Step 8 |

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
| **PyMuPDF (fitz)** | 提取 PDF 全文文本 | Step 8 | ⬜ 可选 |
| **python-docx** | 提取/生成 .docx | Step 2b/2c | ⬜ 可选 |
| **fpdf2 (>=2.5.1)** | 生成中文 PDF 报告 | Step 2b/6d | ⬜ 可选 |
| **numpy** | 图表数据处理 | Step 7g | ⬜ 可选 |
| **matplotlib** | 科研图表生成 | Step 7g | ⬜ 可选 |
| **Pillow** | 图片生成/海报 | Step 7g | ⬜ 可选 |
| **Zotero MCP Server** | 对话读写 Zotero 文库 | Step 6-7 | ⬜ 可选 |

---

## 脚本速查表

| 脚本 | 步骤 | 用途 |
|------|------|------|
| `scripts/search_by_topic.py` | 4 | 多渠道检索（Semantic Scholar / Crossref / OpenAlex）+ 🆕 引文网络 + 语义缓存 |
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
| `scripts/learn_journal_style.py` | 6f | 目标期刊风格学习 🆕 |
| `scripts/generate_section_blueprints.py` | 6f | 章节蓝图生成 🆕 |
| `scripts/batch_read_pdfs.py` | 7 | 批量提取 PDF 全文文本 |
| `scripts/citation_audit.py` | 7h | 写后引用审计 🆕 |
| `scripts/generate_figures.py` | 7g | 科研图表生成 🆕 |
| `scripts/md_to_pdf.py` | 2/3/4/7f | Markdown → PDF 转换器 |
| `scripts/md_to_docx.py` | 7/8 | Markdown → DOCX 转换器 |
| `config/publishers.toml` | 5 | 集中式出版社知识库 |

---

## 参考文件

| 文件 | 关联步骤 |
|------|---------|
| `references/error_log.md` 🆕 | 全部 — AI 错误积累与修正规则 |
| `references/decision_log.md` 🆕 | 全部 — 结构性决策记录 |
| `references/term_aliases.md` 🆕 | Step 2/3/7/8 — 术语标准化映射 |
| `references/search-query-frameworks.md` | Step 3 — 检索查询框架参考 |
| `references/rcs-rubric.md` 🆕 | Step 4 — 主题匹配度评鉴启发指南（RCS 启发） |
| `references/literature-review-matrix-schema.md` | Step 6e — 13 列综述矩阵定义 |
| `references/literature-review-docx-guide.md` | Step 7 — 综述 DOCX 写作结构 |
| `references/gbt7714-2015-citation-format.md` | Step 7 — GB/T 7714 引用格式 |
| `references/citation-audit-guide.md` | Step 7h — 引用审计方法论 |
| `references/direct-api-search-fallback.md` | Step 4 — search_by_topic.py 不可用时的直接 API 检索方案 |
| `references/nature-figure-style-guide.md` | Step 7g — 科研图表设计规则 |
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
├── references/                       ← 模板与参考文档（含 🆕 error_log/decision_log/term_aliases）
└── docs/
```
