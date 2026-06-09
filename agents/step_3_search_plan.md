# Step 3: 生成文献检索方案

> 基于大纲和关键词，生成结构化检索方案。L1→L2→L3 分层路由架构 + 概念块布尔模型 + 反模式检查。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `大纲关键词.md` — Step 2 产出（章节大纲 + 关键词清单 + 章节证据需求表）
- [ ] `研究主题.md` — Step 1 产出（tier/search_tier + 聚焦主题 + 预审结论）
- [ ] `references/search-query-frameworks.md` — 检索查询框架参考（概念块布尔模型 + PICO + 反模式清单）
- [ ] `.skill-state/term_aliases.md` — 🆕 术语标准化映射（确保查询用词与大纲一致）
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则
- [ ] `.skill-state/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 将论文大纲拆解为子课题检索方案
- 构建概念块布尔查询（Concept Block / PICO / Methods-focused）
- 反模式检查（8 项）
- 分配 L1→L2→L3 分层路由
- 生成多策略检索计划（relevance / cited / recent）

---

## 3. 不适用任务 (Non-applicable Tasks)

以下任务不属于本 Step 范围：

- 大纲生成 → 路由到 `agents/step_2_outline.md`
- 执行检索 → 路由到 `agents/step_4_search_score.md`
- 文献评分 → 路由到 `agents/step_4_search_score.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 章节大纲 | Step 2 `大纲关键词.md` | .md | ✅ |
| 关键词清单 | Step 2 `大纲关键词.md` | .md | ✅ |
| 章节证据需求表 | Step 2 `大纲关键词.md` | .md | ✅ |
| 术语映射表 | Step 2 → .skill-state/term_aliases.md | .md | ✅ |

**Step 2 字段读取规则：**

| 字段 | 用途 |
|------|------|
| 章节大纲 | 决定检索子课题编号、章节归属和检索顺序 |
| 关键词清单 | 提供核心词、同义词/缩写、上位词、下位词、方法词、场景词、指标词、排除词 |
| 章节证据需求表 | 决定每个子课题需要找综述、方法、实验、数据、标准、案例中的哪类证据 |
| 检索语言 | 决定中文/英文/中英文混合路由 |
| search_tier 或 tier | 决定 limit、策略数量和补充源 |

**Tier 读取优先级：**

1. 优先读取 `研究主题.md` 顶层 `tier`
2. 若无顶层字段，读取 `研究主题.md` 的 `search_tier.tier`
3. 若仍缺失，读取 `大纲关键词.md` 的 `search_tier`
4. 全部缺失时默认 `standard`

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 检索方案.md | .md | v3.1：含 search_tasks + 分层路由 + 概念块拆解 + 反模式检查 |
| 检索方案.pdf | .pdf | 自动由 md_to_pdf.py 生成 |

---

## 6. 执行流程 (Execution Flow)

### Step 3 执行流程

```
Step 2 产出（大纲关键词.md）
  → ① 领域识别：判断工科子领域（机械/电气/土木/材料/控制/信号/AI...）
  → ② 读取章节证据需求表：按章节ID + 证据类型生成 search_tasks
  → ③ 框架选择：Concept Block（工科默认）/ PICO / Methods-focused
  → ④ 概念块拆解：每个概念块 ≥2 同义词 + 可选排除词
  → ⑤ 组装布尔查询：(syn1 OR syn2) AND (syn3 OR syn4) NOT (excl)
  → ⑥ 反模式检查（8 项）
  → ⑦ 读 Step 2 产出中的「检索语言」字段 → 中文→L1 CNKI→L2 Wanfang；英文→L1 OpenAlex→L2 Crossref→L2 Semantic Scholar→L3 PubMed
  → 产出：检索方案.md → 检索方案.pdf
```

### 3a-0. Search Tasks 结构化模板

`检索方案.md` 必须包含机器可读的 `search_tasks`，供 Step 4 执行：

```yaml
search_language: 中文|英文|中英文混合
tier: quick|standard|deep
search_tasks:
  - id: S1
    chapter_id: ch1
    chapter_title: "绪论"
    evidence_type: "review|method|experiment|data|standard|case"
    question_to_answer: ""
    framework: "concept_block|pico|methods_focused"
    query_blocks:
      - name: "研究对象"
        terms: ["term1", "term2"]
      - name: "方法"
        terms: ["term3", "term4"]
    exclusion_terms: []
    route:
      language: "zh|en|mixed"
      l1: ["cnki|openalex"]
      l2: ["wanfang|crossref|semantic_scholar|arxiv"]
      l3: ["pubmed"]
    recommended_commands: []
    anti_patterns_checked: true
```

**生成规则：**

- 每个 `search_task` 必须绑定 `chapter_id` 和 `evidence_type`
- 一个章节可生成多个任务，例如 `ch2-method`、`ch2-experiment`
- `question_to_answer` 必须来自章节证据需求表，不得凭空新增
- `query_blocks` 优先使用关键词清单中的核心词、同义词/缩写、方法词、场景词、指标词
- `exclusion_terms` 优先来自关键词清单的排除词

### 3a. 查询构建框架

#### 框架选择

| 框架 | 适用场景 | 概念块结构 |
|------|---------|-----------|
| **Concept Block**（工科默认） | 探索性检索、大多数工科问题 | 2-4 个核心概念块，每个含 2-5 个同义词 |
| **PICO** | 有明确干预/对比的工科问题 | Population + Intervention + Comparator + Outcome |
| **Methods-focused** | 方法学论文 | Method + Application + Validation |

#### 概念块模型

```
✅ 正确 — 概念块模型：
  C1 — 冷却对象: ("cold plate" OR "liquid cooling" OR "microchannel")
  C2 — 方法: ("topology optimization" OR "shape optimization" OR "generative design")
  C3 — 验证: ("experimental" OR "test rig" OR "measurement")
  排除: NOT ("PCM" OR "phase change" OR "spray cooling")
  组合: C1 AND C2 AND C3 NOT 排除
```

#### 🆕 术语一致性规则

- 概念块中的**核心词**必须与 `.skill-state/term_aliases.md` 中的 Main Term 一致
- 同义词展开时，将 Aliases 列的内容作为 OR 候选项
- 若发现大纲关键词使用了与众不同的术语变体，在此处统一为 Main Term

#### AND 块数限制

| AND 块数 | 预期结果 | 建议 |
|:--------:|---------|------|
| 2 | 100-500 条 | ✅ 推荐 |
| 3 | 20-200 条 | ✅ 常见 |
| 4 | 5-50 条 | ⚠️ 边界 |
| 5+ | 0-10 条 | ❌ 禁止，拆分为 2 个独立查询 |

### 3b. 反模式检查清单

| # | 反模式 | 说明 |
|---|--------|------|
| 1 | `language=english` 过滤 | ❌ 过严，丢弃中日韩研究 |
| 2 | 🔴 CNKI/万方检索不带 `--language zh` | ❌ 中文库中混有英文论文，必须加 `--language zh` |
| 3 | 无意义限定词 | ❌ `AND "human"` 等 |
| 4 | AND 块数 > 4 | ❌ 召回率断崖下跌 |
| 5 | 单概念无双同义词 | ⚠️ 每个概念块至少 2 个同义词 |
| 6 | 全文搜索优先 | ⚠️ 优先 `title.search` |
| 7 | 排除词用方法学术语 | ⚠️ 如 `NOT "simulation"` 会误杀 |

### 3c. 工科检索分层架构

路由由 Step 2 产出中的 **「检索语言」** 字段决定。如果直接进入 Step 3（无 Step 2 产出），则从关键词/查询词中自动检测：含中文字符 → 中文路由；否则 → 英文路由。

```
检索语言: 中文
  → CNKI + Wanfang     ← 双源并行检索（--parallel），结果在 Step 4b 以 DOI 去重合并。
                         同一论文出现在两个源 → Step 4c 评分「主题匹配度」+1。
                         两库高度重叠，并行再合并是最高效策略。
  → 🔴 必须加 --language zh   ← CNKI 和万方数据库中包含中文学术期刊发表的英文论文。
                                  这些英文论文难以通过 CDP 下载管线获取，应在检索阶段排除。
                                  --language zh 会：(1) CNKI 端设置 isinEn=0 停用中英文扩展；
                                  (2) 万方端设置 lang=chi URL 参数；(3) 结果级标题语言检测安全网。

检索语言: 英文
  → L1  OpenAlex         ← 全学科覆盖最广（2.5 亿+），默认首选
     L2  Crossref         ← DOI/出版社元数据补充（必选源，不可跳过）
     L2  Semantic Scholar ← CS 交叉子领域并行，传统工科回退；用于影响力/引文富集
     L2  arXiv (条件触发)  ← 🆕 仅 CS/AI 跨域信号时启用（T-0~T-4 新鲜度窗口）
     L3  PubMed           ← 仅医工交叉启用

> **🔴 Deep tier 下 Crossref 强制规则：** 当检索深度为 deep 时，Crossref 必须作为英文文献补充检索源执行，
> 不得仅用 OpenAlex 完成英文检索。Standard tier 下，若 Semantic Scholar 返回 429 或中文源不可用，
> Crossref 同样必须启用作为补充源。

检索语言: 中英文混合 → 按子课题拆分，分别走中文/英文路由
```

> **为什么中文不走 OpenAlex？** OpenAlex 的中文文献覆盖率仅 24%，且 92% 的中文论文被错标为英文。CNKI + 万方是中文学术文献的可靠覆盖组合。

### 3c.1 🆕 CNKI 触发条件

| 信号 | 触发 CNKI? | 说明 |
|------|:---------:|------|
| 查询含中文字符 | ✅ YES | 中文查询以 CNKI 为 L1（主检索），万方为 L2（补充） |
| 用户明确要求"知网"/"CNKI"/"硕博论文" | ✅ YES | 显式要求 |
| 仅英文查询且无中文语境 | ⚠️ 推荐 | Agent 判断是否遗漏国内团队英文发表 |
| 用户明确要求"仅英文" | ❌ NO | 尊重用户意愿 |

> **CNKI 访问方式**：通过 CDP Chrome 浏览器实现。校园网下浏览器自动 IP 认证，无需额外操作；
> 校外 → CARSI/RVPN 登录（需在 CDP Chrome 中完成一次机构登录，登录态持久化）。
> CNKI 没有可用的纯 HTTP 搜索 API，所有检索均通过 CDP 浏览器完成。
> **CNKI 优势**：支持硕博论文检索、支持多排序策略（相关度/时间/被引/下载）、支持调用 Export API 获取 GB/T 7714 引用格式。

### 3c.2 Wanfang 触发条件

| 信号 | 触发 Wanfang? | 说明 |
|------|:------------:|------|
| 查询含中文字符 | ✅ YES | 中文查询以 Wanfang 为 L2（补充检索），补全 CNKI 可能遗漏的医药/自然科学文献 |
| 用户明确要求"中文文献"/"万方"/"Wanfang" | ✅ YES | 显式要求 |
| 仅英文查询且无中文语境 | ⚠️ 推荐 | Agent 判断是否可能遗漏国内团队工作 |
| 用户明确要求"仅英文" | ❌ NO | 尊重用户意愿 |

> **Wanfang 访问方式**：自动检测。校内IP直连（零配置），校外CARSI SSO需在CDP Chrome中完成一次机构登录。
> **Wanfang 限制**：万方 Web 搜索仅支持默认排序，不支持多策略（relevance/cited/recent）切换。在 L2 阶段统一使用 `--source wanfang` 或通过 T2 级联调用。

**🆕 arXiv 触发条件：**

| 信号 | 触发 arXiv? | 说明 |
|------|:----------:|------|
| 查询含 "machine learning" / "deep learning" / "neural network" / "transformer" | ✅ YES | CS/AI 核心术语 |
| 查询含 "computer vision" / "NLP" / "reinforcement learning" / "large language model" | ✅ YES | CS 子领域 |
| 查询含 "AI" / "artificial intelligence" / "LLM" / "GPT" / "graph neural" | ✅ YES | AI 通用术语 |
| 用户明确要求"最新预印本" / "arXiv" / "preprint" | ✅ YES | 显式要求 |
| 传统工科（机械/电气/土木/材料/化工）且无上述信号 | ❌ NO | 默认跳过 |
| 医工交叉 | ❌ NO | PubMed 覆盖 |

**触发时**：在检索方案中写入 `arxiv_enabled: true` + arXiv 查询命令。**未触发时**：写入 `arxiv_enabled: false`。

### 3d. 多策略检索

每个子课题的 L1 OpenAlex 检索同时跑 3 条策略线：

| 策略线 | 排序方式 | 产出 |
|--------|---------|------|
| **By relevance** | `sort=relevance_score:desc` | 最佳主题匹配 |
| **By citations** | `sort=cited_by_count:desc` | 高引经典 |
| **By recency** | `sort=publication_date:desc` | 最新发表 |

> 同一篇论文出现在 ≥2 条策略线中 → 提升最终评分的「主题匹配度」维度。

### 3e. Tier-driven 检索参数配置 🆕

> 按“顶层 tier → search_tier.tier → 大纲 search_tier → standard 默认值”的顺序读取检索深度，自动配置检索参数。

| Tier | limit/策略 | strategies | 补充策略 | 适用场景 |
|------|:--------:|-----------|---------|---------|
| Quick | 30 | relevance only | 无 | 快速摸底、博三冲刺 |
| Standard（默认） | 50 | relevance + cited + recent | 无 | 一般文献检索、开题 |
| Deep | 100 | relevance + cited + recent | + seminal cutoff + review type | 综述写作、深度研究 |

**配置写入**：在检索方案顶层和每个 `search_task` 中标注 `tier: quick|standard|deep`，Step 4 根据 tier 选择 `--limit` 值。

### Pre-flight 检查

```bash
python3 scripts/search_by_topic.py --preflight
```

---

## 7. 质量门槛 (Quality Gates)

- [ ] 领域识别和框架选择正确
- [ ] `search_tasks` 已生成，且每个任务绑定章节ID、证据类型和检索问题
- [ ] 每个概念块 ≥ 2 个同义词
- [ ] AND 块数 ≤ 4
- [ ] 反模式检查 8 项全部通过（含 🔴 `--language zh` 检查）
- [ ] L1→L2→L3 分层路由分配合理
- [ ] 🆕 arXiv 触发条件已检测（arxiv_enabled: true/false）
- [ ] 🆕 Tier 检索参数已配置（顶层 tier + 每个 search_task 的 tier）
- [ ] 🆕 核心术语与 `.skill-state/term_aliases.md` 中 Main Term 一致
- [ ] 🆕 CNKI 触发条件已检测（cnki_enabled: true/false + 访问模式：IP/CDP）
- [ ] 🆕 Wanfang 触发条件已检测（wanfang_enabled: true/false + 凭证存在性）
- [ ] Pre-flight 检查已通过

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `检索方案.md` 已生成（含 search_tasks + 完整概念块拆解 + 分层路由 + 反模式检查）
- [ ] `检索方案.pdf` 已自动生成

### 术语一致性检查 🆕
- [ ] 检索方案中的核心词是否与 `.skill-state/term_aliases.md` 中的 Main Term 一致？
- [ ] 是否发现了新的术语变体？→ 追加到 Aliases 列

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 框架选择不当 → 追加到 `.skill-state/error_log.md`
  - 同义词展开遗漏 → 追加到 `.skill-state/error_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：执行多渠道检索（Step 4）
  > **下一步 → Step 4：** 按检索方案的 L1→L2→L3 分层路由执行多渠道检索，对结果进行 5 维度评分和 Tier 分级筛选。

---

## 9. 故障排除 (Troubleshooting)

- **Pre-flight 检查失败**：检查网络连接，确认各 API 端点可达
- **检索结果预期过少**：减少 AND 块数（4→3→2），放宽同义词范围
- **术语不一致**：回查 `.skill-state/term_aliases.md`，确保概念块核心词与 Main Term 对齐
- **search_tasks 与大纲脱节**：回查 Step 2 的章节证据需求表，确保每个任务都有章节ID和 evidence_type
