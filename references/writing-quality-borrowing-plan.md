# 写作质量借鉴与融入方案

> 目标：把外部 workflow 里对“写作质量”的有效做法，转成当前 skill 已有的工件和闸门，而不是新增一套并行写作系统。

style_profile / section_blueprints / writing_rationale_matrix 是当前落点。

## 适用范围

这个方案只处理写作质量相关的借鉴，重点是：

- 章节组织是否更清楚
- 段落是否先论证、后展开
- 风格是否稳定
- 证据是否先收敛再进正文
- 返修是否可追踪

不处理：

- 新增公开 Step
- 新增独立写作模式
- 直接复制外部原句
- 把外部默认体裁变成全局默认值

## 当前 skill 已有的吸收位

| 外部可借鉴点 | 当前吸收位 | 落地方式 |
|---|---|---|
| 章节先行、再正文 | `section_blueprints` | 先锁定每节功能、长度、claim 和禁写项 |
| 风格学习 | `style_profile` | 抽取句长、语域、引用密度、标题层级和过渡方式 |
| 论证编排 | `writing_rationale_matrix` / `argument_plan` | 把“为什么这样写”显式化 |
| 深读组织 | `deep_read_cards` | 把外部的“读深一点”转成 claim/method/boundary 卡片 |
| 证据约束 | `evidence_pack` / 证据矩阵 | 先判定能写多强，再决定写什么 |
| 修订闭环 | `revision_roadmap` / `response_letter_skeleton` / `draft_risk_summary` | 把问题、动作、风险和回退写清楚 |

这里吸收的是结构、语言和修订模式，不是原句。

## 融入原则

1. 先提炼稳定模式，再写入现有 schema。
2. 只吸收结构、节奏、证据组织和修订方式，不吸收模板化句子。
3. 借鉴必须服务当前任务目标，不能反过来改写任务边界。
4. 任何新规则先落到 `style_profile`、`section_blueprints`、`writing_rationale_matrix`，再考虑是否值得补到说明文档。
5. 如果外部做法和当前证据等级冲突，以证据边界为准。

## 落地流程

1. 选样本。
2. 标注可借鉴点。
3. 分三类归档：结构类、语言类、修订类。
4. 映射到当前工件。
5. 用 `writing-antipatterns` 做反向校验。
6. 只把“能稳定复用”的部分写进 Step 7 规则。

## 结构类借鉴

优先吸收这几类结构特征：

- 每节只有一个主功能
- 小节之间有明确承上启下
- 先给 claim，再给证据，再给解释
- 章节功能和证据等级绑定

这些内容应落到：

- `section_function`
- `key_claims`
- `evidence_needed`
- `do_not_write`
- `transition_from`
- `transition_to`
- `risk_flags`

## 语言类借鉴

优先吸收这几类语言特征：

- 句长节奏
- 术语一致性
- 引用密度
- 过渡短语
- 语域收口

这些内容应落到：

- `style_profile`
- `style_notes`
- `writing_rationale_matrix`

## 修订类借鉴

优先吸收这几类修订特征：

- 先找问题，再改正文
- 先写风险，再做收口
- 修订动作和证据状态绑定
- 回退路径明确

这些内容应落到：

- `revision_roadmap.md`
- `response_letter_skeleton.md`
- `draft_risk_summary.md`

## 禁止项

- 不把“看起来顺”的句子直接当成规则
- 不把某个目标期刊的局部写法扩展成全局默认
- 不把风格样本里的表达直接搬进正文
- 不得把外部句子或默认体裁直接搬进正文
- 不在没有证据时用语言美化掩盖证据空洞

## 最小验收

借鉴方案成立的标志不是“多了一个说明文件”，而是：

1. 外部样本能被拆成可执行约束。
2. 这些约束能映射到现有工件。
3. 写作时能拦住直写正文和强 claim 扩写。
4. 修订时能回到可追踪的风险与证据边界。
