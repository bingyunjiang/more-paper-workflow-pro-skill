# 确定性写作诊断（AI 味与机械化表达）

本文件定义 Step 8 内部使用的“AI 味确定性检查”规则族、映射边界和处理矩阵。

它的目标不是判断文本“是否由 AI 生成”，而是把**可规则化识别的机械化表达风险**收口为稳定诊断项，供 Step 8 的 `language_mechanical` 诊断、`revision_ledger` 问题闭环和 `润色质量报告` 使用。

## 作用边界

- 只检查表达层确定性风险。
- 不判断学术观点真假。
- 不判断引用是否真实存在。
- 不把“像 AI 写的”直接等同于“不能发表”或“必须回退”。
- 不替代 Step 7 写作，不替代 Step 7 引用审计。

## 六组固定规则族

### 1. 套话短语规则

检查高频空泛短语和模板化句式。

示例：

- 英文：`plays a crucial role`、`it is worth noting that`、`paving the way for`
- 中文：`值得注意的是`、`综上所述`、`不言而喻`

默认处理：

- `severity=WARN`
- 零星出现只记录
- 密集出现进入 Step 8 可直接修订队列

### 2. 机械连接词堆积规则

检查段首或句首连接词使用过密。

示例：

- 英文：`Moreover / Furthermore / Additionally / Notably`
- 中文：`此外 / 另外 / 首先 / 其次 / 更重要的是`

默认处理：

- 只在“扎堆”时触发
- `severity=WARN`
- 建议改为自然逻辑衔接或删去冗余连接

### 3. 伪洞见与悬垂表达规则

检查看似提升深度、实则空转的表达模板。

示例：

- `..., highlighting the importance of ...`
- `..., underscoring ...`
- 结尾挂抽象洞见但未增加实质信息的从句

默认处理：

- `severity=WARN`
- 允许 Step 8 直接改成独立陈述句、限定句或删除

### 4. 空泛归因规则

检查没有具体指向的“研究表明/专家认为”类表达。

示例：

- `Studies have shown`
- `Experts believe`
- `研究表明`
- `学者认为`

默认处理：

- `severity=WARN`
- issue 主类型仍为 `language_mechanical`
- 若紧贴关键 claim，可附加 `citation_risk_note`
- 不在 Step 8 直接补新证据，只提示“需回查 Step 7 审计或原文支持”

### 5. 句长节奏过匀规则

检查句长过于均匀、节奏机械的问题。

默认处理：

- 只做整体诊断，不对每句单独报错
- `severity=INFO` 或轻度 `WARN`
- 用于支持“语言机械化”判断，不单独决定总结果
- 只在整段/整章层面给出修改建议

### 6. 冗余破折号与插入语规则

检查插入性破折号、过度解释性补充、句内人工拉伸结构。

默认处理：

- `severity=INFO/WARN`
- 作为语言收口建议，不触发回退
- 与 Step 8 的 Level 3 表达风险清理对齐

## 映射规则

- 大多数 AI 味规则命中：`issue_type=language_mechanical`
- 若命中同时涉及术语混乱：
  - `issue_type=language_mechanical`
  - 在 `problem` 或 `evidence_basis` 中标注 `term_consistency_related`
- 若命中同时暴露“空泛归因贴着关键结论”：
  - 主类型仍为 `language_mechanical`
  - `next_action` 可指向 `return_to_step_7_citation_audit`
- 不允许把单纯词表命中映射为：
  - `evidence_gap`
  - `structure_drift`
  - `contribution_overclaim`
  除非已有其他独立证据支持该判断

## 动作矩阵

### 可在 Step 8 直接修订

- 套话短语
- 机械连接词堆积
- 悬垂 `-ing` / 伪洞见尾句
- 冗余破折号/插入语
- 明显重复表达
- 句子表面机械化但不改变 claim 的措辞

默认动作：

- `allowed_action=直接修改` 或 `局部补写`
- `next_action=保留修改`

### 可修但需轻量含义审计

- 涉及限定词、比较词、因果词的 AI 味表达
- 会影响句子强度的模板化短语
- 与引用落点相邻的空泛归因

默认动作：

- `meaning_audit_required=true`
- 审计通过才可关闭 issue
- 否则 `next_action=转人工复核` 或 `return_to_step_7_citation_audit`

### 只提醒，不在 Step 8 内硬修

- 统计层面的句长均匀
- 轻度被动语态偏高
- 少量风格化重复但作者可能有意保留的节奏

默认动作：

- 写入 `润色质量报告.md`
- 可不进入逐条修改
- 不影响 Step 8 总完成结论
