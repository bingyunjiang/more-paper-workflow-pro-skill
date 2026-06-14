# 目标期刊风格学习方法论

> 面向 `learn_journal_style.py` 和 Step 7.2 的参考文档。定义如何从范文提取风格画像、两种分析深度的取舍规则、以及风格画像如何指导 Step 7 写作。

## 范文选择标准

选取范文时应满足以下条件：

| 标准 | 要求 | 理由 |
|------|------|------|
| **时效性** | 近 3 年内发表 | 期刊风格可能随时间演变 |
| **高引用** | 引用量在同一期刊中排前 20% | 高质量论文更能代表期刊标准 |
| **主题接近** | 与你的研究主题在同一子领域 | 你的引用密度/章节结构与范文最好可比 |
| **类型匹配** | 范文的 paper_type 与你的相同 | research/methods/review 的结构区别很大 |

## Flash vs Pro 模式

| 维度 | Flash（3 篇范文） | Pro（6 篇范文） |
|------|------------------|-----------------|
| **分析时长** | ~3 分钟 | ~8 分钟 |
| **适用场景** | 初次投稿该期刊，快速对齐格式 | 核心目标期刊，需要深度模仿 |
| **分析维度** | 格式化规范 + 章节结构 + 引用密度 | Flash 全部 + 句式分析 + 论证模式提取 |
| **产出文件** | `style_profile.md` | `style_profile.md` + `research_dossier.md` |
| **统计可靠性** | 弱——3 篇样本易受单篇偏差影响 | 中等——6 篇可识别稳定模式 |

**建议：** 首次投稿先跑 Flash 快速对齐格式，确定该期刊是核心目标后再跑 Pro 做深度风格学习。

## 风格分析维度

### 1. 格式化规范

| 指标 | 提取方法 | 写入 style_profile |
|------|---------|-------------------|
| 摘要字数 | 提取范文摘要，统计 word count | `abstract_word_count: {min, max, avg}` |
| 章节标题风格 | 检查是否使用编号（1./I./无编号） | `section_heading_style: numbered/unnumbered/mixed` |
| 段落长度 | 统计每段句子数分布 | `paragraph_length: {min, max, avg_sentences}` |

### 2. 章节结构

| 指标 | 提取方法 | 写入 style_profile |
|------|---------|-------------------|
| 典型章节顺序 | 提取所有范文的章节名，找最常见顺序 | `section_order: [Introduction, Method, ...]` |
| 章节数 | 统计每篇范文的一级章节数 | `typical_section_count: {min, max, avg}` |
| 子节密度 | 统计每篇二级子节数 | `subsections_per_paper` |

### 3. 引用模式

| 指标 | 提取方法 | 写入 style_profile |
|------|---------|-------------------|
| 参考文献总数 | 统计参考文献节条目数 | `total_references_range: {min, max, avg}` |
| 引用风格 | 检查正文引用格式 [1] / (Author, Year) | `reference_format: numbered/author-year` |
| 各章引用密度 | 统计每章引用标记数 / 该章总词数 | `citation_density_per_section` |

### 4. 语言风格

| 指标 | 提取方法 | 写入 style_profile |
|------|---------|-------------------|
| 平均句长 | 分词 → 计句 → 平均 | `avg_sentence_length` |
| 被动语态比例 | 正则匹配被动模式 → 除以总句数 | `passive_voice_ratio` |
| 模糊限定频率 | 统计 hedging 词汇（may/suggest/indicate...） | `hedging_per_1000_words` |
| 常用过渡短语 | 提取段首/段尾的过渡词，按频率排序 | `transition_phrases: [top 10]` |

## 风格画像如何指导 Step 7 写作

`style_profile.md` 的每一项都直接映射到 Step 7 的写作规则：

| style_profile 指标 | 对应的 Step 7 规则 | 示例 |
|-------------------|-------------------|------|
| `abstract_word_count` | 7.6.1 摘要子类型与长度约束 | "控制在 180-250 词" |
| `section_order` | 7.4 论文类型、目标体裁与语言识别 | "该期刊的 Methods 在 Experiments 之前" |
| `reference_format` | 7.2/7.4 引用格式与目标体裁规则 | "IEEE 编号引用 [1]" |
| `avg_sentence_length` | 7.7.1 轻量可读性整理 | "句长保持在 22 词左右" |
| `passive_voice_ratio` | 7.2/7.4 语言规则 | "多用主动态——范文被动仅 15%" |
| `total_references_range` | 7.9 实时引文支撑 | "控制在 35-45 条参考文献" |
| `paragraph_length` | 7.7.1 轻量可读性整理 | "每段 3-6 句，不要全部 4 句" |
| `transition_phrases` | 7.8 章节级写作提示 | "该期刊常用 'In contrast,' / 'Furthermore,'" |

## 限制与边界

1. **仅分析表面特征** — 脚本提取的是可量化的格式化/结构/语言特征，不涉及"论证质量"、"创新性"等深层判断
2. **LaTeX vs Word** — 分析结果偏向 LaTeX 论文（更容易提取结构化信息），Word 论文的结构化程度低
3. **样本偏差** — Flash 模式 3 篇范文可能不代表期刊所有论文的风格
4. **学科差异** — 同一期刊不同子领域的论文风格可能不同，建议选取与你主题最接近的范文
5. **不替代期刊官方指南** — 风格画像是从范文推断的，期刊的 Author Guidelines 才是权威来源
