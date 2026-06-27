# 材料/机械/工程写作领域增强包

本文件是 Step 7 的可选领域增强包，只在任务命中材料、机械、热变形、显微组织、工程机理或目标期刊明确属于相关领域时加载。它不改变 Step 7/8 的通用边界，不替代 PDF 原文、Zotero note、annotation 或用户实验数据。

加载范围：只在任务命中材料、机械、热变形、显微组织或工程机理时加载；不得作为所有论文的全局默认写作规则。

## 触发条件

命中以下任一类信号时启用：

- 材料体系：合金、复合材料、CNTs/Al、铝基、镁合金、钢、陶瓷、增强相、晶粒、析出相
- 热加工/机械过程：热变形、压缩、轧制、剪切、应变速率、真应变、流变应力、加工图
- 显微组织：EBSD、TEM、SEM、XRD、KAM、GOS、HAGB、LAGB、织构、取向差、位错
- 机理术语：CDRX、DDRX、DRV、DRX、PSN、Zener pinning、CNT pinning、load transfer
- 体裁/期刊：MSEA、Acta、Scripta、JMPT、塑性工程学报、材料热处理学报、中文核心材料/机械论文

## 1. materials_system_card

写材料类论文前，必须确认当前材料体系是否清楚：

- 基体/合金牌号
- 增强相或第二相
- 制备工艺
- 热处理状态
- 初始组织
- 样品方向、取样位置和尺度
- 对照组或基准材料

缺失这些字段时，只能写背景或待补证据，不能写强机理判断。

## 2. thermomechanical_process_card

热变形、塑性加工或机械性能段落至少核对：

- 温度
- 应变速率
- 真应变
- 应力状态
- 压缩/剪切/轧制/弯曲路径
- 保温、冷却或加载历史
- 流变曲线、加工图或应力-应变数据来源

参数句属于 `claim_strength=parameter`，必须有 PDF、表格、用户数据或标准文件锚点。

## 3. microstructure_evidence_card

显微组织 claim 必须说明证据类型和可见范围：

- EBSD: KAM、GOS、HAGB/LAGB、取向差、织构、晶粒尺寸统计
- TEM: 位错、亚晶、界面、析出相、SAED、EDS
- SEM: 形貌、断口、第二相分布
- XRD: 相组成、织构、峰位/峰宽变化
- 统计要求：样本量、误差棒、尺度条、取样位置、处理方式

若只有形貌图，没有统计或相鉴定，不能写“证明机制”，只能写“提示存在/可能相关”。

## 4. mechanism_discrimination_card

材料机理段落必须比较竞争机制，避免“只要晶粒细化就写 DRX”。

| 观察 | 候选机制 | 必要证据 | 不能只靠 |
|---|---|---|---|
| 晶粒细化 | CDRX | LAGB 到 HAGB、亚晶旋转、KAM/GOS 演化、取向差连续增加 | 晶粒变小 |
| 原晶界新晶粒 | DDRX | 原晶界鼓出、项链状组织、迁移晶界、HAGB 新晶粒 | HAGB fraction 增加 |
| KAM 降低 | DRV 或再结晶后软化 | KAM 降低、亚晶形成、流变软化及空间对应 | 把恢复直接等同于再结晶 |
| 细晶区尺寸稳定 | Zener/CNT pinning | CNT 位于晶界、TEM/EDS/SAED、尺寸稳定统计 | 只因加入 CNT 就推断钉扎 |
| 强度提高 | 载荷传递/细晶/位错/第二相强化 | 力学数据、界面证据、断口或模型支撑 | 只看强度提升 |

### DRX_discrimination_matrix

动态再结晶相关 claim 必须先判别机制，再决定动词强度。`DRX` 只能作为总称；若正文写 CDRX、DDRX 或 DRV，必须说明判据。

| 机制 | 可支持的证据组合 | 常见误判 | 允许写法 |
|---|---|---|---|
| CDRX | LAGB 向 HAGB 转化、亚晶旋转、取向差连续增加、KAM/GOS 演化、晶内渐进式取向分裂 | 只因晶粒细化就判定 CDRX | “提示 CDRX 参与”“可解释为连续再结晶过程” |
| DDRX | 原晶界鼓出、项链状新晶粒、迁移晶界、原晶界附近 HAGB 新晶粒、流变软化与空间位置对应 | 只因 HAGB fraction 增加就判定 DDRX | “符合 DDRX 特征”“可能存在不连续再结晶形核” |
| DRV | KAM 或位错密度降低、亚晶形成、流变软化、位错重排，没有清晰新晶粒形核证据 | 把恢复直接写成再结晶 | “动态回复可能贡献软化”“不能单独证明再结晶” |
| PSN | 大颗粒附近局部取向梯度、新晶粒围绕颗粒形核、颗粒尺寸/分布证据 | 只因存在第二相就写 PSN | “可能诱发 PSN，需要颗粒邻域证据” |

硬边界：

- 只有晶粒尺寸变小，不得写“证明发生 DRX”。
- 只有 HAGB 比例升高，不得区分 CDRX/DDRX。
- 只有 KAM 降低，不得把 DRV 写成 DRX。
- 缺少空间对应关系时，不得把流变软化直接归因到单一机制。

### EBSD_claim_evidence_matrix

EBSD 指标只能支撑对应范围内的 claim：

| EBSD 证据 | 可支持 | 不能单独支持 |
|---|---|---|
| KAM | 局部取向梯度、相对位错密度变化、变形储能趋势 | 精确位错密度、具体再结晶机制证明 |
| GOS | 区分低畸变晶粒、辅助识别再结晶/回复状态 | 单独证明 CDRX 或 DDRX |
| HAGB/LAGB | 晶界类型比例、亚晶向高角晶界演化线索 | 单独证明形核路径 |
| misorientation profile | 亚晶旋转、取向差连续演化 | 没有统计时支撑全局机制 |
| IPF / grain map | 晶粒形貌、取向分布、局部细化 | 无统计时支撑显著性比较 |
| texture / pole figure | 织构变化、变形路径线索 | 单独证明强化机制 |

EBSD 图表必须记录 `step_size / cleanup_method / grain_threshold / HAGB_LAGB_threshold / sample_region`。缺这些信息时，图表 claim 标记 `risk_flags=ebsd_processing_missing`。

### TEM_SEM_XRD_claim_boundary

| 表征 | 可支持 | 不能单独支持 | 高风险提示 |
|---|---|---|---|
| TEM | 位错、亚晶、界面、析出相、CNT 位置、SAED 局部相鉴定 | 全局相含量、统计显著性、宏观强化贡献 | 缺比例尺、缺取样位置、缺 SAED/EDS |
| SEM | 形貌、断口、颗粒分布、宏观缺陷 | 原子尺度界面、细晶机制、相鉴定 | 只有形貌不能写机制证明 |
| EDS | 元素分布、界面或颗粒成分线索 | 晶体结构、相唯一性证明 | 点扫/面扫需说明区域 |
| SAED | 局部晶体结构或取向关系 | 全样品相组成 | 需绑定 TEM 区域 |
| XRD | 相组成、织构或峰宽变化线索 | 局部界面机制、纳米尺度分布 | 峰重叠和定量方法需说明 |

### CNT_Al_strengthening_mechanism_matrix

CNTs/Al 或类似金属基复合材料不能把“加入 CNT”直接写成钉扎或载荷传递。必须区分候选机制：

| 候选机制 | 需要证据 | 不能只靠 | 降级写法 |
|---|---|---|---|
| load transfer | 界面结合、断口拔出/断裂、力学模型、模拟或应力传递路径 | 强度提高、加入 CNT | “可能参与载荷传递” |
| Orowan strengthening | CNT/颗粒间距、尺寸分布、位错绕过证据或模型 | 纳米增强相存在 | “可能存在绕过强化贡献” |
| CTE mismatch strengthening | 热膨胀失配、冷却历史、位错密度变化、模型估算 | 热处理过程存在 | “热失配可能引入额外位错” |
| grain refinement | 晶粒尺寸统计、误差棒、加工路径一致 | 单张组织图 | “与晶粒细化相关” |
| Zener/CNT pinning | CNT 位于晶界、尺寸稳定统计、界面 TEM/EDS/SAED、热稳定对比 | 加入 CNT 或晶粒小 | “提示钉扎效应，仍需界面证据” |
| second phase / precipitation | 相鉴定、尺寸/体积分数、分布统计 | XRD 弱峰或形貌点 | “可能存在第二相贡献” |

### mechanism_overclaim_examples

| 过强写法 | 问题 | 保守改写 |
|---|---|---|
| “EBSD 证明发生 CDRX” | EBSD 单图通常不足以证明完整机制 | “EBSD 中 LAGB/HAGB 与 KAM 变化提示 CDRX 可能参与组织演化” |
| “CNTs 钉扎晶界导致细晶稳定” | 需要 CNT 位于晶界和尺寸稳定统计 | “细晶稳定可能与 CNT 相关，仍需界面定位和统计证据支撑钉扎判断” |
| “强度提高源于载荷传递增强” | 强度提高不是载荷传递的唯一证据 | “强度提高可能由载荷传递、细晶和位错强化共同贡献” |
| “KAM 降低说明再结晶完成” | KAM 降低也可能来自回复 | “KAM 降低说明局部畸变减弱，可能对应回复或再结晶后软化” |

## 5. figure_claim_panel_card

图文一致性最低要求：

- 每条图表 claim 绑定 `figure_id / table_id / panel_id`
- 图注和正文解释必须回答同一条 claim
- “如图所示”后面的解释只能来自图中可见信息、图注、统计表或全文锚点
- 缺 panel、缺标尺、缺统计、缺样本量时，必须写入 `risk_flags`

典型 `risk_flags`：

- `visual_claim_without_panel`
- `scale_bar_missing`
- `sample_size_missing`
- `statistics_missing`
- `phase_identification_missing`
- `mechanism_discrimination_missing`
- `cross_material_transfer_risk`

## 6. journal_style_card

目标体裁不同，写法不同：

- MSEA / Acta / Scripta：强调机制证据、图表清晰度、创新边界和定量支撑
- JMPT / 工程机械类期刊：强调工艺路径、参数窗口、可复现条件和工程适用性
- 中文核心：术语一致、图表编号规范、实验条件完整、讨论不过度外推
- 学位论文：需要更长的机理链和背景铺垫，但仍不能用篇幅替代证据

详细期刊/体裁差异见 `references/domain-packs/materials-journal-style.md`。该文件只在目标期刊或体裁明确时加载，不作为材料领域的全局默认风格。

## 7. 与 Step 7/8 的边界

- Step 7 使用本领域包生成 `mechanism_cards`、`mechanism_argument_plan`、`figure_table_panel_binding` 和 `evidence_gap_list`
- Step 8 只用本领域包识别 `mechanism_bluff`、降强度、补边界句或提示回退
- 没有全文、图表、实验、仿真或用户数据时，不得把材料机理写成已证明结论
