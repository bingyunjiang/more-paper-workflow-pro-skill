# Step 4: 多渠道检索与相关性筛选

> 按 Step 3 方案的 L1→L2→L3 分层路由逐子课题检索，对结果进行 5 维度评分和 Tier 分级筛选。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，优先确认以下工件是否可用；若同时存在 JSON 和 Markdown，优先读取 JSON 机器源：

- [ ] `检索方案.json` / `检索方案.md` — Step 3 产出（`检索方案.json` 为机器执行源，`检索方案.md` 为人工审阅版）
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

Step 4 的直接入口不强制生成完整 7 件套。只有用户要求“完成标准 Step 4 交付”时，才按 7 件套质量门执行；如果用户只要求评分已有文献、生成报告或转入下载/Zotero，应输出当前可用产物和缺失项清单，不要求回跑 Step 3。

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

## 5. 标准输出 (Standard Outputs) 🔴 7 件套强制交付

> **🔴 所有 7 个产出必须全部生成，Step 4 才算完成。仅生成 .md 不算完成。**
> 所有产出仅含 **T1-T3 论文**（T4 已在 4d 剔除）。

| # | 输出 | 格式 | 生成工具 | 说明 |
|---|------|------|---------|------|
| 1 | 检索文献表 | .md | Agent 直接写入 | 最终版（原始+扩展），顶部含饱和度摘要，底部含 PRISMA-S 摘要 |
| 2 | 检索文献表 | .xlsx | `generate_retrieval_report.py` | openpyxl 生成，冻结表头+自动筛选+Tier 色标 |
| 3 | 检索报告 PDF | .pdf | `generate_search_report.py` → `md_to_pdf.py` | 检索方法论报告 PDF，面向审稿人/导师 |
| 4 | 文献库 | .bib | `generate_retrieval_report.py` | 全量 T1-T3，含 Tier/Score/influential_citations/子课题归属 |
| 5 | 饱和度曲线快照 🆕 | .json | `discovery_curve.py`（4f 步骤） | 文献覆盖率估算，含置信区间；< 30 篇时标注跳过 |
| 6 | **检索报告** 🆕 | .md | `generate_search_report.py`（4g 步骤） | **完整检索方法论报告**：检索范围→流水线→评分→分布→饱和度→行动建议 |
| 🆕 7 | **中文论文元数据 JSON** 🆕 | .json | Agent 直接写入（4g.1b 步骤） | 仅 source=cnki/wanfang 的行，供 Step 5 下载与 Step 6 Zotero 中文条目入库使用 |
| 🆕 8 | **workflow search results JSON** 🆕 | .json | `search_by_topic.py --export_workflow_json` | Step 4 机器主输出，供 Step 5/6/7 继续消费 |

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

---

## 6. 执行流程 (Execution Flow)

### 检索执行

按 Step 3 的 `search_tasks` 逐任务执行。每个任务都必须保留 `id`、`chapter_id`、`evidence_type`、`tier`、`source`，并写入后续检索文献表。

> 从本版开始，Step 4 的机器主输出是 `workflow_search_results.json`。`检索文献表.md/.xlsx`、`检索报告.md/.pdf`、`文献库.bib` 和 `中文论文元数据.json` 都应视为围绕该 JSON 生成的展示层、审阅层和交接层。

### 4a-4h 阶段输入输出表

| 阶段 | 输入 | 动作 | 输出 |
|------|------|------|------|
| 4a 引文验证 | 原始检索结果 | DOI/元数据校验；中文 source id 保护 | 验证后候选表 |
| 4b 去重合并 | 多源候选表 | DOI 归一化；无 DOI 用 title+author+year | 去重文献表 |
| 4c 五维评分 | 去重文献表 + search_tasks | 主题/方法/来源/时效/影响力评分 | 带 score 的文献表 |
| 4d Tier 分级 | 带 score 的文献表 | T1/T2/T3/T4 判定；T4 剔除 | T1-T3 文献表 |
| 4e 引文扩展 | T1 种子 | 单轮 1-hop 扩展 + 闭环评分 | 扩展后 T1-T3 文献表 |
| 4f 饱和度估算 | 全量 T1-T3 | 覆盖率估算 | `saturation_snapshot.json` |
| 4g 报告生成 | 最终 T1-T3 + 饱和度 | 生成 7 件套 | 标准交付文件 |
| 4h 完成检查 | 7 件套 | 文件存在性 + 字段完整性检查 | Step 5 handoff |

> **中文查询路由：** 查询含中文字符时，CNKI（L1 主检索）+ Wanfang Data（L2 补充）双路检索。

### 4a 文献可信度三态机制

> 4a 的目标是判断“文献条目本身是否可追溯、可入库、可引用候选”，不是判断它是否支撑某个 claim；claim 支撑关系留到 Step 7.7/7.11。

**三态定义：**

| 状态 | 判定 | 后续处理 |
|------|------|----------|
| `VERIFIED` | 可信公开源返回稳定 DOI/ID，且 title/year/authors 基本匹配 | 可进入 4b-4d，按评分与 Tier 参与筛选 |
| `VERIFIED_LOCAL` | CNKI/万方等中文源有 `source_id` 或 `article_url`，且 title/authors/year/publication_title 可追溯 | 可进入 4b-4d；不得因无 DOI 降级或剔除 |
| `WARN` | 存在真实不确定性：标题/年份/作者冲突、摘要缺失、来源弱、无稳定详情页、疑似重复、元数据残缺 | 保留进入人工审查队列；可评分，但写作时只能作背景/待补查线索 |
| `REJECT` | DOI 指向另一篇论文、关键元数据明显冲突、0 可追溯来源、明确撤稿或假条目 | 不进入最终 T1-T3 主表和 `文献库.bib`；只在检索报告异常清单中保留痕迹 |

**关键规则：**
1. `VERIFIED` 不要求至少 2 个来源一致。Crossref / OpenAlex / Semantic Scholar / PubMed / arXiv 任一可信源即可确认，只要稳定标识与核心元数据闭环。
2. 多源一致只提高 `verification_confidence=high`，不是进入 `VERIFIED` 的硬门槛。
3. 中文无 DOI 文献默认不是 `REJECT`。CNKI/万方条目只要有稳定详情页或 source_id，并能追溯标题、作者、年份、来源，即标为 `VERIFIED_LOCAL`。
4. WARN 是“需要人审或补证据”，不是“低质量文献”。中文核心、会议论文、新预印本和数据库覆盖弱领域不得因单源而自动降为 WARN。
5. 撤稿或表达关注应优先标记 `REJECT`；如只是 corrigendum/erratum，按具体影响写入 `warn_class`。

**4a 必写字段：**

| 字段 | 值域/示例 | 说明 |
|------|-----------|------|
| `verification_status` | `VERIFIED` / `VERIFIED_LOCAL` / `WARN` / `REJECT` | 文献条目可信度三态 |
| `verification_confidence` | `high` / `medium` / `low` | 多源一致或强来源为 high；单可信源通常 medium；弱来源/残缺为 low |
| `warn_class` | `metadata-mismatch`, `missing-abstract`, `weak-source`, `no-stable-url`, `legacy-unverified`, `retracted` | 仅 WARN/REJECT 必填；VERIFIED 可空 |
| `verified_sources` | `crossref`, `openalex`, `semantic_scholar`, `cnki`, `wanfang` | 实际确认过的来源，多个用逗号分隔 |

`检索文献表.md` 主表必须包含上述 4 列；`generate_retrieval_report.py` 会将其写入 Excel 和 BibTeX note，供 Step 6/7 继续读取。

### CHECKPOINT W — CP-CITATION-WARN

当 4a 产生的异常会改变最终 T1-T3 纳入策略、下游关键引用策略，或涉及 `REJECT` 条目的保留/剔除处置时，才输出 warning checkpoint。仅把 `WARN` 条目列入背景性候选、综述矩阵候选、待补查清单或异常清单，不触发 checkpoint。

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

### 英文源执行规则（公开 API，无需认证，直接跑）

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

### 中文源 preflight + 认证（仅中文查询触发）

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

### L2 Crossref 🆕（DOI/出版社元数据补充，Deep tier 必跑）

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

### L1 CNKI 🆕

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

### L2 Wanfang Data

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

### Tier-driven 检索参数 🆕

> 优先读取 `search_tasks[].tier`；若缺失，则按 Step 3 顶层 `tier`、Step 1 顶层 `tier`、Step 1 `search_tier.tier`、默认 `standard` 的顺序回退。

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

> **CNKI + 万方备注** 🆕：无真实 DOI 的论文使用 `cnki.{title_hash}` 或 `wanfang.{title_hash}` 作为标识符。
> 这些条目不进入 Crossref 验证（跳过步骤①），直接进入评分阶段。
> 若有真实 DOI（`10.xxxx/...` 格式），则正常验证。
> `cnki.xxx` / `wanfang.xxx` 是内部 source id，不是真实 DOI；后续导入 Zotero 时不得写入 DOI 字段，只能写入 `Extra` 或等价元数据字段。
>
> **中文论文文章 URL 保留** 🆕：中文论文（source=cnki/wanfang）在检索结果中必须保留**文章详情页 URL**，
> 写入检索文献表的 `文章链接` 列。此 URL 是 Step 5 Chinese CDP Round 下载的入口。
> CNKI 检索结果中的 `briefDl_D` 链接和 Wanfang 结果中的详情页链接均需保留。
> 若无可用 URL，标注 `⚠️ 缺文章页URL`，该论文将无法在 Step 5 自动下载。

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

**评分回溯规则：**

- 主题匹配度必须参考 `search_tasks[].question_to_answer`
- 方法学严谨性必须参考 `search_tasks[].evidence_type`，例如 `experiment` 任务更重视实验/对照证据
- 同一论文服务多个 `search_task` 时，保留多重归属，不覆盖原归属
- 评分理由中至少写明一个匹配词或匹配证据，避免黑箱分数

**证据层级提示（解释层增强，不改核心状态机）：**

- `VERIFIED / VERIFIED_LOCAL / WARN / REJECT` 仍是 Step 4 的核心信任状态，不替换。
- 在评分说明和检索报告中，应补充“证据层级说明”，帮助用户区分：
  - **高相关** 不等于 **高证据等级**
  - **高证据等级** 不等于 **与当前 research question 高匹配**
- 系统综述 / 方法学敏感任务下，检索报告应额外说明：
  - 哪些条目适合作背景综述
  - 哪些条目适合作方法依据
  - 哪些条目仅能作低风险补充

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

### 4g: 生成检索报告（强制全套交付） 🆕

> **🔴 强制规则**：本步骤为阻塞式步骤。在所有检索、评分、扩展、饱和度分析完成后，**必须**生成以下 **5 个文件 + 1 个饱和度快照 + 1 个中文 JSON**。
> **仅生成 .md 不算完成 Step 4。** 4h 完成检查点会逐一验证文件存在。

**4g.1 生成 .md 检索文献表**（Agent 直接写入）

Agent 生成最终版 .md 文件，**仅含 T1-T3**（T4 已剔除），格式如下：

**必须保留的回溯字段：**

| 字段 | 说明 |
|------|------|
| search_task_id | 来自 Step 3 `search_tasks[].id` |
| chapter_id | 来自 Step 3 `search_tasks[].chapter_id` |
| chapter_title | 来自 Step 3 `search_tasks[].chapter_title` |
| evidence_type | review/method/experiment/data/standard/case |
| source | openalex/crossref/semantic_scholar/arxiv/pubmed/cnki/wanfang |
| tier | quick/standard/deep |
| score | 0-25 |
| paper_tier | T1/T2/T3 |
| article_url | 中文论文详情页 URL；英文可为空 |

**.md 顶部 — 饱和度摘要**：
```
## 检索概况
- 检索日期：YYYY-MM-DD
- Tier：quick / standard / deep
- 数据库：OpenAlex, Semantic Scholar, Crossref[, arXiv][, CNKI][, Wanfang Data][, PubMed]
- 原始检索：X 篇 → 去重后 Y 篇 → 评分后 Z 篇 (T1: a, T2: b, T3: c, T4: d 剔除)
- 引文扩展：+X 篇 (T1: a, T2: b, T3: c)，种子 Y 篇 [若触发]
- 最终文献：Z 篇 (T1-T3)
- 饱和度：coverage% (CI: ci_l%–ci_u%) [✅ 覆盖良好 / ⚠️ 中等 / ❌ 不足]
```

**.md 正文 — 检索文献表**：
| search_task_id | chapter_id | evidence_type | DOI/source_id | 标题 | 作者 | 年份 | 期刊/会议 | 来源 | 评分 | Tier | 引用数 | 影响力引用 | 旗标 | 文章链接 | 摘要 |
|----------------|------------|---------------|---------------|------|------|------|-----------|------|------|------|--------|------------|------|----------|------|
| S1 | ch2 | method | 10.1016/... | Topology optimization... | Zhang Y et al. | 2024 | Int J Heat Mass Transfer | openalex | 20 | T1 | 45 | 12 | — |  | This paper presents a novel topology optimization approach... |

**.md 底部 — PRISMA-S 摘要**（可折叠区域）：
- 7 项已执行：数据库、多源、策略、日期、记录数、去重、记录管理
- 9 项未执行：标注原因"非本自动化检索范围"

**4g.1b 生成 `中文论文元数据.json`** 🆕

> 触发条件：检索文献表中有任意 `source=cnki` 或 `source=wanfang` 的行。无中文论文时跳过此步。

Agent 从检索文献表中提取中文论文行，写入 `中文论文元数据.json`。该文件不仅供 Step 5 下载使用，也作为 Step 6 中文 Zotero 条目入库的最小元数据来源：

```json
[
  {
    "title": "中文论文标题",
    "source": "cnki",
    "source_id": "cnki.a1b2c3d4...",
    "article_url": "https://kns.cnki.net/kcms2/article/abstract?...",
    "doi": "",
    "authors": ["张三", "李四"],
    "year": "2024",
    "publication_title": "中文期刊名",
    "abstract": "中文摘要",
    "language": "zh-CN"
  },
  {
    "title": "另一篇中文论文",
    "source": "wanfang",
    "source_id": "wanfang.e5f6g7h8...",
    "article_url": "https://www.wanfangdata.com.cn/details/...",
    "doi": "10.xxxx/real.doi..."
  }
]
```

**字段约束：**

| 字段 | 必填 | 说明 |
|------|:--:|------|
| `title` | ✅ | 论文标题原文 |
| `source` | ✅ | `"cnki"` 或 `"wanfang"`（小写） |
| `source_id` | ✅ | 内部稳定标识符，如 `cnki.xxx` / `wanfang.xxx`；不得当作真实 DOI |
| `article_url` | ✅ | 文章详情页 URL；**无可用 URL 的行不写入 JSON**（写入也无法下载，不如提前排除） |
| `doi` | 可选 | 仅填写真实 DOI（`10.xxxx/...`）；无真实 DOI 时留空 |
| `authors` | 强烈建议 | 中文作者数组；缺失会导致 Zotero 引用条目不可用 |
| `year` | 强烈建议 | 发表年份 |
| `publication_title` | 强烈建议 | 期刊/会议/学位授予单位等来源名称 |
| `abstract` | 可选 | 中文摘要，用于评分、归类和综述矩阵 |
| `language` | 建议 | 固定为 `zh-CN` |

> **设计意图**：CNKI/万方中文文献多数无法通过 DOI 直接导入 Zotero。`中文论文元数据.json` 必须保存足够的中文元数据，后续 Step 6 通过 CSL JSON / Zotero update 方式创建完整中文条目；`cnki.xxx` / `wanfang.xxx` 只作为 `source_id` 写入 Zotero `Extra`，不写入 DOI 字段。

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

**若触发综述 / 系统综述分支，检索报告需额外结构化说明：**

- `screening rationale`：为什么保留当前文献
- `exclusion buckets`：剔除条目的主要原因分类

目标是回答“为什么留下这些文献”，而不只是“检到了这些文献”。

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
  "source_breakdown": {"openalex": 65, "semantic_scholar": 30, "crossref": 25, "wanfang": 18, "cnki": 22},
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

> 饱和度快照 `saturation_snapshot.json` 已生成，饱和度分析内容已完整内嵌至 `检索报告.md` 第 7 章。确认文件存在。

```
[ -f saturation_snapshot.json ] && echo "✅ saturation_snapshot.json" || echo "⚠️ 缺失（可能 < 30 篇）"
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
# 饱和度快照（条件性：≥ 30 篇时必须存在）
if [ -f "saturation_snapshot.json" ]; then
  echo "✅ saturation_snapshot.json（饱和度内容已内嵌至 检索报告.md 第 7 章）"
else
  echo "⚠️ saturation_snapshot.json 不存在（可能因 < 30 篇未触发 4f）"
fi
# 中文论文元数据（条件性：有 CNKI/万方论文时必须存在）
if [ -f "中文论文元数据.json" ]; then
  echo "✅ 中文论文元数据.json"
else
  echo "⚠️ 中文论文元数据.json 不存在（若无中文论文可跳过）"
fi
```

**4h.2 汇报与记录**

- [ ] 向用户展示 5 交付物清单 + 文件路径 + 关键数字（总数/T1-T3 分布/饱和度）
- [ ] 更新 `.skill-state/decision_log.md`（引文扩展统计 + 最终文献分布）
- [ ] 更新 `.skill-state/error_log.md`（本轮新出现的错误/偏差）

**4h.3 转交 Step 5**

仅在 **7 交付物全部验证通过** 后，输出以下转交信息：

> **✅ Step 4 完成 → 下一步 Step 5：开始批量下载。**
>
> 交付物：
> - `检索文献表.md` — 文献检索表（Z 篇 T1-T3）
> - `检索文献表.xlsx` — 可筛选排序的 Excel 版
> - `检索报告.pdf` — 完整检索方法论报告 PDF（面向审稿人/导师）
> - `文献库.bib` — BibTeX 文献库（含 Tier/Score/influential_citations）
> - `检索报告.md` — 完整检索方法论报告（8 章节，面向审稿人）
> - `saturation_snapshot.json` — 饱和度曲线快照 [若 ≥ 30 篇]
> - `中文论文元数据.json` — 中文论文结构化数据 [若有 CNKI/Wanfang 论文] 🆕
>
> 当前文献库共 X 篇（T1: a | T2: b | T3: c，含引文扩展 Y 篇）。饱和度 Z%。
> 中文论文：N 篇（CNKI: a | Wanfang: b）。
> 按出版商自动路由 → Sci-Hub → SD CDP → IEEE CDP → Generic CDP → Chinese CDP。

---

## 7. 质量门槛 (Quality Gates) 🔴 阻塞式

> 以下检查项**全部通过**才能进入 4h 完成。任一未通过 → 回到对应子步骤修复。

- [ ] 4a 文献可信度验证已完成——每条保留文献均有 `verification_status` / `verification_confidence` / `verified_sources`；WARN/REJECT 均有 `warn_class`
- [ ] Step 3 `search_tasks` 已展开，每条结果保留 search_task_id/chapter_id/evidence_type/tier/source
- [ ] 4b DOI 去重已完成——无重复条目
- [ ] 4c 五维度评分已完成——参考了 rcs-rubric 定性启发
- [ ] 4d Tier 分级已完成——T4 已剔除
- [ ] 🆕 4e 引文网络扩展已完成（若有 T1 触发）——新论文已评分+分级
- [ ] 🆕 4f 饱和度曲线已生成（若 ≥ 30 篇）
- [ ] 🔴 4g.1 `.md` 检索文献表已写入——含饱和度+PRISMA-S 摘要+可信度字段，仅含 T1-T3
- [ ] 🔴 4g.2 `generate_retrieval_report.py` 已成功执行——`.xlsx` + `.bib` 已生成
- [ ] 🔴 4g.3 饱和度快照 `saturation_snapshot.json` 存在（若 ≥ 30 篇）或已标注跳过原因

---

## 8. 收尾检查 (Closing Checks)

> 4g 检索报告和 4h 完成步骤已涵盖大部分收尾工作。此处做最终核对。

### 产出完整性 🔴 逐一确认

在执行 4h 汇报之前，必须用 `ls` 或文件存在性检查确认以下 **7 个文件** 全部存在：

| # | 文件 | 检查命令 | 若缺失 |
|---|------|---------|--------|
| 1 | `检索文献表.md` | `[ -f "检索文献表.md" ]` | 回到 4g.1 |
| 2 | `检索文献表.xlsx` | `[ -f "检索文献表.xlsx" ]` | 回到 4g.2 |
| 3 | `检索报告.pdf` | `[ -f "检索报告.pdf" ]` | 回到 4g.2b |
| 4 | `文献库.bib` | `[ -f "文献库.bib" ]` | 回到 4g.2 |
| 5 | `检索报告.md` | `[ -f "检索报告.md" ]` | 回到 4g.2b |
| 6 | `saturation_snapshot.json` | `[ -f "saturation_snapshot.json" ]` | 若 ≥ 30 篇回到 4f；若 < 30 篇标注跳过 |
| 🆕 7 | `中文论文元数据.json` | `[ -f "中文论文元数据.json" ]` | 若有中文论文回到 4g.1b；若无中文论文标注「无中文论文」跳过 |

**🔴 仅当以上 7 个检查项全部通过（或 #6/#7 合理跳过）后，才能进入 4h.3 转交 Step 5。**

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
