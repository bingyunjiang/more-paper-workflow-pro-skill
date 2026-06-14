# Step 8 Router: 润色与保守修订入口

本文件是 Step 8 的路由层，不替代 [step_8_polishing.md](./step_8_polishing.md)。

## 1. 作用

- 把润色任务先做 revision scope 判定
- 默认保守改写，不将 Step 8 变成开放式重写器
- 按 `paper_type / language / target_genre / revision_scope` 最小加载
- Step 8 只消费已有正文并做成稿级精修；不接管 Step 7 的正文生成、证据合成、引用审计或修稿路线图。

## 2. revision_scope

- `local-polish`：局部润色
- `section-revision`：章节级修订
- `full-manuscript-pass`：全稿一轮保守精修

## 3. 路由规则

- 用户只给一段或一节 -> `local-polish`
- 用户给一章并要求优化结构 -> `section-revision`
- 用户给完整稿件并要求最终精修 -> `full-manuscript-pass`

## 4. Artifact Passport 读取规则

Step 8 启动时先检查 `$CWD/.skill-state/artifact_passport.json`：

- 有 `draft` 时，可直接进入 `local-polish / section-revision / full-manuscript-pass`，具体由文本范围和用户目标决定。
- 有 `polishing` 时，按 `resume` 或局部修订处理。
- 只有 `citation_audit`、没有正文时，只能做风险解释或回到 Step 7 审计/修稿计划，不能假装已进入润色。
- 缺引用审计时，Step 8 只做润色与术语终验风险标记，不替代 Step 7 的引用审计结论。
- Passport 的全局 `route_mode` 不覆盖 Step 8 的 `revision_scope / target_genre`。

## 5. 加载顺序

1. `manifest.step8.yaml`
2. `static/core/output-contract.md`
3. `references/polish-modes.md`
4. `references/ai-trace-taxonomy.md`
5. `agents/step_8_polishing.md`

## 6. 输出要求

Step 8 默认必须明确：

- 保留了哪些原结构
- 哪些修改属于语言清理，哪些属于结构修订
- 哪些问题只是提醒，需回到 Step 7 处理
