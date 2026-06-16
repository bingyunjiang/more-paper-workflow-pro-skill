# Step 1 Router: 研究主题与选题预审入口

本文件是 Step 1 的新入口层，不替代 [step_1_topic.md](./step_1_topic.md)。

## 作用

- 识别当前请求是否应进入 Step 1
- 判断入口轴：`user_stage` / `goal_type` / `search_depth` / `evidence_risk`
- 以最小加载方式把请求路由给旧版 Step 1 主协议

## 入口命中条件

优先命中以下意图：

- 研究方向模糊，需要聚焦
- 已有大方向，但不知道怎么收窄成题目
- 希望判断选题值不值得做
- 希望预判创新性、重要性、可行性

若用户已给完整大纲或完整初稿，则不进入本 Step。

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
