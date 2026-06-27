# 审稿人视角写作缺陷库

本文件用于 Step 7 的 `pre-review`、`revision-roadmap` 和 Step 8 的 `review-style-polish`。它模拟常见审稿关注点，但不冒充真实审稿意见，也不预测录用结果。

## 使用边界

- 只用于发现论文结构、证据、工程验证、图表和 claim 风险。
- 不新增文献、不替作者做实验、不把候选诊断写成最终结论。
- 每个缺陷都必须给出 `defect_id / severity / evidence_basis / recommended_action / rollback_target`。

## 严重性

| severity | 含义 | 默认动作 |
|---|---|---|
| `critical` | 阻塞当前稿件可信度，通常需要补证据、补实验或重写论证 | 回退 Step 7/4/6 或作者决策 |
| `major` | 明显影响审稿阅读或说服力，可通过补证据、降强度、重排论证修复 | 写入修稿路线图 |
| `minor` | 表达、格式、图表说明或局部边界问题 | Step 8 可保守修复 |

## 1. novelty_and_positioning_defects

- `novelty_claim_not_scoped`: 创新性没有限定对象、场景或对比范围。
- `first_claim_without_search_coverage`: 写“首次/首创”但没有检索覆盖、竞品或文献边界。
- `contribution_list_not_backed_by_results`: 贡献点没有在结果/讨论中逐条回扣。
- `gap_too_generic`: 研究缺口只有“研究不足/缺乏系统研究”，没有具体技术矛盾。

## 2. evidence_and_citation_defects

- `metadata_only_supports_strong_claim`: 摘要/元数据支撑强参数、机制或创新 claim。
- `citation_does_not_support_sentence`: 引用只相关但不支撑当前句。
- `one_citation_overloaded`: 一个引用被用来支撑过多不同 claim。
- `missing_primary_source`: 关键方法、标准、数据或参数没有原始来源。

## 3. method_and_reproducibility_defects

- `parameter_table_missing`: 方法缺关键参数表。
- `baseline_missing_or_unfair`: 缺基准，或基准与本文方法工况不一致。
- `dataset_or_scenario_missing`: 数据来源、场景数量、时间粒度或样本范围不清。
- `ablation_missing_for_algorithm_claim`: 算法/AI/优化方法 claim 缺消融或灵敏度分析。
- `simulation_experiment_boundary_blurred`: 仿真、HIL、样机实验和现场数据边界混淆。

## 4. result_and_figure_defects

- `figure_not_supporting_claim`: 图表不能支撑正文 claim。
- `figure_without_condition`: 图注或正文缺工况、单位、变量或测试条件。
- `peak_metric_overused`: 只报峰值指标，缺全范围曲线或代表性工况。
- `statistical_or_uncertainty_missing`: 需要统计/重复实验/误差分析但未提供。
- `result_without_comparison`: 结果没有与基准、文献、控制组或工程要求对比。

## 5. discussion_and_claim_defects

- `mechanism_claim_without_validation`: 机制 claim 缺实验、仿真、图表或对比验证。
- `correlation_written_as_causation`: 把相关性写成因果证明。
- `limitation_missing`: 讨论和结论缺局限。
- `engineering_constraint_ignored`: 忽略温度、容量、成本、寿命、标准、安全、用户行为或并网约束。
- `generalization_beyond_scope`: 从单一材料、样机、场景或仿真外推到普遍结论。

## 6. power_energy_specific_defects

- `only_simulation_no_hardware_for_hardware_claim`: 只有仿真却写硬件可行或工程验证。
- `efficiency_without_test_conditions`: 效率 claim 缺仪器、功率等级、温度、负载点或输入输出范围。
- `stability_claim_without_stability_evidence`: 稳定性 claim 缺小信号、Bode/Nyquist、Lyapunov、扰动实验或 HIL。
- `v2g_benefit_without_degradation_or_user_constraint`: V2G 收益不考虑电池退化、SOC 窗口、用户可用性。
- `ems_optimization_without_constraints`: EMS 优化只给目标函数或收益，不给约束、基准和场景。
- `wireless_charging_without_misalignment_or_emc`: 无线充电只给对准效率，不给偏移、负载范围或 EMI/EMC。

## 输出格式

审稿式缺陷报告按以下顺序输出：

1. `Review setup`
2. `Top blocking defects`
3. `Major defects by category`
4. `Evidence or experiment actions`
5. `Claims to downgrade`
6. `Recommended next move`

每条缺陷最小字段：

| 字段 | 说明 |
|---|---|
| `defect_id` | 稳定缺陷编号 |
| `category` | novelty / evidence / method / result / discussion / power_energy |
| `severity` | critical / major / minor |
| `location` | 章节、段落、图表或 claim |
| `evidence_basis` | 来自草稿、argument_plan、图表、引用审计或当前依据不足 |
| `recommended_action` | 降强度、补证据、补图表、补实验、重排论证或回退 |
| `rollback_target` | none / step_7_argument_plan / step_7_citation_audit / step_4_or_6_evidence_repair / author_decision |
