# 通用科学写作质量 Rubric

本文件约束 Step 7 / Step 8 的基础科学写作质量。它只处理读者理解、句子推进、段落功能和图表论证顺序，不改变 claim 强度，不替代引用审计，也不能把候选证据包装成强证据。

## 适用边界

- Step 7：用于 `section_blueprints`、`argument_plan`、正文生成前的可读性与论证顺序检查。
- Step 8：用于 Level 2 / Level 3 的可读性诊断和局部衔接修复。
- 不适用：新增文献、提高证据等级、重写章节主论证、改变作者贡献点。

若本 rubric 与 `claim_strength / required_evidence / evidence_anchor` 冲突，以证据审计结果为准。

## 1. subject_action_audit

检查句子的主语和动作是否让读者一眼知道“谁做了什么”。

| 字段 | 说明 |
|---|---|
| `subject` | 读者需要持续追踪的对象，如材料体系、拓扑、算法、变量、实验组 |
| `action_verb` | 主要动作，优先用动词承载，不藏在名词化结构里 |
| `nominalization_risk` | 主要动作是否被写成“影响/提升/优化/分析/研究”等抽象名词 |
| `subject_verb_distance` | 主语和谓语之间是否夹入过多限定语 |
| `reader_repair_needed` | 读者是否需要回读才能找出主语、动作或逻辑对象 |

降级信号：

- 主语是“本文/本研究/相关工作”，但真正对象是参数、机制、拓扑或数据。
- 动作藏在“进行……分析”“实现……优化”“产生……影响”中。
- 主语和动作距离过远，导致句子中段失焦。

## 2. old_new_flow_audit

检查段内每句是否从旧信息自然过渡到新信息。

| 字段 | 说明 |
|---|---|
| `backward_link` | 句首承接前句、前段或图表中的已知对象 |
| `new_information` | 本句新增的变量、结果、解释或限制 |
| `stress_position` | 句末是否放置本句最重要的新信息 |
| `topic_shift_intentional` | 段内话题切换是否有明确目的 |

降级信号：

- 句首突然引入新对象，前文没有铺垫。
- 句末只放“具有重要意义/表现良好/提供参考”等空泛结尾。
- 段落对象从方法跳到结果、再跳到意义，但没有逻辑桥接。

## 3. paragraph_function_audit

每段只承担一个主要任务，避免一段同时写背景、方法、结果和讨论。

| 字段 | 说明 |
|---|---|
| `paragraph_role` | `context / gap / approach / result / comparison / mechanism / implication / limitation` |
| `first_sentence_function` | 首句是否定义本段任务 |
| `last_sentence_function` | 末句是否收束本段任务 |
| `single_task` | 是否只有一个主任务 |
| `transition_to_next` | 是否为下一段留下明确连接 |

降级信号：

- 段首在提问题，段末却跳到贡献宣称。
- 结果段中混入未验证机制解释。
- 一段同时承担综述、方法说明、实验结果和意义升华。

## 4. figure_first_argument_plan

结果、讨论、机制、工程验证章节应先组织图表和数据 message，再写正文。

| 字段 | 说明 |
|---|---|
| `figure_or_table_id` | 图号、表号、panel 或数据源 |
| `data_message` | 图表能直接支持的核心信息 |
| `claim_supported` | 图表支撑的 claim |
| `caption_scope` | 图注已经说明的变量、条件和边界 |
| `text_before_figure` | 正文引出句要提出的观察问题 |
| `text_after_figure` | 图后解释句只能解释图表可见范围 |

降级信号：

- 图表没有明确 message，只作为装饰或堆料。
- 图后解释超出图表可见范围。
- 结果段先写机制结论，再补图表作为背书。

## 5. phrasebank_guardrail

短语库只能帮助表达功能，不能替代证据。

- 可用：引出研究缺口、限定范围、过渡对比、说明方法边界。
- 不可用：把弱证据改写成强 claim，把候选机制包装成确定结论，把摘要级信息写成全文级判断。
- 句式替换不得改变 `claim_strength`、`required_evidence`、`support_grade` 或 `downgrade_required`。

## Step 7 使用规则

- 在正文前先检查 `section_blueprints` 是否有清晰段落功能和图表顺序。
- 每个强结果句、参数句、机制句应能通过 `figure_first_argument_plan` 或引用审计追溯证据。
- 若 `subject_action_audit` 和 `old_new_flow_audit` 暴露读者障碍，先修蓝图和段落顺序，再生成正文。

## Step 8 使用规则

- 只修读者障碍、衔接断裂、句子失焦和表达机械化。
- 不因为句子更顺就提高 claim 强度。
- 发现证据不足、图表断裂或章节功能错误时，回退 Step 7，而不是在 Step 8 继续润色。
