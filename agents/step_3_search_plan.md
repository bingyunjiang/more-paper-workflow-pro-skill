# Step 3: 生成文献检索方案

> 基于大纲和关键词，生成结构化检索方案。L1→L2→L3 分层路由架构 + 概念块布尔模型 + 反模式检查。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_2_outline.md` — 大纲关键词（章节结构 + 关键词清单）
- [ ] `agents/step_1_topic.md` — 🆕 Tier 元数据（检索深度：quick/standard/deep）
- [ ] `references/search-query-frameworks.md` — 检索查询框架参考（概念块布尔模型 + PICO + 反模式清单）
- [ ] `references/term_aliases.md` — 🆕 术语标准化映射（确保查询用词与大纲一致）
- [ ] `references/error_log.md` — 已知错误及修复规则
- [ ] `references/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 将论文大纲拆解为子课题检索方案
- 构建概念块布尔查询（Concept Block / PICO / Methods-focused）
- 反模式检查（7 项）
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
| 大纲关键词 | Step 2 | .md | ✅ |
| 术语映射表 | Step 2 → references/term_aliases.md | .md | ✅ |

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 检索方案.md | .md | v3.0：含分层路由 + 概念块拆解 + 反模式检查 |
| 检索方案.pdf | .pdf | 自动由 md_to_pdf.py 生成 |

---

## 6. 执行流程 (Execution Flow)

### Step 3 执行流程

```
Step 2 产出（大纲关键词.md）
  → ① 领域识别：判断工科子领域（机械/电气/土木/材料/控制/信号/AI...）
  → ② 框架选择：Concept Block（工科默认）/ PICO / Methods-focused
  → ③ 概念块拆解：每个概念块 ≥2 同义词 + 可选排除词
  → ④ 组装布尔查询：(syn1 OR syn2) AND (syn3 OR syn4) NOT (excl)
  → ⑤ 反模式检查（7 项）
  → ⑥ 分层路由分配：L1 OpenAlex → L2 Semantic Scholar → L3 PubMed/CNKI
  → 产出：检索方案.md → 检索方案.pdf
```

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

- 概念块中的**核心词**必须与 `references/term_aliases.md` 中的 Main Term 一致
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
| 2 | 无意义限定词 | ❌ `AND "human"` 等 |
| 3 | AND 块数 > 4 | ❌ 召回率断崖下跌 |
| 4 | 单概念无双同义词 | ⚠️ 每个概念块至少 2 个同义词 |
| 5 | 全文搜索优先 | ⚠️ 优先 `title.search` |
| 6 | 排除词用方法学术语 | ⚠️ 如 `NOT "simulation"` 会误杀 |

### 3c. 工科检索分层架构

```
L1  OpenAlex         ← 全学科覆盖最广（2.5 亿+），默认首选
L2  Semantic Scholar ← CS 交叉子领域并行，传统工科回退
L2  arXiv (条件触发)  ← 🆕 仅 CS/AI 跨域信号时启用（T-0~T-4 新鲜度窗口）
L3  PubMed           ← 仅医工交叉启用
L3  Wanfang Data     ← 🆕 中文文献自动检索（机构IP直连或CARSI SSO登录）
                   本文库尚不支持 CNKI（无开放 API）
```

### 3c.1 🆕 Wanfang 触发条件

| 信号 | 触发 Wanfang? | 说明 |
|------|:------------:|------|
| 查询含中文字符 | ✅ YES | 只要有中文关键词即推荐启用 |
| 用户明确要求"中文文献"/"万方"/"Wanfang" | ✅ YES | 显式要求 |
| 仅英文查询且无中文语境 | ⚠️ 推荐 | Agent 判断是否可能遗漏国内团队工作 |
| 用户明确要求"仅英文" | ❌ NO | 尊重用户意愿 |

> **Wanfang 访问方式**：自动检测。校内IP直连（零配置），校外CARSI SSO需在CDP Chrome中完成一次机构登录。
> **Wanfang 限制**：万方 Web 搜索仅支持默认排序，不支持多策略（relevance/cited/recent）切换。在 L3 阶段统一使用 `--source wanfang` 或通过 T3 回退调用。

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

> 从 Step 1e 的 `研究主题.md` YAML 元数据中读取 tier，自动配置检索深度。

| Tier | limit/策略 | strategies | 补充策略 | 适用场景 |
|------|:--------:|-----------|---------|---------|
| Quick | 30 | relevance only | 无 | 快速摸底、博三冲刺 |
| Standard（默认） | 50 | relevance + cited + recent | 无 | 一般文献检索、开题 |
| Deep | 100 | relevance + cited + recent | + seminal cutoff + review type | 综述写作、深度研究 |

**配置写入**：在检索方案的每个子课题中标注 `tier: quick|standard|deep`，Step 4 根据 tier 选择 `--limit` 值。

### Pre-flight 检查

```bash
python3 scripts/search_by_topic.py --preflight
```

---

## 7. 质量门槛 (Quality Gates)

- [ ] 领域识别和框架选择正确
- [ ] 每个概念块 ≥ 2 个同义词
- [ ] AND 块数 ≤ 4
- [ ] 反模式检查 7 项全部通过
- [ ] L1→L2→L3 分层路由分配合理
- [ ] 🆕 arXiv 触发条件已检测（arxiv_enabled: true/false）
- [ ] 🆕 Tier 检索参数已配置（tier: quick/standard/deep）
- [ ] 🆕 核心术语与 `references/term_aliases.md` 中 Main Term 一致
- [ ] 🆕 Wanfang 触发条件已检测（wanfang_enabled: true/false + 凭证存在性）
- [ ] Pre-flight 检查已通过

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `检索方案.md` 已生成（含完整概念块拆解 + 分层路由 + 反模式检查）
- [ ] `检索方案.pdf` 已自动生成

### 术语一致性检查 🆕
- [ ] 检索方案中的核心词是否与 `references/term_aliases.md` 中的 Main Term 一致？
- [ ] 是否发现了新的术语变体？→ 追加到 Aliases 列

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 框架选择不当 → 追加到 `references/error_log.md`
  - 同义词展开遗漏 → 追加到 `references/error_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：执行多渠道检索（Step 4）
  > **下一步 → Step 4：** 按检索方案的 L1→L2→L3 分层路由执行多渠道检索，对结果进行 5 维度评分和 Tier 分级筛选。

---

## 9. 故障排除 (Troubleshooting)

- **Pre-flight 检查失败**：检查网络连接，确认各 API 端点可达
- **检索结果预期过少**：减少 AND 块数（4→3→2），放宽同义词范围
- **术语不一致**：回查 `references/term_aliases.md`，确保概念块核心词与 Main Term 对齐
