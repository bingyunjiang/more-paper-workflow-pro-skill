# RCS 启发的主题匹配度评鉴指南

> 本文借鉴 paper-search-pro 的 RCS (Relevance to Core Search) 评鉴体系的定性锚定概念，
> 为 Step 4 的「主题匹配度」维度提供更精确的判断参照。本文**不引入独立的 RCS 评分** —
> 主题匹配度仍为 0-5 分制，属于现有五维度评分体系的一部分。

## 1. 匹配度等级锚定

### 0-1 分：无关 (Off-topic)

论文与查询主题无实质关联。关键词可能表面重叠，但内容是另一个领域。

**示例（查询："冷板液冷拓扑优化"）：**
- "Phase change material for building thermal management" → **0** (PCM 是明确排除的方向)
- "Topology optimization of bridge structures" → **1** (方法相同，但应用场景完全不同)

**判断标准：**
- 0 分 = 完全无关，不应出现在结果中
- 1 分 = 关键词重叠但实质不相关

### 2-3 分：弱相关 (Tangentially Related)

论文触及查询主题但仅作为背景、附带提及，或在迥异的上下文中讨论。

**示例（查询："冷板液冷拓扑优化"）：**
- "A review of electronics cooling methods" 提到冷板作为 10 种方法之一 → **2**
- "Microchannel heat sink optimization for CPU cooling" (对象不同，同为液冷) → **3**

**判断标准：**
- 2 分 = 主题被提及但不核心
- 3 分 = 相关领域但不同的子方向

### 4 分：相关但非核心 (Related but Not Core)

论文实质性地涉及查询的某些维度，但未完全击中核心问题。

**示例（查询："冷板液冷拓扑优化"）：**
- "Experimental study of cold plate with serpentine channels" (有冷板但无拓扑优化) → **4**
- "Topology optimization of heat sinks: a review" (有拓扑优化但非冷板) → **4**

**判断标准：**
- 覆盖 2-3 个查询维度中的 1 个
- 方法/对象/目标有部分对齐
- 设计老旧或方法论较弱，但仍值得参考

### 5 分：高度相关 / 奠基性 (Core / Foundational)

论文直接命中查询核心，具备适当的方法论和实验验证。这是用户极可能引用的核心文献。

**示例（查询："冷板液冷拓扑优化"）：**
- "Topology optimization of liquid-cooled cold plates for EV charging: experimental validation" → **5**
- Dede (2009) "Multiphysics topology optimization of cold plates" (奠基性工作，高引) → **5**

**判断标准：**
- 直接命中查询主题
- 方法学扎实（有实验验证 > 纯仿真）
- 高引用量或近期高影响力论文

---

## 2. 特殊标注旗标

| 旗标 | 含义 | 对主题匹配度的影响 |
|------|------|-------------------|
| `no_abstract_uncertain` | 无摘要或摘要为空，仅凭标题判断 | 降低 0-1 分，最高不超过 4 分 |
| `off_topic_despite_keywords` | 标题/关键词匹配但摘要显示内容无关 | 直接设为 0-1 分 |
| `abstract_unavailable` | 摘要字段为 "N/A" / "[paywalled]" / 极短 (<20 字符) | 同 no_abstract_uncertain |
| `recent_unindexed` | 新预印本 (arXiv T-0~T-4)，暂无引用和收录信息 | 不因缺少引用而降分；纯按标题+摘要判断 |
| `parse_failed_uncertain` | 论文数据格式异常（标题缺失/摘要乱码） | 设为 0 分，标记待人工审核 |

---

## 3. 评鉴纪律

### 避免分数膨胀
- 默认起点为 **3 分**（弱相关），确凿匹配才能给 4-5 分
- 高引用 ≠ 高相关 —— 引用量属于「影响力」维度，不应影响「主题匹配度」
- 顶刊 ≠ 高相关 —— 来源质量属于「来源质量」维度，不应影响「主题匹配度」
- 一篇论文的作者知名度与主题匹配度无关

### 避免分数贬低
- 不要因为论文新（引用少）而压低匹配度 —— 用 `recent_unindexed` 旗标保护
- 不要因为非英文论文而压低匹配度 —— OpenAlex 包含中日韩论文，按内容判断
- 不要因为预印本 / arXiv 而压低匹配度 —— 用 `recent_unindexed` 旗标保护

### 不确定时
- 在两个相邻分数间犹豫 → **向下取整**（4 vs 5 → 4）
- 不确定是否需要打旗标 → **打旗标**（agent 受益于不确定性信号）
- 无摘要但标题强相关 → 最高 4 分 + `no_abstract_uncertain` 旗标

---

## 4. 与五维度评分体系的整合

本文指南**仅影响「主题匹配度」维度（权重 35%）**。其余四个维度的评分逻辑保持不变：

| 维度 | 权重 | 本文影响 |
|------|:----:|:--------:|
| 主题匹配度 | 35% | ✅ 本文提供锚定参考 |
| 方法学严谨性 | 20% | 不受影响 |
| 来源质量 | 15% | 不受影响 |
| 时效性 | 15% | 受 `recent_unindexed` 旗标间接保护 |
| 影响力 | 15% | 不受影响（但 `recent_unindexed` 旗标提醒不要因缺少引用而降分） |

---

## 5. 使用方式

Step 4 agent 在评分时：
1. 对每篇论文按本文的 4 级锚定描述确定主题匹配度 0-5 分
2. 检查是否需要打特殊旗标，将旗标写入结果表格的 `Flag` 列
3. 在评分理由中引用本文的具体等级（如 "rcs-rubric L4：直接命中冷板液冷拓扑优化，有实验验证"）
4. 确保每个 Tier 的分数分布合理：T1(≥20) 通常不超总篇数的 20%，T2(15-19) 不超 30%
