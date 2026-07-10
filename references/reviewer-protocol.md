# Reviewer Protocol

本文件服务 Step 1 预审和 Step 7 `pre-review` 模式。

## 目标

用审稿人视角暴露问题，但不伪造 reviewer 身份。

## 共用评审轴

- originality
- importance
- technical soundness
- evidence adequacy
- readability / structure

## 五维锚定量表

每个维度使用 1-5 分，并必须同时记录 `score / evidence_locations / reason`。没有正文位置或工件证据的裸分数无效。

| 分数 | 可复现含义 |
|---:|---|
| 1 | 核心内容缺失，或当前结论无法成立 |
| 2 | 存在阻塞性缺陷，必须回退补证据或重构 |
| 3 | 可形成受限草稿，但仍有明确 MAJOR 问题 |
| 4 | 达到内部送审水平，只剩可定位的小修或边界项 |
| 5 | 在当前 `assessment_boundary` 和证据范围内未发现实质性缺陷 |

机器工件固定为 `reviewer_scorecard.json`，schema 为 `reviewer-scorecard.v1`：

```json
{
  "schema_version": "reviewer-scorecard.v1",
  "draft_sha256": "当前评审稿 SHA-256",
  "assessment_boundary": "full_document | chapter | section | abstract",
  "scores": {
    "originality": {"score": 3, "evidence_locations": ["Introduction"], "reason": ""},
    "importance": {"score": 3, "evidence_locations": ["Introduction"], "reason": ""},
    "technical_soundness": {"score": 4, "evidence_locations": ["Methods", "Results"], "reason": ""},
    "evidence_adequacy": {"score": 4, "evidence_locations": ["citation_audit.md"], "reason": ""},
    "readability_structure": {"score": 3, "evidence_locations": ["full_document"], "reason": ""}
  },
  "critical_issues": []
}
```

Step 7 完成门：`technical_soundness >= 4`、`evidence_adequacy >= 4`、其余维度 `>= 3`，且 `critical_issues` 必须为空。进入 `evidence_closed / ready_for_step8` 时，`draft_sha256` 必须与当前稿件一致；评分只覆盖 `assessment_boundary`，不得把局部评审写成全文通过。

## 输出格式建议

- `Review setup`
- `Major strengths`
- `Major concerns`
- `Technical failings`
- `What blocks a stronger claim`
- `Recommended next move`

## 严重性分级

- `CRITICAL`：阻塞强 claim 或投稿/送审前必须先处理的问题，例如核心证据缺失、章节功能错误、贡献点与正文不一致。
- `MAJOR`：审稿人或导师会明显注意到的问题，例如引用落点薄弱、技术链条断裂、图表没有支撑正文 claim。
- `MINOR`：局部表达、术语、格式或可读性问题，不单独改变论文主判断。

严重性分级只服务修订优先级，不预测录用结果，不伪造正式 reviewer 身份。

## 使用边界

- 不替代正式投稿评审
- 不做编辑决定预测
