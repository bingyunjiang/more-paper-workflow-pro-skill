# Showcase

本目录用于展示 `more-paper-workflow-pro-skill` 的关键中间产物和最终产物样例，帮助用户理解每个 Step 会生成什么，而不是只看流程说明。

建议优先查看：

- `search_report_sample.md`：Step 4 `检索报告.md` 样例
- `zotero_mapping_sample.md`：Step 6 `文献-Zotero架构对照.md` 样例
- `style_profile_sample.md`：Step 7.2 风格画像样例
- `revision_roadmap_sample.md`：Step 7.12 修稿路线图样例
- `citation_audit_sample.md`：Step 7.15 三层引用审计样例
- `polish_quality_report_sample.md`：Step 8 润色质量报告样例
- `diagnostic_summary_ai_trace_sample.md`：Step 8 AI 味确定性检查摘要区块样例
- `revision_ledger_ai_trace_sample.json`：Step 8 合并 AI 味 issue 后的 `revision_ledger` 片段样例
- `step8_ai_trace_demo.md`：Step 8 AI 味确定性检查执行入口示例
- `../demo/step8-ai-trace-demo/`：可直接复制运行的最小 Step 8 demo 目录

其中 `.skill-state/ai_trace_diagnostics.json` 现在应理解为 Step 8 的**运行态状态源之一**，而不只是调试输出：它既给 `run_step8_ai_trace.py` 提供机器层诊断结果，也能被 `artifact_passport.json` / 路由层消费，影响 Step 8 readiness、风险提示和推荐下一步。

这些样例应保持脱敏，不包含真实受限论文全文。
