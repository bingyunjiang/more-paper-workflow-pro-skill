# Revision Roadmap

## 何时使用
- 已收到审稿意见，需要先解读再执行修改
- 想知道哪些意见只改措辞、哪些必须回退 Step 4/6/7.2
- 需要 Point-by-Point 回应骨架，但还不想直接改正文

## 最小输入
- 审稿意见全文
- 最好同时提供已有草稿、章节范围或目标期刊/目标答辩场景

## 主要产出
- `revision_roadmap.md`
- `response_letter_skeleton.md`
- `evidence_gap_list.md`

## 闭环语义
- 问题识别
- 修订动作
- 证据状态
- 验证结果
- 下一步动作
- 问题状态

## 最小闭环字段
- `issue_id`
- `chapter_binding`
- `claim_binding`
- `problem_summary`
- `action_type`
- `evidence_status`
- `verification_result`
- `next_action`
- `issue_state`
- `state_reason`

`issue_state` 固定值域：
- `identified`
- `routed`
- `in_revision`
- `verification_pending`
- `closed`
- `blocked_author_decision`
- `blocked_evidence`
- `invalid_or_not_applied`

这些字段只记录问题生命周期，不规定具体写作策略、修辞路径或段落组织方式。

## 常见阻塞点
- 不能只做文字摘要；每条意见都要绑定章节和 claim
- 发现证据不足时，优先提出补文献/补 PDF/补 Zotero/重做风格蓝图
- `retrieval_candidates.json` 只能作候选提醒，不能当作已补证据
- 回应骨架不是“已完成修改”，只是后续执行模板
