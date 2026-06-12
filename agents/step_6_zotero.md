# Step 6: Zotero 文库管理

> Step 6 负责把 Step 4 的 BibTeX 条目、Step 2 的论文大纲、Step 5/其他来源的 PDF 附件池整理成一个可审阅、可恢复、可追溯的 Zotero 文库整理计划，并尽可能完成低风险 Zotero 写入。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，优先确认当前任务需要哪些输入；若缺少标准链路产物，则在本 Step 内生成 plan-only 映射、只读扫描结果或缺口报告，而不是要求用户回跑前序步骤：

- [ ] `agents/step_2_outline.md` — 大纲关键词（章节结构 + 术语映射表；可缺失，缺失时允许从现有集合名/用户目录反推最小结构）
- [ ] `agents/step_4_search_score.md` — 检索筛选结果与 `文献库.bib` 生成规则（可缺失，缺失时允许从 BibTeX/JSON/现有 Zotero 反推 plan-only）
- [ ] `agents/step_5_download.md` — Step 5 下载 PDF（paper-temp/）及后续补下载入口（可缺失，只影响附件来源说明）
- [ ] `references/zotero-structure-template.md` — Zotero 架构示例
- [ ] `references/zotero-outline-mapping.md` — 文献与集合对齐思路
- [ ] `references/zotero-output-contract.md` — 🆕 JSON + Markdown 双工件输出契约
- [ ] `references/zotero-entry-modes.md` — 🆕 Step 6 direct-entry 模式
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则
- [ ] `.skill-state/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 依据 Step 2 论文大纲生成 Zotero 集合架构（6a）
- 依据 Step 4 `文献库.bib` 和 6a 架构生成文献-集合对照表（6b）
- 通过 Zotero MCP 创建 Zotero 集合并检查架构一致性（6c）
- 将 PDF 附件池中的文件纳入附件状态判断，生成安全的附件处理策略（6d）

---

## 3. 不适用任务 (Non-applicable Tasks)

- 论文写作 → 路由到 `agents/step_7_writing.md`
- 文献综述矩阵 → 路由到 `agents/step_7_writing.md`
- 目标期刊风格学习 → 路由到 `agents/step_7_writing.md`
- PDF 下载 → 路由到 `agents/step_5_download.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 大纲关键词 / 章节结构 | Step 2 / 用户已有目录 / 当前 Step 反推 | `大纲关键词.md`、目录、草稿、集合层级 | 规划集合时推荐其一 |
| 筛选后文献库 | Step 4 / 用户已有文献库 | `文献库.bib`、workflow JSON、CSL JSON | 计划导入时推荐其一 |
| PDF 附件池 | Step 5 / 原有文件 / 后续补下载 | `paper-temp/`、用户指定目录、补下载目录 | 附件规划时推荐 |
| Zotero 模式选择 | 用户确认 | `local` / `cloud` / `skip` | ✅ |
| Zotero MCP 可写连接 | 环境配置 | MCP 工具 | 仅真实写入时必选 |

> 标准链路下推荐使用 Step 4 生成的 `文献库.bib`。但 Step 6 不把它当成唯一合法入口：若用户已有 Zotero 文库、已有 BibTeX/CSL JSON、已有 workflow search results JSON、已有 PDF 目录或只想整理现有集合，也可直接进入本步骤。

**工件读取优先级：**

从本版开始，Step 6 对上游输入的优先顺序为：

1. `workflow_search_results.json`
2. `文献库.bib`
3. `文献-Zotero架构对照.json`
4. 对应 Markdown 审阅版

如果 JSON 和 Markdown 同时存在，以 JSON 为准；Markdown 仅作为人工审阅和解释层。

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| `zotero-架构.md` | Markdown | 基于论文大纲生成的 Zotero 集合结构 |
| `zotero-架构.json` | JSON | 供 MCP 递归创建集合使用的树结构 |
| `文献-Zotero架构对照.md` | Markdown | 人类审阅版映射表，可截断长字段 |
| `文献-Zotero架构对照.json` | JSON | 机器执行源，所有字段完整，禁止截断 |
| `pdf-附件池索引.json` | JSON | 多来源 PDF 的完整路径、来源、匹配状态 |
| Zotero 集合 | Zotero | 与 `zotero-架构.json` 一致的集合树 |
| Zotero 条目 + PDF 附件状态 | Zotero / JSON | 元数据可低风险导入；PDF 附件默认只判断状态，不直接挂载 |

---

## 6. 执行流程 (Execution Flow)

### 6.0：Zotero MCP 写入能力检查

执行任何 Zotero 写操作前，先确认 MCP 工具可用且具备写入能力：

```bash
python3 scripts/setup_zotero.py --install --target auto
python3 scripts/setup_zotero.py --smoke-test
```

**必须确认：**
1. Zotero 桌面端已运行，且本地文库可访问。
2. `zotero_create_collection`、`zotero_add_by_bibtex`、`zotero_add_from_file`、`zotero_manage_collections` 等写入工具可用。
3. 如果当前本地 API 配置只读，必须切换到可写 MCP 配置（Web API / hybrid / 上游支持的本地写入模式），否则不能执行 6c/6d。

**如果用户选择跳过 Zotero 写入，或当前 MCP 不可写：**
1. 只执行 6a 和 6b。
2. 在 `文献-Zotero架构对照.md/json` 中把集合创建、条目导入、PDF 附件标记为「后续手动处理」。
3. 缺文件不是致命错误；应在 JSON 顶层写入 readiness、blocking_missing、nonblocking_missing、warnings 和 recommended_next_step。

**独立入口规则：**
如果用户已有 Zotero 文库、已有 PDF 目录、已有 BibTeX/CSL JSON 或只想整理某个集合，可直接从 Step 6 开始，不要求补跑 Step 1-5。Agent 可先读取 Zotero、生成对照表、检查重复、扫描 PDF、生成写入计划；只有即将实际修改 Zotero 这个外部持久状态时，才触发 `CP-ZOTERO-WRITE`。

**Step 6 入口第一问：**

进入 Step 6 后，必须先确认 Zotero 模式：`local` / `cloud` / `skip`。该选择决定后续读写能力和附件策略；不得静默默认 cloud。

| 模式 | 允许动作 | 禁止/限制 |
|------|----------|-----------|
| `local` | 读取本地 Zotero、生成计划、在确认后写入集合/条目、尽可能处理附件 | 写入前仍需 `CP-ZOTERO-WRITE` |
| `cloud` | 元数据规划、Web API 可用范围内的条目/集合操作 | 通常不能自动挂载本地 PDF，必须提示附件限制 |
| `skip` | 只生成 `文献-Zotero架构对照.md/json` 和 `pdf-附件池索引.json` | 不调用 Zotero 写入工具 |

**Direct-entry input contract：**

| 可接受输入 | 最小处理 | 输出 |
|------------|----------|------|
| `文献库.bib` + PDF 目录 | 生成 plan-only 对照与附件索引 | `文献-Zotero架构对照.*`、`pdf-附件池索引.json` |
| workflow search results JSON | 转为 Zotero plan 候选，中文保留 source_id/article_url | plan-only JSON |
| 已有 Zotero 集合 key/路径 | 只读扫描集合、条目、附件状态 | 最小映射和缺口报告 |
| CSL JSON / 中文论文元数据 | 中文条目 plan，Extra 写 source_id，不伪造 DOI | 中文入库计划 |
| 只有 PDF 文件夹 | 扫描附件池，按文件名/元数据尝试匹配 | PDF index + 未匹配清单 |

`scripts/build_zotero_plan.py` 是 plan-only 入口：可在缺少部分输入时继续生成 readiness、blocking_missing、nonblocking_missing、warnings、recommended_next_step。它不调用 Zotero MCP，不修改 Zotero 文库。

**双工件契约：**

无论从哪种入口进入，只要 Step 6 生成了正式整理结果，默认应同时产出：

- 一个可机读 JSON
- 一个可人工审阅 Markdown

缺输入时也应优先产出 plan-only 双工件，而不是只给口头建议。

### CHECKPOINT W — CP-ZOTERO-WRITE（Zotero 外部状态写入确认）

`CP-ZOTERO-WRITE` 不是 Step 6/7 的入口门，也不是读取 Zotero 前的许可门。它只表示：执行任何会改变 Zotero 文库的写操作前，必须输出 checkpoint 块并等待用户明确确认写入范围。只读操作、计划生成、查重和 dry-run 不触发本 checkpoint。

```md
## CHECKPOINT W — CP-ZOTERO-WRITE

entry_mode: normal_chain|direct_entry|resume|repair|partial_artifact
status: confirmed_by_workflow|satisfied_by_user_artifact|satisfied_by_agent_reconstruction
blocks_next: actual Zotero write operations only
must_confirm: true

summary:
- 即将创建/复用的集合数量
- 即将导入、移动或更新的条目数量
- WARN 待审项、REJECT 排除项和附件动作风险

does_not_block:
- 读取 Zotero 集合/条目/笔记/附件
- 生成 `文献-Zotero架构对照.md/json`
- 扫描 PDF 附件池
- 查重报告和写入 dry-run

required_confirmation:
- “确认 CP-ZOTERO-WRITE”
```

---

### 6a：根据 Step 2 大纲生成 Zotero 架构

输入：`大纲关键词.md`

```bash
python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md --json zotero-架构.json

# 可选：显式覆盖根集合名
python3 scripts/organize_zotero.py 大纲关键词.md \
  --root-name "自定义根集合名" \
  --output zotero-架构.md --json zotero-架构.json
```

输出：
- `zotero-架构.md`：给用户审阅的集合结构和标签方案
- `zotero-架构.json`：给 6c MCP 自动创建集合使用的树结构

**质量要求：**
- 根集合应尽量明确；标准链路下优先从 `大纲关键词.md` 中解析论文标题，direct-entry 时也允许从用户目录、现有 Zotero 根集合、项目名或用户指定名称中反推。
- 根集合解析优先级：
  1. `## 论文标题` 下方第一段非空文本。
  2. `论文题目：xxx`、`题目：xxx`、`标题：xxx`、`研究主题：xxx`。
  3. YAML/frontmatter 中的 `title`。
  4. 一级标题，但必须排除 `论文大纲与关键词`、`论文大纲`、`大纲关键词` 等模板标题。
  5. 全部失败时回退为 `论文文献库`。
- 用户显式传入 `--root-name` 时，以用户指定为准。
- 一级集合应对应论文主要章节或研究方向。
- 二级/三级集合应对应子问题、方法路线、证据类型或关键主题。
- 不为单篇论文创建集合；单篇论文归属通过条目、标签和附件体现。
- 架构生成后先向用户展示概要，确认后再进入 6b。

---

### 6b：生成文献-Zotero架构对照

输入：
- `文献库.bib`（Step 4 筛选后的 BibTeX 文献库）
- `中文论文元数据.json`（如存在中文文献；兼容旧名 `chinese_papers.json` / `chinese_metadata.json`）
- `zotero-架构.md`
- `zotero-架构.json`
- PDF 附件池目录：Step 5 下载目录（通常为 `paper-temp/`）、项目原有 PDF 目录、用户后续补下载目录

推荐命令：

```bash
python3 scripts/build_zotero_plan.py \
  --bib 文献库.bib \
  --structure zotero-架构.json \
  --pdf-dir paper-temp/ \
  --chinese 中文论文元数据.json \
  --output 文献-Zotero架构对照.json \
  --review 文献-Zotero架构对照.md \
  --pdf-index pdf-附件池索引.json
```

输出：
- `文献-Zotero架构对照.md`：人类审阅版，可为排版截断标题/摘要/URL/PDF 文件名等长字段
- `文献-Zotero架构对照.json`：机器执行源，所有字段必须完整保留，禁止截断
- `pdf-附件池索引.json`：记录所有候选 PDF 的完整路径、来源、匹配结果

**核心任务：**
结合 BibTeX 条目的 title / author / year / doi / abstract / note 字段，与 `zotero-架构` 的集合和标签方案匹配，生成每篇文献应该进入哪个 Zotero 集合的对照表。

**PDF 附件池规则：**
- 不假设 PDF 只来自 Step 5。
- 附件池可包含：Step 5 下载的 PDF、用户项目中原已有 PDF、后续补下载 PDF、手动整理目录中的 PDF。
- 执行 6b 前先扫描附件池，生成 `pdf-附件池索引.json`。
- 每个 PDF 记录完整路径、文件名、来源目录、文件大小、可提取标题/DOI/source_id（如能提取）、匹配状态。
- 同名或疑似重复 PDF 不删除，标记为 duplicate_candidate，等待人工确认或按匹配置信度选择。

**Markdown 审阅表推荐字段：**

| 字段 | 说明 |
|------|------|
| 序号 | 稳定编号 |
| citekey | BibTeX citation key |
| 标题 | BibTeX title |
| source/source_id | `openalex` / `crossref` / `cnki` / `wanfang`；中文条目必须有 `cnki.xxx` / `wanfang.xxx` |
| DOI/URL | 真实 DOI 或详情页 URL；中文合成 ID 不得放入 DOI |
| Tier/Score | 来自 BibTeX note 字段 |
| 可信度状态 | 来自 Step 4 的 `verification_status` / `verification_confidence` / `warn_class` / `verified_sources` |
| 推荐集合路径 | 如 `论文文献库 / 2-方法 / P1-D1 数值模拟` |
| 推荐标签 | 来自 6a 标签方案，可多值 |
| 条目导入方式 | 英文 DOI / 英文 BibTeX / 中文 CSL JSON / 手动补全 |
| 匹配理由 | 关键词、摘要、子课题、note 字段依据 |
| PDF 文件 | Step 5 下载到的本地 PDF 文件名或「未找到」 |
| 导入状态 | 待导入 / 已导入 / 待人工确认 |
| 附件状态 | 待关联 / 已关联 / 缺 PDF |

**JSON 执行源最低字段：**
```json
{
  "schema_version": "1.2",
  "root_collection": "从大纲解析出的论文标题",
  "readiness": "complete|partial|blocked",
  "can_continue": true,
  "blocking_missing": [],
  "nonblocking_missing": [],
  "warnings": [],
  "recommended_next_step": "",
  "records": [
    {
      "record_id": "stable-001",
      "citekey": "zhang2024_example",
      "source": "cnki",
      "source_id": "cnki.a1b2c3d4",
      "language": "zh-CN",
      "title": "完整标题，不截断",
      "authors": ["张三", "李四"],
      "year": "2024",
      "publication_title": "完整期刊名/会议名/学位授予单位",
      "doi": "",
      "article_url": "https://完整详情页URL",
      "abstract": "完整摘要，不截断",
      "tier": "T1",
      "score": "22",
      "subtopic": "S1: 子课题名称",
      "verification_status": "VERIFIED_LOCAL",
      "verification_confidence": "medium",
      "warn_class": "",
      "verified_sources": "cnki",
      "collection_path": ["论文文献库", "2-方法", "P1-D1 数值模拟"],
      "collection_key": "",
      "tags": ["P1-D1", "数值模拟"],
      "import_method": "csl_json",
      "pdf_path": "/完整/path/to/file.pdf",
      "pdf_source": "existing|step5|supplemental|manual",
      "pdf_match_confidence": "high|medium|low|none",
      "matched_pdf_candidates": [],
      "zotero_item_key": "",
      "import_status": "pending|ready|metadata_incomplete|manual_required",
      "attachment_status": "missing|found|already_attached|duplicate_candidate|conflict|unknown|rejected",
      "attachment_action": "skip|manual_drag|add_from_file_then_merge|wait_for_attach_tool|none",
      "existing_attachment_keys": [],
      "notes": ""
    }
  ]
}
```

> `文献-Zotero架构对照.md` 只供人工审阅；6c/6d 的集合创建、条目导入、PDF 附件关联、状态回写必须以 `文献-Zotero架构对照.json` 为准。

**匹配规则：**
1. 英文/国际文献：优先使用真实 DOI 精确匹配 PDF 文件名、下载日志或文献表。
2. CNKI/万方中文文献：不得依赖 DOI；优先使用 `source + source_id`、`article_url`、标题规范化匹配 PDF 和 Zotero 条目。
3. DOI 缺失时，使用标题规范化匹配；标题仍不可靠时标记为「待人工确认」。
4. 优先依据 BibTeX `note` 中的 `subtopic`、`Tier`、`Score` 字段匹配集合。
5. 其次依据 title / abstract / keywords 与 `zotero-架构.md` 的集合名、标签说明匹配。
6. 不确定归属时不要硬分配，放入 `待确认` 集合或在对照表中标注「待人工确认」。

**中文文献元数据规则：**
- `cnki.xxx` / `wanfang.xxx` 是内部 source id，不是真实 DOI。
- Zotero 的 DOI 字段只能填写真实 `10.xxxx/...` DOI。
- 无真实 DOI 的中文条目必须把 `source_id`、`source`、`article_url`、Tier、Score、subtopic 写入 Zotero `Extra` 或等价字段。
- 中文条目必须优先从 `中文论文元数据.json` 读取 authors、year、publication_title、abstract、language，不能只依赖 `文献库.bib`；旧名 `chinese_papers.json` / `chinese_metadata.json` 仅作为兼容输入。

**质量要求：**
- 每个 BibTeX 条目必须出现在对照表中。
- 每个 T1/T2/T3 条目必须有推荐集合路径。
- 每个条目必须保留 Step 4 的可信度字段；旧 BibTeX 缺失时标记 `verification_status=WARN`、`warn_class=legacy-unverified`，但不中断。
- `verification_status=REJECT` 的记录不得进入 Zotero 写入队列；只保留在异常清单或补查候选中。
- `verification_status=WARN` 的记录可进入计划表，但必须保留 `warn_class`，写入前作为待审项向用户展示。
- 中文条目必须有 `source_id` 和 `article_url`；缺作者/年份/来源名称时必须列入「中文元数据待补全」清单。
- 缺真实 DOI、缺 PDF、重复条目、无法判定集合的文献必须单独列出。
- `文献-Zotero架构对照.json` 中所有用于机器执行的字段禁止截断；Markdown 中的截断不得反向污染 JSON。
- 6c/6d 所有 Zotero 写入操作都以 `文献-Zotero架构对照.json` 为准。
- `scripts/build_zotero_plan.py` 只生成中间产物，不调用 Zotero MCP、不修改 Zotero 文库。
- 缺 `文献库.bib` 时输出 `readiness=blocked`；缺 `zotero-架构.json` 时允许进入 `待确认集合`；缺 PDF 目录时写 warning，不中断。

---

### 6c：通过 Zotero MCP 创建集合并检查架构一致性

输入：`zotero-架构.json`

**创建流程（递归，每个子集合的 `parent_collection` 传直接父级 key）：**

```
# Step 1 — 幂等性检查
zotero_search_collections(query="{zotero-架构.json 中的根集合名}")
  → 如果已存在，询问用户：跳过 / 补充缺失 / 新建带日期后缀的根集合

# Step 2 — 创建或复用根集合
zotero_create_collection(name="{zotero-架构.json 中的根集合名}")
  → root_key

# Step 3 — 按 zotero-架构.json 递归创建子集合
zotero_create_collection(name="1-基础", parent_collection=root_key)
  → l1_key

zotero_create_collection(name="P0-A1 基础理论", parent_collection=l1_key)
  → l2_key

# Step 4 — 验证
zotero_get_collections()
  → 与 zotero-架构.json 逐级对照
```

**关键规则：**
- 创建集合时只以 `zotero-架构.json` 中的根集合名为准，不再硬编码 `论文文献库`。
- `parent_collection` 始终传直接父级的 8 位 key，不能偷懒传根 key。
- 每创建或复用一个集合，立即记录 `collection_path → collection_key` 映射。
- 集合已存在时复用 key；不得创建同名重复集合。
- 中途中断后，下次执行必须能通过幂等性检查续跑。

**一致性检查：**
- 根集合名称一致。
- 每一级子集合数量一致。
- 每个集合的父子关系一致。
- `文献-Zotero架构对照.json` 中出现的所有推荐集合路径都能找到对应 Zotero collection key。
- 如发现缺失、多余、错层集合，先报告并征求用户确认，再补建或调整。

**完成后报告：**
- 新建集合数、复用集合数、失败集合数。
- 根集合 key。
- `collection_path → collection_key` 映射摘要。
- 架构一致性结论：通过 / 有差异但已修复 / 仍需人工处理。

---

### 6d：导入条目并生成/执行附件处理策略

输入：
- `文献库.bib`
- `中文论文元数据.json`（如存在中文文献；兼容旧名 `chinese_papers.json` / `chinese_metadata.json`）
- `文献-Zotero架构对照.json`
- `pdf-附件池索引.json`
- `collection_path → collection_key` 映射
- PDF 附件池目录（Step 5 / 原有 / 后续补下载 / 手动整理）

**目标：**
将 Step 4 的英文 BibTeX 条目和中文增强元数据低风险导入 Zotero，并把条目放入 6b 推荐的集合；PDF 附件默认只判断状态和处理策略，不自动挂载到已有条目。

**推荐执行顺序：**
1. 分流条目：先排除 `verification_status=REJECT`，再按 `source` / `source_id` / 标题语言把英文国际文献与 CNKI/万方中文文献分开；`WARN` 条目作为待审项展示。
2. 英文元数据导入：有真实 DOI 时优先 `zotero_add_by_doi`；批量场景可用 `zotero_add_by_bibtex`。
3. 中文元数据导入：优先用 `中文论文元数据.json` 构造 CSL JSON，通过 `zotero_add_by_csl_json` 创建条目；必要时再用 `zotero_update_item` 补全作者、年份、刊名、摘要、URL、language、Extra。旧名 `chinese_papers.json` / `chinese_metadata.json` 仅作为兼容输入。
4. 查重：英文用 DOI/title；中文用 `source_id` / `article_url` / title+first_author+year，不用合成 ID 当 DOI 查重。
5. 移入集合：按 `文献-Zotero架构对照.json` 的推荐集合路径调用 `zotero_manage_collections`。
6. 附件状态判断：从 `pdf-附件池索引.json` 选择候选文件；英文按 DOI 优先；中文按 `source_id` / `article_url` / 标题优先；先判断 `missing` / `found` / `already_attached` / `duplicate_candidate` / `conflict`。
7. 附件验证：用 `zotero_get_item_children` / `zotero_get_items_children` 检查每个条目是否有 PDF 附件。
8. 附件动作建议：默认写入 `attachment_action`，不直接执行高风险动作。
9. 回写状态：更新 `文献-Zotero架构对照.json` 和 `pdf-附件池索引.json` 中的导入状态、附件状态、匹配置信度，并同步生成/刷新 `文献-Zotero架构对照.md` 审阅版。

**当前 Zotero MCP 附件限制：**
- 当前 MCP 没有直接“向已有 item 添加本地 PDF 附件”的工具。
- `zotero_add_from_file` 是“从本地 PDF/EPUB 创建 Zotero 条目并附带文件”的入口，不是 attach-to-existing 工具。
- 少量附件推荐在 Zotero 桌面端手动拖拽到对应条目。
- 批量回退可以先用 `zotero_add_from_file` 创建临时/重复条目，再用 `zotero_merge_duplicates` 将该条目合并到 keeper；执行前必须 dry-run 并确认。

**中文条目 CSL JSON 最低字段：**
```json
{
  "type": "article-journal",
  "title": "中文论文标题",
  "author": [{"family": "张三"}, {"family": "李四"}],
  "issued": {"date-parts": [[2024]]},
  "container-title": "中文期刊名",
  "abstract": "中文摘要",
  "URL": "https://kns.cnki.net/...",
  "language": "zh-CN",
  "note": "Source: cnki | Source ID: cnki.xxxxx | Tier: T1 | Score: 22 | Subtopic: S1"
}
```

> 只有存在真实 DOI 时才写 `DOI` 字段；不要把 `cnki.xxx` / `wanfang.xxx` 写入 `DOI`。

**一致性检查：**
- `文献库.bib` 中每个条目：Zotero 中都有唯一条目或明确标记为重复/失败。
- CNKI/万方中文条目：Zotero 中的 title、author、year、publicationTitle/来源、URL、language、Extra/source_id 必须完整。
- T1/T2/T3 条目：必须有集合归属；缺 PDF 时必须列入「缺附件清单」。
- PDF 文件：不得静默忽略；每个候选 PDF 必须能追溯到匹配状态和建议动作。
- 附件池中未匹配 PDF 必须列入「未关联 PDF 清单」，不得静默忽略。
- Zotero 条目：不得只导入元数据却未移动到推荐集合，除非 JSON 记录标记为「待人工确认」。
- 已有同 DOI / 同 hash / 同名同大小附件时，必须标记 `already_attached` 或 `duplicate_candidate`，不得重复挂载。

**附件动作规则：**
| 情况 | attachment_status | attachment_action |
|------|-------------------|-------------------|
| 已有同 DOI / 同 hash 附件 | `already_attached` | `skip` |
| 同名同大小候选 | `duplicate_candidate` | `skip` |
| 多个候选 PDF | `conflict` | `none` |
| 无附件且唯一高置信 PDF | `found` | `manual_drag` 或 `add_from_file_then_merge` |
| 当前 MCP 无直接挂载工具 | `found` | 不生成直接挂载动作 |

**失败与回退：**
| 情况 | 处理 |
|------|------|
| DOI 匹配失败 | 标题规范化匹配；仍失败则标记「待人工确认」 |
| 中文文献无 DOI | 正常情况；使用 `source_id` / `article_url` / 标题匹配，不报错 |
| 中文元数据缺作者/年份/来源 | 回到 Step 4/5 从 CNKI/万方详情页补抽，或标记「中文元数据待补全」 |
| PDF 缺失 | 记录到缺附件清单，路由回 Step 5 补下载 |
| PDF 来自原有目录或后续补下载 | 纳入附件池索引，按同一匹配规则关联，不要求来自 Step 5 |
| 一个条目匹配多个 PDF | 标记 duplicate_candidate，优先选 DOI/source_id 命中的文件，低置信度需人工确认 |
| 一个 PDF 匹配多个条目 | 不自动关联，标记 conflict，等待人工确认 |
| 条目重复 | 保留最完整条目，必要时提示用户合并 |
| 附件工具不可写 / 无 attach-to-existing | 保留元数据导入结果，提示手动拖拽或 `add_from_file_then_merge` 回退 |
| 集合 key 丢失 | 回到 6c 重新生成 `collection_path → collection_key` 映射 |

---

## 7. 质量门槛 (Quality Gates)

- [ ] `文献库.bib` 已存在，且只包含 Step 4 筛选后文献。
- [ ] `zotero-架构.md` 与 Step 2 大纲章节一一对应。
- [ ] `文献-Zotero架构对照.md/json` 覆盖每个 BibTeX 条目。
- [ ] `文献-Zotero架构对照.json` 所有机器字段完整无截断。
- [ ] `pdf-附件池索引.json` 已扫描所有 PDF 来源目录。
- [ ] Zotero 集合树与 `zotero-架构.json` 一致。
- [ ] T1/T2/T3 条目已导入 Zotero 并进入对应集合。
- [ ] T1/T2/T3 条目 PDF 附件状态已判断；缺失、重复、冲突、已存在项已分别列入清单。
- [ ] 重复条目、缺 DOI、缺 PDF、待人工确认项已单独报告。

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `zotero-架构.md` 已生成
- [ ] `zotero-架构.json` 已生成
- [ ] `文献-Zotero架构对照.md` 已生成
- [ ] `文献-Zotero架构对照.json` 已生成并更新状态
- [ ] `pdf-附件池索引.json` 已生成并更新匹配状态
- [ ] 如果 `skip` 或 plan-only：readiness、blocking_missing、nonblocking_missing、recommended_next_step 已写入
- [ ] 如果执行 Zotero 写入：`CP-ZOTERO-WRITE` 已确认，集合创建完成并通过一致性检查
- [ ] PDF 附件状态与建议动作已写回；高风险挂载动作已等待人工确认

### 错误日志更新
- [ ] 文献无法匹配集合 → 追加到 `.skill-state/error_log.md`
- [ ] PDF 无法匹配条目 → 追加到 `.skill-state/error_log.md`
- [ ] Zotero MCP 写入失败 → 追加到 `.skill-state/error_log.md`

### 决策日志更新
- [ ] 是否调整了文库架构策略？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否人工改判文献集合归属？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否采用手动附件导入回退？→ 记录到 `.skill-state/decision_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：开始写作前证据组织与论文写作（Step 7）
  > **下一步 → Step 7：** Zotero 文库、集合归属和 PDF 附件已准备好，接下来生成综述矩阵、学习目标期刊风格，并开始撰写论文。

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **Zotero MCP 连接失败**：运行 `python3 scripts/setup_zotero.py --smoke-test` 诊断。
- **MCP 本地模式只读**：切换到可写 MCP 配置后再执行创建集合、导入条目、关联附件。
- **文献无法归类**：回到 6b，依据 title / abstract / note 重新标注，必要时设为「待人工确认」。
- **PDF 附件缺失**：回到 Step 5 补下载，或在 Zotero 桌面端手动添加附件。
- **集合结构不一致**：回到 6c，以 `zotero-架构.json` 为准补建缺失集合并重跑一致性检查。
