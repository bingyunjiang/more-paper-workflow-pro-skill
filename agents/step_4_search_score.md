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

## 5. 标准输出 (Standard Outputs) 🔴 6 件套强制交付

> **🔴 所有 6 个产出必须全部生成，Step 4 才算完成。仅生成 .md 不算完成。**
> 所有产出仅含 **T1-T3 论文**（T4 已在 4d 剔除）。

| # | 输出 | 格式 | 生成工具 | 说明 |
|---|------|------|---------|------|
| 1 | 检索文献表 | .md | Agent 直接写入 | 最终版（原始+扩展），顶部含饱和度摘要，底部含 PRISMA-S 摘要 |
| 2 | 检索文献表 | .xlsx | `generate_retrieval_report.py` | openpyxl 生成，冻结表头+自动筛选+Tier 色标 |
| 3 | 检索报告 PDF | .pdf | `generate_search_report.py` → `md_to_pdf.py` | 检索方法论报告 PDF，面向审稿人/导师 |
| 4 | 文献库 | .bib | `generate_retrieval_report.py` | 全量 T1-T3，含 Tier/Score/influential_citations/子课题归属 |
| 5 | 饱和度曲线快照 🆕 | .json | `discovery_curve.py`（4f 步骤） | 文献覆盖率估算，含置信区间；< 30 篇时标注跳过 |
| 6 | **检索报告** 🆕 | .md | `generate_search_report.py`（4g 步骤） | **完整检索方法论报告**：检索范围→流水线→评分→分布→饱和度→行动建议 |

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

### L3 Wanfang Data 🆕

> 中文文献自动检索。支持两种访问模式：
> 1. **机构 IP 直连**（校园网/VPN）：自动检测，无需额外配置
> 2. **CARSI SSO 登录**（校外）：需在 CDP Chrome 中完成一次机构登录
> 万方无多策略（relevance/cited/recent）支持，搜索请求为单次网页查询。

```bash
# L3 Wanfang Data：中文文献检索
python3 scripts/search_by_topic.py "冷板拓扑优化" \
  --source wanfang --limit 50 --output s1_l3_wanfang.bib

# 概念块布尔查询模式（PQ 语法自动转换）
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source wanfang --limit 50 --output s1_l3_wanfang.bib

# 通过 T3 回退：OpenAlex T1 → 不足时万方补充
python3 scripts/search_by_topic.py "battery thermal management" \
  --t1 openalex --t2 semantic_scholar --t3 wanfang --limit 50
```
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

> **万方数据备注** 🆕：万方论文没有真实 DOI 时使用 `wanfang.{title_hash}` 作为标识符。
> 这些条目不进入 Crossref 验证（跳过步骤①），直接进入评分阶段。
> 若有真实 DOI（`10.xxxx/...` 格式），则正常验证。

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
  --output saturation_snapshot.json \
  --report 饱和度分析报告.md
```

**解读输出**：

| coverage_estimate | CI 宽度 | Agent 判断 |
|:-----------------:|:-------:|-----------|
| ≥ 0.85 | < 0.15 | ✅ 覆盖良好 |
| ≥ 0.85 | > 0.15 | ⚠️ 信心不足 |
| 0.6–0.85 | — | ⚠️ 中等覆盖 |
| < 0.6 | — | ❌ 覆盖不足 |
| fit_failed | — | ⚠️ 无法拟合 |

### 4g: 生成检索报告（强制全套交付） 🆕

> **🔴 强制规则**：本步骤为阻塞式步骤。在所有检索、评分、扩展、饱和度分析完成后，**必须**生成以下 **5 个文件 + 1 个饱和度快照**。
> **仅生成 .md 不算完成 Step 4。** 4h 完成检查点会逐一验证文件存在。

**4g.1 生成 .md 检索文献表**（Agent 直接写入）

Agent 生成最终版 .md 文件，**仅含 T1-T3**（T4 已剔除），格式如下：

**.md 顶部 — 饱和度摘要**：
```
## 检索概况
- 检索日期：YYYY-MM-DD
- Tier：quick / standard / deep
- 数据库：OpenAlex, Semantic Scholar, Crossref[, arXiv][, Wanfang Data][, PubMed]
- 原始检索：X 篇 → 去重后 Y 篇 → 评分后 Z 篇 (T1: a, T2: b, T3: c, T4: d 剔除)
- 引文扩展：+X 篇 (T1: a, T2: b, T3: c)，种子 Y 篇 [若触发]
- 最终文献：Z 篇 (T1-T3)
- 饱和度：coverage% (CI: ci_l%–ci_u%) [✅ 覆盖良好 / ⚠️ 中等 / ❌ 不足]
```

**.md 正文 — 检索文献表**：
| DOI | 标题 | 作者 | 年份 | 期刊/会议 | 来源 | 评分 | Tier | 引用数 | 影响力引用 | 旗标 | 子课题 |
|-----|------|------|------|-----------|------|------|------|--------|------------|------|--------|
| ... | ...  | ...  | ...  | ...       | ...  | ...  | ...  | ...    | ...        | ...  | ...    |

**.md 底部 — PRISMA-S 摘要**（可折叠区域）：
- 7 项已执行：数据库、多源、策略、日期、记录数、去重、记录管理
- 9 项未执行：标注原因"非本自动化检索范围"

**4g.2 生成全套交付物（一键脚本）** 🔴 必须执行

> .md 文件写入完成后，**立即执行以下命令**生成 .xlsx + .bib：

```bash
python3 scripts/generate_retrieval_report.py 检索文献表.md
```

该脚本自动完成：
| 产出 | 格式 | 说明 |
|------|------|------|
| 检索文献表 | .xlsx | openpyxl 生成，列：DOI/标题/作者/年份/期刊/来源/评分/Tier/引用数/影响力引用/旗标/子课题，含冻结表头+自动筛选+Tier 色标 |
| 文献库 | .bib | 全量 T1-T3，含 Tier/Score/influential_citations/子课题归属在 note 字段 |

**脚本依赖**：`pip install openpyxl`（必选，已在依赖清单中）

**4g.2b 生成检索报告（完整方法论）** 🔴 必须执行

> 检索报告是一份**独立的、人类可读的方法论文档**，涵盖从检索到筛选到评级的全过程。
> 不同于检索文献表（纯数据表），检索报告面向读者和审稿人，解释"怎么搜的、为什么这样搜、搜到了什么"。
> **该脚本自动同时生成 `检索报告.md` 和 `检索报告.pdf`。**

```bash
# 基础用法（无元数据 JSON 时也能生成，会标注缺失项）
python3 scripts/generate_search_report.py \
  --results 检索文献表.md \
  --saturation saturation_snapshot.json \
  --output 检索报告.md

# 完整用法（推荐：先保存 search_metadata.json 再运行）
python3 scripts/generate_search_report.py \
  --results 检索文献表.md \
  --metadata search_metadata.json \
  --saturation saturation_snapshot.json \
  --output 检索报告.md
```

**检索报告 8 大章节**：

| 章节 | 内容 |
|------|------|
| 1. 检索概览 | 日期/深度/数据库/策略/全流程数字一览 |
| 2. 检索范围与方法 | L1→L2→L3 路由表 + 概念块检索式 + Tier 参数 |
| 3. 检索结果流水线 | PRISMA-S 文本流程图 + 16 项合规清单 |
| 4. 评分维度与方法 | 五维度权重表 + Tier 分级 + 特殊旗标解释 |
| 5. 最终文献库分析 | Tier/子课题/年份/来源/期刊/Top10/引用 七维分布 |
| 6. 引文网络扩展 | 种子数/新增数/去重/评分闭环摘要 |
| 7. 饱和度分析 | 覆盖率 + CI + 解释 + 行动建议 |
| 8. 下一步行动 | 下载路由 → Zotero → 写作 |

**元数据 JSON（可选但推荐）**：Agent 在检索过程中保存 `search_metadata.json` 以生成更完整的报告：

```json
{
  "raw_total": 120,
  "after_dedup": 95,
  "after_verify": 72,
  "t4_removed": 23,
  "expansion_added": 15,
  "expansion_seeds": 5,
  "expansion_t1": 2, "expansion_t2": 7, "expansion_t3": 6,
  "arxiv_enabled": false,
  "source_breakdown": {"openalex": 65, "semantic_scholar": 30, "crossref": 25, "wanfang": 18},
  "query_summary": [
    {"subtopic": "S1: XXX", "query": "(cold plate OR ...) AND (topology ...) AND ..."}
  ]
}
```

> 如未提供 `--metadata`，脚本会从 .md 表格中推导可用的数据，缺失章节标注 `⚠️ 需补充`。

**.bib 文件含完整标签示例**：
```bibtex
@article{liu_topology_2025,
  title     = {Topology Optimization of Cold Plate Flow Channels...},
  author    = {Liu, ... and Zhang, ...},
  journal   = {Applied Thermal Engineering},
  year      = {2025},
  doi       = {10.1016/j.applthermaleng.2025.127040},
  note      = {Tier T1 | Score: 22 | source: openalex | influential_citations: 15 | subtopic: S1: 冷板拓扑优化}
}
```

**4g.3 验证饱和度快照 + 检索报告** 🔴 必须检查

> 饱和度快照 `saturation_snapshot.json`、可读报告 `饱和度分析报告.md`、和 `检索报告.md` 已生成。确认文件存在。

```
[ -f saturation_snapshot.json ] && echo "✅ saturation_snapshot.json" || echo "⚠️ 缺失（可能 < 30 篇）"
[ -f 饱和度分析报告.md ] && echo "✅ 饱和度分析报告.md" || echo "⚠️ 缺失（可能 < 30 篇）"
[ -f 检索报告.md ] && echo "✅ 检索报告.md" || echo "❌ 缺失 — 需回到 4g.2b"
```

### 4h: 完成（交付物验证门） 🆕

> 🔴 **阻塞式检查点**：以下 **6 个交付物** 必须全部存在，Step 4 才算完成。
> 任一缺失 → 回到对应子步骤补充生成，不得声明 Step 4 完成。

**4h.1 交付物存在性验证** 🔴

```bash
# 逐一检查 5 个交付物
for f in "检索文献表.md" "检索文献表.xlsx" "检索报告.pdf" "文献库.bib" "检索报告.md"; do
  if [ -f "$f" ]; then
    echo "✅ $f"
  else
    echo "❌ 缺失: $f — 需回到 4g.2 补充生成"
  fi
done
# 饱和度快照 + 报告（条件性：≥ 30 篇时必须存在）
if [ -f "saturation_snapshot.json" ]; then
  echo "✅ saturation_snapshot.json"
else
  echo "⚠️ saturation_snapshot.json 不存在（可能因 < 30 篇未触发 4f）"
fi
if [ -f "饱和度分析报告.md" ]; then
  echo "✅ 饱和度分析报告.md"
else
  echo "⚠️ 饱和度分析报告.md 不存在（可能因 < 30 篇未触发 4f）"
fi
```

**4h.2 汇报与记录**

- [ ] 向用户展示 5 交付物清单 + 文件路径 + 关键数字（总数/T1-T3 分布/饱和度）
- [ ] 更新 `references/decision_log.md`（引文扩展统计 + 最终文献分布）
- [ ] 更新 `references/error_log.md`（本轮新出现的错误/偏差）

**4h.3 转交 Step 5**

仅在 **6 交付物全部验证通过** 后，输出以下转交信息：

> **✅ Step 4 完成 → 下一步 Step 5：开始批量下载。**
>
> 交付物：
> - `检索文献表.md` — 文献检索表（Z 篇 T1-T3）
> - `检索文献表.xlsx` — 可筛选排序的 Excel 版
> - `检索报告.pdf` — 完整检索方法论报告 PDF（面向审稿人/导师）
> - `文献库.bib` — BibTeX 文献库（含 Tier/Score/influential_citations）
> - `检索报告.md` — 完整检索方法论报告（8 章节，面向审稿人）
> - `saturation_snapshot.json` — 饱和度曲线快照 [若 ≥ 30 篇]
>
> 当前文献库共 X 篇（T1: a | T2: b | T3: c，含引文扩展 Y 篇）。饱和度 Z%。
> 按出版商自动路由 → Sci-Hub → SD CDP → IEEE CDP → Generic CDP。

---

## 7. 质量门槛 (Quality Gates) 🔴 阻塞式

> 以下检查项**全部通过**才能进入 4h 完成。任一未通过 → 回到对应子步骤修复。

- [ ] 4a 引文验证已完成——无效 DOI 已剔除
- [ ] 4b DOI 去重已完成——无重复条目
- [ ] 4c 五维度评分已完成——参考了 rcs-rubric 定性启发
- [ ] 4d Tier 分级已完成——T4 已剔除
- [ ] 🆕 4e 引文网络扩展已完成（若有 T1 触发）——新论文已评分+分级
- [ ] 🆕 4f 饱和度曲线已生成（若 ≥ 30 篇）
- [ ] 🔴 4g.1 `.md` 检索文献表已写入——含饱和度+PRISMA-S 摘要，仅含 T1-T3
- [ ] 🔴 4g.2 `generate_retrieval_report.py` 已成功执行——`.xlsx` + `.bib` 已生成
- [ ] 🔴 4g.3 饱和度快照 `saturation_snapshot.json` 存在（若 ≥ 30 篇）或已标注跳过原因

---

## 8. 收尾检查 (Closing Checks)

> 4g 检索报告和 4h 完成步骤已涵盖大部分收尾工作。此处做最终核对。

### 产出完整性 🔴 逐一确认

在执行 4h 汇报之前，必须用 `ls` 或文件存在性检查确认以下 **5 个文件** 全部存在：

| # | 文件 | 检查命令 | 若缺失 |
|---|------|---------|--------|
| 1 | `检索文献表.md` | `[ -f "检索文献表.md" ]` | 回到 4g.1 |
| 2 | `检索文献表.xlsx` | `[ -f "检索文献表.xlsx" ]` | 回到 4g.2 |
| 3 | `检索报告.pdf` | `[ -f "检索报告.pdf" ]` | 回到 4g.2b |
| 4 | `文献库.bib` | `[ -f "文献库.bib" ]` | 回到 4g.2 |
| 5 | `检索报告.md` | `[ -f "检索报告.md" ]` | 回到 4g.2b |
| 6 | `saturation_snapshot.json` | `[ -f "saturation_snapshot.json" ]` | 若 ≥ 30 篇回到 4f；若 < 30 篇标注跳过 |

**🔴 仅当以上 6 个检查项全部通过（或 #6 合理跳过）后，才能进入 4h.3 转交 Step 5。**

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 评分偏差 → `references/error_log.md`
  - DOI 验证失败新模式 → `references/error_log.md`
  - 饱和度曲线拟合失败 → `references/error_log.md`
  - 引文扩展查询失败 → `references/error_log.md`
  - `generate_retrieval_report.py` 执行失败 → `references/error_log.md`

### 决策日志更新 🆕
- [ ] 评分权重调整？→ `references/decision_log.md`
- [ ] 筛选阈值修改？→ `references/decision_log.md`
- [ ] 🆕 引文扩展统计（新增 X 篇/种子 Y 篇）→ `references/decision_log.md`
- [ ] 🆕 最终交付物生成结果 → `references/decision_log.md`

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **Pre-flight 检查失败**：运行 `python3 scripts/search_by_topic.py --preflight` 验证各 API 端点可达性
- **检索结果过少**：检查 AND 块数是否超过 4；回退到 L2/L3
- **评分偏差**：回顾 error_log 中的评分偏差记录
