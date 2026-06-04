# 中文技术文档批量提取与 PDF 分析报告生成

> 适配场景：分析现有工程技术文档（.docx/.doc）组合 → 生成结构化中文分析报告 PDF

## 快速启动

### 1. 批量提取 .docx 文本

```python
import docx
doc = docx.Document(path)
texts = [p.text for p in doc.paragraphs if p.text.strip()]
```

### 2. 批量提取 .doc（旧格式）文本 — macOS 专用

```python
import subprocess
# macOS textutil 原生支持 .doc → .txt
subprocess.run(["textutil", "-convert", "txt", "-output", outpath, path])
with open(outpath, "r") as f:
    lines = [l.strip() for l in f if l.strip()]
```

> `textutil` 是 macOS 内置工具，无需额外安装。Linux/Windows 上可用 `antiword` 或 `libreoffice --headless --convert-to txt` 替代。

### 3. 生成中文 PDF 报告（fpdf2 + STHeiti）

#### 字体注册

```python
from fpdf import FPDF

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
        # fpdf2 >= 2.5.1: uni 参数已废弃，直接 add_font
        self.add_font("STHeiti", "", font_path)
```

#### 典型表格布局

```python
def table_header(self, cols, widths):
    """表头行：深蓝底色+白色字"""
    self.set_font("STHeiti", "B", 9)
    self.set_fill_color(30, 60, 120)
    self.set_text_color(255, 255, 255)
    for col, w in zip(cols, widths):
        self.cell(w, 8, col, border=1, fill=True, align="C")
    self.ln()

def table_row(self, cells, widths, aligns=None, fill=False):
    """数据行：交替底色"""
    self.set_font("STHeiti", "", 8.5)
    self.set_text_color(40, 40, 40)
    if fill:
        self.set_fill_color(240, 245, 255)
    for i, (cell, w) in enumerate(zip(cells, widths)):
        a = aligns[i] if aligns else "C"
        self.cell(w, 7, str(cell), border=1, align=a, fill=fill)
    self.ln()
```

#### 页面布局

```python
def header(self):
    if self.page_no() == 1: return
    self.set_font("STHeiti", "", 8)
    self.set_text_color(128, 128, 128)
    self.cell(0, 6, "报告标题", align="L")
    self.cell(0, 6, f"第 {self.page_no()} 页", align="R", new_x="LMARGIN", new_y="NEXT")
    self.line(10, 14, 200, 14)
    self.ln(4)

def footer(self):
    self.set_y(-15)
    self.set_font("STHeiti", "", 7)
    self.set_text_color(160, 160, 160)
    self.cell(0, 10, f"{self.page_no()}/{{nb}}", align="C")
```

## 已知陷阱

### 1. STHeiti 不支持 Emoji

```
Font ... is missing the following glyphs: '📘' (\U0001f4d8), '✅' (\u2705)
```

**修复：** 避用 emoji 作为正文内容。在 fpdf2 单元格中若需状态标识，用纯文字替代（如 `[是]` / `[否]` / `[完成]`）。

### 2. fpdf2 >= 2.5.1 `uni` 参数废弃

```python
# ❌ 旧版
self.add_font("STHeiti", "", font_path, uni=True)
# ✅ 新版（uni 参数已废弃）
self.add_font("STHeiti", "", font_path)
```

### 3. 超大 .docx 文件（30MB+）

含大量图片的 .docx（如带截图的技术报告）加载时可能较慢（5-10s）。合理使用 timeout=30，或先 cp 到临时目录处理。

### 4. .doc 旧格式的 TOC 域代码

textutil -convert txt 可能暴露未更新的 TOC 域代码（如 `{ TOC \\o "1-3" \\h \\z ... }`）。不影响主体内容提取，但建议在报告中标注"目录需在 Word 中更新域代码"。

### 5. 文件重名检测

批处理前检查重复文件（如 (1) 副本），避免重复分析。建议用 os.listdir + os.path.getsize 做预扫描。
