# Step 8 AI Trace Demo Folder

这个目录是可直接复制运行的最小 Step 8 demo 样本。

## 目录内容

```text
step8-ai-trace-demo/
├── README.md
└── 论文初稿.md
```

## 用法

在仓库根目录运行：

```bash
python3 scripts/run_step8_ai_trace.py --project-root examples/demo/step8-ai-trace-demo
```

## 预期输出

运行后，该目录下会新增：

- `.skill-state/ai_trace_diagnostics.json`
- `diagnostic_summary.md`
- `revision_ledger.json`
- `revision_ledger.md`
- `润色质量报告.md`

## 适合什么场景

- 想验证 Step 8 AI-trace 链条是否能跑通
- 想快速理解输出工件之间的关系
- 想给新用户一个可复制、可直接运行的最小样本
