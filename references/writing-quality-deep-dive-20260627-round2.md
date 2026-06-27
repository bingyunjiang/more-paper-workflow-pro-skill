# 写作质量深挖备忘录：通用科学写作与电力电子方向

日期：2026-06-27

范围：

- 继续忽略“合规下载 / 公开展示口径 / Sci-Hub 口径收敛”。
- 本轮只深挖写作质量、证据链、图表表达、工程/电力电子方向适配。

## 1. 新结论

More Paper 的写作质量提升不能只围绕材料/机械。对用户长期方向（充电桩、储能、电力电子、EMS、V2G、快充、无线充电、超级电容）而言，还需要两类补充：

1. 通用科学写作质量 rubric：解决句子清晰、段落推进、图表先行、论证顺序、摘要/引言/方法/结果/讨论边界。
2. 电力电子/能源系统证据门：解决拓扑、控制、损耗、效率、热管理、稳定性、并网、EMS、V2G、标准与实验可复现问题。

材料/机械领域包适合解决“显微组织/机理判别”，但不能覆盖电力电子论文常见风险：仿真替代实验、效率/损耗不闭合、控制稳定性没证明、并网/V2G 只讲收益不讲约束、EMS 优化只给目标函数不交代边界条件。

## 2. 外部资料转化

### 2.1 Duke Scientific Writing Resource

可执行转化：

- `subject_action_audit`
  - 检查句子主语是否是读者需要追踪的对象。
  - 检查动作是否落在动词上，而不是藏在 nominalization 中。
  - 检查主语和动词是否距离过远。
- `old_new_flow_audit`
  - 句首承接旧信息，句末放新信息或重点。
  - 段内每句应与前句有可见连接。
- `paragraph_coherence_audit`
  - 首句和末句是否回答同一段落功能。
  - 段落是否只有一个主任务。

落点：

- Step 7：写前 `section_blueprints` 和 `argument_plan`。
- Step 8：只处理可读性和局部衔接，不改变证据边界。

### 2.2 Gopen & Swan / Reader Expectation

可执行转化：

- `topic_position`: 句首放上下文、已知信息、读者正在追踪的对象。
- `stress_position`: 句末放本句最需要强调的新信息。
- `reader_energy`: 如果读者需要回读才能知道主语、动作或上下文，就标为可读性风险。

适合生成机器字段：

- `topic_link`
- `stress_payload`
- `backward_link`
- `reader_repair_needed`

### 2.3 Whitesides 写作顺序

可执行转化：

- 先组织图、表、数据、结论和大纲，再写正文。
- 对结果/讨论章节，先生成 `figure_first_argument_plan`。
- 若没有图表或数据支撑，不写强结果解释。

落点：

- `argument_plan_first`
- `figure_first_discussion`
- `claim_order_check`

### 2.4 IEEE Author Center

IEEE 对工程论文给出直接可执行的结构边界：

- 标题要具体、简洁、描述性，避免空泛“new/novel”。
- 摘要应总结研究、结论和潜在影响，且自包含。
- 引言应定位已有文献、说明问题和重要性。
- 方法应说明做了什么和怎么做，使研究可复现。
- 结果应呈现获得的结果，图表用于趋势或精确数值。
- 讨论说明结果意味着什么以及贡献在哪里。
- 结论可以写更广泛影响，但不要夸大。
- 参考文献必须直接支撑工作，不应堆无关引用。
- 图形要准确、清晰，并考虑灰度/色盲可读性。

这些可以转成工程论文的硬质量门，而不是风格建议。

## 3. 建议新增：通用科学写作质量 rubric

建议文件：

- `references/scientific-writing-quality-rubric.md`

建议章节：

### 3.1 sentence_clarity_audit

字段：

- `subject`
- `action_verb`
- `nominalization_risk`
- `subject_verb_distance`
- `reader_repair_needed`

触发降级：

- 主语不是实际研究对象。
- 主要动作藏在名词中。
- 主语和动词距离过长。

### 3.2 old_new_flow_audit

字段：

- `backward_link`
- `new_information`
- `stress_position`
- `topic_shift_intentional`

触发降级：

- 句首突然引入新对象。
- 句末只放空话，不放本句重点。
- 段落对象跳动但没有逻辑推进。

### 3.3 paragraph_function_audit

字段：

- `paragraph_role`
- `first_sentence_function`
- `last_sentence_function`
- `single_task`
- `transition_to_next`

触发降级：

- 一段同时做背景、方法、结果和讨论。
- 段首提出的问题和段末结论不匹配。

### 3.4 figure_first_argument_plan

字段：

- `figure_or_table_id`
- `data_message`
- `claim_supported`
- `caption_scope`
- `text_before_figure`
- `text_after_figure`

触发降级：

- 图表没有明确 message。
- 图后解释超出图表可见范围。
- 结果段落先写机制结论，再补图表。

### 3.5 phrasebank_guardrail

原则：

- Phrasebank 只能提供表达功能候选，不提供证据。
- 句式替换不得改变 claim 强度。
- 未通过证据审计的 claim 不能用更顺的表达包装。

## 4. 建议新增：电力电子/充电/V2G 领域包

建议文件：

- `references/domain-packs/power-electronics-ev-energy-writing.md`

### 4.1 power_topology_card

检查：

- 拓扑结构是否清楚：AC/DC、DC/DC、LLC、DAB、Vienna、三电平、矩阵变换器等。
- 开关器件、频率、磁件、母线电压、功率等级是否交代。
- 对比对象是否一致：同功率、同输入/输出、电压范围、冷却条件。

高风险：

- 只给效率曲线，不交代测试条件。
- 只说“高效率/高功率密度”，没有损耗分解或体积/质量基准。

### 4.2 control_and_stability_card

检查：

- 控制对象：电压、电流、功率、SOC、频率、相位、阻抗。
- 控制方法：PI、MPC、droop、PLL、滑模、预测控制、强化学习等。
- 稳定性证据：小信号模型、Bode/Nyquist、Lyapunov、阻抗稳定、仿真扰动、实验阶跃。
- 参数鲁棒性：负载、温度、器件、通信延迟、采样频率。

高风险：

- 只给仿真波形就写“系统稳定”。
- 只说“鲁棒性强”，没有参数扰动或边界条件。

### 4.3 efficiency_loss_thermal_card

检查：

- 损耗来源：开关损耗、导通损耗、磁损、驱动损耗、辅助电源、散热。
- 效率测量：仪器、功率等级、负载点、温度、输入输出范围。
- 热管理：热阻、冷却方式、温升、稳态/瞬态热结果。

高风险：

- 峰值效率替代全负载效率图。
- 仿真效率替代实测效率。
- 温升结果没有环境温度和稳态条件。

### 4.4 EMS_optimization_card

检查：

- 目标函数：成本、碳排、峰谷差、SOC 健康、用户等待、变压器负载。
- 约束：SOC、功率、电价、车流、储能容量、并网功率、用户行为、通信延迟。
- 基准：无 EMS、规则控制、传统优化、已有算法。
- 可复现：数据来源、时间粒度、场景数量、求解器、随机种子。

高风险：

- 只给总成本下降，不说明电价、负荷、车流和约束。
- 强化学习/AI 方法没有基准和消融。

### 4.5 V2G_grid_claim_card

检查：

- 功率流：V1G / V2G / V2H / V2B / V2X 是否区分。
- 服务类型：削峰填谷、频率响应、备用、无功支撑、电压调节。
- 电池影响：循环、SOC 窗口、退化成本、用户可用性。
- 并网约束：逆变器容量、标准、通信、安全、聚合商、市场规则。

高风险：

- 只写“V2G 提升电网稳定性”，没有电网指标或控制策略。
- 只写收益，不写电池退化和用户约束。

### 4.6 wireless_fast_charging_card

检查：

- 快充：倍率、充电曲线、热限制、电池寿命、安全边界。
- 无线充电：耦合系数、偏移、效率、EMI/EMC、异物检测、补偿拓扑。
- 超级电容：功率密度、能量密度、循环寿命、等效串联电阻、热表现。

高风险：

- 只比较充电时间，不写热、安全和寿命。
- 无线充电只给最大效率，不给偏移和负载范围。

## 5. 建议新增：工程论文目标体裁包

建议文件：

- `references/domain-packs/power-energy-journal-style.md`

建议覆盖：

- IEEE Transactions 风格：方法、可复现性、图表清晰、直接支撑引用。
- Applied Energy / Energy 风格：系统边界、场景、能源/经济/环境指标。
- 工程中文核心：参数完整、图表规范、结果不过度外推。
- 学位论文：系统架构、控制策略、实验平台、仿真与实验边界分清。

## 6. 修改计划

### P1：新增通用科学写作 rubric

文件：

- `references/scientific-writing-quality-rubric.md`

接入：

- `agents/step_7_writing.md` 预读清单
- `agents/step_8_polishing.md` Level 2 / Level 3 可读性诊断

测试：

- rubric 必须包含 `subject_action_audit / old_new_flow_audit / paragraph_function_audit / figure_first_argument_plan / phrasebank_guardrail`
- rubric 必须声明不改变 claim 强度、不替代证据审计

### P2：新增电力电子/EV/能源领域包

文件：

- `references/domain-packs/power-electronics-ev-energy-writing.md`

接入：

- Step 7 预读清单：仅在任务命中充电桩、储能、电力电子、EMS、V2G、快充、无线充电、超级电容等方向时加载。
- `mechanism_analysis`：增加 `evidence_modality` 的工程扩展，如 `waveform / efficiency_curve / thermal_map / grid_metric / optimization_result / hardware_prototype`。

测试：

- 领域包必须包含 `power_topology_card / control_and_stability_card / efficiency_loss_thermal_card / EMS_optimization_card / V2G_grid_claim_card / wireless_fast_charging_card`
- 明确不作为材料论文默认规则。

### P3：新增工程能源目标体裁包

文件：

- `references/domain-packs/power-energy-journal-style.md`

测试：

- 包含 IEEE、Applied Energy/Energy、中文核心、学位论文。
- 声明目标期刊/体裁明确时才加载。

### P4：脚本层以后再做

本轮不建议立即修改脚本。先把合同和领域包打稳，再考虑：

- `audit_engineering_claims.py`
- `audit_figure_claim_bindings.py` 增加工程图表类型
- `deterministic_writing_diagnostics.py` 增加工程空话规则

## 7. 来源记录

- Duke Scientific Writing Resource, Lesson 1: Subjects and Actions
  - https://sites.duke.edu/scientificwriting/lesson-1-subjects-and-actions/
- Duke Scientific Writing Resource, Lesson 2: Cohesion, Coherence, and Emphasis
  - https://sites.duke.edu/scientificwriting/lesson-2-cohesion-coherence-and-emphasis/
- Duke Scientific Writing Resource, Lesson 3: Concision and Simplicity
  - https://sites.duke.edu/scientificwriting/lesson-3-concision-and-simplicity/
- Gopen & Swan, The Science of Scientific Writing
  - https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf
- IEEE Author Center, Structure Your Article
  - https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- IEEE Author Center, Create Graphics for Your Article
  - https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/
- IEEE Author Center, Research Reproducibility
  - https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/research-reproducibility/
