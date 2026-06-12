# Step 8 Router: 润色与保守修订入口

本文件是 Step 8 的路由层，不替代 [step_8_polishing.md](./step_8_polishing.md)。

## 1. 作用

- 把润色任务先做 revision scope 判定
- 默认保守改写，不将 Step 8 变成开放式重写器
- 按 `paper_type / language / target_genre / revision_scope` 最小加载

## 2. revision_scope

- `local-polish`：局部润色
- `section-revision`：章节级修订
- `full-manuscript-pass`：全稿一轮保守精修

## 3. 路由规则

- 用户只给一段或一节 -> `local-polish`
- 用户给一章并要求优化结构 -> `section-revision`
- 用户给完整稿件并要求最终精修 -> `full-manuscript-pass`

## 4. 加载顺序

1. `manifest.step8.yaml`
2. `static/core/output-contract.md`
3. `references/polish-modes.md`
4. `references/ai-trace-taxonomy.md`
5. `agents/step_8_polishing.md`

## 5. 输出要求

Step 8 默认必须明确：

- 保留了哪些原结构
- 哪些修改属于语言清理，哪些属于结构修订
- 哪些问题只是提醒，需回到 Step 7 处理
