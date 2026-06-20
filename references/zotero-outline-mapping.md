# Zotero 文库与论文大纲对照表 PDF 生成方案

## 用途

文库调整（Step 6.3）完成后，生成一份可视化对照文档，展示每章每节对应的 Zotero 集合及文献覆盖情况。

## 写作阶段读取纪律

- 该对照不仅用于展示，也用于 Step 7 的取证边界控制。
- 写作时按“大纲节号/标题 -> Zotero 子集合”读取；写 `1.1` 就只读 `1.1` 对应集合，写 `1.1.1` 就只读 `1.1.1` 对应集合。
- 不得因为同章下还有其他相关集合，就默认扫完整章、完整分册或整个 Zotero 文库。
- 若当前小节证据不足，可以扩展到同章相邻集合，但必须在输出中说明扩展原因和扩展范围。
- 对照表应尽量细化到“章-节-小节”层级，避免只给章级集合名，导致写作时范围过大。

## 输出示例结构

```
封面：论文标题 + "Zotero文库与论文大纲对应关系"
第1-5章 + 创新点：逐节对照表（大纲节号 | 集合名 | 篇数 | 覆盖色块）
覆盖热力图总览：Ch1~Ch6 六行色块，一目了然
图例：✅充足 🟡偏少 🔴缺口 🔵原创
附录：最终文库结构 + 需补充的缺口清单
```

## 技术方案

### 方案 A：fpdf2（推荐，纯 Python，中文支持好）

```python
from fpdf import FPDF

# 使用系统自带中文字体
pdf = FPDF()
pdf.add_font('STHeiti', '', '/System/Library/Fonts/STHeiti Medium.ttc')

# 表格绘制：每行数据，最后一列用颜色块标注
def row(texts, col_widths, colors=None):
    # colors: list of (r,g,b) tuples per column, or None
    x0, y0 = pdf.get_x(), pdf.get_y()
    for i, (txt, cw) in enumerate(zip(texts, col_widths)):
        x = x0 + sum(col_widths[:i])
        if colors and colors[i]:
            pdf.set_fill_color(*colors[i])
            pdf.rect(x, y0, cw, 5, 'DF')
        pdf.set_xy(x+1, y0+0.5)
        pdf.cell(cw-2, 4, txt)
    pdf.set_xy(x0, y0+5)
```

### 方案 B：python-docx

如有 Word 需求，用 python-docx 替代 fpdf2，生成 .docx 格式。

## 色标规范

| 色标 | RGB | 含义 | 覆盖情况 |
|------|-----|------|---------|
| 绿色 | (220,245,220) | ✅ 充足 | 篇数足够支撑写作 |
| 黄色 | (255,255,220) | 🟡 偏少 | 需补充或重点利用 |
| 红色 | (255,220,220) | 🔴 缺口 | 需检索或作研究空白 |
| 蓝色 | (220,235,255) | 🔵 原创 | 无文献，论文自创贡献 |

## 覆盖热力图格式

每行格式：`ChN 章名  ✅✅🟡🔴🔵`（每章 N 个符号对应 N 个小节）

```
Ch1 绪论    🟡🟡🔴🔴🟡🟡
Ch2 机理    ✅✅✅✅🔴🔴
Ch3 源控    ✅✅✅✅✅🔵
Ch4 路径    ✅✅✅✅🟡🔵
Ch5 验证    🟡✅✅✅✅
```
