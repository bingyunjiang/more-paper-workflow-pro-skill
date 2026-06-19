# Polish

## 何时使用
- 已有初稿，需要进入 Step 8 进行结构精炼、术语统一、受约束补写与修订后验证
- 只想润色局部章节、摘要或指定段落
- 想保留 Step 7 的证据边界，不重新发明引用结论
- 想自动检查 AI 味、机械化表达、空泛套话和载体层 hygiene，但不把这些诊断误当成证据问题

## 最小输入
- 初稿 `.md/.docx/文本`
- 可选：评审报告、引用审计报告、`.skill-state/term_aliases.md`

## 主要产出
- `论文润色稿.md/.docx`
- `diagnostic_summary.md`
- `revision_ledger.json/md`
- `修改对照表`
- `术语一致性报告`
- `润色质量报告`

## 内部诊断重点
- Step 8 会自动做 AI 味确定性检查，属于 `language_mechanical` 的诊断来源之一
- 结果会并入 `diagnostic_summary.md`、`revision_ledger.json/md`、`润色质量报告`
- 该检查帮助识别机械化表达、空泛套话和载体层问题
- 它不会把用户风格偏好强行改写成统一文风
- 它不会因为“像 AI”就直接判定稿件失败
- 机器层结构化结果可由 `scripts/deterministic_writing_diagnostics.py` 生成，再并入 `revision_ledger`
- 若需要一个真实执行入口，优先使用 `scripts/run_step8_ai_trace.py`，默认串起 `论文初稿.md -> .skill-state/ai_trace_diagnostics.json -> diagnostic_summary.md -> revision_ledger.json/md`

## 常见阻塞点
- 没有评审报告时可继续，但必须标记“评审依据不足”
- 没有引用审计报告时可继续，但不得声称引用安全已通过
- Step 8 可以提示引用风险，但不能替代 Step 7 的完整引用审计
