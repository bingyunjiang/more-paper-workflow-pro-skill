# more-paper-workflow-pro-skill 工作流架构契约

本文档记录当前 skill 的运行边界和标准产物链。它不是用户快速开始页；`README.md` 继续作为 GitHub 对外概览，运行时规则以 `SKILL.md` 与 `agents/step_*.md` 为准。

## 四层权威边界

| 层级 | 职责 | 不承担 |
| --- | --- | --- |
| `README.md` | 对外展示、能力概览、推荐入口 | 详细执行规则、checkpoint 细节、脚本参数真相 |
| `SKILL.md` | 运行时路由、checkpoint 协议、`.skill-state/` 初始化、脚本速查 | 单步执行细则 |
| `agents/step_*.md` | 每个 Step 的输入契约、执行顺序、质量门、交付物 | 底层下载/检索/转换实现 |
| `scripts/` | 可复用工具实现与 CLI 入口 | 定义工作流语义或替代 agent 决策 |

## 8 步产物链

| Step | 标准输入 | 标准产物 | 机器接口 |
| --- | --- | --- | --- |
| Step 1 主题 | 用户研究意图、约束、材料 | `研究主题.md` | 主题、范围、限制条件 |
| Step 2 大纲 | 主题或已有目录 | `大纲关键词.md`、`章节证据需求表` | 章节、关键词、证据需求 |
| Step 3 检索方案 | 大纲、关键词、证据需求 | `检索方案.md` | `search_tasks` |
| Step 4 检索评分 | `search_tasks` 或等价查询 | 7 件套：`检索文献表.md/.xlsx`、`检索报告.md/.pdf`、`文献库.bib`、`saturation_snapshot.json`、`中文论文元数据.json` | `workflow-contracts.v1` search results JSON |
| Step 5 下载 | DOI、中文 article URL、publisher URL、workflow search results | PDF 池、下载日志、下载 manifest | `DownloadManifestItem` / `DownloadResult` |
| Step 6 Zotero | 文献库、PDF 池、中文元数据、Zotero 架构 | `zotero-架构.md/json`、`文献-Zotero架构对照.md/json`、`pdf-附件池索引.json` | plan-only Zotero plan JSON |
| Step 7 写作 | Zotero/证据矩阵、PDF 附件池、写作蓝图 | `论文初稿.md`、指定章节、引用审计报告 | `ReportInputs`、证据矩阵 |
| Step 8 润色 | 初稿、术语表、审计结果 | `论文润色稿.md/.docx` | 风险标记、术语终验结果 |

## 正式脚本入口

| 阶段 | 正式入口 | 说明 |
| --- | --- | --- |
| 检索 | `scripts/search_by_topic.py` | 唯一顶层检索入口；新增来源应进入 source adapter，而不是新增平行顶层脚本 |
| 下载 | `scripts/unified_download_router.py` | 统一 DOI、中文 article URL、publisher URL、workflow JSON 到 provider/strategy |
| Zotero plan | `scripts/build_zotero_plan.py` | 只生成计划和索引，不写 Zotero |
| 检索报告 | `scripts/generate_search_report.py`、`scripts/generate_retrieval_report.py` | 消费检索表或标准 workflow JSON |

下载 provider 脚本如 `generic_publisher_downloader.py`、`sd_download.py`、`download_via_scihub.py`、`download_via_ieee.py` 保留为 strategy/provider 能力，不应重新成为工作流主入口。

## 不得破坏的运行规则

- 任意 Step 都可以直接进入。checkpoint 记录当前输入依据和风险，不作为线性流程锁。
- Step 4 的 7 件套交付物必须保持兼容；新增 workflow JSON 只能作为机器接口补强。
- CNKI/Wanfang 保留 `--language zh`、长 CDP 会话和串行可靠性优先的运行策略。
- `build_zotero_plan.py` 必须保持 plan-only，不调用 Zotero MCP，不修改外部文库。
- 所有 Zotero 写入动作必须经过 `CP-ZOTERO-WRITE`，只读、规划、dry-run 不应被该 checkpoint 阻塞。
- `.skill-state/` 属于项目运行态；不要把运行日志或 checkpoint 写入 `references/templates/`。

## 标准契约模块

`scripts/workflow_contracts.py` 提供轻量数据结构和 JSON 读写：

- `SearchTask`
- `SearchResultRecord`
- `DownloadManifestItem`
- `DownloadResult`
- `ZoteroPlanRecord`
- `ReportInputs`

当前 schema version 为 `workflow-contracts.v1`。它的目标是固定字段语义和阶段边界，不要求一次性迁移所有旧脚本。
