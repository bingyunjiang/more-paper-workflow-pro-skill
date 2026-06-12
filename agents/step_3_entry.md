# Step 3 Router: 检索方案入口

本文件是 Step 3 的轻量路由层，不替代 [step_3_search_plan.md](./step_3_search_plan.md)。

## 1. 作用

- 判断用户要的是“检索计划”，不是“直接执行检索”
- 根据请求把 Step 3 细分为不同 workflow
- 避免在 Step 3 装载 Step 5/6/7 的重内容

## 2. workflow 轴

- `standard`：常规结构化检索方案
- `citation-expansion`：向前/向后引用扩展方案
- `prisma-s`：检索透明度与日志方案
- `chinese-sources`：中文源优先的检索策略

## 3. 路由规则

- 明确要求“设计检索式/数据库方案/关键词框架” -> `standard`
- 明确要求“引文网络/向前向后引用/参考文献扩展” -> `citation-expansion`
- 明确要求“PRISMA/PRISMA-S/检索合规/透明度” -> `prisma-s`
- 明确要求“知网/万方/中文文献路线” -> `chinese-sources`

混合请求允许命中多个 workflow，但主输出仍是单一搜索计划。

## 4. 加载顺序

1. `manifest.step3.yaml`
2. `static/core/output-contract.md`
3. `references/evidence-tier-policy.md`
4. workflow 对应 reference
5. `agents/step_3_search_plan.md`

## 5. 输出要求

Step 3 产物至少应交付：

- 关键词组
- 数据库与优先级
- inclusion / exclusion 边界
- 预期 evidence tier
- 进入 Step 4 的执行建议
