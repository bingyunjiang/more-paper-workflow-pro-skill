# Zotero

## 何时使用
- 已有 `文献库.bib`、PDF 或 Zotero 文库，需要进入 Step 6
- 想生成 Zotero 架构、文献-集合对照、附件池索引
- 想生成 `capability_index.json/md`，快速判断当前文献资产能支持哪些 Step
- 想检查缺附件、错集合、条目与 PDF 不一致

## 最小输入
- `文献库.bib`、Zotero 集合/条目或 PDF 目录中的一种
- 可选：`zotero-架构.md/json`、`文献-Zotero架构对照.json`
- 推荐同时提供：`workflow_search_results.json` 或 `文献-大纲对照.json`，用于复用前序文献-大纲映射

## 主要产出
- `zotero-架构.md/json`
- `文献-Zotero架构对照.md/json`
- `pdf-附件池索引.json`
- `capability_index.json/md`

## 常见阻塞点
- 必须先确认模式：`local / cloud / skip`
- 写入前需要确认集合结构，不建议静默入库
- 新建集合和子集合优先依据 Step 2 大纲二级目录；关键词和证据类型只做标签或降级匹配
- 有前序文献-大纲映射时，入库集合路径应直接复用该映射，不重新按关键词猜章节
- `REJECT` 文献不能进入 Zotero 写入计划
- capability index 只说明资产能力和推荐入口，不能把候选、摘要或文件名匹配直接当作证据
