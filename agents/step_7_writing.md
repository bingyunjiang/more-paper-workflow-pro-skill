# Step 7: 论文写作

> 利用 Step 1-6 的所有产出，以下载的 PDF 作为知识库，撰写正式学术论文。
> **核心原则：每处引用必须来自实际 PDF 内容，抑制大模型幻觉。**

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `研究主题.md` — Step 1 产出（研究方向 + 预审结论）
- [ ] `大纲关键词.md` — Step 2 产出（章节结构） + `.skill-state/term_aliases.md` 🆕
- [ ] `检索文献表.md` — Step 4 产出（参考文献 + 评分）
- [ ] `文献库.bib` — Step 4 产出（筛选后 BibTeX 文献库）
- [ ] `zotero-架构.md` — Step 6 产出（Zotero 集合结构）
- [ ] `文献-Zotero架构对照.md/json` — Step 6 产出（文献到集合、PDF 附件的映射；JSON 为完整机器源）
- [ ] `.skill-state/term_aliases.md` — 🆕 术语标准化映射（确保写作用词与检索一致）
- [ ] `references/literature-review-matrix-schema.md` — 综述矩阵 schema
- [ ] `references/journal-style-learning-guide.md` — 期刊风格学习方法论
- [ ] `references/gbt7714-2015-citation-format.md` — 引用格式规范
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则

---

## 2. 适用任务 (Applicable Tasks)

- 撰写完整学术论文（5 种 paper_type × 3 种语言）
- 写文献综述（review 类型专属 8 节骨架 + 7 条纪律）
- 写中英文双边摘要
- 实时引文支撑（7e）
- 同行评审仿真 + Rebuttal 预演（7f）
- 科研图表生成（7g）
- 写后引用审计（7h）

---

## 3. 不适用任务 (Non-applicable Tasks)

- 大纲生成 → 路由到 `agents/step_2_outline.md`
- 文献检索 → 路由到 `agents/step_4_search_score.md`
- 论文润色 → 路由到 `agents/step_8_polishing.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 研究主题 | Step 1 | .md | ✅ |
| 大纲关键词 | Step 2 | .md | ✅ |
| 检索文献表 | Step 4 | .md | ✅ |
| BibTeX 文献库 | Step 4 | .bib | ✅ |
| PDF 知识库 | Step 5 | paper-temp/*.pdf | ✅ |
| Zotero 架构 | Step 6 | .md | ✅ |
| 文献-Zotero架构对照 | Step 6 | .md/.json | ✅ |
| 综述矩阵 | Step 7.0 | .csv/.md | 写作前生成 |
| 期刊风格画像 | Step 7.1 | .md | 🆕 |
| 章节蓝图 | Step 7.1 | .md | 🆕 |

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 综述矩阵 | CSV/Markdown | 13 列证据矩阵 |
| research_dossier/ | 目录 | 期刊风格画像 + 章节蓝图 + 写作逻辑矩阵 |
| 论文初稿 | .md / .docx | 含完整结构和参考文献 |
| 中→英术语对照表 | .md | zh-to-en 模式额外产出 |
| 评审报告 + rebuttal-预演 | .md → .pdf | 7f 质量门产出 |
| 图表 | SVG/PDF/TIFF | 7g 产出，保存到 figures/ |
| 引用审计报告 | .md → .pdf | 7h 产出 |

---

## 6. 执行流程 (Execution Flow)

### 前置输入

写作开始前，确认以上所有前置输入文件可访问。

### 7.0: 生成文献综述矩阵（写作前证据组织）

**13 列矩阵：** 作者年份 | 标题 | 研究问题 | 理论/概念 | 数据/样本 | 方法 | 核心发现 | 贡献 | 局限 | 与我的主题关系 | 可引用摘录 | 我的笔记 | DOI/URL

**输入优先级：**
```
1. Zotero 笔记 (zotero_get_notes)              ← 最高优先级
2. PDF 标注/高亮 (zotero_get_annotations)       ← 精读标注
3. Zotero 元数据 (zotero_get_item_metadata)     ← 标题/作者/DOI/摘要
4. PDF 全文 (zotero_get_item_fulltext)          ← 完整原文
5. BibTeX/摘要 (文献库.bib / abstractNote)       ← 最低优先级
```

> 不要一上来就读 PDF 全文。先用笔记、标注、元数据和 `文献-Zotero架构对照.json` 判断优先级；`.md` 只用于人工审阅。

**缺失值约定：** `未提及`（论文确实未讨论）/ `待补充`（计划后续补全）/ `推断：{内容}`（基于已有信息合理推断）

### 7.1: 目标期刊风格学习与写作蓝图

**核心理念：** paper_type 轴告诉你"写什么类型的论文"，目标期刊风格学习告诉你"怎么写才能让这个期刊的读者和审稿人觉得'这是自己人写的'"。

**工作流：**
```
Step 7.1-1: 风格剖析      → style_profile.md        (四维度量化：格式化/结构/引用/语言)
Step 7.1-2: 章节蓝图      → section_blueprints.md    (逐节写作计划：论证链+证据映射+图表位置)
Step 7.1-3: 写作逻辑矩阵  → writing_rationale_matrix.md (逐单元理由)
Step 7.1-4: LaTeX 校验    → latex_check.md（可选）
```

**两种分析深度：**

| 模式 | 范文数 | 时长 | 产出 | 适用场景 |
|------|:---:|------|------|------|
| **Flash** | 3 篇 | ~3 min | `style_profile.md` | 初次投稿该期刊 |
| **Pro** | 6 篇 | ~8 min | `style_profile.md` + `research_dossier.md` | 核心目标期刊 |

```bash
python3 scripts/learn_journal_style.py --target-journal "Applied Thermal Engineering" --pdf-dir paper-temp/ --mode flash
python3 scripts/generate_section_blueprints.py research_dossier/style_profile.md 大纲关键词.md --evidence 综述矩阵.csv --output research_dossier/
python3 scripts/generate_writing_rationale.py research_dossier/section_blueprints.md --style-profile research_dossier/style_profile.md --output research_dossier/writing_rationale_matrix.md
```

### 7a: 论文类型与语言双轴识别

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
| **zh-to-en** | 中文草稿→英文成稿 | 按目标期刊 |

### 7b: 写作模式选择

| 模式 | 触发场景 |
|------|----------|
| `full` | 已有清晰大纲和文献，直接逐章完整撰写 |
| `outline-only` | 不确定结构，先生成详细大纲 |
| `plan` | 需要多轮引导交互来厘清论点 |
| `abstract-only` | 仅写中英文摘要 |
| `argument-first` | 先写一句话核心论点，确保方向正确再展开 |

### 7c: 语言差异化规则

**zh-to-en 特殊规则（中国研究者最常用场景）：**
1. 术语锁定：写作开始前先列出"中→英关键术语对照表"
2. 中文笔记→英文翻译四步法（提取论点→按英文逻辑重排序→英文撰写→检查翻译腔）
3. 识别中文写作特有的"英文不该有"的模式
4. 中文数字和单位的英文转换

### 7d: 章节级写作规则

**摘要：** en: 150-250 words / zh: 300-500 字 | 结构：问题→方法→关键结果→意义

**引言/绪论：** 三层递进（大背景→子领域 gap→本文贡献 3-5 条）| 贡献条目标注对应章节

**相关工作/文献综述：** 按主题分组，**禁止按论文逐条罗列** | 每组末尾对比"本文与这些工作的不同"

**方法/实验方案：** 先符号后公式 | 按逻辑顺序非时间线 | 图表在引用后出现

**实验与结果：** 以研究问题开头 | 图表自包含 | 数据→分析→解释三层递进

**结论：** 不是摘要的复读 | 诚实说局限（2-3 条） | 具体未来方向

#### 7d.1 段落与句子级自查

**① 每段一个工作（One paragraph, one job）：** 8 种可选类型：context / gap / approach / result / comparison / mechanism / implication / limitation

**② 从证据向外写：** 证据/数据 → 解释 → 结论

**③ 校准动词强度：** show/demonstrate → suggest/indicate → may/could

**④ 清除虚假新颖性声明：** 扫描 first/novel/unprecedented 等词的滥用

**⑤ 段落流检查：** 一段一个信息，首句是主题句，后续句与上句有显式关系

#### 🆕 术语对齐检查

- 每章写作前，确认本章核心术语与 `.skill-state/term_aliases.md` 中 Recommended page 匹配
- 中文论文：全篇统一使用 Main Term 的中文形式
- 英文论文：全篇统一使用 Main Term 的英文形式
- 同一概念在全文中的术语形式不超过 1 个（禁止同义词轮换）

### 7e: 实时引文支撑

**分段引用工作流（7 步）：**
```
写完一段正文 →
  ① Segment — 将段落拆为可引用的 claim 片段
  ② Parse — 每个 claim 提取关键词 + 判断是否需要新引用
  ③ Search — 按期刊范围搜索
  ④ Evaluate — 打开摘要验证（Strong/Moderate/Weak）
  ⑤ Export — 输出为 Zotero .bib 格式
  ⑥ Report — 每段写完后简要报告引文匹配结果
  ⑦ 用户确认后写入引用标注
```

**引用密度指南：** 引言每 2-3 句 1 条 | 相关工作每段 3-8 条 | 方法每段 1-2 条 | 实验每段 1-3 条 | 讨论每段 2-4 条 | 结论 0-1 条

### 防幻觉机制（核心）

| 机制 | 说明 |
|------|------|
| **先读后写** | 引用某篇文献前，必须读取 PDF 全文 |
| **交互确认** | 每章写前与用户沟通参考哪几篇 PDF |
| **索引必达** | 每处引用标注索引号 |
| **不编造引用** | 未读取过 PDF 的文献，不得引用 |
| **原文比对** | 引用具体数据时注明 PDF 来源 |

### 7f: 同行评审仿真（质量门）

五维度评分（0-10 分 + 权重）：原创性 20% / 方法严谨性 25% / 证据充分性 25% / 论证连贯性 15% / 写作质量 15%

三审稿人视角：Reviewer A（方法严谨性）/ Reviewer B（创新性）/ Reviewer C（清晰度与完整性）

Rebuttal Letter 预演：不等真实投稿，在质量门阶段就预演 rebuttal——暴露"以为能说服审稿人、实际说服不了"的薄弱环节。

**限 2 轮修改。** 评分 < 5 的维度 → 回到对应步骤补足。

### 7g: 科研图表生成 🆕

支持 10 种图表类型（grouped_bar / stacked_bar / trend_line / heatmap_seq / heatmap_div / bubble_scatter / radar_polar / gridspec / fill_between）。

```bash
python3 scripts/generate_figures.py 论文初稿.md --data data/ --output figures/
```

设计规则：三级信息层次 / 直标优于图例 / 无反冗余面板 / 低饱和度配色 / 绿色红色仅用于方向性。

### 7h: 写后引用审计 🆕

> 核心目的：抓"LLM 把标题相关的论文当成支撑某个具体声明的论文"这种张冠李戴。

```
稿件 → 提取所有引用标记 [1][2]...[N] → 逐条：
  ① 获取被引论文摘要（Crossref / Semantic Scholar API）
  ② 定位稿件中引用该论文的具体声明（claim sentence）
  ③ 判断：摘要内容是否支撑这个 claim？
     ✅ 支撑 / 🟡 弱支撑 / ❌ 不支撑
  ④ 输出审计报告
```

```bash
python3 scripts/citation_audit.py 论文初稿.md --output 引用审计报告.md
```

四种误引模式：标题-摘要张冠李戴 / 综述当实证 / 贡献过度归因 / 数据编造

---

## 7. 质量门槛 (Quality Gates)

- [ ] paper_type 和 language 已识别
- [ ] 7.0 综述矩阵：13 列完整，证据优先级规则已遵循
- [ ] 7.1 期刊风格：Flash 或 Pro 模式已完成，style_profile.md 已生成
- [ ] 防幻觉机制：每处引用均来自实际 PDF 内容
- [ ] 7d.1 段落自查：每段一个工作 / 从证据向外写 / 动词校准 / 无虚假新颖性 / 段落流
- [ ] 🆕 术语对齐：核心术语与 `.skill-state/term_aliases.md` 一致
- [ ] 7f 同行评审：五维评分全部 ≥ 5 分（<5 分已回退修复）
- [ ] 7h 引用审计：❌ 不支撑引用已移除或替换

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `论文初稿.md` 已生成
- [ ] `论文初稿.docx` 已自动生成
- [ ] `综述矩阵.csv` + `综述矩阵.md` 已生成
- [ ] 期刊风格产出：`research_dossier/` 目录完整
- [ ] `评审报告.md` + `rebuttal-预演.md` 已生成
- [ ] `引用审计报告.md` 已生成
- [ ] figures/ 目录图表完整

### 术语对齐检查 🆕
- [ ] 逐章扫描核心术语，确认与 `.skill-state/term_aliases.md` 一致
- [ ] 发现术语不一致 → 修正为 Main Term → 如 Main Term 不当 → 更新 term_aliases.md → 记录到 decision_log.md

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 引用编造 → 追加到 `.skill-state/error_log.md`
  - 综述矩阵证据填充错误 → 追加到 `.skill-state/error_log.md`
  - 期刊风格分析偏差 → 追加到 `.skill-state/error_log.md`
  - 术语混用 → 追加到 `.skill-state/error_log.md`
  - 7h 审计发现系统性误引 → 追加到 `.skill-state/error_log.md`

### 决策日志更新 🆕
- [ ] 是否调整了章节结构？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否修改了 paper_type 判定？→ 记录到 `.skill-state/decision_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：论文润色（Step 8）
  > **下一步 → Step 8：** 同行评审通过 + rebuttal 预演无遗漏 + 引用审计无重大问题后，进入精炼润色、去 AI 痕迹，提升至可投稿水平。

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **引用不足**：运行 7e 扩展搜索补充引用；检查引用密度指南
- **AI 痕迹明显**：7d.1 自查步骤逐项检查；Step 8 Level 3 去 AI 化
- **引用审计大量不支撑**：7h 逐条处理，❌ 级别优先替换或移除
- **术语不一致**：回查 `.skill-state/term_aliases.md`，全篇统一为 Main Term
