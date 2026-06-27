# 机理分析写作契约

本文件约束 Step 7 的内部 `mechanism_analysis` 写作准备层。它不新增公开 Step，也不新增用户可选写作模式；用户仍可直接说“写机理分析/机制分析/影响规律分析”，Agent 内部先完成机理卡片再写正文。

## 触发条件

命中以下“两段式触发”时启用：

### 第一段：机制候选召回

满足任一条件即可标记 `mechanism_candidate=true`：

- 章节标题或用户任务命中 `mechanism_core_terms`
  - 中文：`机理`、`机制`、`失效机理`、`控制机理`、`损伤机理`、`调控机制`、`驱动机制`、`演化机理`
  - 英文：`mechanism`、`mechanistic`、`failure mechanism`、`damage mechanism`、`driving mechanism`、`governing mechanism`
- 章节标题或用户任务命中 `mechanism_judgement_terms`
  - 中文：`成因`、`原因`、`根本原因`、`内在原因`、`主导因素`、`关键因素`、`决定因素`、`竞争关系`、`判别依据`
  - 英文：`root cause`、`governing factor`、`key determinant`、`dominant factor`
- 章节标题或用户任务命中 `mechanism_path_terms`
  - 中文：`影响规律`、`演化规律`、`作用路径`、`演化路径`、`转变路径`、`传导路径`、`传导链`、`作用链`、`反馈机制`、`耦合关系`
  - 英文：`causal pathway`、`evolution pathway`、`transition pathway`、`transfer path`、`causal chain`、`feedback mechanism`、`interaction effect`、`coupling`

### 第二段：机制增强确认

只有满足以下任一条件，才正式进入 `mechanism_analysis`：

- 命中 `mechanism_core_terms`
- 同时命中 `mechanism_judgement_terms` 与 `mechanism_path_terms`
- `argument_plan` 中的核心 claim 需要解释变量如何影响结果
- `argument_plan.mechanism_path` 非空
- `required_evidence` 或 `evidence_needed` 中出现：`变量传导`、`边界条件`、`机理验证`、`作用路径`
- 引用审计发现机理 claim 只有综述性或摘要级证据

若只命中第一段、不满足第二段：保留普通章节写作链，不进入 `mechanism_analysis`。

### 防误触发

- 单纯 `研究现状`、`方法介绍`、`实验结果汇总`、`参数优化结果` 默认不触发
- 仅有 `影响因素`、`影响分析`、`因素研究`，但没有 `原因 / 路径 / 机理 / 主导 / 演化 / 反馈` 之一时，不触发
- 若章节属于 `方法设计`、`实验装置`、`数据来源`，即使偶发命中 `control` / `mechanism` 单词，也不自动进入 `mechanism_analysis`
- 若触发来源仅为英文泛词 `control`、`effect`、`analysis`，必须与 `mechanism_judgement_terms` 或 `mechanism_path_terms` 联合命中

## 工件链

```text
deep_read_cards.json/md
  -> mechanism_cards.json/md
  -> mechanism_argument_plan.json/md
  -> mechanism_claim_audit.json/md
  -> mechanism_paragraph_audit.json/md
  -> 当前小节正文
```

`deep_read_cards` 负责读文献，`mechanism_cards` 负责整理机理链，`mechanism_argument_plan` 负责决定哪些 claim 可以进入正文。

推荐先执行：

```bash
python3 scripts/build_mechanism_argument_plan.py --cards-json deep_read_cards.json --output-dir .
python3 scripts/audit_mechanism_claims.py --plan-json mechanism_argument_plan.json
python3 scripts/audit_mechanism_paragraphs.py --draft-md 当前小节草稿.md --plan-json mechanism_argument_plan.json
```

若已有 MinerU ZIP 解析出的 `figure_index.json`，可追加 `--figure-index figure_index.json` 升级图表锚点；没有 MinerU 时不得阻塞写作，只能把图表证据降级为 `figure_evidence_status=unavailable_without_mineru_or_manual_pdf_check`。

若来源是 Zotero 条目，不得只因为 `deep_read_cards.json` 中 `source_trace.mineru_zip` 为空就直接判定“无 MinerU 图表锚点”。必须先检查 parent item 的 child attachments，查找 `LLM-for-Zotero-MinerU-cache-*.zip`；本地模式下还应按附件 key 到 Zotero storage 定位 ZIP。只有确认 Zotero children、本地 storage 和用户提供资产均无 ZIP/`figure_index.json` 后，才可降级为无图表锚点。

简写规则：不得直接判定“无 MinerU 图表锚点”，必须先完成 Zotero 附件核验。

## mechanism_cards 最小字段

| 字段 | 说明 |
|---|---|
| phenomenon | 要解释的现象或工程问题 |
| state_variables | 状态量、控制量、扰动量、关键参数 |
| causal_chain | 变量如何逐级传导到结果 |
| governing_model | 方程、等效模型、控制逻辑、能量流/信息流模型 |
| boundary_conditions | 工况、假设、适用范围、约束 |
| evidence_anchor | PDF 页码、chunk、图号、表号、实验/仿真条件 |
| alternative_explanations | 可能削弱当前解释的其他机制或反证 |
| validation_path | 用实验、仿真、消融、对比或图表验证的路径 |
| claim_limit | 可写 claim 强度与必须降级的边界 |
| mechanism_type | GF / GR / CDRX / DDRX / DRV / DRX 等机制标签 |
| discriminates_against | 当前机制需要和谁区分 |
| transfer_risk | 是否存在跨材料 / 跨体系外推风险 |
| figure_claim_binding | claim 绑定到哪张图、哪类图、哪些 panel |
| discrimination_matrix_used | 是否使用 CDRX/DDRX/DRV/CNT 等判别矩阵 |
| evidence_modality | `EBSD / TEM / SEM / XRD / flow_curve / mechanical_test / simulation / user_data` |
| claim_strength | `mechanism` / `numeric_comparison` / `parameter` 等句子强度 |
| required_evidence | 当前机制 claim 的最低证据要求 |
| downgrade_required | 证据不足时是否必须降强度 |

材料/机械/工程类任务还应按需加载 `references/domain-packs/materials-mechanics-writing.md`，把材料体系、热变形条件、显微组织证据和竞争机制判别纳入 `mechanism_cards`。

## 材料机制判别字段

当任务涉及 EBSD、TEM、SEM、XRD、KAM、GOS、HAGB/LAGB、织构、热变形、CDRX、DDRX、DRV、PSN、Zener pinning、CNT load transfer 等内容时，`mechanism_cards` 额外记录：

| 字段 | 说明 |
|---|---|
| materials_system | 合金/基体、增强相、制备工艺、热处理状态、初始组织 |
| thermomechanical_path | 温度、应变速率、真应变、应力状态、压缩/剪切/轧制路径 |
| microstructure_evidence | EBSD/TEM/SEM/XRD/KAM/GOS/HAGB/LAGB/织构等证据 |
| competing_mechanisms | CDRX/DDRX/DRV/PSN/Zener pinning/load transfer 等候选机制 |
| discrimination_evidence | 区分竞争机制所需证据 |
| insufficient_basis | 不能单独作为证明的依据 |

## 段落规则

机理段落默认使用以下推进链：

```text
现象 -> 状态量/控制量 -> 作用路径 -> 证据锚点 -> 适用边界 -> 回扣本节问题
```

不得把“文献 A 研究了、文献 B 发现了”当作机理分析。文献引用只用于支撑链条中的具体环节。

若 `mechanism_type` 已明确，正文还应尽量说明它与 `discriminates_against` 中竞争机制的区别；否则段落容易退化成“解释型综述”而非“判别型机理分析”。

若 `target_genre=thesis`，机理章节默认采用“判定句优先、解释句收束”的章节语言风格：先给机制判断，再补证据与边界，不以口语化解释推进段落。

## 降级规则

| 缺失项 | 允许写法 | 禁止写法 |
|---|---|---|
| causal_chain | 候选解释、可能机制 | 确定性因果结论 |
| boundary_conditions | 一般性现象说明 | 跨工况泛化结论 |
| validation_path | 理论解释或推断 | 已证明、验证了 |
| evidence_anchor | 背景性说明 | 图表、方程、参数、数值级结论 |
| full_text evidence | 背景或待精读提示 | 强机制判断 |

证据层级固定为：

```text
MinerU 图表锚点 > PDF 页/段落锚点 > PDF 全文无页码锚点 > 摘要/元数据
```

无 MinerU 或无 `figure_index.json` 时，仍可写机理链，但只能基于 PDF 全文/页段/摘要证据进行保守表述；不得自动写“如图 X 所示”“图中可见”等视觉判断，也不得补写未核验的图号、公式号、页码或精确数值。

若 `transfer_risk` 为 `cross_material_requires_boundary` 或 `same_family_different_material`，正文必须显式写边界句，如“该模型提供解释框架，但不能直接替代当前材料体系中的实验机制证据”。

## 风格约束

- 学位论文机理章节应优先使用“据此可判定”“由此表明”“进一步可归结为”“需要指出的是”等书面连接句。
- 应减少“如果说……那么……”“换言之”“也就是说”“这个判断也说明了”等解释腔连接句，避免段落节奏被口语化解释主导。
- 机理段落应尽量采用“机制判别句 -> 图文/全文证据 -> 边界句 -> 收束句”的结构，而不是先铺解释再迟迟落结论。
- “图的价值不在于……而在于……”这类元评论式句法可用，但每段至多 1 处，且必须直接服务于机制判别。

## 质量门

- 每个机理强 claim 必须绑定至少一个全文级证据锚点。
- 有竞争解释时，正文必须说明边界或保留不确定性。
- 不能用摘要级证据支撑实验参数、模型细节、图表解释或机制证明。
- 没有实验、仿真或对比验证时，不得把相关性写成因果证明。
- 没有验证路径时，措辞必须降级为“可能说明/可解释为/提示存在”。
- `mechanism_claim_audit` 中 `downgrade_required` 的 claim 不得以强机理结论进入正文。
- `mechanism_paragraph_audit` 中命中的 `cross_material_claim_missing_boundary`、`visual_reference_without_figure_id`、`mechanism_discrimination_not_explicit` 应在定稿前处理。
- 若 `target_genre=thesis`，应额外自查是否存在解释腔过密、判定句滞后和口语化连接句堆叠。

### 科学空话 / 机理空话诊断

以下命中项应进入 Step 8 的 `mechanism_bluff` 或 Step 7 的机理段落审计，但不能替代引用审计：

- `mechanism_without_state_variables`：只有“促进/抑制/改善”，没有状态量或控制量。
- `causal_jump_without_validation`：从性能变化直接跳到微观机制，没有验证路径。
- `visual_claim_without_panel`：写“图中可见/如图所示”，但无 figure/table/panel 锚点。
- `proof_verb_without_evidence`：使用“证明/验证/揭示”但缺全文、图表、实验或仿真证据。
- `generic_strengthening_list`：晶粒细化、位错强化、第二相强化、载荷传递等套话并列，但没有当前体系证据。

命中以上规则时，默认动作是 `downgrade_claim`、补边界句或回退 Step 7/4/6 补证据；不得在 Step 8 中新增外部证据。
