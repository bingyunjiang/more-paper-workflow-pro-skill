# 图表与写作接口

本文件只定义 Step 7 中文字与图表任务的接口，不替代具体绘图规范。

## 目标

明确一张图在写作中承担什么功能，并把“写文 + 插图”视作同一条图文证据链。

## 图表接口字段

- figure_id
- table_id
- panel_id
- purpose
- related_section
- claim_supported
- claim_id
- claim_text
- claim_strength
- required_data
- status
- figure_source
- figure_asset_mode
- figure_intent
- evidence_basis
- caption_anchor
- text_anchor
- evidence_modality
- support_type
- support_status
- figure_table_panel_binding
- downgrade_required
- replacement_hint
- figure_risk_note
- risk_flags

## 图-表-panel 绑定矩阵

所有图表相关 claim 必须生成 `figure_table_panel_binding`，而不是只写“如图所示”。最小记录：

```json
{
  "claim_id": "C-001",
  "claim_text": "",
  "claim_strength": "background|trend|parameter|numeric_comparison|mechanism|novelty",
  "figure_id": "",
  "table_id": "",
  "panel_id": "",
  "caption_anchor": "",
  "text_anchor": "",
  "evidence_modality": "EBSD|TEM|SEM|XRD|flow_curve|mechanical_test|waveform|efficiency_curve|loss_breakdown|thermal_map|grid_metric|optimization_result|hardware_prototype|HIL|field_data|standard|simulation|user_data",
  "support_type": "direct|partial|contextual|not_supported",
  "support_status": "support|weak-support|not-supported|cannot-judge",
  "downgrade_required": false,
  "risk_flags": []
}
```

材料/机械基础 `evidence_modality` 子集保持为：`EBSD|TEM|SEM|XRD|flow_curve|mechanical_test|simulation|user_data`。电力电子/能源系统任务可在此基础上扩展 `waveform / efficiency_curve / loss_breakdown / thermal_map / grid_metric / optimization_result / hardware_prototype / HIL / field_data / standard`。

若 `claim_strength=mechanism / numeric_comparison / parameter`，但缺少图/表/panel、图注或正文锚点，应标记 `downgrade_required=true`，并把正文改成保守表达或写入 `evidence_gap_list.md`。

## 最小图文单元

- 正文引出句
- 图或表
- 图后解释句

三者必须回答同一条 claim。正文引出句提出要观察的问题，图或表提供可见证据，图后解释句只解释图中能支撑的范围，不得补写图中看不出来的机制、数值或统计结论。

## 常见用途

- 背景示意
- 方法流程
- 实验结果
- 对比分析
- 案例展示

## 边界

- 图表任务可以在 Step 7 发起
- `auto_insert_figures=true` 时，优先要求条目下存在 `LLM-for-Zotero-MinerU-cache-*.zip` 或等价图文资产包
- 没有 MinerU ZIP 但本地 PDF 可读时，允许通过 PyMuPDF 直接抽取 `pdf_direct` 候选图；该候选必须标记为低置信、无 caption、待人工确认
- 没有 MinerU ZIP 且 PDF 不可读或无候选图时，才只保留正文图位占位，不自动选图
- 没有 figure/table/panel 绑定时，不得自动写“如图 X 所示”“图中可见”“由图证明”
- 具体图形设计和导出细节可继续由现有图表参考处理
