#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Generate academic-reference.docx as a pandoc --reference-doc template.

Configures Chinese + English fonts, standard A4 academic margins,
and heading styles. Run once to produce the template that
md_to_docx.py auto-detects as --reference-doc.

Dependencies:
  - python-docx: pip install python-docx

Usage:
  python3 scripts/generate_academic_reference_docx.py
  python3 scripts/generate_academic_reference_docx.py --output custom.docx
"""

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import sys
import os
import argparse

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def _set_cjk_font(style, east_asian: str, latin: str = "Times New Roman"):
    """Set both CJK (east-Asian) and Latin font in a style's run properties."""
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), east_asian)
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)
    rFonts.set(qn("w:cs"), latin)


def _set_paragraph_spacing(style, line_spacing: float = 1.5,
                           space_before: Pt = None, space_after: Pt = None):
    """Configure paragraph spacing for a style."""
    pf = style.paragraph_format
    pf.line_spacing = line_spacing
    if space_before is not None:
        pf.space_before = space_before
    if space_after is not None:
        pf.space_after = space_after


def create_academic_reference_docx(output_path: str):
    """Generate a Chinese academic paper reference .docx for pandoc."""

    doc = Document()

    # ── Page setup: A4 with standard Chinese academic margins ──
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    # ── Default style definitions ──
    # These style names match what pandoc maps Markdown elements to.
    # When passed as --reference-doc, pandoc inherits these definitions.

    # Title
    title_style = doc.styles["Title"]
    title_style.font.size = Pt(18)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_cjk_font(title_style, "黑体")
    _set_paragraph_spacing(title_style, line_spacing=1.5,
                           space_before=Pt(12), space_after=Pt(12))

    # Heading 1: 黑体 16pt bold, centered
    h1 = doc.styles["Heading 1"]
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0, 0, 0)
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_cjk_font(h1, "黑体")
    _set_paragraph_spacing(h1, line_spacing=1.5,
                           space_before=Pt(12), space_after=Pt(6))

    # Heading 2: 黑体 14pt bold
    h2 = doc.styles["Heading 2"]
    h2.font.size = Pt(14)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0, 0, 0)
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_cjk_font(h2, "黑体")
    _set_paragraph_spacing(h2, line_spacing=1.5,
                           space_before=Pt(10), space_after=Pt(4))

    # Heading 3: 黑体 13pt bold
    h3 = doc.styles["Heading 3"]
    h3.font.size = Pt(13)
    h3.font.bold = True
    h3.font.color.rgb = RGBColor(0, 0, 0)
    h3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_cjk_font(h3, "黑体")
    _set_paragraph_spacing(h3, line_spacing=1.5,
                           space_before=Pt(8), space_after=Pt(4))

    # Heading 4: 楷体 12pt bold
    h4 = doc.styles["Heading 4"]
    h4.font.size = Pt(12)
    h4.font.bold = True
    h4.font.color.rgb = RGBColor(0, 0, 0)
    h4.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_cjk_font(h4, "楷体")
    _set_paragraph_spacing(h4, line_spacing=1.5,
                           space_before=Pt(6), space_after=Pt(2))

    # Normal: 宋体 12pt (Chinese) / Times New Roman 12pt (Latin), 1.5x line spacing
    normal = doc.styles["Normal"]
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _set_cjk_font(normal, "宋体", "Times New Roman")
    _set_paragraph_spacing(normal, line_spacing=1.5,
                           space_before=Pt(0), space_after=Pt(0))

    # First Paragraph (no indent after heading)
    if "First Paragraph" in [s.name for s in doc.styles]:
        fp_style = doc.styles["First Paragraph"]
        fp_style.font.size = Pt(12)
        _set_cjk_font(fp_style, "宋体", "Times New Roman")
        _set_paragraph_spacing(fp_style, line_spacing=1.5)

    # Body Text (with first-line indent)
    body = doc.styles["Body Text"]
    body.font.size = Pt(12)
    body.paragraph_format.first_line_indent = Cm(0.74)  # ~2 Chinese chars
    _set_cjk_font(body, "宋体", "Times New Roman")
    _set_paragraph_spacing(body, line_spacing=1.5)

    # Block Text (for blockquotes)
    if "Block Text" in [s.name for s in doc.styles]:
        bt = doc.styles["Block Text"]
        bt.font.size = Pt(10.5)
        _set_cjk_font(bt, "楷体", "Times New Roman")
        _set_paragraph_spacing(bt, line_spacing=1.25)

    # ── Save ──
    doc.save(output_path)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"✅ 参考样式文档已生成: {output_path} ({size_kb} KB)", flush=True)
    print(f"   A4, 宋体/Times New Roman 12pt, 1.5 倍行距", flush=True)
    print(f"   标题: 黑体 16-18pt, 正文: 宋体 12pt", flush=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="生成 Chinese academic reference .docx for pandoc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              → references/academic-reference.docx
  %(prog)s --output custom-ref.docx     → 自定义输出路径
        """,
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="输出路径（默认: references/academic-reference.docx）",
    )
    args = parser.parse_args()

    # Default output path
    if args.output:
        output_path = args.output
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(
            os.path.dirname(script_dir),
            "references",
            "academic-reference.docx",
        )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    create_academic_reference_docx(output_path)


if __name__ == "__main__":
    main()
