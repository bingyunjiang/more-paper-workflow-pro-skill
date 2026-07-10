# Claim-Evidence Readiness

本文件用于连接 Step 4 检索结果和 Step 7 写作需求。

## 判断问题

一个子主题是否已经“足够可写”，至少看三点：

- 是否有 2-5 篇能直接支撑关键 claim 的 T1/T2 文献
- 是否有足够背景文献解释问题来源
- 是否存在明显证据空洞

## readiness 级别

- `not-ready`
  - 还不能写，需补检索
- `background-ready`
  - 可写背景，但不能写关键结论
- `draft-ready`
  - 可写章节草稿
- `strong-ready`
  - 可写并可做较强论证

## 输出用途

- Step 4 可据此指出哪些章节仍需补查
- Step 7 可据此安排先写哪些部分

## Step 7 完成状态

- `draft_ready`：当前写作范围的正文和风险说明已形成；允许摘要级、元数据级或待补证据项，不要求 Step 1-6 工件存在。
- `evidence_closed`：`claim_evidence_audit.json` 与当前稿件 `draft_sha256` 一致，`unresolved_count=0`，reviewer scorecard 同样绑定当前稿件。
- `ready_for_step8`：在 `evidence_closed` 基础上，当前写作范围内的图表解析和必要质量门也已关闭。

自动摘要筛查只能生成候选支撑判断。`numeric_comparison / parameter / mechanism / novelty` 等强 claim 即使摘要关键词匹配，也必须保持 `partial + downgrade_required=true`，直到全文、页码、图表或检索覆盖证据完成解释性复核。

```bash
python3 scripts/validate_step7_output.py <output-dir> --target-state draft_ready
python3 scripts/validate_step7_output.py <output-dir> --target-state evidence_closed
python3 scripts/validate_step7_output.py <output-dir> --target-state ready_for_step8
```
