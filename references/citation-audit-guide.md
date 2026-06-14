# 引用审计方法论

> 面向 `citation_audit.py` 和 Step 7.15 的参考文档。定义三级可信度判定标准、claim-摘要匹配规则、常见误引模式。

## 审计流程

```
稿件 → 提取所有引用标记 [1][2]...[N] → 逐条：
  ① 从参考文献列表或检索文献表拿到被引论文的 DOI/标题
  ② 通过 Crossref / Semantic Scholar API 获取被引论文摘要
  ③ 定位稿件中引用该论文的具体声明（claim）
  ④ 判断：摘要内容是否支撑这个 claim？
  ⑤ 输出审计报告，标注每条引用的可信度
```

## 三级可信度判定标准

### ✅ 支撑 — 引用恰当

**判定条件（满足 ≥2 条）：**
- claim 中的关键术语在摘要中出现 ≥60%
- 摘要明确包含与 claim 一致的研究方法（method/experiment/simulation/survey）
- 摘要中的结论方向与 claim 一致
- claim 声明的是该论文的核心贡献（标题/摘要直接描述）

**示例：**
> **Claim:** "冷板流道拓扑优化可降低泵功消耗 15%（Zhang, 2023）"
> **摘要:** "...topology optimization of cold plate channels reduced pump power by 15% compared to parametric designs..."
> → ✅ 支撑：摘要直接确认了具体数据和结论

---

### 🟡 弱支撑 — 建议核对全文

**判定条件（满足任 1 条）：**
- claim 的关键术语命中率在 20%-60% 之间
- 摘要主题相关，但未明确出现 claim 中的具体结论/数据
- 摘要讨论的方法与 claim 一致，但未提及时效/场景/条件限定
- claim 依赖论文的某张图/某张表的数据，但摘要未涉及

**示例：**
> **Claim:** "与 Li (2021) 的 CFD 仿真结果一致，高流量下温均性出现拐点"
> **摘要:** "...CFD simulation of cold plate thermal performance under various flow rates... temperature distribution analyzed..."
> → 🟡 弱支撑：摘要提及 CFD 和温度分布，但未明确提到"温均性拐点"——可能在全文中讨论，需核对

---

### ❌ 不支撑 — 可能引用不当

**判定条件（满足任 1 条）：**
- claim 关键术语命中率 <20%
- 摘要讨论的是完全不同的方法/场景/结论
- 摘要的研究对象与 claim 不一致（如 claim 说"电池"，摘要说"数据中心"）
- claim 引用了具体数据，但该数据在摘要中反向矛盾

**示例：**
> **Claim:** "该冷板方案将电池温度控制在 42°C 以下（Wang, 2022）"
> **摘要:** "...review of battery thermal management strategies... various cooling methods compared qualitatively..."
> → ❌ 不支撑：这是一篇综述，不包含具体实验数据，无法支撑"42°C"这样的定量声明

---

### ⚠️ 无法判断 — 缺摘要

**条件：**
- API 无法获取摘要（Crossref/Semantic Scholar 均无）
- 被引论文为中文期刊且无英文摘要
- 被引论文为会议论文且摘要不可获取

**处理：** 通过 Zotero MCP 获取全文后重新审计，或手动核实。

## 常见误引模式

### 模式 1：标题-摘要张冠李戴

LLM 看到标题包含关键词就引用，但摘要内容其实是不同主题。

**信号：** 术语命中率 20%-40%，但摘要结论方向与 claim 不同。

### 模式 2：综述当实证

LLM 把综述论文当成实证研究引用，声称"该方法将性能提升 15%"——综述不报告一手数据。

**信号：** 摘要中出现 "review", "survey", "overview", "summarize"。

### 模式 3：贡献过度归因

LLM 把论文 A 的方法错误归因给论文 B（通过标题混淆）。

**信号：** claim 中的方法/结论与摘要中的方法/结论有交叉但不一致。

### 模式 4：数据编造

LLM 编造了具体数字，但被引论文中根本没有这个数据。

**信号：** claim 包含具体数字（百分数、温度、压力），但摘要中无任何量化结果。

## claim-摘要匹配关键词

匹配时应重点关注以下几类词：

| 类别 | 英文 | 中文 |
|------|------|------|
| **方法词** | method, approach, algorithm, model, framework, simulation, experiment, CFD, FEM | 方法、算法、模型、仿真、实验 |
| **结果词** | result, finding, show, demonstrate, indicate, reduce, increase, improve, achieve | 结果表明、证明了、降低了、提高了、达到 |
| **数据词** | %, percent, °C, kPa, W/mK, Reynolds, sample, n= | 百分比、温度、压力、样本量 |
| **对象词** | 领域特定术语（如 cold plate, battery, topology optimization）| 领域特定术语 |

## 批量审计策略

- **全量审计**：适用于引用 ≤30 篇的稿件，逐篇获取摘要
- **分层审计**：先审计 Tier 1（≥20 分）的引用，再覆盖 Tier 2
- **抽样审计**：适用于长篇综述（>60 篇引用），随机抽检 20% 覆盖所有章节
- **增量审计**：仅审计 Step 7.9 中标记为"扩展搜索"的引用（非已下载文献）
