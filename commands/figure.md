# Figure

## 何时使用

- 从 CSV、实验数据或统计结果生成论文图表
- 重绘论文原图、截图、裁剪图或光栅曲线
- 做曲线数字化、视觉对齐、语义审计或矢量验证
- 生成带 manifest、QA、checksums 和可移植验证的复现包

## 自动路由

1. 只选择并插入已有 MinerU/PDF/图片资产时，不启动绘图后端。
2. 基于可信结构化数据生成普通新图时，使用 `quick`。
3. 输入参考图、VisualSpec，或要求重绘、数字化、严格 QA、可编辑矢量和可复现交付时，使用 `reproduction`。
4. 用户显式指定 backend 时覆盖自动判断；严格后端缺依赖时必须失败，不得降级。

## 统一入口

```bash
python scripts/generate_figures.py --backend quick --spec figures.json --output figures
python scripts/generate_figures.py --backend reproduction --spec visualspec.json --source source.png --output bundle --require-strict
```

详细协议按需读取 `references/scientific-figure-reproduction.md`。
