# Step 4: 多渠道检索与相关性筛选

> 按 Step 3 方案的 L1→L2→L3 分层路由逐子课题检索，对结果进行 5 维度评分和 Tier 分级筛选。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_3_search_plan.md` — 检索方案（含 L1→L2→L3 路由和概念块布尔查询）
- [ ] `agents/step_1_topic.md` — 🆕 Tier 元数据（检索深度：quick/standard/deep）
- [ ] `references/search-query-frameworks.md` — 检索查询框架参考
- [ ] `references/rcs-rubric.md` — 🆕 主题匹配度评鉴启发指南
- [ ] `references/error_log.md` — 已知错误及修复规则
- [ ] `references/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 按检索方案的 L1→L2→L3 分层路由逐子课题执行文献检索
- 对检索结果进行引文验证（DOI 有效性 + 元数据完整性）
- 多源检索结果 DOI 去重合并
- 五维度相关性评分（主题匹配度/方法学严谨性/来源质量/时效性/影响力）
- Tier 分级筛选（T1/T2/T3/T4）
- 统一 .bib 导出（含评分标签和子课题归属）

---

## 3. 不适用任务 (Non-applicable Tasks)

以下任务不属于本 Step 范围：

- 检索方案设计 → 路由到 `agents/step_3_search_plan.md`
- PDF 下载 → 路由到 `agents/step_5_download.md`
- 文献综述矩阵 → 路由到 `agents/step_6_zotero.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 检索方案 | Step 3 | .md | ✅ |
| 检索执行参数 | 检索方案中的 L1/L2/L3 路由配置 | 文本 | ✅ |

---

## 5. 标准输出 (Standard Outputs)

> 所有产出仅含 **T1-T3 论文**（T4 已在 4d 剔除）。

| 输出 | 格式 | 说明 |
|------|------|------|
| 检索文献表 | .md | 最终版（原始+扩展），顶部含饱和度摘要，底部含 PRISMA-S 摘要 |
| 检索文献表 | .xlsx | 🆕 agent 用 openpyxl 生成，可直接筛选排序 |
| 检索文献表 PDF | .pdf | 自动由 md_to_pdf.py 生成 |
| 文献库 | .bib | 全量 T1-T3，含 Tier/Score/influential_citations/子课题归属 |
| 饱和度曲线快照 🆕 | .json | 文献覆盖率估算，含置信区间 |

---

## 6. 执行流程 (Execution Flow)

### 检索执行

按 Step 3 方案的 L1→L2→L3 分层路由逐子课题检索：

```bash
# L1 OpenAlex：每子课题跑 3 策略（relevance + cited + recent），每策略 50 条
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source openalex --strategy relevance --limit 50 --output s1_l1_rel.bib
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source openalex --strategy cited --limit 50 --output s1_l1_cited.bib
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source openalex --strategy recent --limit 50 --output s1_l1_recent.bib

# L2 Semantic Scholar：CS 交叉子领域并行，传统工科在 L1<30 时回退
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source semantic_scholar --limit 50 --output s1_l2.bib

# 传统用法（向后兼容，不使用概念块）：
python3 scripts/search_by_topic.py "cold plate liquid cooling optimization" \
  --t1 openalex --t2 semantic_scholar --limit 50 --output s1_results.bib
```

### Tier-driven 检索参数 🆕

> 从 Step 1e 的 `研究主题.md` YAML 元数据中读取 tier，自动调整检索参数。

| Tier | limit/策略 | strategies | 补充策略 |
|------|:--------:|-----------|---------|
| Quick | 30 | relevance only | 无 |
| Standard（默认） | 50 | relevance + cited + recent | 无 |
| Deep | 100 | relevance + cited + recent | + seminal cutoff + review type |

### L2 arXiv 条件触发 🆕

> 仅当 Step 3 检索方案标记了 `arxiv_enabled: true` 时执行。

```bash
# L2 arXiv：仅 CS/AI 跨域信号时触发（T-0~T-4 新鲜度窗口）
python3 scripts/arxiv_helper.py "query string" \
  --days 4 --limit 20 --output s1_l2_arxiv.json
```

### 4a: 引文验证

在评分之前先验证——剔除 DOI 无效、元数据残缺的条目，避免后续下载白费功夫。

```
检索结果 → 逐条验证：
  ① DOI 格式合法性（正则 + Crossref API 校验）
  ② 元数据完整性：title / authors / year / journal 是否在结果中存在
  ③ 标记问题条目：
     ⚠️ DOI 无效 → 跳过（无法下载）
     ⚠️ 缺作者/年份 → 尝试从 Crossref 补全
     ✅ 完整 → 进入评分
```

### 4b: DOI 去重

多源检索会产生重复（同一篇论文从 Semantic Scholar 和 Crossref 各返回一次）：

```
去重策略：
  - 主键：DOI（大小写 + 前缀统一后比对）
  - 无 DOI 时：title + first_author + year 组合键
  - 冲突时保留元数据最完整的条目
```

### 4c: 相关性评分（v3.0 五维度）

检索结果按以下维度打分（每项 0-5 分，满分 25）。评分时参考 `references/rcs-rubric.md` 中 4 级锚定描述和特殊旗标：

| 维度 | 权重 | 说明 |
|------|:----:|------|
| 主题匹配度 | **35%** | 标题+摘要与研究主题的相关程度；参考 rcs-rubric 锚定：无关(0-1)/弱相关(2-3)/相关非核心(4)/高度相关+奠基(5)；同一论文出现在 ≥2 条策略线中 → 该维度 +1 |
| 方法学严谨性 | **20%** | 采用的方法/实验设计是否可靠——有实验验证 > 纯仿真，有对照实验 > 无对照 |
| 来源质量 | **15%** | 期刊/会议等级（SCI 一区/CCF-A > 二区 > 三区/四区 > 无检索） |
| 时效性 | **15%** | 近 3 年 5 分，近 5 年 4 分，近 10 年 3 分，更早 2 分。recent_unindexed 旗标保护：新预印本不因缺引用而降分 |
| 影响力 | **15%** | 引用量 + Semantic Scholar influentialCitationCount。no_abstract_uncertain 旗标保护：无摘要论文最高 4 分 |

### 4d: 筛选标准（Tier 分级）

| 等级 | 分数范围 | 处理 |
|------|---------|------|
| ⭐ Tier 1 | ≥20 | 核心文献，必须下载 |
| 📘 Tier 2 | 15-19 | 重要文献，尽量下载 |
| 📄 Tier 3 | 10-14 | 参考文献，有选择下载 |
| ⬜ Tier 4 | <10 | **剔除 —— 不进入后续导出（.bib / .md / .xlsx 均不含 T4）** |


### 4e: 引文网络扩展（单轮 1-hop） 🆕

> **设计约束**：**单轮**——不做第二跳。**仅 T1 种子论文**——最多 10 篇。**新论文在此步内完成评分+分级闭环**，不跳回 4c/4d。

**触发条件**：T1 (≥20分) 论文数 > 0。

**执行**：对每篇 T1 论文调用一次 citation-network：

```bash
# 对每篇 T1 论文：
python3 scripts/search_by_topic.py --citation-network <DOI> \
  --refs-limit 30 --cited-by-limit 50 \
  --existing-dois existing_dois.txt \
  --output expanded_<seq>.json
```

**评分闭环**（在 4e 内部完成）：
1. 收集所有 `expanded_*.json` → 合并去重
2. 与现有文献库做 DOI 去重（排除已有）
3. **对新增论文执行 4c 五维度评分**（复用相同维度+rcs-rubric 启发）
4. **对新增论文执行 4d Tier 分级**（T1-T4 判定）
5. **T4 (<10分) 剔除**，T1-T3 追加到检索文献表，标注 `source: openalex_citation_network`
6. 记录到 `decision_log`：新增 X 篇（T1: a, T2: b, T3: c），种子 Y 篇

**防爆炸规则**：
- 最多 10 篇种子论文（T1 only）
- refs-limit 30 + cited-by-limit 50 = 每篇最多 80 条原始结果
- 经去重后通常新增 100-200 篇
- **不做第二跳**（单轮限定）

### 4f: 饱和度曲线估算 🆕

> 基于**全量 T1-T3 文献**（原始 + 扩展）计算最终覆盖率。仅参考，不强制停止。
> **条件门**：≥ 30 篇 → 执行；< 30 篇 → 跳过，标注 `insufficient_data`。

```bash
python3 scripts/discovery_curve.py \
  --results 检索文献表.md \
  --output saturation_snapshot.json
```

**解读输出**：

| coverage_estimate | CI 宽度 | Agent 判断 |
|:-----------------:|:-------:|-----------|
| ≥ 0.85 | < 0.15 | ✅ 覆盖良好 |
| ≥ 0.85 | > 0.15 | ⚠️ 信心不足 |
| 0.6–0.85 | — | ⚠️ 中等覆盖 |
| < 0.6 | — | ❌ 覆盖不足 |
| fit_failed | — | ⚠️ 无法拟合 |

### 4g: 生成检索报告 🆕

> **统一交付物**。在所有检索、评分、扩展、饱和度分析完成后执行。仅导出 **T1-T3 论文**（T4 已剔除）。

**产出清单**：

| 产出 | 格式 | 生成方式 |
|------|------|---------|
| 检索文献表 | .md | Agent 生成最终版，顶部嵌入饱和度摘要，底部嵌入 PRISMA-S 摘要 |
| 检索文献表 | .xlsx | Agent 用 openpyxl 生成，列：DOI/标题/年份/来源/评分/Tier/旗标/引用/influential_citations |
| 检索文献表 | .pdf | `python3 scripts/md_to_pdf.py 检索文献表.md` |
| 文献库 | .bib | `python3 scripts/search_by_topic.py --export-bib 检索文献表.md --output 文献库.bib`（仅含 T1-T3） |

**.md 顶部 — 饱和度摘要**：
```
## 检索概况
- 检索日期：YYYY-MM-DD
- Tier：quick / standard / deep
- 数据库：OpenAlex, Semantic Scholar, Crossref[, arXiv][, PubMed]
- 原始检索：X 篇 → 去重后 Y 篇 → 评分后 Z 篇 (T1: a, T2: b, T3: c, T4: d 剔除)
- 引文扩展：+X 篇 (T1: a, T2: b, T3: c)，种子 Y 篇 [若触发]
- 最终文献：Z 篇 (T1-T3)
- 饱和度：coverage% (CI: ci_l%–ci_u%) [✅ 覆盖良好 / ⚠️ 中等 / ❌ 不足]
```

**.md 底部 — PRISMA-S 摘要**（精简自原 4f）：
- 7 项已执行：数据库、多源、策略、日期、记录数、去重、记录管理
- 9 项未执行：标注原因"非本自动化检索范围"
- 不单独生成 `prisma_s_log.md`，摘要直接写入 .md 末尾可折叠区域

**.bib 文件含完整标签**：
```bibtex
@article{liu_topology_2025,
  title     = {Topology Optimization of Cold Plate Flow Channels...},
  author    = {Liu, ... and Zhang, ...},
  journal   = {Applied Thermal Engineering},
  year      = {2025},
  doi       = {10.1016/j.applthermaleng.2025.127040},
  note      = {Tier 1 | Score: 22/25 | influential_citations: 15 | S1: 冷板拓扑优化}
}
```

### 4h: 完成 🆕

- [ ] 向用户汇报检索报告路径 + 关键数字
- [ ] 更新 `references/decision_log.md`（引文扩展统计）
- [ ] 明确下一步

> **下一步 → Step 5：** 开始批量下载。当前文献库共 X 篇（T1-T3，含引文扩展 Y 篇）。饱和度 Z%。按出版商自动路由 → Sci-Hub → SD CDP → IEEE CDP → Generic CDP。

---

## 7. 质量门槛 (Quality Gates)

- [ ] 4a 引文验证已完成——无效 DOI 已剔除
- [ ] 4b DOI 去重已完成——无重复条目
- [ ] 4c 五维度评分已完成——参考了 rcs-rubric 定性启发
- [ ] 4d Tier 分级已完成——T4 已剔除
- [ ] 🆕 4e 引文网络扩展已完成（若有 T1 触发）——新论文已评分+分级
- [ ] 🆕 4f 饱和度曲线已生成（若 ≥ 30 篇）
- [ ] 🆕 4g 检索报告已生成（.md + .xlsx + .pdf + .bib，仅含 T1-T3）

---

## 8. 收尾检查 (Closing Checks)

> 4g 检索报告和 4h 完成步骤已涵盖大部分收尾工作。此处做最终核对。

### 产出完整性
- [ ] `检索文献表.md` 已生成（含饱和度+PRISMA-S 摘要，仅 T1-T3）
- [ ] `检索文献表.xlsx` 已生成（openpyxl，可直接筛选排序）
- [ ] `检索文献表.pdf` 已自动生成
- [ ] `文献库.bib` 已导出（全量 T1-T3，含 Tier/Score/influential_citations）
- [ ] 🆕 `saturation_snapshot.json` 已生成（若 ≥ 30 篇）

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 评分偏差 → `references/error_log.md`
  - DOI 验证失败新模式 → `references/error_log.md`
  - 饱和度曲线拟合失败 → `references/error_log.md`
  - 引文扩展查询失败 → `references/error_log.md`

### 决策日志更新 🆕
- [ ] 评分权重调整？→ `references/decision_log.md`
- [ ] 筛选阈值修改？→ `references/decision_log.md`
- [ ] 🆕 引文扩展统计（新增 X 篇/种子 Y 篇）→ `references/decision_log.md`

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **Pre-flight 检查失败**：运行 `python3 scripts/search_by_topic.py --preflight` 验证各 API 端点可达性
- **检索结果过少**：检查 AND 块数是否超过 4；回退到 L2/L3
- **评分偏差**：回顾 error_log 中的评分偏差记录
