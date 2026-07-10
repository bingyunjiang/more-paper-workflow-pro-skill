# Step 7 Figure Marker Syntax

写作中需要引用参考文献的图/表时，不要中断写作去手动翻图库。使用轻量标记声明图位：

```markdown
充电桩内部采用模块化布局，12个模块分左右两列排列。
[图: 充电桩内部结构]

气流从 AIC 进入，经模块区域后从 AOC 排出...
[图: 气流截面方向]
```

## 规则

- 标记格式：`[图: 简短描述]`（全角/半角冒号均可）
- 描述要具体（如「充电桩内部结构」），不要写「示意图」「见下图」等模糊描述
- 每处 `[图: xxx]` 只声明一张图，不要合并
- 同一张图被多处引用时，脚本只分配给第一处，后续需改写描述或手动处理
- `[图: xxx]` 前应有完整的正文引出句，可用句号、冒号或逗号自然收束；标记语法不得强迫作者预留半句话
- `[图: xxx]` 后一行必须紧跟对该图的解释，说明该图展示了什么、如何支撑论点

示例：

```markdown
理解这一结构布局是后续热分析和风道优化的前提。
[图: 充电桩内部结构]
该图展示了模块的对称布局...
```

## 解析时机

当前章节写作完成后，调用：

```bash
python scripts/resolve_figure_refs.py \
  --draft draft.md \
  --cards deep_read_cards.json \
  --output draft_resolved.md
```

## 图片来源优先级

1. MinerU ZIP 有 caption 的图（最高质量）
2. MinerU ZIP 无 caption 的图
3. `figure_index.json` 候选
4. PyMuPDF 直接从 PDF 抽图（最低质量，无 caption）

脚本会将每个 `[图: xxx]` 替换为完整的「引出句 + 图片 + 图注」单元。未匹配到图的标记保留占位符并生成警告。

如果当前没有 `deep_read_cards`，先跑 `scripts/build_deep_read_cards.py` 为章节对应的文献生成卡片。脚本支持 `--cards` 参数重复传入多组卡片（每章一份）。
