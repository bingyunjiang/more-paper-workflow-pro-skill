# 博士学位论文整篇论证合同

本合同用于 `target_genre=thesis` 且目标为博士学位论文的 Step 7。它补充章节级写作门，关注整篇论文是否形成可答辩、可复核的原创论证，不以篇幅、术语密度或复杂句式冒充博士深度。

## 1. 直接进入与完成状态

- Step 7 可从大纲、已有章节、PDF、Zotero、证据包或仅有研究问题直接进入，不要求补跑 Step 1-6。
- 输入不完整时建立 `doctoral_thesis_map.json` 的 provisional 版本，并把缺口写成待确认项；这不阻塞局部写作或 `draft_ready`。
- 只有声明 `evidence_closed / ready_for_step8` 时，才要求映射与当前稿件哈希一致、审计结果为 `doctoral_ready`。
- 局部章节不得伪造尚未完成的整篇闭环；未覆盖部分必须标为 `not_in_current_scope` 或 `requires_author_input`。

## 2. 博士深度的八个闭环

1. **中心问题闭环**：用可研究、可反驳的中心问题统摄子问题，说明对象、条件、矛盾和评价准则。
2. **研究问题闭环**：每个 RQ 绑定章节、方法、结果、结论及未解决边界，不能只绑定背景材料。
3. **贡献闭环**：每项贡献绑定具体结果和证据，区分理论、方法、实证、数据或工程贡献。
4. **新颖性边界**：逐项对照最近邻工作，说明相同点、真正增量、未声称内容及检索覆盖边界。
5. **章节功能闭环**：每章说明它解决哪个 RQ、承接什么前提、产出什么判断、如何转入下一章。
6. **可复现闭环**：研究对象、数据、变量、参数、基线、实验/仿真步骤、统计方法和环境可复核；不适用项必须给理由。
7. **反证与边界闭环**：记录负结果、冲突证据、替代解释、失效工况、外推限制和威胁有效性因素。
8. **跨章综合闭环**：结论不是章节摘要拼接，而是形成跨章命题，回答各结果如何共同改变对中心问题的认识。

## 3. `doctoral_thesis_map.json` 最小结构

```json
{
  "schema_version": "doctoral-thesis-map.v1",
  "draft_sha256": "...",
  "scope": "full_thesis|chapter|section",
  "central_research_problem": "...",
  "research_questions": [{"id":"RQ1","question":"...","chapter_ids":["C3"],"result_ids":["R1"],"conclusion":"...","status":"closed"}],
  "results": [{"id":"R1","summary":"...","evidence_anchors":["table-3-2"],"boundary":"..."}],
  "contributions": [{"id":"K1","type":"method","claim":"...","result_ids":["R1"],"evidence_anchors":["table-3-2"],"chapter_ids":["C3"],"nearest_work":"...","novelty_boundary":"...","not_claimed":"..."}],
  "chapters": [{"id":"C3","function":"...","rq_ids":["RQ1"],"claim_ids":["CL1"],"evidence_anchors":["table-3-2"],"transition_from":"C2","transition_to":"C4"}],
  "reproducibility": {"research_object":"...","data_or_materials":"...","variables_and_parameters":"...","baselines":"...","procedure":"...","analysis_method":"...","environment":"...","na_reasons":[]},
  "negative_and_conflicting_evidence": [{"item":"...","treatment":"..."}],
  "cross_chapter_synthesis": [{"proposition":"...","chapter_ids":["C3","C4"],"result_ids":["R1","R2"],"boundary":"..."}],
  "limitations_and_transfer_boundaries": ["..."],
  "authorial_decisions": [{"decision":"...","rationale":"...","status":"author_confirmed"}],
  "unresolved_author_inputs": []
}
```

## 4. 写作执行规则

- 先写“本章在整篇论证中完成什么判断”，再展开材料；不得按文献、实验或图表出现顺序堆叠。
- 结果章区分观察、分析与解释；讨论章比较替代解释并返回 RQ；结论逐项回答 RQ，并严格回扣已证实的贡献。
- 贡献措辞由证据强度决定。`首次、突破、填补空白、揭示机制` 必须同时具备近邻比较、检索覆盖和直接证据。
- 方法细节以第三方能否复核为准。缺少关键数据、代码或参数时要说明可复现等级和缺失原因。
- 作者必须确认贡献、因果解释、方法选择、限制和实践含义等核心智识判断；Agent 可以组织与质询，不能代替作者虚构确认。

### 4.1 逐章全局控制循环

逐章写作不是把全文地图切碎。每次进入一章都必须执行同一个 `prepare -> write -> close -> incremental audit` 循环：

1. **prepare**：读取当前 `doctoral_thesis_map.json` 和稿件哈希，为本章生成 `chapter_logic_snapshot.json`。快照必须冻结中心问题、本章 RQ、允许使用的 claim/结果/贡献、前章已完成结论、后章预留内容、承上/启下关系和当前风险。
2. **write**：正文只能在快照允许范围内展开；后章预留 claim 不得提前闭合，前章已有结论不得换词重复冒充新贡献。
3. **close**：用 `chapter_close_record.json` 记录本章实际形成的 claim、结果、证据锚点、边界、反证、未解决问题和下一章必须承接的命题。
4. **conflict check**：检查抢写后章、跨章 claim 重复、未登记结果、RQ 漏答、贡献强度漂移、术语漂移和过渡断裂。存在冲突时只输出报告，不回写全局地图。
5. **atomic write-back**：无冲突时才原子更新当前章节状态、稿件哈希和 `chapter_cycle_log`；不得顺带改写其他章节的学术判断。
6. **incremental audit**：每章关闭后检查当前已写范围；整篇 `doctoral_ready` 仍由最终审计判定。

推荐入口：

```bash
python3 scripts/doctoral_chapter_cycle.py prepare 论文初稿.md doctoral_thesis_map.json C3 chapter_logic_snapshot.json
python3 scripts/doctoral_chapter_cycle.py close 论文初稿.md doctoral_thesis_map.json chapter_logic_snapshot.json chapter_close_record.json
```

direct-entry 只有当前章材料时，`prepare` 可生成 `provisional` 快照并把未知的前后章关系列入 `global_context_gaps`，不要求补跑 Step 1-6；但不得把 provisional 状态描述为全文逻辑已经闭环。

## 5. 完成判定

运行 `scripts/audit_doctoral_thesis_readiness.py`。结果分为：

- `provisional`：允许直接进入和继续写作，但不能声称博士整篇论证已闭环。
- `doctoral_ready`：当前稿件哈希一致，所有必需闭环成立，可进入 `evidence_closed / ready_for_step8`。
- `blocked`：用户要求高完成状态，但存在未绑定 RQ/贡献、不可复核方法、未处理冲突证据或待作者确认的核心判断。
