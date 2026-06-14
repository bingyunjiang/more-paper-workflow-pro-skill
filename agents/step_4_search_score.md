# Step 4: 多渠道检索与相关性筛选

> 按 Step 3 方案的 L1→L2→L3 分层路由逐子课题检索，对结果进行 5 维度评分和 Tier 分级筛选。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，优先确认以下工件是否可用；若同时存在 JSON 和 Markdown，优先读取 JSON 机器源：

- [ ] `检索方案.json` / `检索方案.md` — Step 3 产出（`检索方案.json` 为机器执行源，`检索方案.md` 为人工审阅版）
- [ ] `retrieval_index_manifest.json` — 🆕 检索索引复用清单（如存在，先判断是否 still reusable）
- [ ] `研究主题.md` — Step 1 产出（tier/search_tier + 聚焦主题 + 预审结论）
- [ ] `references/search-query-frameworks.md` — 检索查询框架参考
- [ ] `references/rcs-rubric.md` — 🆕 主题匹配度评鉴启发指南
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则
- [ ] `.skill-state/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 按检索方案的 L1→L2→L3 分层路由逐子课题执行文献检索
- 对检索结果进行引文验证（DOI 有效性 + 元数据完整性）
- 多源检索结果 DOI 去重合并
- 五维度相关性评分（主题匹配度/方法学严谨性/来源质量/时效性/影响力）
- Tier 分级筛选（T1/T2/T3/T4）
- 统一 .bib 导出（含评分标签和子课题归属）
- 生成或更新 `retrieval_index_manifest.json`，记录本轮 `workflow_search_results.json`、metadata cache 和检索结果索引的复用状态

---

## 3. 不适用任务 (Non-applicable Tasks)

以下任务不属于本 Step 范围：

- 检索方案设计 → 路由到 `agents/step_3_search_plan.md`
- PDF 下载 → 路由到 `agents/step_5_download.md`
- 文献综述矩阵 → 路由到 `agents/step_7_writing.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 检索方案 | Step 3 | .md | ✅ |
| search_tasks | Step 3 `检索方案.md` | YAML/Markdown | ✅ |
| 检索执行参数 | search_tasks 中的 tier + L1/L2/L3 路由配置 | 文本 | ✅ |

**独立入口规则：**

如果用户已有检索方案、检索式、关键词组合、数据库清单、文献表或 BibTeX，可直接从 Step 4 开始，不要求回跑 Step 3。Agent 应在当前 Step 内完成：

1. 将用户材料整理为最小 `search_tasks` 或 direct scoring/import plan。
2. 输出 `CHECKPOINT 3 — CP-SEARCH`，设置 `entry_mode: direct_entry` 或 `partial_artifact`，`status: satisfied_by_user_artifact` 或 `satisfied_by_agent_reconstruction`。
3. 用户明确“确认 CP-SEARCH”后，才执行真实多源检索命令；生成 dry-run 摘要、评分用户已有文献表、格式转换或报告生成不需要补跑完整 Step 3。

**Direct-entry input contract：**

| 可接受输入 | 最小处理 | 是否触发 CP-SEARCH |
|------------|----------|--------------------|
| `search_tasks` / `检索方案.md` | 直接执行或 dry-run 检索计划 | 真实检索前触发 |
| 用户给定检索式/数据库清单 | 包装为最小 `search_tasks` | 真实检索前触发 |
| 已有 `检索文献表.md` / `.xlsx` | 只做评分、报告、格式补齐 | 不触发，除非继续联网检索 |
| 已有 `文献库.bib` / workflow search results JSON | 导入为标准结果集，补报告或交给 Step 5/6 | 不触发，除非继续联网检索 |

Step 4 的直接入口不强制生成完整标准交付物。只有用户要求“完成标准 Step 4 交付”时，才按核心交付质量门执行；如果用户只要求评分已有文献、生成报告或转入下载/Zotero，应输出当前可用产物和缺失项清单，不要求回跑 Step 3。

**Step 3 字段读取规则：**

| 字段 | 用途 |
|------|------|
| search_tasks[].id | 输出表中的子课题归属和文件名前缀 |
| search_tasks[].chapter_id / chapter_title | 关联 Step 2 章节，供 Step 6/7 回溯 |
| search_tasks[].evidence_type | 影响评分解释和后续证据类型归类 |
| search_tasks[].question_to_answer | 判断主题匹配度和检索覆盖 |
| search_tasks[].query_blocks | 生成布尔查询与执行命令 |
| search_tasks[].route | 决定中文/英文源执行顺序 |
| search_tasks[].tier | 决定 limit、策略和补充源 |

---

## 5. 标准输出 (Standard Outputs)

> 标准 Step 4 完成时，必须生成核心交付物；条件性交付物按触发条件生成或明确标注跳过原因。所有最终导出的文献表和 BibTeX 仅含 **T1-T3 论文**（T4 已在 4.5 剔除或单独进入排除说明）。

**核心交付物：**

| # | 输出 | 格式 | 生成工具 | 说明 |
|---|------|------|---------|------|
| 1 | workflow search results JSON | .json | `search_by_topic.py --export_workflow_json` 或 Agent 标准化写入 | Step 4 机器主输出，供 Step 5/6/7 继续消费 |
| 2 | 检索文献表 | .md | Agent 直接写入 | 人工审阅版，顶部含筛选依据、饱和度摘要，底部含 PRISMA-S 摘要 |
| 3 | 检索文献表 | .xlsx | `generate_retrieval_report.py` | openpyxl 生成，冻结表头+自动筛选+Tier 色标 |
| 4 | 检索报告 | .md | `generate_search_report.py` | 完整检索方法论报告：检索范围→流水线→评分→分布→饱和度→行动建议 |
| 5 | 检索报告 | .pdf | `generate_search_report.py` → `md_to_pdf.py` | 面向审稿人/导师的 PDF 报告 |
| 6 | 文献库 | .bib | `generate_retrieval_report.py` | 全量 T1-T3，含 Tier/Score/influential_citations/子课题归属 |
| 7 | retrieval index manifest | .json | Agent 直接写入或由检索脚本补写 | 记录检索结果和元数据索引复用状态；不是证据裁决 |

**条件性交付物：**

| # | 输出 | 格式 | 触发条件 | 说明 |
|---|------|------|----------|------|
| 8 | 饱和度曲线快照 | .json | T1-T3 文献数 ≥ 30 | 文献覆盖率估算，含置信区间；不足 30 篇时标注跳过 |
| 9 | 中文论文元数据 JSON | .json | 存在 source=cnki/wanfang 的行 | 供 Step 5 下载与 Step 6 Zotero 中文条目入库使用 |

**统一文件命名规范：**

| 产出 | 推荐文件名 |
|------|------------|
| 检索文献表 Markdown | `检索文献表.md` |
| 检索文献表 Excel | `检索文献表.xlsx` |
| 检索报告 Markdown | `检索报告.md` |
| 检索报告 PDF | `检索报告.pdf` |
| 文献库 BibTeX | `文献库.bib` |
| 饱和度快照 | `saturation_snapshot.json` |
| 中文论文元数据 | `中文论文元数据.json` |
| workflow search results JSON | `workflow_search_results.json` |
| retrieval index manifest | `retrieval_index_manifest.json` |

---

## 6. 执行流程 (Execution Flow)

### 4.0. 检索执行总览

按 Step 3 的 `search_tasks` 逐任务执行。每个任务都必须保留 `id`、`chapter_id`、`evidence_type`、`tier`、`source`，并写入后续检索文献表。

> 从本版开始，Step 4 的机器主输出是 `workflow_search_results.json`。`检索文献表.md/.xlsx`、`检索报告.md/.pdf`、`文献库.bib` 和 `中文论文元数据.json` 都应视为围绕该 JSON 生成的展示层、审阅层和交接层。`retrieval_index_manifest.json` 记录这些检索资产是否可复用，但不替代评分表和人工审阅。

### 4.0.1. 阶段输入输出表

| 阶段 | 输入 | 动作 | 输出 |
|------|------|------|------|
| 4.1 文献可信度验证 | 原始检索结果 | DOI/元数据校验；中文 source id 保护 | 验证后候选表 |
| 4.2 去重合并 | 多源候选表 | DOI 归一化；无 DOI 用 title+author+year | 去重文献表 |
| 4.3 筛选依据确认 | 去重文献表 + search_tasks | 向用户展示评分维度、权重、阈值和排除规则 | 用户确认或调整后的 screening basis |
| 4.4 五维评分 | 去重文献表 + screening basis | 主题/方法/来源/时效/影响力评分 | 带 score 的文献表 |
| 4.5 Tier 分级 | 带 score 的文献表 | T1/T2/T3/T4 判定；T4 剔除 | T1-T3 文献表 |
| 4.6 引文扩展 | T1 种子 | 单轮 1-hop 扩展 + 闭环评分 | 扩展后 T1-T3 文献表 |
| 4.7 饱和度估算 | 全量 T1-T3 | 覆盖率估算 | `saturation_snapshot.json` 或跳过说明 |
| 4.8 报告生成与完成检查 | 最终 T1-T3 + 标准输出 | 生成交付物 + 字段完整性检查 + 索引复用状态 | Step 5/6 handoff |

> **中文查询路由：** 查询含中文字符时，CNKI（L1 主检索）+ Wanfang Data（L2 补充）双路检索。

### 4.1. 文献可信度三态机制

> 4.1 的目标是判断“文献条目本身是否可追溯、可入库、可引用候选”，不是判断它是否支撑某个 claim；claim 支撑关系留到 Step 7.9/7.15。

**三态定义：**

| 状态 | 判定 | 后续处理 |
|------|------|----------|
| `VERIFIED` | 可信公开源返回稳定 DOI/ID，且 title/year/authors 基本匹配 | 可进入 4.2-4.5，按评分与 Tier 参与筛选 |
| `VERIFIED_LOCAL` | CNKI/万方等中文源有 `source_id` 或 `article_url`，且 title/authors/year/publication_title 可追溯 | 可进入 4.2-4.5；不得因无 DOI 降级或剔除 |
| `WARN` | 存在真实不确定性：标题/年份/作者冲突、摘要缺失、来源弱、无稳定详情页、疑似重复、元数据残缺 | 保留进入人工审查队列；可评分，但写作时只能作背景/待补查线索 |
| `REJECT` | DOI 指向另一篇论文、关键元数据明显冲突、0 可追溯来源、明确撤稿或假条目 | 不进入最终 T1-T3 主表和 `文献库.bib`；只在检索报告异常清单中保留痕迹 |

**关键规则：**
1. `VERIFIED` 不要求至少 2 个来源一致。Crossref / OpenAlex / Semantic Scholar / PubMed / arXiv 任一可信源即可确认，只要稳定标识与核心元数据闭环。
2. 多源一致只提高 `verification_confidence=high`，不是进入 `VERIFIED` 的硬门槛。
3. 中文无 DOI 文献默认不是 `REJECT`。CNKI/万方条目只要有稳定详情页或 source_id，并能追溯标题、作者、年份、来源，即标为 `VERIFIED_LOCAL`。
4. WARN 是“需要人审或补证据”，不是“低质量文献”。中文核心、会议论文、新预印本和数据库覆盖弱领域不得因单源而自动降为 WARN。
5. 撤稿或表达关注应优先标记 `REJECT`；如只是 corrigendum/erratum，按具体影响写入 `warn_class`。

**4.1 必写字段：**

| 字段 | 值域/示例 | 说明 |
|------|-----------|------|
| `verification_status` | `VERIFIED` / `VERIFIED_LOCAL` / `WARN` / `REJECT` | 文献条目可信度三态 |
| `verification_confidence` | `high` / `medium` / `low` | 多源一致或强来源为 high；单可信源通常 medium；弱来源/残缺为 low |
| `warn_class` | `metadata-mismatch`, `missing-abstract`, `weak-source`, `no-stable-url`, `legacy-unverified`, `retracted` | 仅 WARN/REJECT 必填；VERIFIED 可空 |
| `verified_sources` | `crossref`, `openalex`, `semantic_scholar`, `cnki`, `wanfang` | 实际确认过的来源，多个用逗号分隔 |

`检索文献表.md` 主表必须包含上述 4 列；`generate_retrieval_report.py` 会将其写入 Excel 和 BibTeX note，供 Step 6/7 继续读取。

### CP-CITATION-WARN

当 4.1 产生的异常会改变最终 T1-T3 纳入策略、下游关键引用策略，或涉及 `REJECT` 条目的保留/剔除处置时，才输出 warning checkpoint。仅把 `WARN` 条目列入背景性候选、综述矩阵候选、待补查清单或异常清单，不触发 checkpoint。

```md
## CHECKPOINT W — CP-CITATION-WARN

entry_mode: normal_chain|direct_entry|repair|partial_artifact
status: blocked
blocks_next: final T1-T3 library and downstream citation use
must_confirm: true

summary:
- 列出会影响主表纳入、关键引用或 REJECT 处置的 WARN/REJECT 条目数量、warn_class 分布和风险范围。

user_options:
1. 删除 REJECT，WARN 保留但标注
2. 逐条审查 WARN/REJECT
3. 回退补元数据或补检索来源

does_not_block:
- 将 WARN 作为背景候选或待补查线索
- 在综述矩阵中保留候选记录并显式标注 warn_class
- 低风险主题归类、去重、来源统计和异常清单整理

required_confirmation:
- “确认 CP-CITATION-WARN”
```

### 4.0.2. 英文源执行规则（公开 API，无需认证，直接跑）

> 英文源全部是公开 API，与机构账号无关。执行时按 tier 选择启用的源，遇错处理即可，无需等待用户。

| 数据源 | Deep tier | Standard tier | Quick tier | 遇错行为 |
|--------|-----------|---------------|-----------|---------|
| **OpenAlex** | ✅ 必跑 | ✅ 必跑 | ✅ 必跑 | FAIL → ❌ 中止（唯一不可跳过） |
| **Crossref** | ✅ **必跑** | ⚠️ OpenAlex < 30 或 SemSch 429 → 必跑 | ⬜ 跳过 | FAIL → 报告标注缺失 |
| **Semantic Scholar** | ✅ 跑 | ✅ 跑 | ⬜ 跳过 | 429 → ⬜ 跳过不阻塞 |
| **arXiv** | ✅ 仅 CS/AI 信号 | 同左 | ⬜ 跳过 | FAIL → 跳过 |
| **PubMed** | ✅ 仅医工交叉 | 同左 | ⬜ 跳过 | FAIL → 跳过 |

> **规则：** OpenAlex 唯一不可跳过；Crossref deep tier 必跑；Semantic Scholar 429 不阻塞。

---

### 4.0.3. 中文源 preflight + 认证（仅中文查询触发）

> 中文源（CNKI/万方）在校园网外需要 CARSI 机构登录。**中文源的问题不阻塞英文源——英文源先行，中文源认证同步处理。**

```
执行顺序：
  1. 🏃 英文源命令先行（上表），不等待中文源
  2. 🔍 同时跑中文源 preflight：python3 scripts/search_by_topic.py --preflight
  3. 📊 中文 preflight 结果：
     ├─ IP 直连 OK  → 直接跑 CNKI/万方命令
     └─ CDP/CARSI   → 进入下方认证流程
```

**中文源路由决策：**

| 数据源 | Preflight 结果 | 行为 |
|--------|:------------:|------|
| **CNKI** | IP 直连 OK | ✅ 直接跑，无需用户操作 |
| **CNKI** | CDP/CARSI | 🔐 先问用户是否有机构账号（见下方流程） |
| **CNKI** | 用户无机构账号 | 📝 确认后跳过，报告标注「中文源: 用户无机构账号」 |
| **CNKI** | 用户选择跳过 | 📝 报告标注「中文源: 用户跳过」 |
| **Wanfang** | IP 直连 OK | ✅ 直接跑，无需用户操作 |
| **Wanfang** | CDP/CARSI | 🔐 先问用户是否有机构账号（见下方流程） |
| **Wanfang** | 用户无机构账号 | 📝 确认后跳过，报告标注「中文源: 用户无机构账号」 |
| **Wanfang** | 用户选择跳过 | 📝 报告标注「中文源: 用户跳过」 |

**中文源认证流程（CDP/CARSI 时——CHECKPOINT W — CP-DOWNLOAD-LOGIN）：**

```
🔐 检测到 CNKI/万方需要 CARSI 机构登录。

   第一步：先问用户：
   > "CNKI/万方需要机构账号（CARSI SSO）才能访问。请问你有学校/机构的统一身份认证账号吗？"
   > 选项 A: 有账号 → 🚀 执行下方「交互式批量检索」流程
   > 选项 B: 没有账号 → 确认是否跳过中文源，报告中标注原因
   > 选项 C: 不确定 → 建议先尝试 CARSI 登录页查看学校列表

   第二步（用户选 A — 有账号）：
   🚀 Agent 执行交互式批量检索（一条命令内完成全部操作，防止 CDP 断连）：

   a) Agent 基于 Step 3 检索方案，汇总所有 CNKI/Wanfang 查询 → 写入临时 JSON 文件
      （文件格式见下方 queries.json 模板）

   b) Agent 启动一条长驻 exec_command（yield_time_ms=30000）：
        bash scripts/batch_chinese_search.sh <queries.json> --output-dir <output/>

   c) 脚本自动处理 CDP Chrome：
      ├─ 端口 9223 已有 CDP → 复用（打印 CDP_ALIVE）
      └─ 无 CDP → 自动启动 Chrome → 导航到 CNKI/万方 → 等待就绪（打印 CDP_READY）

   d) 脚本打印 === LOGIN_REQUIRED === 后阻塞等待 stdin

   e) Agent 检测到 === LOGIN_REQUIRED ===，告知用户：
      「Chrome 已自动打开并导航到 CNKI/万方，请完成 CARSI 机构登录后回复「已登录」」

   f) 用户完成 CARSI 登录后回复「已登录」

   g) Agent 调用 write_stdin("go\n")，脚本继续执行全部检索

   h) 逐条执行查询（打印 SEARCH_START:Sx / SEARCH_DONE:Sx:N）
      每条命令自动加 --no-cache（避免空结果毒化缓存）和 --language zh

   i) 脚本打印 === ALL_DONE === 汇总结果数 + .bib 文件列表

   第二步（用户选 B — 无机构账号）：
   > "确认跳过 CNKI/万方中文检索。检索报告中将标注「中文源: 用户无机构账号」。"
   > 可以建议备用方案：联系学校图书馆获取 VPN、或使用 iData 等第三方镜像。
   ⚠️ 确认后继续英文源检索，不阻塞流程。
```

> 该认证 checkpoint 的 `entry_mode` 可为 `normal_chain` 或 `direct_entry`。用户明确完成登录并确认 `CP-DOWNLOAD-LOGIN` 后，Agent 才能继续中文源检索；英文公开 API 检索不受该 checkpoint 阻塞。

**queries.json 模板（Agent 动态生成）：**
```json
[
  {"id":"S1","query":"冷板拓扑优化","source":"cnki","limit":50,"strategy":"relevance"},
  {"id":"S1","query":"冷板拓扑优化","source":"wanfang","limit":50},
  {"id":"S2","query":"液冷板 结构优化 传热","source":"cnki","limit":50}
]
```

**Agent 执行参考命令：**
```bash
# 1. Agent 动态生成查询 JSON 文件
cat > .skill-state/chinese_queries.json << 'JSONEOF'
[
  {"id":"S1","query":"子课题1","source":"cnki","limit":50,"strategy":"relevance"},
  {"id":"S1","query":"子课题1","source":"wanfang","limit":50}
]
JSONEOF

# 2. 启动交互式批量检索（一条命令，CDP 不会断连）
bash scripts/batch_chinese_search.sh .skill-state/chinese_queries.json \
  --output-dir .skill-state/

# 3. 检测到 === LOGIN_REQUIRED === 后告知用户登录，等回复后用 write_stdin("go\n")
# 4. 检测到 === ALL_DONE === 后取结果
```

**CDP Chrome 手动启动（备用）：**
```bash
# 仅当 batch_chinese_search.sh 自动启动失败时手动兜底
open -na "Google Chrome" --args --remote-debugging-port=9223 \
  --remote-allow-origins=http://127.0.0.1:9223 \
  --no-first-run --no-default-browser-check \
  --disable-blink-features=AutomationControlled \
  --user-data-dir="$HOME/.hermes/chrome_sd_profile" \
  https://kns.cnki.net/kns8s/

# 验证 CDP 是否就绪
for i in {1..10}; do
  if curl -s "http://127.0.0.1:9223/json/version" >/dev/null 2>&1; then
    echo "✅ CDP ready on :9223"; break
  fi
  sleep 1
done
```

# L1 OpenAlex：每子课题跑 3 策略（relevance + cited + recent），每策略 50 条
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source openalex --strategy relevance --limit 50 --export-bib s1_l1_rel.bib
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source openalex --strategy cited --limit 50 --export-bib s1_l1_cited.bib
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source openalex --strategy recent --limit 50 --export-bib s1_l1_recent.bib

# L2 Semantic Scholar：CS 交叉子领域并行，传统工科在 L1<30 时回退
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source semantic_scholar --limit 50 --export-bib s1_l2.bib

# 传统用法（向后兼容，不使用概念块）：
python3 scripts/search_by_topic.py "cold plate liquid cooling optimization" \
  --t1 openalex --t2 semantic_scholar --limit 50 --export-bib s1_results.bib

### 4.0.4. L2 Crossref（DOI/出版社元数据补充，Deep tier 必跑）

> 🆕 按 Step 3 路由规则，Deep tier 下 **必须执行**，不得仅用 OpenAlex 完成英文检索。
> Standard tier 在 OpenAlex 结果不足或 Semantic Scholar 429 时也必须启用。
> Crossref 提供 DOI 归一化 + 出版社元数据（期刊名、页码、卷期号），
> OpenAlex 和 Semantic Scholar 经常缺这些字段。

```bash
# L2 Crossref：逐子课题补检，结果与 OpenAlex DOI 去重
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source crossref --limit 50 --export-bib s1_l2_crossref.bib

# 多子课题可合并在一条命令中
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source crossref --limit 50 --export-bib all_l2_crossref.bib
```

### 4.0.5. L1 CNKI

> 🆕 中文文献主检索。支持两种访问模式：
> 1. **IP 直连**（校园网/VPN）：自动 POST/GET HTTP 检索，零配置，支持多策略排序
> 2. **CDP 浏览器**（校外 CARSI/RVPN）：通过 CDP Chrome 使用新 SPA 界面检索
> CNKI 支持多策略切换（相关度/时间/被引），可使用 `--strategy` 参数。

```bash
# CNKI 中文文献检索（🔴 必须带 --language zh，排除英文论文）
python3 scripts/search_by_topic.py "冷板拓扑优化" \
  --source cnki --language zh --limit 50 --export-bib s1_cnki.bib

# CNKI 多策略检索（被引排序）
python3 scripts/search_by_topic.py "冷板拓扑优化" \
  --source cnki --language zh --strategy cited --limit 50 --export-bib s1_cnki_cited.bib

# 概念块布尔查询模式
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source cnki --language zh --limit 50 --export-bib s1_cnki.bib

# T1 CNKI + T2 Wanfang 级联
python3 scripts/search_by_topic.py "冷板拓扑优化" \
  --t1 cnki --t2 wanfang --language zh --limit 50
```

### 4.0.6. L2 Wanfang Data

> 中文文献补充检索。支持两种访问模式：
> 1. **机构 IP 直连**（校园网/VPN）：自动检测，无需额外配置
> 2. **CARSI SSO 登录**（校外）：需在 CDP Chrome 中完成一次机构登录
> 万方无多策略（relevance/cited/recent）支持，搜索请求为单次网页查询。

```bash
# L2 Wanfang Data：中文文献检索（🔴 必须带 --language zh）
python3 scripts/search_by_topic.py "冷板拓扑优化" \
  --source wanfang --language zh --limit 50 --export-bib s1_l2_wanfang.bib

# 概念块布尔查询模式（PQ 语法自动转换）
python3 scripts/search_by_topic.py --bool query_plan.json \
  --source wanfang --language zh --limit 50 --export-bib s1_l2_wanfang.bib

# 通过 T2 补充：CNKI T1 → 不足时万方补充
python3 scripts/search_by_topic.py "冷板拓扑优化" \
  --t1 cnki --t2 wanfang --language zh --limit 50
```

### 4.0.7. Tier-driven 检索参数

> 优先读取 `search_tasks[].tier`；若缺失，则按 Step 3 顶层 `tier`、Step 1 顶层 `tier`、Step 1 `search_tier.tier`、默认 `standard` 的顺序回退。

| Tier | limit/策略 | strategies | 补充策略 |
|------|:--------:|-----------|---------|
| Quick | 30 | relevance only | 无 |
| Standard（默认） | 50 | relevance + cited + recent | 无 |
| Deep | 100 | relevance + cited + recent | + seminal cutoff + review type |

### 4.0.8. L2 arXiv 条件触发

> 仅当 Step 3 检索方案标记了 `arxiv_enabled: true` 时执行。

```bash
# L2 arXiv：仅 CS/AI 跨域信号时触发（T-0~T-4 新鲜度窗口）
python3 scripts/arxiv_helper.py "query string" \
  --days 4 --limit 20 --output s1_l2_arxiv.json
```

### 4.1.1. 引文验证执行细则

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

> **CNKI + 万方备注** 🆕：无真实 DOI 的论文使用 `cnki.{title_hash}` 或 `wanfang.{title_hash}` 作为标识符。
> 这些条目不进入 Crossref 验证（跳过步骤①），直接进入评分阶段。
> 若有真实 DOI（`10.xxxx/...` 格式），则正常验证。
> `cnki.xxx` / `wanfang.xxx` 是内部 source id，不是真实 DOI；后续导入 Zotero 时不得写入 DOI 字段，只能写入 `Extra` 或等价元数据字段。
>
> **中文论文文章 URL 保留** 🆕：中文论文（source=cnki/wanfang）在检索结果中必须保留**文章详情页 URL**，
> 写入检索文献表的 `文章链接` 列。此 URL 是 Step 5 Chinese CDP Round 下载的入口。
> CNKI 检索结果中的 `briefDl_D` 链接和 Wanfang 结果中的详情页链接均需保留。
> 若无可用 URL，标注 `⚠️ 缺文章页URL`，该论文将无法在 Step 5 自动下载。

### 4.2. DOI 去重

多源检索会产生重复（同一篇论文从 Semantic Scholar 和 Crossref 各返回一次）：

```
去重策略：
  - 主键：DOI（大小写 + 前缀统一后比对）
  - 无 DOI 时：title + first_author + year 组合键
  - 冲突时保留元数据最完整的条目
```

### 4.3. 筛选依据确认（用户可见）

在 4.1 文献可信度验证和 4.2 去重完成后，正式评分和剔除前，必须把本轮筛选依据以对话框或 checkpoint 形式展示给用户。目标是让用户知道“检索后根据什么筛选”，并允许用户调整权重、阈值或排除规则。

**筛选依据来源：**

| 依据 | 来源 | 作用 |
|------|------|------|
| 研究问题 / 子课题 | `search_tasks[].question_to_answer`、用户当前描述 | 决定主题匹配度 |
| 章节或任务归属 | `search_tasks[].chapter_id`、`chapter_title` | 决定后续 Step 6/7 可追溯性 |
| 证据类型 | `search_tasks[].evidence_type` | 决定方法学严谨性的解释重点 |
| 检索层级 | `tier` / `search_tier` | 决定源、limit、扩展策略 |
| 文献可信度 | 4.1 的 `VERIFIED / VERIFIED_LOCAL / WARN / REJECT` | 决定能否进入主表或异常清单 |
| 用户偏好 | 用户指定期刊、年份、语言、研究对象、方法边界 | 覆盖默认阈值或排除项 |

**默认评分维度：**

| 维度 | 权重 | 说明 |
|------|:----:|------|
| 主题匹配度 | 35% | 标题+摘要与研究主题、子课题、问题目标的相关程度 |
| 方法学严谨性 | 20% | 方法/实验/数据是否能支撑当前任务；实验、对照、数据质量按任务解释 |
| 来源质量 | 15% | 期刊/会议/机构来源、索引情况、出版稳定性 |
| 时效性 | 15% | 近 3 年优先；经典文献可因 foundational role 保留 |
| 影响力 | 15% | 引用量、influentialCitationCount、领域内代表性 |

**默认 Tier 阈值：**

| 等级 | 分数范围 | 默认处理 |
|------|----------|----------|
| Tier 1 | ≥20 | 核心文献，必须下载 |
| Tier 2 | 15-19 | 重要文献，尽量下载 |
| Tier 3 | 10-14 | 参考文献，有选择下载 |
| Tier 4 | <10 | 不进入最终导出；进入排除说明或异常清单 |

**CHECKPOINT 4.3 - CP-SCREENING-BASIS：**

```md
## CHECKPOINT 4.3 - CP-SCREENING-BASIS

entry_mode: normal_chain|direct_entry|partial_artifact
status: waiting_user_confirmation
must_confirm: true
blocks_next: scoring, Tier grading, final T1-T3 export

screening_basis:
- research_question_basis: <本轮用于判断相关性的研究问题/子课题>
- inclusion_rules: <纳入规则，如主题、方法、年份、语言、来源>
- exclusion_rules: <排除规则，如无关主题、元数据不可追溯、撤稿、重复>
- scoring_dimensions: 主题匹配度35 / 方法学20 / 来源质量15 / 时效性15 / 影响力15
- tier_thresholds: T1>=20, T2=15-19, T3=10-14, T4<10
- trust_boundary: VERIFIED/VERIFIED_LOCAL 可进入主表；WARN 标注风险；REJECT 不进入主表

user_options:
1. 确认使用默认筛选依据
2. 调整权重、阈值、年份范围、语言范围或排除规则
3. 暂不剔除，只生成候选清单和风险说明

does_not_block:
- 元数据验证
- 去重
- 来源统计
- dry-run 报告
- direct-entry 下的已有文献表格式补齐

required_confirmation:
- "确认 CP-SCREENING-BASIS"
```

用户确认或调整后的筛选依据必须写入 `检索文献表.md` 顶部、`检索报告.md` 的评分方法章节，以及 `.skill-state/decision_log.md`。如用户选择“暂不剔除”，Step 4 可以输出候选清单和风险说明，但不得声称已经完成最终 T1-T3 文献库。

### 4.4. 相关性评分（v3.0 五维度）

按 4.3 用户确认后的 `screening_basis` 对去重文献表打分。每项仍按 0-5 评分，满分 25；评分解释可参考 `references/rcs-rubric.md`，但不得把 RCS 启发当成唯一筛选依据。

**评分回溯规则：**

- 主题匹配度必须参考 `search_tasks[].question_to_answer` 或用户在 4.3 确认的研究问题。
- 方法学严谨性必须参考 `search_tasks[].evidence_type`，例如 `experiment` 任务更重视实验/对照证据。
- 同一论文服务多个 `search_task` 时，保留多重归属，不覆盖原归属。
- 每条 T1/T2 评分理由至少写明一个匹配词、摘要依据、方法依据或来源依据，避免黑箱分数。

**证据层级提示（解释层增强，不改核心状态机）：**

- `VERIFIED / VERIFIED_LOCAL / WARN / REJECT` 仍是 Step 4 的核心信任状态，不替换。
- 高相关不等于高证据等级。
- 高证据等级不等于与当前 research question 高匹配。
- 系统综述 / 方法学敏感任务下，检索报告应说明哪些条目适合作背景综述、方法依据或低风险补充。

### 4.5. 筛选标准（Tier 分级）

按 4.3 确认后的阈值执行 Tier 分级。若用户未修改阈值，使用默认 T1-T4；若用户修改阈值，必须把修改理由写入 `decision_log` 和检索报告。

| 等级 | 分数范围 | 处理 |
|------|---------|------|
| Tier 1 | ≥20 | 核心文献，必须下载 |
| Tier 2 | 15-19 | 重要文献，尽量下载 |
| Tier 3 | 10-14 | 参考文献，有选择下载 |
| Tier 4 | <10 | 不进入后续导出（`.bib` / `.md` / `.xlsx` 均不含 T4）；进入排除说明或异常清单 |

### 4.6. 引文网络扩展（单轮 1-hop）

> 设计约束：单轮，不做第二跳；仅 T1 种子论文，最多 10 篇；新增论文在 4.6 内复用 4.4/4.5 完成评分和分级闭环。

**触发条件：** T1 论文数 > 0，且 4.3 未选择“暂不剔除，只生成候选清单”。

```bash
# 对每篇 T1 论文：
python3 scripts/search_by_topic.py --citation-network <DOI> \
  --refs-limit 30 --cited-by-limit 50 \
  --existing-dois existing_dois.txt \
  --output expanded_<seq>.json
```

**评分闭环：**

1. 收集所有 `expanded_*.json` 并合并去重。
2. 与现有文献库做 DOI 去重，排除已有。
3. 对新增论文复用 4.4 五维度评分。
4. 对新增论文复用 4.5 Tier 分级。
5. T4 剔除，T1-T3 追加到检索文献表，标注 `source: openalex_citation_network`。
6. 记录到 `decision_log`：新增 X 篇（T1: a, T2: b, T3: c），种子 Y 篇。

**防爆炸规则：**

- 最多 10 篇种子论文。
- refs-limit 30 + cited-by-limit 50 = 每篇最多 80 条原始结果。
- 不做第二跳。

### 4.7. 饱和度曲线估算

> 基于全量 T1-T3 文献（原始 + 扩展）计算最终覆盖率。它只用于解释检索覆盖，不强制停止工作流。

**条件门：** T1-T3 文献数 ≥ 30 时执行；少于 30 篇时跳过，并标注 `insufficient_data`。

```bash
python3 scripts/discovery_curve.py \
  --results 检索文献表.md \
  --output saturation_snapshot.json
```

**解读输出：**

| coverage_estimate | CI 宽度 | Agent 判断 |
|:-----------------:|:-------:|-----------|
| ≥ 0.85 | < 0.15 | 覆盖良好 |
| ≥ 0.85 | > 0.15 | 信心不足 |
| 0.6-0.85 | - | 中等覆盖 |
| < 0.6 | - | 覆盖不足 |
| fit_failed | - | 无法拟合 |

### 4.8. 报告生成、索引清单与完成检查

4.8 统一处理最终交付物生成、`retrieval_index_manifest.json` 更新、文件存在性验证和 Step 5/6 转交。标准 Step 4 只有通过 4.8，才可声明完成。

**4.8.1 生成 `检索文献表.md`**

Agent 生成最终版 `.md` 文件，仅含 T1-T3（T4 进入排除说明）。顶部必须展示筛选依据，让用户回看“根据什么筛选”。

**必须保留的回溯字段：**

| 字段 | 说明 |
|------|------|
| `search_task_id` | 来自 Step 3 `search_tasks[].id` |
| `chapter_id` | 来自 Step 3 `search_tasks[].chapter_id` |
| `chapter_title` | 来自 Step 3 `search_tasks[].chapter_title` |
| `evidence_type` | review/method/experiment/data/standard/case |
| `source` | openalex/crossref/semantic_scholar/arxiv/pubmed/cnki/wanfang |
| `tier` | quick/standard/deep |
| `score` | 0-25 |
| `paper_tier` | T1/T2/T3 |
| `article_url` | 中文论文详情页 URL；英文可为空 |

**顶部必须包含：**

```md
## 检索概况
- 检索日期：YYYY-MM-DD
- Tier：quick / standard / deep
- 数据库：OpenAlex, Semantic Scholar, Crossref[, arXiv][, CNKI][, Wanfang Data][, PubMed]
- 原始检索：X 篇 -> 去重后 Y 篇 -> 评分后 Z 篇 (T1: a, T2: b, T3: c, T4: d 剔除)
- 引文扩展：+X 篇 (T1: a, T2: b, T3: c)，种子 Y 篇 [若触发]
- 最终文献：Z 篇 (T1-T3)
- 饱和度：coverage% (CI: ci_l%-ci_u%) [若执行]

## 筛选依据
- 研究问题依据：...
- 纳入规则：...
- 排除规则：...
- 评分维度与权重：...
- Tier 阈值：...
- 用户确认：CP-SCREENING-BASIS confirmed / adjusted / candidate-only
```

**4.8.2 生成 `中文论文元数据.json`（条件性）**

触发条件：检索文献表中存在 `source=cnki` 或 `source=wanfang` 的行。无中文论文时跳过并记录原因。

字段约束：

| 字段 | 必填 | 说明 |
|------|:--:|------|
| `title` | 是 | 论文标题原文 |
| `source` | 是 | `cnki` 或 `wanfang` |
| `source_id` | 是 | 内部稳定标识符，不得当作真实 DOI |
| `article_url` | 是 | 文章详情页 URL；无 URL 的行不写入 JSON |
| `doi` | 可选 | 仅填写真实 DOI |
| `authors` | 建议 | 中文作者数组 |
| `year` | 建议 | 发表年份 |
| `publication_title` | 建议 | 期刊/会议/学位授予单位等来源名称 |
| `abstract` | 可选 | 中文摘要 |
| `language` | 建议 | 固定为 `zh-CN` |

**4.8.3 生成 `.xlsx`、`.bib`、`检索报告.md/.pdf`**

```bash
python3 scripts/generate_retrieval_report.py 检索文献表.md

python3 scripts/generate_search_report.py \
  --results 检索文献表.md \
  --saturation saturation_snapshot.json \
  --output 检索报告.md
```

检索报告必须包含 4.3 的筛选依据、五维评分说明、Tier 分级、排除原因、引文扩展摘要、饱和度解释和下一步行动。综述或系统综述场景下，还必须显式写出 `screening rationale`（为什么保留当前文献）和 `exclusion buckets`（剔除条目的主要原因分类）。

**4.8.4 更新 `retrieval_index_manifest.json`**

Step 4 执行真实检索、导入已有文献表或更新 `workflow_search_results.json` 后，必须生成或更新 `retrieval_index_manifest.json`。

最小字段：

| 字段 | 说明 |
|------|------|
| `schema_version` | 固定为 `retrieval-index.v1` |
| `index_scope` | `search_results / metadata_cache / candidate_locator` |
| `source_artifacts` | `workflow_search_results.json`、`检索文献表.xlsx`、`文献库.bib` 等来源 |
| `search_task_ids` | 覆盖的 search task |
| `source_count` | 覆盖的检索源数量 |
| `record_count` | 结果记录数量 |
| `index_levels` | 如 `metadata_only / abstract_only / pdf_chunk_pending` |
| `sources` | OpenAlex / Crossref / Semantic Scholar / CNKI / Wanfang 等 |
| `reusable_for` | `step5_download_routing / step6_capability_index / step7_candidate_locator` |
| `authority` | `non_evidence / candidate_only` |
| `staleness` | `fresh / stale / unknown` |
| `rebuild_triggers` | search_tasks、筛选条件、route 或源结果变化时的重建条件 |
| `warnings` | 复用风险 |

边界：

- `retrieval_index_manifest.json` 可以帮助 Step 5 下载、Step 6 capability index 和 Step 7 候选证据定位。
- 它不能把检索命中、摘要、metadata cache 或候选 chunk 直接升级为正文证据。
- 它不直接进入正文、综述矩阵，也不能驱动引用审计结论。
- 评分、纳入/排除、Tier 分级仍以 Step 4 文献表和 `workflow_search_results.json` 为准。

**4.8.5 完成检查与转交**

核心交付物必须存在：

| # | 文件 | 若缺失 |
|---|------|--------|
| 1 | `workflow_search_results.json` | 回到检索结果标准化 |
| 2 | `检索文献表.md` | 回到 4.8.1 |
| 3 | `检索文献表.xlsx` | 回到 4.8.3 |
| 4 | `检索报告.md` | 回到 4.8.3 |
| 5 | `检索报告.pdf` | 回到 4.8.3 |
| 6 | `文献库.bib` | 回到 4.8.3 |
| 7 | `retrieval_index_manifest.json` | 回到 4.8.4 |

条件性交付物必须存在或有跳过说明：

| 文件 | 触发条件 | 若缺失 |
|------|----------|--------|
| `saturation_snapshot.json` | T1-T3 文献数 ≥ 30 | 回到 4.7 |
| `中文论文元数据.json` | 存在 CNKI/Wanfang 论文 | 回到 4.8.2 |

4.8 汇报时必须向用户展示：交付物路径、T1/T2/T3 数量、T4 排除数量、WARN/REJECT 数量、筛选依据确认状态、饱和度状态、下一步推荐入口。

---

## 7. 质量门槛 (Quality Gates)

> 以下检查项**全部通过**才能进入 4.8 完成。任一未通过 → 回到对应子步骤修复。

- [ ] 4.1 文献可信度验证已完成——每条保留文献均有 `verification_status` / `verification_confidence` / `verified_sources`；WARN/REJECT 均有 `warn_class`
- [ ] Step 3 `search_tasks` 已展开，每条结果保留 search_task_id/chapter_id/evidence_type/tier/source
- [ ] 4.2 DOI 去重已完成——无重复条目
- [ ] 4.3 筛选依据已向用户展示，且 `CP-SCREENING-BASIS` 已确认、调整或标注 candidate-only
- [ ] 4.4 五维度评分已完成——参考用户确认后的 `screening_basis`，并保留评分理由
- [ ] 4.5 Tier 分级已完成——T4 已剔除或进入排除说明
- [ ] 4.6 引文网络扩展已完成（若有 T1 触发）——新论文已评分+分级
- [ ] 4.7 饱和度曲线已生成（若 ≥ 30 篇）或已标注跳过原因
- [ ] 4.8 核心交付物已生成——含 `workflow_search_results.json`、`检索文献表.md/.xlsx`、`检索报告.md/.pdf`、`文献库.bib`、`retrieval_index_manifest.json`
- [ ] `检索文献表.md` 和 `检索报告.md` 均包含筛选依据、纳入规则、排除规则和 Tier 阈值

---

## 8. 收尾检查 (Closing Checks)

> 文件存在性和字段完整性由 4.8.5 统一处理。此处只保留运行记录、成功判据和失败分流，避免再次维护一套交付物清单。

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 评分偏差 → `.skill-state/error_log.md`
  - DOI 验证失败新模式 → `.skill-state/error_log.md`
  - 饱和度曲线拟合失败 → `.skill-state/error_log.md`
  - 引文扩展查询失败 → `.skill-state/error_log.md`
  - `generate_retrieval_report.py` 执行失败 → `.skill-state/error_log.md`

### 决策日志更新 🆕
- [ ] 评分权重调整？→ `.skill-state/decision_log.md`
- [ ] 筛选阈值修改？→ `.skill-state/decision_log.md`
- [ ] 🆕 引文扩展统计（新增 X 篇/种子 Y 篇）→ `.skill-state/decision_log.md`
- [ ] 🆕 最终交付物生成结果 → `.skill-state/decision_log.md`

### 成功判据
- [ ] 去重、评分、分级和缺口说明都已形成
- [ ] 可把当前结果安全交给 Step 5，而不是只给一个模糊“检索结束”结论

### 完成前必须确认
- [ ] 只有在去重结果、评分分级、缺口说明都齐全时，才能声称“检索完成”
- [ ] WARN/REJECT/待补查条目必须显式分流，不能混进“已完成文献库”

### 失败分流
- 结果太少/太偏：先按 `references/failure-triage.md` 判定是关键词层、数据源层还是筛选阈值层
- 中文元数据不足：先补 article_url/source_id，再决定是否进入下载
- 交付物缺失：回对应子步骤补产物，不直接转 Step 5

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **Pre-flight 检查失败**：运行 `python3 scripts/search_by_topic.py --preflight` 验证各 API 端点可达性
- **检索结果过少**：检查 AND 块数是否超过 4；回退到 L2/L3
- **评分偏差**：回顾 error_log 中的评分偏差记录
