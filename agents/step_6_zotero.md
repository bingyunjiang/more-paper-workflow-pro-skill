# Step 6: Zotero 文库管理

> Step 6 负责把 Step 4 的 BibTeX 条目、Step 2 的论文大纲、Step 5 的 PDF 附件组织成一个一致的 Zotero 文库。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_2_outline.md` — 大纲关键词（章节结构 + 术语映射表）
- [ ] `agents/step_4_search_score.md` — 检索筛选结果与 `文献库.bib` 生成规则
- [ ] `agents/step_5_download.md` — Step 5 下载 PDF（paper-temp/）及后续补下载入口
- [ ] `references/zotero-structure-template.md` — Zotero 架构示例
- [ ] `references/zotero-outline-mapping.md` — 文献与集合对齐思路
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则
- [ ] `.skill-state/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 依据 Step 2 论文大纲生成 Zotero 集合架构（6a）
- 依据 Step 4 `文献库.bib` 和 6a 架构生成文献-集合对照表（6b）
- 通过 Zotero MCP 创建 Zotero 集合并检查架构一致性（6c）
- 将 PDF 附件池中的文件导入 Zotero，关联到对应条目并检查附件一致性（6d）

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
| 大纲关键词 | Step 2 | `大纲关键词.md` | ✅ |
| 筛选后文献库 | Step 4 | `文献库.bib` | ✅ |
| PDF 附件池 | Step 5 / 原有文件 / 后续补下载 | `paper-temp/`、用户指定目录、补下载目录 | ✅ |
| Zotero MCP 可写连接 | 环境配置 | MCP 工具 | ✅ |

> 前提条件：Step 4 检索与筛选后的文献必须已有 BibTeX 格式交付物。标准文件名为 `文献库.bib`，由 `python3 scripts/generate_retrieval_report.py 检索文献表.md` 生成。

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
| Zotero 条目 + PDF 附件 | Zotero | 每条文献条目关联对应 PDF 附件 |

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

**如果用户选择跳过 Zotero 写入：**
1. 只执行 6a 和 6b。
2. 在 `文献-Zotero架构对照.md/json` 中把集合创建、条目导入、PDF 附件标记为「后续手动处理」。

---

### 6a：根据 Step 2 大纲生成 Zotero 架构

输入：`大纲关键词.md`

```bash
python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md --json zotero-架构.json
```

输出：
- `zotero-架构.md`：给用户审阅的集合结构和标签方案
- `zotero-架构.json`：给 6c MCP 自动创建集合使用的树结构

**质量要求：**
- 根集合必须明确，如 `论文文献库` 或以论文主题命名的根集合。
- 一级集合应对应论文主要章节或研究方向。
- 二级/三级集合应对应子问题、方法路线、证据类型或关键主题。
- 不为单篇论文创建集合；单篇论文归属通过条目、标签和附件体现。
- 架构生成后先向用户展示概要，确认后再进入 6b。

---

### 6b：生成文献-Zotero架构对照

输入：
- `文献库.bib`（Step 4 筛选后的 BibTeX 文献库）
- `chinese_papers.json` / `chinese_metadata.json`（如存在中文文献）
- `zotero-架构.md`
- `zotero-架构.json`
- PDF 附件池目录：Step 5 下载目录（通常为 `paper-temp/`）、项目原有 PDF 目录、用户后续补下载目录

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
  "schema_version": "1.0",
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
      "collection_path": ["论文文献库", "2-方法", "P1-D1 数值模拟"],
      "collection_key": "",
      "tags": ["P1-D1", "数值模拟"],
      "import_method": "csl_json",
      "pdf_path": "/完整/path/to/file.pdf",
      "pdf_source": "existing|step5|supplemental|manual",
      "pdf_match_confidence": "high|medium|low|none",
      "zotero_item_key": "",
      "import_status": "pending",
      "attachment_status": "pending",
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
- 中文条目必须优先从 `chinese_papers.json` / `chinese_metadata.json` 读取 authors、year、publication_title、abstract、language，不能只依赖 `文献库.bib`。

**质量要求：**
- 每个 BibTeX 条目必须出现在对照表中。
- 每个 T1/T2 条目必须有推荐集合路径。
- 中文条目必须有 `source_id` 和 `article_url`；缺作者/年份/来源名称时必须列入「中文元数据待补全」清单。
- 缺真实 DOI、缺 PDF、重复条目、无法判定集合的文献必须单独列出。
- `文献-Zotero架构对照.json` 中所有用于机器执行的字段禁止截断；Markdown 中的截断不得反向污染 JSON。
- 6c/6d 所有 Zotero 写入操作都以 `文献-Zotero架构对照.json` 为准。

---

### 6c：通过 Zotero MCP 创建集合并检查架构一致性

输入：`zotero-架构.json`

**创建流程（递归，每个子集合的 `parent_collection` 传直接父级 key）：**

```
# Step 1 — 幂等性检查
zotero_search_collections(query="论文文献库")
  → 如果已存在，询问用户：跳过 / 补充缺失 / 新建带日期后缀的根集合

# Step 2 — 创建或复用根集合
zotero_create_collection(name="论文文献库")
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

### 6d：导入 PDF 文献并关联到对应 Zotero 条目

输入：
- `文献库.bib`
- `chinese_papers.json` / `chinese_metadata.json`（如存在中文文献）
- `文献-Zotero架构对照.json`
- `pdf-附件池索引.json`
- `collection_path → collection_key` 映射
- PDF 附件池目录（Step 5 / 原有 / 后续补下载 / 手动整理）

**目标：**
将 Step 4 的英文 BibTeX 条目和中文增强元数据导入 Zotero，再从 PDF 附件池中把匹配的 PDF 作为附件关联到对应条目，并把条目放入 6b 推荐的集合。

**推荐执行顺序：**
1. 分流条目：按 `source` / `source_id` / 标题语言把英文国际文献与 CNKI/万方中文文献分开。
2. 英文元数据导入：有真实 DOI 时优先 `zotero_add_by_doi`；批量场景可用 `zotero_add_by_bibtex`。
3. 中文元数据导入：优先用 `chinese_papers.json` / `chinese_metadata.json` 构造 CSL JSON，通过 `zotero_add_by_csl_json` 创建条目；必要时再用 `zotero_update_item` 补全作者、年份、刊名、摘要、URL、language、Extra。
4. 查重：英文用 DOI/title；中文用 `source_id` / `article_url` / title+first_author+year，不用合成 ID 当 DOI 查重。
5. 移入集合：按 `文献-Zotero架构对照.json` 的推荐集合路径调用 `zotero_manage_collections`。
6. 关联 PDF：从 `pdf-附件池索引.json` 选择匹配文件；英文按 DOI 优先；中文按 `source_id` / `article_url` / 标题优先；用 `zotero_add_from_file` 或可用的附件工具把 PDF 关联到对应父条目。
7. 附件验证：用 `zotero_get_item_children` / `zotero_get_items_children` 检查每个条目是否有 PDF 附件。
8. 回写状态：更新 `文献-Zotero架构对照.json` 和 `pdf-附件池索引.json` 中的导入状态、附件状态、匹配置信度，并同步生成/刷新 `文献-Zotero架构对照.md` 审阅版。

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
- T1/T2 条目：必须有集合归属；缺 PDF 时必须列入「缺附件清单」。
- PDF 文件：不得孤立存在；每个成功匹配的 PDF 必须能追溯到 Zotero 条目。
- 附件池中未匹配 PDF 必须列入「未关联 PDF 清单」，不得静默忽略。
- Zotero 条目：不得只导入元数据却未移动到推荐集合，除非 JSON 记录标记为「待人工确认」。

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
| 附件工具不可写 | 保留元数据导入结果，提示切换可写 MCP 配置或手动拖拽附件 |
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
- [ ] T1/T2/T3 条目 PDF 附件已关联；缺失项已列入缺附件清单。
- [ ] 重复条目、缺 DOI、缺 PDF、待人工确认项已单独报告。

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `zotero-架构.md` 已生成
- [ ] `zotero-架构.json` 已生成
- [ ] `文献-Zotero架构对照.md` 已生成
- [ ] `文献-Zotero架构对照.json` 已生成并更新状态
- [ ] `pdf-附件池索引.json` 已生成并更新匹配状态
- [ ] Zotero 集合创建完成并通过一致性检查
- [ ] PDF 已作为附件关联到对应 Zotero 条目

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
