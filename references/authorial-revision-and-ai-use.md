# 作者声音、修订责任与 AI 使用合同

Step 8 的目标是提高准确性、连贯性、体裁适配和作者声音，而不是规避 AIGC 检测。任何检测器都可能误判，Skill 不承诺“通过检测”、不以检测分数为优化目标，也不通过刻意制造错别字、随机句式、虚假引用或扰动可读性来伪装人工写作。

## 1. 三类修订

- `editorial_only`：语法、标点、术语一致性、重复压缩、明确指代和不改变含义的衔接，可直接执行并做保真审计。
- `author_confirmed`：贡献表述、因果解释、方法选择、结果意义、局限和实践含义，仅在作者已有明确决定或确认后修订。
- `requires_author_input`：会改变论证、责任主体、claim 强度或学术立场的建议；只给选项和影响，不擅自写入终稿。

## 2. 恢复真实作者声音

- 优先保留作者稳定使用的术语、判断方式、限定语和论证节奏，而非套用通用“学术腔”。
- 删除空泛元话语、同义反复、整齐划一的段落模板和没有信息增量的总结句。
- 用具体对象、动作、证据和边界替代“具有重要意义”“值得注意的是”等悬空评价。
- 允许句长与段落功能自然变化，但不得为制造所谓 burstiness/perplexity 而随机改写。
- 所有改写继续受 protected spans、claim 强度和引用落点约束。

## 3. `authorial_revision_record.json`

```json
{
  "schema_version": "authorial-revision-record.v1",
  "draft_sha256_before": "...",
  "draft_sha256_after": "...",
  "scope": "full_manuscript|chapter|local",
  "revisions": [{"location":"...","category":"editorial_only","summary":"...","meaning_changed":false}],
  "authorial_decisions": [{"topic":"contribution K1","decision":"...","status":"author_confirmed","source":"author_message|existing_draft|pending"}],
  "unresolved_author_inputs": [],
  "ai_use_disclosure": {"status":"declared|not_required|requires_author_confirmation","tools_or_models":[],"use_scope":"language_editing","policy_basis":"institution_or_publisher_rule"}
}
```

`full_manuscript` 或 audited polish 必须生成完整记录。direct-entry 的局部低风险润色可以生成最小记录，不要求补跑 Step 7；但只要出现高风险智识修改，就必须进入 `requires_author_input`，不得输出 `ready_for_finalize`。

## 4. 终验边界

- 语言修订可在作者未在线时继续，前提是含义不变且保真审计通过。
- 未确认的贡献、因果、方法、局限或含义修改会阻塞 `ready_for_finalize`，但不阻塞输出带标记的润色草案。
- AI 使用披露按学校、期刊、基金或机构规则执行；不得删除真实使用记录以制造“无 AI”表象。
- 检测器结果只能作为需人工复核的弱信号，不能作为学术诚信或作者身份的单一证据。

