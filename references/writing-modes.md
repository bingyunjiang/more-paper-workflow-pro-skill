# Step 7 写作模式

## 模式列表

### `full-document`

从证据组织到完整起草。

### `chapter-only`

只写一个或多个指定章节。

### `continue-existing`

在已有草稿上续写、补写、替换局部内容。

### `abstract-only`

只写中文摘要、英文摘要或双语摘要，不扩展论文主体。

### `review-only`

只输出综述主体，不扩展为完整论文。

### `revision-only`

根据审稿意见或明确修订目标进行定向修订；证据不足时先生成修订路线和缺口清单。

## 专项操作

专项操作使用独立的 `operation` 轴，不占用写作范围 `mode`：

- `write`：按当前 `mode` 执行写作。
- `citation-audit`：不扩写正文，只检查 claim 与引文是否匹配。
- `figure`：只处理图表设计、生成、复现与图文接口。
- `pre-review`：从审稿人视角预审当前稿件或核心摘要。

## 默认原则

- 模式先于 prose 风格
- 先确认 `mode + operation`，再加载深 reference
- `operation` 不是新的公开 Step；四类操作都保留在 Step 7 内
