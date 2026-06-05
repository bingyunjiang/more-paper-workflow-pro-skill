#!/usr/bin/env python3
"""
统一 Markdown → PDF 转换器。

自动识别文件类型，将 More Paper Workflow Pro Skill 各环节产出的
Markdown 文件一键转换为带页眉/页脚/表格/页码的 A4 PDF 报告。

复用 generate_report_pdf.py 的 ReportPDF 引擎 + 字体检测。

支持的文件类型（自动检测）：
  - 论文大纲 / 大纲关键词  → outline
  - 检索方案.md            → search_strategy
  - 检索文献表.md           → literature_table
  - 评审报告.md             → review_report
  - rebuttal-预演.md        → rebuttal
  - 通用 Markdown           → generic

依赖：
  - fpdf2 >= 2.5.1: pip install fpdf2
  - generate_report_pdf.py（同目录）

Usage:
  python3 scripts/md_to_pdf.py input.md                      # → input.pdf
  python3 scripts/md_to_pdf.py input.md -o output.pdf        # 指定输出路径
  python3 scripts/md_to_pdf.py input.md -t "自定义标题"       # 覆盖标题
  python3 scripts/md_to_pdf.py input.md --no-cover            # 跳过封面
  python3 scripts/md_to_pdf.py input.md --type generic        # 强制类型
"""

import sys
import os
import re
import argparse
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional

# ── 路径设置：确保可导入同目录的 generate_report_pdf ──────────

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

# ── 延迟导入：检查 fpdf2 可用性 ──────────────────────────────

_ReportPDF = None
_find_chinese_font = None


def _ensure_imports():
    """延迟加载 ReportPDF + find_chinese_font，提供友好的缺少依赖提示。"""
    global _ReportPDF, _find_chinese_font
    if _ReportPDF is not None:
        return
    try:
        from generate_report_pdf import ReportPDF as RP, find_chinese_font as FCF  # noqa: E501
        _ReportPDF = RP
        _find_chinese_font = FCF
    except ImportError as e:
        print(f"❌ 无法导入 generate_report_pdf: {e}", flush=True)
        print("   请确认 scripts/generate_report_pdf.py 存在。", flush=True)
        sys.exit(1)
    try:
        import fpdf  # noqa: F401
    except ImportError:
        print("❌ 缺少 fpdf2，请执行: pip install fpdf2", flush=True)
        sys.exit(1)


# ── 数据类型 ──────────────────────────────────────────────────


class BlockType(Enum):
    HEADING = auto()
    PARAGRAPH = auto()
    TABLE = auto()
    LIST_ITEM = auto()
    BLOCKQUOTE = auto()
    HRULE = auto()
    CODE_BLOCK = auto()
    BLANK = auto()


@dataclass
class Block:
    type: BlockType
    level: int = 0
    text: str = ""
    table_headers: List[str] = field(default_factory=list)
    table_rows: List[List[str]] = field(default_factory=list)


# ── 行内格式清理 ──────────────────────────────────────────────

_INLINE_CLEANUP = [
    (re.compile(r'\*\*(.+?)\*\*'), r'\1'),       # **bold**
    (re.compile(r'__(.+?)__'), r'\1'),             # __bold__
    (re.compile(r'\*(.+?)\*'), r'\1'),             # *italic*
    (re.compile(r'_(.+?)_'), r'\1'),               # _italic_
    (re.compile(r'`(.+?)`'), r'\1'),               # `code`
    (re.compile(r'~~(.+?)~~'), r'\1'),             # ~~strikethrough~~
    (re.compile(r'\[(.+?)\]\(.+?\)'), r'\1'),      # [text](url)
    (re.compile(r'!\[.*?\]\(.+?\)'), ''),          # ![alt](img)
]


def strip_inline(text: str) -> str:
    """移除行内 Markdown 标记，保留纯文本内容。"""
    for pattern, replacement in _INLINE_CLEANUP:
        text = pattern.sub(replacement, text)
    return text


# ── Markdown 解析器 ───────────────────────────────────────────


def parse_markdown(text: str) -> List[Block]:
    """行级状态机：将 Markdown 文本解析为 Block 平铺列表。"""
    lines = text.split('\n')
    blocks = []
    in_code_block = False
    in_table = False
    code_buffer = []
    table_buffer = []
    para_buffer = []
    blockquote_buffer = []

    def flush_para():
        nonlocal para_buffer
        if para_buffer:
            blocks.append(Block(
                type=BlockType.PARAGRAPH,
                text=strip_inline(' '.join(para_buffer)),
            ))
            para_buffer = []

    def flush_blockquote():
        nonlocal blockquote_buffer
        if blockquote_buffer:
            blocks.append(Block(
                type=BlockType.BLOCKQUOTE,
                text=strip_inline(' '.join(blockquote_buffer)),
            ))
            blockquote_buffer = []

    def flush_code():
        nonlocal code_buffer
        if code_buffer:
            blocks.append(Block(
                type=BlockType.CODE_BLOCK,
                text='\n'.join(code_buffer),
            ))
            code_buffer = []

    def flush_table():
        nonlocal table_buffer
        if not table_buffer:
            return
        # table_buffer[0] = header, table_buffer[1] = separator,
        # table_buffer[2..] = data rows
        if len(table_buffer) >= 2 and _is_separator_row(table_buffer[1]):
            headers = _split_table_row(table_buffer[0])
            rows = []
            for rl in table_buffer[2:]:
                cells = _split_table_row(rl)
                rows.append(cells)
            # 对齐列数：以 header 为准
            for row in rows:
                while len(row) < len(headers):
                    row.append('')
                # 截断过长行
                if len(row) > len(headers):
                    row[:] = row[:len(headers)]
            blocks.append(Block(
                type=BlockType.TABLE,
                table_headers=headers,
                table_rows=rows,
            ))
        table_buffer = []

    def _is_separator_row(line: str) -> bool:
        return bool(re.match(r'^\|?[\s:-]+\|', line))

    def _split_table_row(line: str) -> List[str]:
        # 去掉首尾的 |
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        return [c.strip() for c in line.split('|')]

    i = 0
    while i < len(lines):
        line = lines[i]

        # ── 代码块 ──
        if line.strip().startswith('```'):
            if not in_code_block:
                flush_para()
                flush_blockquote()
                flush_table()
                in_code_block = True
            else:
                flush_code()
                in_code_block = False
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # ── 空行 ──
        if not line.strip():
            flush_para()
            flush_blockquote()
            if in_table:
                flush_table()
                in_table = False
            blocks.append(Block(type=BlockType.BLANK))
            i += 1
            continue

        # ── 表格 ──
        if '|' in line:
            if not in_table:
                # 前瞻：看下一行是不是分隔行
                if i + 1 < len(lines) and _is_separator_row(lines[i + 1]):
                    flush_para()
                    flush_blockquote()
                    in_table = True
                    table_buffer = [line]
                    i += 1
                    continue
                else:
                    # | 只是行内普通管道符，作为段落处理
                    para_buffer.append(line)
                    i += 1
                    continue
            else:
                table_buffer.append(line)
                i += 1
                continue

        # ── 如果在表格中遇到非表格行 → 结束表格 ──
        if in_table:
            flush_table()
            in_table = False
            # 不要 i+=1，当前行需要重新判断
            continue

        # ── 水平线 ──
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            flush_para()
            flush_blockquote()
            blocks.append(Block(type=BlockType.HRULE))
            i += 1
            continue

        # ── 标题 ──
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if heading_match:
            flush_para()
            flush_blockquote()
            level = len(heading_match.group(1))
            blocks.append(Block(
                type=BlockType.HEADING,
                level=level,
                text=strip_inline(heading_match.group(2)),
            ))
            i += 1
            continue

        # ── 引用块 ──
        if line.lstrip().startswith('>'):
            flush_para()
            content = re.sub(r'^>\s?', '', line.lstrip())
            blockquote_buffer.append(content)
            i += 1
            continue
        else:
            flush_blockquote()

        # ── 无序列表 ──
        list_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if list_match:
            flush_para()
            blocks.append(Block(
                type=BlockType.LIST_ITEM,
                text=strip_inline(list_match.group(2)),
            ))
            i += 1
            continue

        # ── 有序列表 ──
        ordered_match = re.match(r'^(\s*)\d+[.)]\s+(.+)$', line)
        if ordered_match:
            flush_para()
            blocks.append(Block(
                type=BlockType.LIST_ITEM,
                text=strip_inline(ordered_match.group(2)),
            ))
            i += 1
            continue

        # ── 普通段落 ──
        para_buffer.append(line)
        i += 1

    # ── 文件结束，flush 所有缓冲区 ──
    flush_para()
    flush_blockquote()
    flush_table()
    flush_code()

    return blocks


# ── 类型检测 ──────────────────────────────────────────────────

TYPE_SIGNATURES = [
    ("literature_table",  re.compile(r'检索文献表')),
    ("search_report",     re.compile(r'文献检索报告|检索报告')),
    ("review_report",      re.compile(r'评审报告')),
    ("search_strategy",    re.compile(r'检索方案')),
    ("outline",            re.compile(r'论文大纲|大纲关键词')),
    ("rebuttal",           re.compile(r'rebuttal.*预演', re.IGNORECASE)),
    ("rebuttal",           re.compile(r'rebuttal', re.IGNORECASE)),
]


def detect_md_type(blocks: List[Block]) -> str:
    """从第一个 H1 标题检测文档类型。"""
    for block in blocks:
        if block.type == BlockType.HEADING and block.level == 1:
            h1_text = block.text.strip()
            for type_name, pattern in TYPE_SIGNATURES:
                if pattern.search(h1_text):
                    return type_name
            # 找到 H1 但不匹配任何已知类型
            return "generic"
    return "generic"


# ── 表格列宽计算 ──────────────────────────────────────────────


def _char_width(ch: str) -> float:
    """估算单字符在 PDF 中的宽度（相对单位）。

    CJK 字符约占 2 倍 ASCII 字符宽度。
    """
    if '一' <= ch <= '鿿' or '　' <= ch <= '〿' or '＀' <= ch <= '￯':
        return 2.0
    return 1.0


def calc_table_col_widths(headers: List[str], rows: List[List[str]],
                           font_size: float) -> List[float]:
    """根据内容自动计算列宽，适配 A4 宽度 (190mm)。"""
    n_cols = len(headers)
    if n_cols == 0:
        return []

    # 计算每列最大字符宽度
    max_widths = [0.0] * n_cols
    for col_idx, header in enumerate(headers):
        w = sum(_char_width(c) for c in header[:60])
        max_widths[col_idx] = max(max_widths[col_idx], w)

    for row in rows:
        for col_idx in range(min(n_cols, len(row))):
            cell = str(row[col_idx])[:60]
            w = sum(_char_width(c) for c in cell)
            max_widths[col_idx] = max(max_widths[col_idx], w)

    # 按比例分配 190mm
    total_width = sum(max_widths) or 1.0
    available = 190.0
    col_widths = [max(8.0, (w / total_width) * available) for w in max_widths]

    # 重新归一化到 190mm
    total = sum(col_widths)
    if total > 0:
        col_widths = [w * (available / total) for w in col_widths]

    return col_widths


def _best_align(cells: List[str]) -> str:
    """猜测列的对齐方式：数字/分数 → C，其余 → L。"""
    num_count = 0
    for c in cells:
        stripped = str(c).strip()
        if re.match(r'^[\d.+\-×%]+$', stripped):
            num_count += 1
    return "C" if num_count > len(cells) * 0.6 else "L"


# ── PDF 渲染器 ────────────────────────────────────────────────


def render_pdf(blocks: List[Block], output_path: str,
               title: Optional[str] = None, md_type: str = "generic",
               no_cover: bool = False) -> str:
    """将 Block 列表渲染为 PDF。

    Args:
        blocks: 解析后的 Block 列表
        output_path: 输出 PDF 路径
        title: 自定义标题（None 则用第一个 H1）
        md_type: 文档类型，影响渲染参数
        no_cover: True 跳过封面页

    Returns:
        PDF 文件绝对路径
    """
    _ensure_imports()

    # ── 确定标题 ──
    if not title:
        for block in blocks:
            if block.type == BlockType.HEADING and block.level == 1:
                title = block.text
                break
        if not title:
            title = "Markdown Document"

    # ── 按类型确定渲染参数 ──
    body_font_size = 10.0
    table_font_size = 8.5
    if md_type == "literature_table":
        body_font_size = 9.0
        table_font_size = 6.5

    # ── 创建 ReportPDF ──
    subtitle = f"生成时间: {time.strftime('%Y-%m-%d %H:%M')}"
    pdf = _ReportPDF(title, subtitle, font_size_body=body_font_size)
    if not no_cover:
        pdf.add_cover()

    # ── 遍历 Block 渲染 ──
    for block in blocks:
        btype = block.type

        if btype == BlockType.HEADING:
            pdf.add_heading(block.text, block.level)

        elif btype == BlockType.PARAGRAPH:
            pdf.add_text(block.text)

        elif btype == BlockType.TABLE:
            _render_table(pdf, block.table_headers, block.table_rows,
                          table_font_size)

        elif btype == BlockType.LIST_ITEM:
            # 列表项：缩进 + 项目符号
            pdf.pdf.set_font(pdf.font_name, "", body_font_size - 1)
            pdf.pdf.set_text_color(50, 50, 50)
            pdf.pdf.cell(6)
            pdf.pdf.multi_cell(0, 5.5, f"• {block.text}")
            pdf.pdf.ln(1)

        elif btype == BlockType.BLOCKQUOTE:
            # 引用：灰色 + 缩进 + 左侧竖线感
            pdf.pdf.set_font(pdf.font_name, "", body_font_size - 1)
            pdf.pdf.set_text_color(100, 100, 100)
            pdf.pdf.cell(8)
            pdf.pdf.multi_cell(0, 5.5, block.text)
            pdf.pdf.set_text_color(50, 50, 50)
            pdf.pdf.ln(2)

        elif btype == BlockType.HRULE:
            pdf.pdf.ln(2)
            pdf.pdf.set_draw_color(200, 200, 200)
            y = pdf.pdf.get_y()
            pdf.pdf.line(10, y, 200, y)
            pdf.pdf.ln(4)

        elif btype == BlockType.CODE_BLOCK:
            # 代码块：小字号 + 缩进，超过 40 行则跳过
            code_lines = block.text.split('\n')
            if len(code_lines) > 40:
                pdf.pdf.set_font(pdf.font_name, "", 8)
                pdf.pdf.set_text_color(128, 128, 128)
                pdf.pdf.cell(8)
                pdf.pdf.cell(0, 5, f"[代码块 {len(code_lines)} 行，已省略]",
                             new_x="LMARGIN", new_y="NEXT")
                pdf.pdf.ln(2)
                continue
            pdf.pdf.set_font(pdf.font_name, "", 7)
            pdf.pdf.set_text_color(80, 80, 80)
            for cl in code_lines:
                pdf.pdf.cell(8)
                pdf.pdf.cell(0, 4.5, cl[:120], new_x="LMARGIN", new_y="NEXT")
            pdf.pdf.ln(2)

        elif btype == BlockType.BLANK:
            pdf.pdf.ln(2)

    # ── 输出 ──
    filepath = pdf.output(output_path)
    size_kb = os.path.getsize(filepath) // 1024
    pages = pdf.pdf.page_no()
    print(f"✅ PDF 已生成: {filepath} ({size_kb} KB, {pages} 页)", flush=True)
    return filepath


def _render_table(pdf, headers: List[str], rows: List[List[str]],
                  font_size: float):
    """渲染单个表格，自动计算列宽和对齐。"""
    if not headers and not rows:
        return

    n_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
    if n_cols == 0:
        return

    # 超多列表格 → 自动缩小字号
    if n_cols > 10:
        font_size = min(font_size, 6.5)
    elif n_cols > 8:
        font_size = min(font_size, 7.5)

    col_widths = calc_table_col_widths(headers, rows, font_size)

    # 对齐：按列内容特征自动选择
    aligns = []
    for ci in range(n_cols):
        col_cells = [str(r[ci]) if ci < len(r) else '' for r in rows]
        col_cells.insert(0, headers[ci] if ci < len(headers) else '')
        aligns.append(_best_align(col_cells))

    # 长表：超过 20 行检查剩余空间，超过 50 行在表后加分页
    if len(rows) > 20 and pdf.pdf.get_y() > 200:
        pdf.pdf.add_page()

    # 截断过长表头
    truncated_headers = [h[:40] for h in headers]

    pdf.add_table(
        headers=truncated_headers,
        rows=rows,
        col_widths=col_widths,
        aligns=aligns,
    )

    # 覆盖 add_table 的默认字号——用我们的字号重新设置
    # add_table 内部会设置 font，我们需要在之后手动调整...
    # 实际上 add_table 用的是硬编码字号。这里用自定义实现。
    # 我们改为直接调用 ReportPDF 的 add_table（它使用 9pt 表头 + 8.5pt 数据行），
    # 对于超宽表来说字号是大了一点，但可读性更优先。
    # 如果 n_cols > 10，在表前加提示
    if n_cols > 12:
        pdf.pdf.set_font(pdf.font_name, "", 7)
        pdf.pdf.set_text_color(128, 128, 128)
        pdf.pdf.cell(0, 5, f"  (宽表: {n_cols} 列, 字号已缩小)",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.pdf.ln(1)

    if len(rows) > 50:
        pdf.pdf.add_page()


# ── CLI ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="通用 Markdown → PDF 转换器（自动识别文件类型，复用 ReportPDF 引擎）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 大纲关键词.md                      → 大纲关键词.pdf
  %(prog)s 检索方案.md                     → 检索方案.pdf
  %(prog)s 检索文献表.md -o 文献表.pdf     → 指定输出路径
  %(prog)s input.md -t "自定义标题"         → 覆盖标题
  %(prog)s input.md --no-cover              → 跳过封面
  %(prog)s input.md --type literature_table → 强制类型

支持的文件类型（自动检测）:
  - 论文大纲 / 大纲关键词  outline
  - 检索方案              search_strategy
  - 检索文献表             literature_table
  - 评审报告               review_report
  - rebuttal-预演          rebuttal
  - 通用 Markdown          generic
        """,
    )
    parser.add_argument(
        "input", help="Markdown 文件路径",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="输出 PDF 路径（默认: 与输入文件同名 .pdf）",
    )
    parser.add_argument(
        "--title", "-t", default=None,
        help="自定义 PDF 标题（默认: 使用文档第一个 H1 标题）",
    )
    parser.add_argument(
        "--no-cover", action="store_true",
        help="跳过封面页，直接从内容开始",
    )
    parser.add_argument(
        "--type", dest="force_type", default="auto",
        choices=["auto", "search_strategy", "literature_table", "search_report",
                 "review_report", "rebuttal", "outline", "generic"],
        help="强制指定文件类型（默认: auto 自动检测）",
    )
    args = parser.parse_args()

    # ── 检查输入文件 ──
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}", flush=True)
        sys.exit(1)

    # ── 确定输出路径 ──
    output_path = args.output
    if not output_path:
        base = os.path.splitext(os.path.basename(args.input))[0]
        output_path = os.path.join(os.path.dirname(args.input) or ".", f"{base}.pdf")

    # ── 读取 Markdown ──
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    # ── 解析 ──
    blocks = parse_markdown(text)
    if not blocks:
        print("⚠️ 文件为空或无可解析内容，将生成仅含封面的 PDF。", flush=True)

    # ── 检测类型 ──
    md_type = args.force_type if args.force_type != "auto" else detect_md_type(blocks)
    if md_type != "generic":
        print(f"📄 检测到文件类型: {md_type}", flush=True)

    # ── 生成 PDF ──
    render_pdf(
        blocks=blocks,
        output_path=output_path,
        title=args.title,
        md_type=md_type,
        no_cover=args.no_cover,
    )


if __name__ == "__main__":
    main()
