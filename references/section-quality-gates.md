# 摘要 / 引言 / 讨论 / 结论专项写作门

本文件约束 Step 7 的主体写作和 Step 8 的保守修订。它只检查章节功能是否成立，不替代引用审计、图表审计或目标期刊格式规范。

## 使用边界

- Step 7：写摘要、引言、讨论、结论前必须确认对应写作门。
- Step 8：润色这些章节时只能修复功能错位、衔接断裂和降强度；若缺证据或缺结果，应回退 Step 7。
- 若目标期刊/学校模板有更具体要求，以用户指定模板为格式优先；但 claim 仍受证据等级约束。

## 1. abstract_quality_gate

摘要必须自包含，不能只是“本文研究了……”的目录式说明。

必须包含：

- `problem`: 研究问题或工程痛点。
- `method`: 方法、模型、实验、仿真、数据或系统方案。
- `result`: 关键结果，优先量化；无量化时要说明结果类型。
- `contribution`: 贡献或意义，必须受结果边界约束。
- `boundary`: 对象、工况、数据范围或证据等级。

常见问题：

- `missing_quantified_result`: 摘要没有任何结果或指标。
- `method_only_abstract`: 只写方法流程，不写发现。
- `overbroad_impact`: 从局部实验/仿真跳到行业级影响。
- `background_heavy`: 背景占比过高，压缩了方法和结果。

## 2. introduction_quality_gate

引言必须完成从领域问题到本文研究问题的收束。

推荐链条：

```text
application_context -> known_progress -> unresolved_gap -> why_gap_matters -> this_work_scope -> contribution_claims
```

必须包含：

- `application_context`: 真实应用或科学背景。
- `known_progress`: 已有研究推进到哪里。
- `unresolved_gap`: 仍未解决的具体问题。
- `why_gap_matters`: 缺口为什么重要。
- `this_work_scope`: 本文只解决哪个范围。
- `contribution_claims`: 贡献点，不得超过本文证据。

常见问题：

- `generic_gap`: 只写“研究不足/有待深入”，没有具体缺口。
- `literature_dump`: 文献罗列多，但没有归纳出研究缺口。
- `novelty_overclaim`: 写“首次/创新”但没有检索覆盖或对比边界。
- `scope_creep`: 引言承诺的问题大于正文实际完成的问题。

## 3. discussion_quality_gate

讨论必须解释结果意味着什么，以及为什么在当前边界下可信。

推荐链条：

```text
key_result -> interpretation -> mechanism_or_system_reason -> comparison -> limitation -> implication
```

必须包含：

- `key_result`: 讨论对象必须来自结果或图表。
- `interpretation`: 解释结果含义，不重复结果描述。
- `mechanism_or_system_reason`: 机制、控制逻辑、工程约束或系统原因。
- `comparison`: 与文献、基准、仿真/实验组或工程要求对比。
- `limitation`: 工况、模型、样本、设备或数据限制。
- `implication`: 在限制内说明意义。

常见问题：

- `result_repetition`: 讨论只是重复结果。
- `mechanism_jump`: 从现象直接跳到机制，没有证据链。
- `missing_limitation`: 不写局限，导致 claim 外推。
- `unsupported_comparison`: 对比没有同工况、同指标或同口径。

## 4. conclusion_quality_gate

结论必须收束本文完成了什么，不能引入新证据或新论点。

必须包含：

- `answer_to_problem`: 回答研究问题。
- `main_findings`: 2-4 条核心发现或工程结论。
- `evidence_scope`: 说明这些结论来自何种证据范围。
- `practical_or_scientific_value`: 在边界内说明价值。
- `future_work`: 只写真实未完成事项，不把缺口伪装成贡献。

常见问题：

- `new_claim_in_conclusion`: 结论引入正文没有支撑的新 claim。
- `abstract_copy`: 结论机械重复摘要。
- `unbounded_generalization`: 把样机/仿真/局部数据写成普遍结论。
- `future_work_as_fix`: 用未来工作掩盖当前证据不足。

## 5. Step 7 输出要求

当写作范围包含摘要、引言、讨论或结论时，`argument_plan` 应增加：

- `section_quality_gate`
- `required_moves`
- `missing_moves`
- `overclaim_risks`
- `rollback_if_missing`

若 `missing_moves` 包含结果、关键证据、图表或正文未支撑贡献，必须降级写作或回退补证据。

## 6. Step 8 修订边界

- 可以修：章节功能错位、段落顺序、重复摘要、空泛意义句、局部边界句。
- 不可以修：补新结果、新增引用、重写贡献点、把结果不足包装成讨论。
- 发现 `new_claim_in_conclusion / novelty_overclaim / mechanism_jump / unsupported_comparison` 时，优先回退 Step 7 引用审计或 argument plan。
