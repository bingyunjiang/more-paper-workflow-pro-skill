# 图表与写作接口

本文件只定义 Step 7 中文字与图表任务的接口，不替代具体绘图规范。

## 目标

明确一张图在写作中承担什么功能，并把“写文 + 插图”视作同一条图文证据链。

## 图表接口字段

- figure_id
- purpose
- related_section
- claim_supported
- required_data
- status
- figure_source
- figure_asset_mode
- figure_intent
- evidence_basis
- replacement_hint
- figure_risk_note

## 最小图文单元

- 正文引出句
- 图或表
- 图后解释句

## 常见用途

- 背景示意
- 方法流程
- 实验结果
- 对比分析
- 案例展示

## 边界

- 图表任务可以在 Step 7 发起
- `auto_insert_figures=true` 时，优先要求条目下存在 `LLM-for-Zotero-MinerU-cache-*.zip` 或等价图文资产包
- 没有 MinerU ZIP 时，只允许正文占位，不自动选图
- 具体图形设计和导出细节可继续由现有图表参考处理
