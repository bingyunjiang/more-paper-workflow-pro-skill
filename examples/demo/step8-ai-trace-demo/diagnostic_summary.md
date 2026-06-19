# diagnostic_summary

## AI 味确定性检查摘要

- 规则族命中数量：3
- 高密度章节/段落：L1 [套话短语规则]；L1 [空泛归因规则]；L3 [结构/资料缺口规则]
- 可直接修复项数量：1
- 需人工复核项数量：1
- 引用/证据型回退数量：1
- 结构/资料缺口回退数量：1

### 规则族分布
- 套话短语规则 ×1
- 空泛归因规则 ×1
- 结构/资料缺口规则 ×1

### 处理提醒
- 风格类命中默认不触发 rollback；仅作为 Step 8 润色诊断与修订分流依据。
- 若空泛归因贴近关键 claim，建议回查 Step 7 引用审计或原文支持。

### Step 8 总判断
- Overall Status：`not_ready_requires_rollback`
- Next Action：`return_to_step_4_or_6`
- 判定理由：存在结构/资料缺口回退项，Step 8 不应在证据底座缺失时继续硬修。

### 统一状态契约
- readiness：`blocked`
- can_continue：`False`
- blocking：['存在待补文献/图表/实验材料，占位提示尚未闭环']
- warnings：[]
- recommended_next_step：`Step 4/6`
