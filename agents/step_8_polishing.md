# Step 8: 论文润色

> 对已有正文进行成稿级精修：全文一致性、句长节奏、深层 AI 痕迹清理、术语终验和保守修订。
> Step 8 只消费正文，不负责正文生成、证据合成、引用审计或修稿路线图。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_7_writing.md` — 论文初稿 + 评审报告 + 引用审计报告
- [ ] `.skill-state/term_aliases.md` — 🆕 术语标准化映射（以本表为基准校验术语一致性）
- [ ] `.skill-state/error_log.md` — 已知 AI 痕迹模式及修复规则
- [ ] `.skill-state/decision_log.md` — 影响润色策略的决策
- [ ] `references/polish-modes.md` — 🆕 revision scope 约束
- [ ] `references/ai-trace-taxonomy.md` — 🆕 AI 痕迹分类表
- [ ] `references/genre-style-axis.md` — 🆕 target_genre 默认规则
- [ ] `references/writing-antipatterns.md` — 🆕 写作反模式回退条件

---

## 2. 适用任务 (Applicable Tasks)

- 逐句精修学术论文
- 去 AI 痕迹（29 种模式识别与清除）
- 注入人味（语音校准 + 有温度的学术表达）
- 句长波动检测与段落节奏优化
- 术语一致性检查（以 term_aliases.md 为基准）
- 成稿级全文一致性检查与保守修订

---

## 3. 不适用任务 (Non-applicable Tasks)

- 论文写作 → 路由到 `agents/step_7_writing.md`
- 引用审计 → 路由到 `agents/step_7_writing.md`（7h）
- 图表生成 → 路由到 `agents/step_7_writing.md`（7g）
- 正文生成、文献整合、证据补强、修稿路线图 → 路由到 `agents/step_7_writing.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 论文初稿 | Step 7 | .md | ✅ |
| 评审报告 | Step 7f | .md | 推荐 |
| 引用审计报告 | Step 7h | .md | 推荐 |

### 输入契约

执行润色前，必须先明确以下上下文：

| 字段 | 说明 | 缺省处理 |
|------|------|----------|
| 初稿路径 | 待润色的 `.md` 初稿文件 | 用户未指定时，使用 Step 7 最新论文初稿 |
| 目标语言 | 中文、英文或中英双语 | 继承 Step 7 初稿语言 |
| 目标体裁 | 期刊论文、学位论文、课程论文、会议论文等 | 继承 Step 7 的 target_genre（旧文档若写 `target_type`，按兼容字段处理） |
| 保留原章节编号 | 是否保持标题层级、章节编号、图表编号不变 | 默认保留 |
| 允许大幅改写 | 是否允许重排段落、改写论证顺序 | 默认不允许，只做局部结构润色 |
| 修订范围 | `local-polish / section-revision / full-manuscript-pass` | 默认 `local-polish` |

**Direct-entry input contract：**

| 可接受输入 | 最小处理 | 降级规则 |
|------------|----------|----------|
| 用户直接提供初稿 `.md/.docx/文本` | 直接进入 Phase 0 输入接收 | 不要求补跑 Step 7 |
| 初稿 + 评审意见 | 按评审意见标记修改任务 | 缺引用审计时不声明引用安全 |
| 初稿 + 引用审计报告 | 保留引用风险和修复建议 | 不重新做完整审计 |
| 只有局部章节/段落 | 只润色指定范围 | 不改全篇结构和未提供章节 |

Step 8 的直接入口只要求有可润色文本。评审报告、引用审计报告、Step 7 完整上下文都是质量增强输入，不是入口门。缺失时按降级规则标记风险，不能要求用户回跑 Step 7。

> **RAG 边界：** Step 8 不直接读取 `retrieval_candidates.json`。若未来引入 RAG，也只能消费 Step 7 已确认后的审计结论或诊断摘要，不允许跳过原文确认层。

**写作工件读取优先级：**

若同时存在 Step 7 的统一工件：

1. `style_profile.json`
2. `section_blueprints.json`
3. `writing_rationale_matrix.json`

则 Step 8 在判断 `target_genre`、章节功能、风险来源时应默认以这些 JSON 为**约束源**，不是仅作参考；对应 `.md` 只作为人工解释和展示层。  
JSON 缺失时，可降级读取 `.md`，但需在质量报告中标记“基于展示层工件解析”，不得伪装为完整风格对齐。

**三工件默认约束关系：**
- `style_profile.json`：约束句长、语域、引用密度、标题层级
- `section_blueprints.json`：约束章节功能、信息顺序、图表位置
- `writing_rationale_matrix.json`：约束保留的论证顺序、不可删改的证据链、保守改写边界

### 缺失输入降级规则

- 缺少评审报告：可以继续润色，但必须在输出报告中标记“评审依据不足”，并只做语言、结构和 AI 痕迹层面的修订。
- 缺少引用审计报告：可以继续润色，但不得声称引用安全已通过；发现疑似虚构引用、证据不足或数据异常时，只能标记为“引用安全提醒”，不替代 Step 7 的完整引用审计。

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| `diagnostic_summary.md` | .md | 标准诊断摘要：问题类型、严重度、是否可在 Step 8 修复、回退目标 |
| 论文润色稿 | .md → .docx | 精修后的终稿 |
| 修改对照表 | .md/.csv | 位置 / 原文 / 修改后 / 修改类型 / 修改原因 / 涉及规则 |
| 术语一致性报告 | .md | 术语修改数、新增术语数、Main Term 变更数 |
| 润色质量报告 | .md | AI 痕迹修复统计、句长波动检查、降级说明 |

---

## 6. 执行流程 (Execution Flow)

### 执行阶段（Phase）与润色层级（Level）的关系

- **Phase** 表示完整执行顺序，从输入接收到日志回写。
- **Level** 表示 Phase 2 内部的四层润色深度，不单独代表完整流程。

| Phase | 阶段 | 输入 | 动作 | 输出 |
|------:|------|------|------|------|
| 0 | 输入接收 | 初稿、评审报告、引用审计报告、共享记忆 | 确认输入契约，记录缺失项和降级状态 | 输入检查摘要 |
| 1 | 初稿诊断 | 初稿 + Step 7 评审/审计信息 | 按章节识别语言、结构、AI 痕迹、术语和引用风险 | `diagnostic_summary.md` + 润色任务清单 |
| 2 | 四层润色 | 初稿 + 任务清单 | 依次执行 Level 1-4，保持章节编号和引用格式稳定 | 润色正文草案 |
| 3 | 对照表生成 | 原文 + 润色正文草案 | 抽取代表性修改，按固定字段记录原因 | 修改对照表 |
| 4 | 术语终验 | 润色正文草案 + `.skill-state/term_aliases.md` | 逐章校验 Main Term、Aliases 和新术语 | 术语一致性报告 |
| 5 | DOCX 导出 | `论文润色稿.md` | 转换为 `.docx`，沿用 Step 7/项目既有样式 | `论文润色稿.docx` |
| 6 | 日志回写 | 质量报告、术语报告、修改对照表 | 仅回写可复用错误和结构性决策 | `.skill-state/` 更新摘要 |

### 职责边界

- Step 8 是成稿级精修器，不接管 Step 7 的生成、整合、审阅、校验流水线。
- Step 8 可以指出引用风险，但不重新做完整引用审计；完整引用审计仍路由到 Step 7。
- Step 8 可以做局部结构润色，但不重写论文大纲；如需重构章节，应回到 Step 2/Step 7。
- Step 8 可以更新术语表；涉及 Main Term 的重大变更时，必须同步记录到 `.skill-state/decision_log.md`。
- Step 8 可以修复写法，但不替 Step 7 重新发明 `target_genre`、章节功能或主论证结构；这些若不清晰，应回退到 Step 7 蓝图层。
- Step 8 不得绕开 `style_profile / section_blueprints / writing_rationale_matrix` 自行重设风格目标；若三工件缺失，只能按降级模式运行并显式记录。
- Step 8 不能解决的问题：新增引用或补证据、修复 claim 与证据不匹配、重构章节功能、修复图表缺失造成的论证断裂、补 systematic-review 筛选协议；以上一律导向回退，不允许“润色硬修”。
- Step 7 已经完成的基础可读性整形不应在 Step 8 中重复展开；Step 8 只处理全局一致性、节奏、终验和成稿级表达质量。

### Phase 1 标准诊断层

进入四层润色前，必须先输出 `diagnostic_summary.md`，至少逐项记录：

| 字段 | 说明 |
|------|------|
| `issue_type` | 问题类型 |
| `severity` | `low / medium / high` |
| `location` | 章节/段落/句子位置 |
| `can_fix_in_step8` | `true / false` |
| `rollback_target` | `none / step_7_revision_only / step_7_citation_audit / step_7_argument_plan / step_4_or_6_evidence_repair` |
| `recommended_action` | 推荐动作 |

**`issue_type` 固定值域：**
- `evidence_gap`
- `structure_drift`
- `language_mechanical`
- `contribution_overclaim`
- `citation_misalignment`

**诊断原则：**
- `language_mechanical` 通常可在 Step 8 修复。
- `evidence_gap`、`structure_drift`、`citation_misalignment` 默认优先考虑回退，而不是本层强行修顺。
- `contribution_overclaim` 需结合 Step 7 的 claim 与证据状态判断，不能只靠降级措辞判定为已解决。

### 润色分层架构（由浅入深）

```
Level 1: 表面清理  → 拼写、语法、标点、缩写统一
Level 2: 结构优化  → 章节逻辑、段落衔接、论证递进
Level 3: 去 AI 化  → 29 种 AI 痕迹识别与清除
Level 4: 注入人味  → 人话校准、语音注入、有温度的学术表达
```

### Level 1 — 表面清理

- 拼写错误（中英文）
- 语法错误（时态不一致、主谓不一致）
- 标点规范（中英文标点混用、空格规范）
- 缩写统一（首次出现全称+缩写，后续只用缩写）

### Level 2 — 结构优化

**反模式回退规则：**

若诊断到以下任一问题，不应直接在 Step 8 内“强行润顺”：

- 文献堆砌，不形成论证
- 章节功能漂移
- 强 claim，弱证据
- 风格目标不明

处理原则：

- 可局部修复的，记录到修改对照表并继续
- 涉及章节蓝图或 target_genre 错位的，写入润色质量报告，建议回到 Step 7

**章节风格指南：**

| 章节 | 句长波动目标 | 段落密度 | 语态偏好 |
|------|:----------:|:-------:|:-------:|
| 摘要 | ≤0.25 | 高密度信息 | 主动/被动混合 |
| 引言/绪论 | ≤0.25 | 递进式 | 主动为主 |
| 相关工作 | ≤0.35 | 主题分组 | 中性 |
| 方法 | ≤0.30 | 逻辑递进 | 被动可接受 |
| 实验 | ≤0.35 | 数据驱动 | 主动/被动混合 |
| 结论 | ≤0.25 | 总结性 | 主动为主 |

**句长波动与段落节奏检测（5 项）：**

| 检查项 | 说明 | 目标 |
|------|------|------|
| 句长波动度 | 连续句子的字数/词数方差 | ≤0.35（引言/结论 0.25） |
| 段落长度均匀化 | 各段行数偏差 | ±30% 以内 |
| 同义替换综合征 | 过度使用同义词轮换 | 术语坚持用同一个词 |
| 二元对比过度 | "not only... but also..." 等 | 每章 ≤1 次 |
| 内联标题列表 | 粗体标题+冒号开头 | 禁用，改用独立标题 |

### Level 3 — 去 AI 化（29 种模式）

**5 大类 29 种 AI 痕迹模式：**

| 类别 | 模式 | 修复 |
|------|------|------|
| **内容类** | 编造数据、虚构引用、贡献夸大、虚假新颖性声明 | 数据→PDF 验证，引用→检索文献表核实 |
| **语法类** | 过度被动语态、无主语句、"there is/are"泛滥、"it is worth noting that"冗余 | 主动态改写、删冗余引导语 |
| **风格类** | 逐论文罗列、空泛概括无证据、"not only but also"、"on the one hand...on the other hand" | 按主题分组、补具体证据 |
| **交流类** | "in conclusion" / "in summary"机械总结、过度过渡词、"as mentioned above"回指 | 用自然叙述替代 |
| **修饰类** | "robust" / "comprehensive" / "novel" 滥用、hedging 过度（may/might/could连用） | 降级到具体描述 |

### Level 4 — 注入人味

**6 种技术：**
1. **句长自然波动** — 长句（25-35 词）+ 短句（5-10 词）交替
2. **适度口语化连接** — "That said," / "Put another way," / "This is not to say..."
3. **个人判断的显式标注** — "We suspect this is because..." / "One interpretation is..."
4. **制造悬念后揭示** — 先提出问题，再给答案
5. **限定词显式使用** — "at least in the cases we examined" / "with the caveat that..."
6. **保持一个"人"的视角** — 作者是一个有判断、有偏好、有疑问的人，不是中立的摘要机器

---

### Phase 3: 修改对照表生成

修改对照表固定使用以下字段：

| 字段 | 说明 |
|------|------|
| 位置 | 章节、段落或句子位置 |
| 原文 | 修改前文本，可截取关键句 |
| 修改后 | 修改后文本 |
| 修改类型 | 语言清理 / 结构优化 / AI 痕迹修复 / 人味注入 / 术语统一 / 引用安全提醒 |
| 修改原因 | 为什么必须改，避免只写“润色” |
| 涉及规则 | Level 编号、术语规则或引用安全提醒 |

记录原则：

- 每章至少保留代表性修改。
- 标点、空格、简单错字不必逐条记录，除非属于系统性错误。
- 引用风险只记录为“引用安全提醒”，不得替代 Step 7 引用审计结论。

### Phase 3.5: 轻量一致性检查（可选增强）

若输入中存在 `response_letter_skeleton.md` 或 `rereview_report.md`，Step 8 只做轻量一致性提醒：

- 润色后正文是否可能与回应信失配
- 是否把原本保守的回应改成了过强 claim

此检查只做告警，不替代 Step 7 的修稿闭环或复评。

---

### Phase 4: 终验 — 🆕 术语一致性检查（增强）

**以 `.skill-state/term_aliases.md` 为基准：**

1. 加载 `.skill-state/term_aliases.md` 获取标准术语映射表
2. 逐章扫描正文，提取所有核心术语
3. 对比映射表：
   - 术语是否与 Main Term 一致？
   - 是否存在同义词轮换（Level 2 中的"同义替换综合征"）？
   - 是否在错误章节使用了不该出现的术语变体？
4. 不一致处理：
   - 修正为 Main Term → 记录到 before/after 表
   - 如果 Main Term 选择不当 → 更新 `.skill-state/term_aliases.md` → 记录到 `.skill-state/decision_log.md`
   - 如果属于新术语 → 追加到 `.skill-state/term_aliases.md`
5. 输出：术语一致性报告（含修改数、新增术语数、映射表更新说明）

---

### Phase 5: DOCX 导出

1. 将终验后的正文保存为 `论文润色稿.md`
2. 使用项目既有 Markdown → DOCX 转换方式生成 `论文润色稿.docx`
3. 导出时保持 Step 7 既有样式、标题层级、图表编号和引用格式
4. 如果 DOCX 生成失败，保留 `.md` 终稿，并在润色质量报告中记录失败原因和可复现命令

---

### Phase 6: 日志回写

日志回写只写运行态 `.skill-state/` 文件，不修改 `references/templates/`：

| 文件 | 写入条件 | 不写入内容 |
|------|----------|------------|
| `.skill-state/error_log.md` | 新发现的可复用 AI 痕迹、系统性术语混用、反复出现的引用风险模式 | 一次性措辞偏好、单句审美判断 |
| `.skill-state/decision_log.md` | Main Term 重大变更、句长波动目标调整、影响后续 Step 的结构性决策 | 普通语法修正、局部句式偏好 |
| `.skill-state/term_aliases.md` | 新术语追加、Main Term/Aliases 修正 | 润色说明、修改理由长文 |

---

## 7. 质量门槛 (Quality Gates)

- [ ] Level 1-4 四层润色全部完成
- [ ] `diagnostic_summary.md` 已生成，且问题已按固定 `issue_type` 分类
- [ ] 句长波动度检测已按章节输出结果（通过 / 超标 / 保留原因）
- [ ] 29 种 AI 模式扫描完成，并输出发现项总数、已修复项、保留项、保留原因
- [ ] 🆕 术语一致性检查完成——以 `.skill-state/term_aliases.md` 为基准，全文术语一致
- [ ] 修改对照表已按“位置 / 原文 / 修改后 / 修改类型 / 修改原因 / 涉及规则”产出
- [ ] 缺少评审报告或引用审计报告时，润色质量报告已标记“审计依据不足”
- [ ] 所有 `.skill-state/` 回写均符合日志边界，不误写 `references/templates/`

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `diagnostic_summary.md` 已生成
- [ ] `论文润色稿.md` 已生成
- [ ] `论文润色稿.docx` 已自动生成
- [ ] 修改对照表（位置 / 原文 / 修改后 / 修改类型 / 修改原因 / 涉及规则）已产出
- [ ] 润色质量报告已产出（AI 痕迹统计、句长波动检查、降级说明）

### 润色质量报告固定区块
- [ ] `Overall Status` 已输出：`ready_for_finalize / ready_with_warnings / not_ready_requires_rollback`
- [ ] `Issues Fixed In Step 8` 已输出
- [ ] `Issues Deferred / Rollback Required` 已输出
- [ ] `Next Action` 已输出：`finalize_polished_draft / return_to_step_7_revision_only / return_to_step_7_citation_audit / return_to_step_7_argument_plan / return_to_step_4_or_6`

### 术语一致性报告 🆕
- [ ] 全文核心术语已与 `.skill-state/term_aliases.md` 对齐
- [ ] 术语修改数：X 处
- [ ] 新增术语数：X 个（已追加到 term_aliases.md）
- [ ] Main Term 变更数：X 个（已记录到 decision_log.md）

### 错误日志更新 🆕
- [ ] 本轮是否发现了新的 AI 痕迹模式？
  - 如有 → 追加到 `.skill-state/error_log.md`，更新 Level 3 模式清单
- [ ] 术语不一致是否为系统性错误？
  - 如有 → 追加到 `.skill-state/error_log.md`，更新 Step 2/3/7 的术语规则
- [ ] 是否仅记录了可复用的系统性错误？
  - 一次性措辞偏好不得写入 `.skill-state/error_log.md`

### 决策日志更新 🆕
- [ ] 是否调整了句长波动目标？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否修改了术语 Main Term 选择？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否只记录了影响后续 Step 的结构性决策？

---

## 9. 故障排除 (Troubleshooting)

- **AI 痕迹除不尽**：回查 `.skill-state/error_log.md` 中的 AI 痕迹记录；Level 3 分类逐类排查
- **术语不一致**：以 `.skill-state/term_aliases.md` 为唯一基准，不依赖直觉判断
- **句长波动过大**：长句拆分、短句合并，目标 ≤0.35
