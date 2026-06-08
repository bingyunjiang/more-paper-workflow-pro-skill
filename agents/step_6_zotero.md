# Step 6: Zotero 文库管理

> Zotero 文库从架构生成到 PDF 导入到一致性调整到综述矩阵到期刊风格学习。这是写作前最后的知识组织步骤。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_5_download.md` — 下载的 PDF（paper-temp/）
- [ ] `agents/step_2_outline.md` — 大纲关键词（大纲结构 + 术语映射表）
- [ ] `references/zotero-structure-template.md` — Zotero 架构示例
- [ ] `references/literature-review-matrix-schema.md` — 综述矩阵 schema
- [ ] `references/journal-style-learning-guide.md` — 期刊风格学习方法论
- [ ] `.skill-state/error_log.md` — 已知错误及修复规则
- [ ] `.skill-state/decision_log.md` — 影响本 Step 的结构性决策

---

## 2. 适用任务 (Applicable Tasks)

- 生成 Zotero 集合架构（6a）
- 导入 PDF 到 Zotero（6b）
- 大纲修订后文库一致性调整（6c）
- 生成文库-大纲对照表 PDF（6d）
- 生成文献综述矩阵（6e）
- 目标期刊风格学习与写作蓝图（6f）

---

## 3. 不适用任务 (Non-applicable Tasks)

- 论文写作 → 路由到 `agents/step_7_writing.md`
- PDF 下载 → 路由到 `agents/step_5_download.md`

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 大纲关键词 | Step 2 | .md | ✅ |
| 下载的 PDF | Step 5 | paper-temp/*.pdf | ✅ |
| 检索文献表 | Step 4 | .md | 用于综述矩阵 |

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| zotero-架构.md | .md | Zotero 集合结构 |
| 综述矩阵.csv + .md | CSV/Markdown | 13 列证据矩阵 |
| research_dossier/ | 目录 | 期刊风格画像 + 章节蓝图 + 写作逻辑矩阵 |

---

## 6. 执行流程 (Execution Flow)

### 6a：生成 Zotero 文库架构

```bash
python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md
```

示例结构：
```
📁 论文文献库
├── 📁 1-基础
│   ├── P0-A1 基础理论 / 综述
│   └── P0-A3 方法综述
├── 📁 2-方向一
│   ├── P1-D1 子方向A
│   └── P1-D2 子方向B
└── 📁 3-方向二
    ├── P0-B1 方法A
    └── P0-B2 方法B
```

### 6b：导入 PDF 到 Zotero

**方式一：手动拖拽（推荐，零配置）** — 拖拽 PDF 到对应集合，Zotero 自动识别元数据。

**方式二：Zotero MCP 对话操作** — 通过 `zotero_add_by_doi` 等工具按 DOI 导入。

```bash
python3 scripts/setup_zotero.py --install --target auto
python3 scripts/setup_zotero.py --smoke-test
```

### 6c：大纲修订后的文库一致性调整

四步流程：映射现有文库结构与优化大纲 → 诊断三端关联性（机理→源控制→路径控制→验证）→ 文献缺口定位（库内冗余/连接带空白/整体缺项）→ 执行调整（先确认再执行）

### 6d：生成文库-大纲对照表 PDF

```bash
python3 scripts/generate_report_pdf.py ...
# 产出：Zotero-大纲对应关系_论文名.pdf
```

### 6e：生成文献综述矩阵（写作前最后质量关）

**13 列矩阵：** 作者年份 | 标题 | 研究问题 | 理论/概念 | 数据/样本 | 方法 | 核心发现 | 贡献 | 局限 | 与我的主题关系 | 可引用摘录 | 我的笔记 | DOI/URL

**证据优先级（逐级回退）：**
```
1. Zotero 笔记 (zotero_get_notes)              ← 最高优先级
2. PDF 标注/高亮 (zotero_get_annotations)       ← 精读标注
3. Zotero 元数据 (zotero_get_item_metadata)     ← 标题/作者/DOI/摘要
4. PDF 全文 (zotero_get_item_fulltext)          ← 完整原文
5. 仅摘要 (abstractNote)                        ← 最低优先级
```

> ⚠️ **不要一上来就读 PDF 全文。** 先用笔记、标注和元数据填表。

**缺失值约定：** `未提及`（论文确实未讨论）/ `待补充`（计划后续补全）/ `推断：{内容}`（基于已有信息合理推断）

### 6f：目标期刊风格学习与写作蓝图 🆕

**核心理念：** Step 7 的 paper_type 轴告诉你"写什么类型的论文"，Step 6f 告诉你"怎么写才能让这个期刊的读者和审稿人觉得'这是自己人写的'"。

**工作流：**
```
Step 6f-1: 风格剖析      → style_profile.md        (四维度量化：格式化/结构/引用/语言)
Step 6f-2: 章节蓝图      → section_blueprints.md    (逐节写作计划：论证链+证据映射+图表位置)
Step 6f-3: 写作逻辑矩阵  → writing_rationale_matrix.md (逐单元理由)
Step 6f-4: LaTeX 校验    → latex_check.md（可选）
```

**两种分析深度：**

| 模式 | 范文数 | 时长 | 产出 | 适用场景 |
|------|:---:|------|------|------|
| **Flash** ⚡ | 3 篇 | ~3 min | `style_profile.md` | 初次投稿该期刊 |
| **Pro** 🔬 | 6 篇 | ~8 min | `style_profile.md` + `research_dossier.md` | 核心目标期刊 |

```bash
python3 scripts/learn_journal_style.py --target-journal "Applied Thermal Engineering" --pdf-dir paper-temp/ --mode flash
python3 scripts/generate_section_blueprints.py research_dossier/style_profile.md 大纲关键词.md --evidence 综述矩阵.csv --output research_dossier/
python3 scripts/generate_writing_rationale.py research_dossier/section_blueprints.md --style-profile research_dossier/style_profile.md --output research_dossier/writing_rationale_matrix.md
```

---

## 7. 质量门槛 (Quality Gates)

- [ ] Zotero 架构与大纲章节一一对应
- [ ] 所有 T1/T2 论文已导入 Zotero
- [ ] 6c 一致性调整：三端关联性检查通过（✅充足/🟡偏少/🔴缺口已标注）
- [ ] 综述矩阵：13 列完整，证据优先级规则已遵循
- [ ] 6f 期刊风格：Flash 或 Pro 模式已完成，style_profile.md 已生成

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] `zotero-架构.md` 已生成
- [ ] PDF 已导入 Zotero 对应集合
- [ ] `综述矩阵.csv` + `综述矩阵.md` 已生成
- [ ] 6f 产出：`research_dossier/` 目录完整

### 错误日志更新 🆕
- [ ] 本轮是否出现新的 AI 操作错误？
  - 文库架构与大纲不一致 → 追加到 `.skill-state/error_log.md`
  - 综述矩阵证据填充错误 → 追加到 `.skill-state/error_log.md`
  - 期刊风格分析偏差 → 追加到 `.skill-state/error_log.md`

### 决策日志更新 🆕
- [ ] 是否调整了文库架构策略？→ 记录到 `.skill-state/decision_log.md`
- [ ] 是否修改了综述矩阵列定义？→ 记录到 `.skill-state/decision_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：开始撰写论文（Step 7）
  > **下一步 → Step 7：** 所有文献准备就绪，综述矩阵构建完毕，目标期刊风格已学习，开始按蓝图撰写论文。

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **Zotero MCP 连接失败**：运行 `python3 scripts/setup_zotero.py --smoke-test` 诊断
- **综述矩阵证据不足**：按证据优先级逐级回退，优先使用 Zotero 笔记和标注
- **期刊风格分析偏差**：确保范文选择来自目标期刊近 3 年高引论文
