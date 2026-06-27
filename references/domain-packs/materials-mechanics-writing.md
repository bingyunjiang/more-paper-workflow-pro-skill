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

## 7. 与 Step 7/8 的边界

- Step 7 使用本领域包生成 `mechanism_cards`、`mechanism_argument_plan`、`figure_table_panel_binding` 和 `evidence_gap_list`
- Step 8 只用本领域包识别 `mechanism_bluff`、降强度、补边界句或提示回退
- 没有全文、图表、实验、仿真或用户数据时，不得把材料机理写成已证明结论
