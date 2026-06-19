# revision_ledger

- issues: 3
- direct_fix_count: 1
- manual_review_count: 1
- overall_status: `not_ready_requires_rollback`
- next_action: `return_to_step_4_or_6`
- readiness: `blocked`
- can_continue: `False`
- recommended_next_step: `Step 4/6`

## Step 8 问题闭环摘要

| issue_id | issue_type | severity | allowed_action | next_action | rule_family |
|---|---|---|---|---|---|
| ai-trace-stock-001 | language_mechanical | warn | 直接修改 | 保留修改 | 套话短语规则 |
| ai-trace-vague-001 | language_mechanical | warn | 人工决定 | return_to_step_7_citation_audit | 空泛归因规则 |
| ai-trace-structgap-001 | language_mechanical | warn | 回退 | return_to_step_4_or_6 | 结构/资料缺口规则 |

## 问题分流

### 可直接修订

- count: 1
- default_next_action: `保留修改`

#### ai-trace-stock-001

- issue_type: `language_mechanical`
- severity: `warn`
- location: `L1`
- allowed_action: `直接修改`
- next_action: `保留修改`
- deficiency_kind: ``
- rule_family: `套话短语规则`
- problem: 检测到套话短语/模板化句式 ×1，建议清理高频空泛表达。
- proposed_revision: 删除套话短语，改为更具体的学术陈述或直接进入论点。
- rule_examples: 值得注意的是

### 需作者决定

- count: 0
- default_next_action: `转人工复核`

- 无

### 当前依据不足

- count: 2
- default_next_action: `return_to_step_7_citation_audit / return_to_step_4_or_6`

#### 引用/证据型回退

- count: 1

##### ai-trace-vague-001

- issue_type: `language_mechanical`
- severity: `warn`
- location: `L1`
- allowed_action: `人工决定`
- next_action: `return_to_step_7_citation_audit`
- deficiency_kind: `citation_evidence`
- rule_family: `空泛归因规则`
- problem: 检测到空泛归因 ×1，若贴近关键 claim 应回查 Step 7 引用审计或原文支持。
- proposed_revision: 改为更具体的来源表述，或保留并补充引用支撑检查。
- rule_examples: 研究表明

#### 结构/资料缺口回退

- count: 1

##### ai-trace-structgap-001

- issue_type: `language_mechanical`
- severity: `warn`
- location: `L3`
- allowed_action: `回退`
- next_action: `return_to_step_4_or_6`
- deficiency_kind: `structure_material`
- rule_family: `结构/资料缺口规则`
- problem: 检测到结构/资料缺口提示 ×2，当前正文显式暴露待补文献、数据、图表或实验材料。
- proposed_revision: 不要在 Step 8 内硬补；先回到 Step 4/6 补资料或证据底座，再继续润色。
- rule_examples: 这里需要补文献, 图表待补

#### 其他待判断缺口

- count: 0

- 无

