# Step 1 Router: 研究主题与选题预审入口

本文件是 Step 1 的新入口层，不替代 [step_1_topic.md](./step_1_topic.md)。

## 作用

- 识别当前请求是否应进入 Step 1
- 判断入口轴：`user_stage` / `goal_type` / `search_depth` / `evidence_risk`
- 以最小加载方式把请求路由给旧版 Step 1 主协议
- 若用户明确要求“弹窗模式 / popup / modal”，则 Step 1 直接按弹窗交互发起，不再先输出普通长段说明

## 入口命中条件

优先命中以下意图：

- 研究方向模糊，需要聚焦
- 已有大方向，但不知道怎么收窄成题目
- 希望判断选题值不值得做
- 希望预判创新性、重要性、可行性

若用户已给完整大纲或完整初稿，则不进入本 Step。

## 交互模式约定

- Step 1 默认允许两种进入方式：`普通对话` 与 `弹窗模式`
- 若用户在启动 skill、进入 Step 1、或描述选题需求时明确说出“用弹窗模式”“弹窗即可”“popup/modal”，应视为强指令
- 命中该指令后，当前轮首要动作是直接发起弹窗收集 Step 1.1 所需最小信息，而不是先展示完整工作流说明
- 弹窗内容仍服务 Step 1 的 `决策包式` 收敛，不改变 Step 1 的产物、边界和后续交接字段
- 若当前智能体或宿主端不支持原生弹窗，则必须自动降级为`结构化文本弹窗`
- `结构化文本弹窗`的要求是：一轮内集中列出当前决策包所需字段，用户一次性回复；不得退化为零散的一问一答

## 轴定义

### `user_stage`

- `master-early`
- `master-late`
- `phd-early`
- `phd-mid`
- `phd-late`
- `researcher`
- `engineer`

### `goal_type`

- `graduation-safe`
- `proposal-ready`
- `journal-submission`
- `review-study`
- `engineering-report`

### `search_depth`

- `quick`
- `standard`
- `deep`

### `evidence_risk`

- `low`
- `medium`
- `high`

## 加载顺序

1. `static/core/output-contract.md`
2. `references/step1-topic-review-rubric.md`
3. `references/step1-handoff-schema.md`
4. `agents/step_1_topic.md`

## 输出要求

除 `研究主题.md` 外，本 Router 还应显式确认：

- 识别出的 4 个入口轴
- 当前是否建议进入 Step 2 或 Step 3
- 若风险较高，指出需要回到 Step 1 的哪个子阶段继续聚焦
