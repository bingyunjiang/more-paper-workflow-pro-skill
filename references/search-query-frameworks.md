# 检索查询框架参考

> 供 Step 3 执行时加载。从 paper-search-pro `query_planner.md` 和 nature-academic-search `search-strategy.md`
> 提炼，适配为工科场景。

## 1. 查询构建流程

```
用户研究方向
  → ① 提取核心概念（2-4 个）
  → ② 识别子领域（决定 L2 路由：CS 交叉 vs 传统工科）
  → ③ 为每个概念列出同义词/缩写/相关术语（≥2 个）
  → ④ 组装布尔查询：(concept1 OR synonym) AND (concept2 OR synonym)
  → ⑤ 添加排除词（NOT 噪音方向）
  → ⑥ 反模式检查
  → ⑦ 按 L1/L2/L3 翻译为各源语法
```

## 2. 框架选择

| 框架 | 适用场景 | 概念块结构 |
|------|---------|-----------|
| **Concept Block** | 工科默认，探索性检索 | 2-4 个核心概念块，每个含 2-5 个同义词 |
| **PICO** | 有明确干预/对比的工科问题 | Population + Intervention + Comparator + Outcome |
| **PEO** | 观测性/现象研究 | Population + Exposure + Outcome |
| **Methods-focused** | 方法学论文 | Method + Application + Validation |

### 2.1 Concept Block（工科默认）

**步骤：**
1. 从研究主题中提取 2-4 个核心概念
2. 为每个概念列举 2-5 个同义词/缩写/相关术语
3. 块内用 OR 连接，块间用 AND 连接
4. 可选项：添加 NOT 排除块（噪音方向）

**示例 — "充电桩冷板液冷散热拓扑优化"：**
```
C1 — 冷却对象: ("cold plate" OR "liquid cooling" OR "microchannel" OR "minichannel")
C2 — 方法: ("topology optimization" OR "shape optimization" OR "generative design")
C3 — 验证: ("experimental" OR "test rig" OR "measurement" OR "prototype")
排除: NOT ("PCM" OR "phase change" OR "spray cooling")

组合: C1 AND C2 AND C3 NOT 排除
```

### 2.2 PICO（工科干预/对比类）

**适用场景：** "方法 A 比方法 B 在场景 X 中效果更好吗？"

| 块 | 含义 | 工科示例 |
|----|------|---------|
| P — Population | 研究对象 | "DC fast charging pile" OR "350kW charger" |
| I — Intervention | 采用的方法 | "cold plate liquid cooling" OR "microchannel heat sink" |
| C — Comparator | 对比方案 | "air cooling" OR " immersion cooling" |
| O — Outcome | 评价指标 | "thermal resistance" OR "junction temperature" OR "pressure drop" |

### 2.3 Methods-focused（方法学论文）

**适用场景：** "有什么方法可以解决 X 问题？"

| 块 | 含义 | 示例 |
|----|------|------|
| Method | 方法名称+变体 | ("topology optimization" OR "SIMP method" OR "level-set method") |
| Application | 应用场景 | ("heat sink" OR "cold plate" OR "electronics cooling") |
| Validation | 验证手段 | ("CFD" OR "numerical simulation" OR "experimental") |

## 3. 概念块构建规则

### 3.1 同义词展开

每个概念块至少包含 **2 个**同义词，推荐 **3-5 个**：

| 展开类型 | 示例 |
|---------|------|
| 全称/缩写 | "computational fluid dynamics" ↔ "CFD" |
| 英式/美式 | "modelling" ↔ "modeling" |
| 上位/下位词 | "liquid cooling" → "water cooling", "oil cooling", "refrigerant" |
| 相关术语 | "topology optimization" → "shape optimization", "generative design" |
| 中英对照 | "冷板" → "cold plate", "liquid cold plate", "LCP" |

### 3.2 排除词（NOT）

用于排除明确不相关的研究方向：

```
✅ 好的排除：
  NOT "PCM" — 排除相变材料方向（不在研究范围内）
  NOT "battery" — 只取充电桩冷板，不要电池热管理

❌ 差的排除：
  NOT "simulation" — 会误杀含"实验+仿真"的论文
  NOT "China" — 地域歧视，无学术意义
```

### 3.3 AND 块数限制

| AND 块数 | 预期结果 | 建议 |
|:--------:|---------|------|
| 2 | 100-500 条 | ✅ 推荐 |
| 3 | 20-200 条 | ✅ 常见 |
| 4 | 5-50 条 | ⚠️ 边界，注意观察召回量 |
| 5+ | 0-10 条 | ❌ 禁止，召回率断崖下跌 |

**若需要 5+ 个概念：** 拆分为 2 个独立查询分别检索，后续合并去重。

## 4. 反模式清单 ← paper-search-pro

检索方案生成时必须逐项检查：

| # | 反模式 | 说明 |
|---|--------|------|
| 1 | `language=english` 过滤 | ❌ 过严，丢弃中日韩研究（有英文摘要即可） |
| 2 | `AND "human"` | ❌ 一半相关论文不含此词；依赖主题聚类而非关键词 |
| 3 | AND 块数 > 4 | ❌ 召回率断崖下跌；拆分多查询 |
| 4 | 单概念无双同义词 | ⚠️ 至少 2 个同义词/块，否则遗漏大量变体表述 |
| 5 | 用全文 `search=` 代替 `title.search=` | ⚠️ 全文搜索噪音大，优先标题搜索，零结果时再 fallback |
| 6 | 排除词用方法学术语 | ⚠️ 如 `NOT "simulation"` 会误杀含实验+仿真的论文 |
| 7 | 用缩写不作全称展开 | ⚠️ "CFD" 应同时匹配 "computational fluid dynamics" |

## 5. 多策略组合 ← paper-search-pro

对每个子课题，L1 OpenAlex 应同时跑 **3 条策略线**，增加结果多样性：

| 策略线 | 排序方式 | 产出 |
|--------|---------|------|
| **By relevance** | `sort=relevance_score:desc` | 最佳主题匹配 |
| **By citations** | `sort=cited_by_count:desc` | 高引经典 + 奠基工作 |
| **By recency** | `sort=publication_date:desc` | 最新发表 |

同一篇论文出现在 ≥2 条策略线中 → 提升评分的「主题匹配度」维度。

### 补充策略（子领域可选）

| 策略 | 用途 | OpenAlex 参数 |
|------|------|--------------|
| **Seminal cutoff** | 找经典文献 | `filter=publication_year:<2021` + `sort=cited_by_count:desc` |
| **Review type** | 找已有综述 | `filter=type:review` |
| **CN author filter** | 找国内团队 | `filter=authorships.institutions.country_code:CN` |

## 6. 各 API 布尔语法对照

统一布尔表达式需要按各 API 翻译：

| 语义 | OpenAlex | Semantic Scholar | Crossref | Wanfang (PQ) 🆕 |
|------|----------|-----------------|----------|-----------------|
| AND | `AND`（`search=` 参数） | 空格（隐式 AND） | `AND`（`query=` 参数） | `AND`（PQ 语法） |
| OR | `OR` | `+` 强制包含 | `OR` | `OR`（同义词括号内） |
| NOT | 不原生支持，用过滤器替代 | `-` 排除 | 不原生支持 | `NOT 标题:term` |
| 精确短语 | `"exact phrase"` | `"exact phrase"` | `"exact phrase"` | `"exact phrase"` |
| 标题限定 | `filter=title.search:...` | `title:` 字段 | `query.title=...` | `标题:term` |

### 翻译示例

**统一布尔表达式：**
```
(cold plate OR liquid cooling OR microchannel) AND (topology optimization OR generative design) NOT (PCM OR phase change)
```

**→ OpenAlex:**
```
search=cold plate OR liquid cooling OR microchannel AND topology optimization OR generative design
filter=title.search:cold plate|liquid cooling|microchannel
```

**→ Semantic Scholar:**
```
+cold plate +"topology optimization" -PCM -"phase change"
```
（S2 用 `+` 表示强制包含，`-` 表示排除，空格为隐式 AND）

**→ Crossref:**
```
query=(cold plate OR liquid cooling) AND (topology optimization OR generative design)
```

**→ Wanfang (PQ):**
```
标题:("cold plate" OR "liquid cooling") AND 标题:("topology optimization" OR "generative design") NOT 标题:"PCM"
```

## 7. 年份启发式

| 用户表述 | 年份范围 |
|---------|---------|
| "最新"/"近期" | `current_year - 5` 至今 |
| "近十年" | `current_year - 10` 至今 |
| "经典"/"奠基" | 不限年份，按引用量排序 |
| "综述" | `current_year - 3` 至今（找最新综述） |
| 未指定 | `current_year - 10` 至今（工科默认） |

## 8. 来源选择

| 来源 | 角色 | 适用条件 |
|------|------|---------|
| **OpenAlex** | L1 搜索 | 所有工科子领域，默认首选 |
| **Semantic Scholar** | L2 搜索+富集 | CS 交叉子领域→并行 L1；传统工科→L1 不足时回退；始终取 `influentialCitationCount` |
| **PubMed** | L3 搜索 | 仅医工交叉（生物医学工程、康复工程等） |
| **Wanfang Data** | L3 自动 🆕 | 中文文献检索（OpenPeriodicalChi / OpenThesis / OpenConference 三集合），需配置 WFDATA_APP_KEY + WFDATA_APP_CODE |
