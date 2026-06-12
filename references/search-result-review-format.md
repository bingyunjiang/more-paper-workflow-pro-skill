# 检索结果评审格式

Step 4 在输出检索结果时，建议统一下列字段。

| 字段 | 说明 |
|---|---|
| record_id | 结果编号 |
| title | 标题 |
| source | 来源数据库 |
| year | 年份 |
| relevance_score | 相关性 |
| evidence_tier | T1/T2/T3/T4 |
| verification_status | VERIFIED / WARN / REJECT |
| key_reason | 分级理由 |
| outline_mapping | 对应章节/子问题 |
| next_action | 保留 / 复核 / 排除 / 下载 |

## 目的

- 减少 Step 4 到 Step 6/7 的语义损耗
- 为 citation audit 提供早期风险标签
