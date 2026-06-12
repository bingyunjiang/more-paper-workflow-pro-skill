# Zotero

## 何时使用
- 已有 `文献库.bib`、PDF 或 Zotero 文库，需要进入 Step 6
- 想生成 Zotero 架构、文献-集合对照、附件池索引
- 想检查缺附件、错集合、条目与 PDF 不一致

## 最小输入
- `文献库.bib`、Zotero 集合/条目或 PDF 目录中的一种
- 可选：`zotero-架构.md/json`、`文献-Zotero架构对照.json`

## 主要产出
- `zotero-架构.md/json`
- `文献-Zotero架构对照.md/json`
- `pdf-附件池索引.json`

## 常见阻塞点
- 必须先确认模式：`local / cloud / skip`
- 写入前需要确认集合结构，不建议静默入库
- `REJECT` 文献不能进入 Zotero 写入计划
