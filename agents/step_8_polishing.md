# Step 8: 论文润色

> 对 Step 7 产出的论文初稿进行精炼、润色、去 AI 痕迹，**同时注入人味**，提升至可投稿水平。
> 核心能力：逐句精修 + before/after/reason 对照表 + 29 种 AI 模式识别 + 句长波动检测。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_7_writing.md` — 论文初稿 + 评审报告 + 引用审计报告
- [ ] `.skill-state/term_aliases.md` — 🆕 术语标准化映射（以本表为基准校验术语一致性）
- [ ] `.skill-state/error_log.md` — 已知 AI 痕迹模式及修复规则
- [ ] `.skill-state/decision_log.md` — 影响润色策略的决策

---

## 2. 适用任务 (Applicable Tasks)

- 逐句精修学术论文
- 去 AI 痕迹（29 种模式识别与清除）
- 注入人味（语音校准 + 有温度的学术表达）
- 句长波动检测与段落节奏优化
- 术语一致性检查（以 term_aliases.md 为基准）

---

## 3. 不适用任务 (Non-applicable Tasks)

- 论文写作 → 路由到 `agents/step_7_writing.md`
- 引用审计 → 路由到 `agents/step_7_writing.md`（7h）
- 图表生成 → 路由到 `agents/step_7_writing.md`（7g）

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 论文初稿 | Step 7 | .md | ✅ |
| 评审报告 | Step 7f | .md | ✅ |
| 引用审计报告 | Step 7h | .md | ✅ |

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 论文润色稿 | .md → .docx | 精修后的终稿 |
| 修改对照表 | before/after/reason 三列 |

---

## 6. 执行流程 (Execution Flow)

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

### Phase 6: 终验 — 🆕 术语一致性检查（增强）

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

## 7. 质量门槛 (Quality Gates)

- [ ] Level 1-4 四层润色全部完成
- [ ] 句长波动度检测通过（各章节目标范围内）
- [ ] 29 种 AI 模式扫描完成，≥90% 已修复
- [ ] 🆕 术语一致性检查完成——以 `.skill-state/term_aliases.md` 为基准，全文术语一致
- [ ] Before/after/reason 三列修改对照表已产出

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `论文润色稿.md` 已生成
- [ ] `论文润色稿.docx` 已自动生成
- [ ] 修改对照表（before/after/reason）已产出

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

### 决策日志更新 🆕
- [ ] 是否调整了句长波动目标？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否修改了术语 Main Term 选择？→ 记录到 `.skill-state/decision_log.md`

---

## 9. 故障排除 (Troubleshooting)

- **AI 痕迹除不尽**：回查 `.skill-state/error_log.md` 中的 AI 痕迹记录；Level 3 分类逐类排查
- **术语不一致**：以 `.skill-state/term_aliases.md` 为唯一基准，不依赖直觉判断
- **句长波动过大**：长句拆分、短句合并，目标 ≤0.35
