#!/usr/bin/env python3
"""Convert a Markdown draft with local images to a Chinese paper-style PDF."""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_report_pdf import find_chinese_font  # noqa: E402
from fpdf.enums import WrapMode  # noqa: E402


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")
IMAGE_RE = re.compile(r"^!\[(.*?)\]\((.*?)\)\s*$")
INLINE_REPLACEMENTS = [
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),
    (re.compile(r"`(.+?)`"), r"\1"),
]


def clean_inline(text: str) -> str:
    for pattern, repl in INLINE_REPLACEMENTS:
        text = pattern.sub(repl, text)
    return text


class PaperPDF:
    def __init__(self, title: str):
        from fpdf import FPDF

        self.pdf = FPDF(format="A4")
        self.title = title
        self.font_name = "Helvetica"
        self._setup_font()
        self.pdf.set_auto_page_break(auto=True, margin=18)
        self.pdf.set_margins(22, 20, 22)
        self.pdf.alias_nb_pages()
        self.pdf.add_page()
        self.pdf.header = self._header
        self.pdf.footer = self._footer

    def _setup_font(self) -> None:
        font_name, font_path = find_chinese_font()
        if font_path:
            self.pdf.add_font(font_name, "", font_path)
            self.pdf.add_font(font_name, "B", font_path)
            self.font_name = font_name

    def _header(self) -> None:
        if self.pdf.page_no() == 1:
            return
        self.pdf.set_font(self.font_name, "", 8)
        self.pdf.set_text_color(120, 120, 120)
        self.pdf.cell(0, 5, self.title[:36], new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_draw_color(210, 210, 210)
        self.pdf.line(22, self.pdf.get_y(), 188, self.pdf.get_y())
        self.pdf.ln(5)

    def _footer(self) -> None:
        self.pdf.set_y(-13)
        self.pdf.set_font(self.font_name, "", 8)
        self.pdf.set_text_color(140, 140, 140)
        self.pdf.cell(0, 8, f"{self.pdf.page_no()}/{{nb}}", align="C")

    def add_title(self, title: str) -> None:
        self.pdf.set_font(self.font_name, "B", 18)
        self.pdf.set_text_color(20, 20, 20)
        self.pdf.multi_cell(0, 9, title, align="L", wrapmode=WrapMode.CHAR)
        self.pdf.ln(6)

    def add_heading(self, text: str, level: int) -> None:
        if self.pdf.get_y() > 245:
            self.pdf.add_page()
        sizes = {2: 13, 3: 11}
        self.pdf.ln(5 if level == 2 else 3)
        self.pdf.set_font(self.font_name, "B", sizes.get(level, 11))
        self.pdf.set_text_color(25, 25, 25)
        self.pdf.multi_cell(0, 7, text, align="L", wrapmode=WrapMode.CHAR)
        self.pdf.ln(1)

    def add_text(self, text: str) -> None:
        self.pdf.set_font(self.font_name, "", 10.2)
        self.pdf.set_text_color(35, 35, 35)
        if text.startswith("**关键词：**") or text.startswith("关键词："):
            self.pdf.set_font(self.font_name, "B", 10.2)
            self.pdf.multi_cell(0, 6.2, text.replace("**", ""), align="L", wrapmode=WrapMode.CHAR)
        elif text.startswith("[") and re.match(r"^\[\d+\]", text):
            self.pdf.set_font(self.font_name, "", 9.2)
            self.pdf.multi_cell(0, 5.3, text, align="L", wrapmode=WrapMode.CHAR)
        elif re.match(r"^\d+\.\s", text):
            self.pdf.multi_cell(0, 6.2, text, align="L", wrapmode=WrapMode.CHAR)
        else:
            self.pdf.cell(8)
            self.pdf.multi_cell(0, 6.2, text, align="L", wrapmode=WrapMode.CHAR)
        self.pdf.ln(1.2)

    def output(self, path: str) -> None:
        self.pdf.output(path)


def add_image(pdf: PaperPDF, image_path: Path, caption: str) -> None:
    if not image_path.exists():
        pdf.add_text(f"[图片缺失: {image_path}]")
        return
    if pdf.pdf.get_y() > 205:
        pdf.pdf.add_page()
    pdf.pdf.ln(3)
    try:
        width = 130
        if "Figure-2" in image_path.name:
            width = 115
        elif image_path.stat().st_size < 20_000:
            width = 105
        x = (210 - width) / 2
        pdf.pdf.image(str(image_path), x=x, w=width)
    except Exception as exc:
        pdf.add_text(f"[图片渲染失败: {image_path.name}; {exc}]")
        return
    pdf.pdf.ln(2.5)
    pdf.pdf.set_font(pdf.font_name, "", 8.6)
    pdf.pdf.set_text_color(70, 70, 70)
    pdf.pdf.multi_cell(0, 4.8, caption, align="L", wrapmode=WrapMode.CHAR)
    pdf.pdf.ln(3)


def convert(input_path: Path, output_path: Path, title: str | None = None) -> None:
    text = input_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not title:
        for line in lines:
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == 1:
                title = clean_inline(match.group(2))
                break
    title = title or input_path.stem
    pdf = PaperPDF(title)
    title_written = False

    paragraph: list[str] = []

    def flush_para() -> None:
        nonlocal paragraph
        if paragraph:
            pdf.add_text(clean_inline(" ".join(paragraph)))
            paragraph = []

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush_para()
            continue
        image_match = IMAGE_RE.match(line)
        if image_match:
            flush_para()
            caption = clean_inline(image_match.group(1))
            image_ref = image_match.group(2)
            add_image(pdf, (input_path.parent / image_ref).resolve(), caption)
            continue
        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_para()
            level = len(heading_match.group(1))
            heading = clean_inline(heading_match.group(2))
            if level == 1 and not title_written:
                pdf.add_title(heading)
                title_written = True
            elif level == 1:
                pdf.add_heading(heading, 2)
            else:
                pdf.add_heading(heading, level)
            continue
        if line.startswith(">"):
            flush_para()
            pdf.add_text(clean_inline(line.lstrip("> ")))
            continue
        paragraph.append(line)

    flush_para()
    pdf.output(str(output_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown with local images to PDF.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--title")
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve() if args.output else input_path.with_suffix(".pdf")
    convert(input_path, output_path, args.title)
    print(f"PDF_WITH_IMAGES: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
