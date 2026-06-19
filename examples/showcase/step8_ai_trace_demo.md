# Step 8 AI Trace Demo

下面是一条可直接运行的 Step 8 AI 味确定性检查链路示例。

## 最小目录结构

```text
demo-project/
├── 论文初稿.md
└── .skill-state/
```

说明：

- 只需要一份 `论文初稿.md` 就能起跑
- `.skill-state/` 可以提前建好，也可以由脚本按需生成

## 最小输入文件

示例 `论文初稿.md` 可只放 1-2 段正文，例如：

```md
值得注意的是，本文方法在系统中起到关键作用。此外，研究表明该方法有效。
这里需要补文献，图表待补。
```

## 命令 1：进入项目目录

```bash
cd demo-project
```

预期：

- 当前目录下能看到 `论文初稿.md`

## 命令 2：运行 Step 8 AI Trace 入口

```bash
python3 scripts/run_step8_ai_trace.py --project-root .
```

预期：

- 终端打印 `draft`、`diagnostics_json`、`diagnostic_summary`、`revision_ledger`、`revision_ledger_md`、`polish_quality_report`

## 命令 3：检查产物

```bash
ls -1 .skill-state/ai_trace_diagnostics.json diagnostic_summary.md revision_ledger.json revision_ledger.md 润色质量报告.md
```

预期：

- 所有 5 个文件都存在

## 默认输出

- `.skill-state/ai_trace_diagnostics.json`
- `diagnostic_summary.md`
- `revision_ledger.json`
- `revision_ledger.md`
- `润色质量报告.md`

## 关键检查点

- `.skill-state/ai_trace_diagnostics.json`
  - 应包含 `summary`
  - 应包含 `step8_decision`
  - 应包含 `status_contract`
- `diagnostic_summary.md`
  - 应包含 `## AI 味确定性检查摘要`
  - 应包含 `### Step 8 总判断`
  - 应包含 `### 统一状态契约`
- `revision_ledger.md`
  - 应包含 `## 问题分流`
  - 应包含 `### 可直接修订 / 需作者决定 / 当前依据不足`
- `润色质量报告.md`
  - 应包含 `## AI 味检查结果`
  - 应包含 `### 统一状态契约`

## 行为说明

1. 读取 `论文初稿.md`
2. 运行 `deterministic_writing_diagnostics.py`
3. 将 `AI 味确定性检查摘要` 区块写入或更新到 `diagnostic_summary.md`
4. 将结构化 issue merge 到 `revision_ledger.json`
5. 从合并后的 JSON 导出正式风格的 `revision_ledger.md`
6. 将 `AI 味检查结果` 区块写入或更新到 `润色质量报告.md`

## 典型用途

- 在 Step 8 开始时快速生成一批 `language_mechanical` 问题
- 为后续保守修订提供高置信度可修项
- 不替代 Step 7 引用审计，只补表达层诊断

## 适合什么时候用

- 已经有初稿，想先跑一轮 Step 8 表达层诊断
- 想先得到一个 `revision_ledger` 分诊单，再决定是否正式润色
- 想让 `.skill-state/ai_trace_diagnostics.json` 成为 Step 8 runtime 状态源，供 `artifact_passport.json` / 路由层继续消费

## 可直接复制的样本目录

如果你不想自己先写第一份输入文件，可直接使用：

- `examples/demo/step8-ai-trace-demo/`

该目录内已经包含可运行的 `论文初稿.md`。在仓库根目录执行：

```bash
python3 scripts/run_step8_ai_trace.py --project-root examples/demo/step8-ai-trace-demo
```
