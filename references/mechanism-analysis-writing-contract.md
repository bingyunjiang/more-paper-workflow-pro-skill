# 机理分析写作契约

本文件约束 Step 7 的内部 `mechanism_analysis` 写作准备层。它不新增公开 Step，也不新增用户可选写作模式；用户仍可直接说“写机理分析/机制分析/影响规律分析”，Agent 内部先完成机理卡片再写正文。

## 触发条件

命中以下任一情况时启用：

- 章节标题或用户任务包含：机理、机制、影响规律、作用路径、耦合关系、传导路径、失效机理、控制机理
- 英文任务包含：mechanism、mechanistic、causal pathway、coupling、transfer path
- `argument_plan` 中的核心 claim 需要解释变量如何影响结果
- 引用审计发现机理 claim 只有综述性或摘要级证据

## 工件链

```text
deep_read_cards.json/md
  -> mechanism_cards.json/md
  -> mechanism_argument_plan.json/md
  -> mechanism_claim_audit.json/md
  -> 当前小节正文
```

`deep_read_cards` 负责读文献，`mechanism_cards` 负责整理机理链，`mechanism_argument_plan` 负责决定哪些 claim 可以进入正文。

推荐先执行：

```bash
python3 scripts/build_mechanism_argument_plan.py --cards-json deep_read_cards.json --output-dir .
python3 scripts/audit_mechanism_claims.py --plan-json mechanism_argument_plan.json
```

若已有 MinerU ZIP 解析出的 `figure_index.json`，可追加 `--figure-index figure_index.json` 升级图表锚点；没有 MinerU 时不得阻塞写作，只能把图表证据降级为 `figure_evidence_status=unavailable_without_mineru_or_manual_pdf_check`。

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

## 段落规则

机理段落默认使用以下推进链：

```text
现象 -> 状态量/控制量 -> 作用路径 -> 证据锚点 -> 适用边界 -> 回扣本节问题
```

不得把“文献 A 研究了、文献 B 发现了”当作机理分析。文献引用只用于支撑链条中的具体环节。

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

## 质量门

- 每个机理强 claim 必须绑定至少一个全文级证据锚点。
- 有竞争解释时，正文必须说明边界或保留不确定性。
- 不能用摘要级证据支撑实验参数、模型细节、图表解释或机制证明。
- 没有实验、仿真或对比验证时，不得把相关性写成因果证明。
- 没有验证路径时，措辞必须降级为“可能说明/可解释为/提示存在”。
- `mechanism_claim_audit` 中 `downgrade_required` 的 claim 不得以强机理结论进入正文。
