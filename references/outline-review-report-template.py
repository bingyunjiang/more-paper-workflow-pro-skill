#!/usr/bin/env python3
"""
通用「大纲评审 PDF 报告生成器」模板
=====================================

所属 Skill: more-paper-workflow — Step 2b 大纲评审
用途: 将结构化评审数据渲染为 A4 中文 PDF 报告
依赖: fpdf2 (`pip install fpdf2`)
中文字体: macOS STHeiti（其他系统需替换 add_font 路径）

使用方式:
    # 方式 1: Python API
    from outline_review_report_template import ReportPDF, generate_report

    data = {
        "thesis": { "title_cn": "...", "title_en": "...", ... },
        "review": { "dimensions": [...], "weighted_score": 6.0 },
        "diagnosis": { "chapters": [...] },
        "priorities": { "p0": [...], "p1": [...], ... },
        "optimized_outline": { "lines": [...] },
    }
    path = generate_report(data, output_path="/path/to/report.pdf")

    # 方式 2: 命令行
    python3 outline_review_report_template.py --data review_data.json --output report.pdf

    # 方式 3: 仅在安装了 fpdf2 的 Python 环境中可用
    # macOS 推荐: /Library/Frameworks/Python.framework/Versions/3.14/bin/python3

数据结构说明: 见本文件末尾的 EXAMPLE_DATA 或运行 --example 查看。

Author: more-paper-workflow v1.0.2+
"""

import datetime
import json
import os
import sys
from typing import Optional

# ─── 字体配置（按操作系统适配） ──────────────────────────────────────────
FONT_PATHS = {
    "darwin": {
        "cn": "/System/Library/Fonts/STHeiti Medium.ttc",
        "mono": "/System/Library/Fonts/Menlo.ttc",
    },
    "linux": {
        "cn": "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    },
    "win32": {
        "cn": "C:\\Windows\\Fonts\\msyh.ttc",
        "mono": "C:\\Windows\\Fonts\\consola.ttf",
    },
}

_COLORS = {
    "primary": (40, 80, 160),
    "text": (50, 50, 50),
    "subtext": (80, 80, 80),
    "muted": (150, 150, 150),
    "white": (255, 255, 255),
    "box_red": (255, 235, 235),
    "box_orange": (255, 245, 225),
    "box_yellow": (255, 255, 220),
    "box_green": (225, 245, 225),
    "box_blue": (235, 240, 255),
    "box_grey": (245, 245, 245),
    "table_header_bg": (40, 80, 160),
    "table_stripe": (248, 248, 252),
}


# ═══════════════════════════════════════════════════════════════════════════
# ReportPDF — 可复用的中文 PDF 基础设施
# ═══════════════════════════════════════════════════════════════════════════

class ReportPDF:
    """带中文支持、封面、页眉页脚、层级标题、表格等功能的 A4 PDF 生成器。

    所有排版方法返回 self，支持链式调用。
    注意: 这不是 FPDF 子类，而是对 fpdf2.FPDF 的封装。
    """

    def __init__(self, font_paths: dict | None = None):
        from fpdf import FPDF

        self.pdf = FPDF("P", "mm", "A4")
        self.pdf.set_auto_page_break(True, 20)
        self.pdf.set_left_margin(18)
        self.pdf.set_right_margin(18)

        # 字体加载
        fp = font_paths or FONT_PATHS.get(sys.platform, FONT_PATHS["darwin"])
        cn_path = fp.get("cn", "")
        mono_path = fp.get("mono", "")
        if not os.path.exists(cn_path):
            raise FileNotFoundError(f"中文字体未找到: {cn_path}。请修改 FONT_PATHS。")
        self.pdf.add_font("CN", "", cn_path)
        if os.path.exists(mono_path):
            self.pdf.add_font("Mono", "", mono_path)

        # 当前报告的元数据（由 generate_report() 设置）
        self._thesis_title = ""

    # ── 内部 helpers ──────────────────────────────────────────────────

    def _font(self, name="CN", size=9.5, bold=False, italic=False, color=None):
        """设置字体并返回 self（链式）。

        CJK 字体 (CN) 通常不含 Bold/Italic 变体，bold 通过深色 + 稍大字号模拟。
        """
        style = ""
        if bold and name != "CN":
            style = "B"
        if italic and name != "CN":
            style += "I"
        self.pdf.set_font(name, style, size)
        if color:
            self.pdf.set_text_color(*color)
        return self

    def _hdr_cell(self, text, w, h=7):
        """表头单元格。"""
        self.pdf.set_fill_color(*_COLORS["table_header_bg"])
        self.pdf.set_text_color(*_COLORS["white"])
        self.pdf.set_draw_color(*_COLORS["table_header_bg"])
        self.pdf.set_font("CN", "", 8.5)
        self.pdf.cell(w, h, f" {text}", border=1, fill=True)

    def _data_cell(self, text, w, h=6.5, stripe=False):
        """数据行单元格。"""
        if stripe:
            self.pdf.set_fill_color(*_COLORS["table_stripe"])
        else:
            self.pdf.set_fill_color(*_COLORS["white"])
        self.pdf.set_text_color(*_COLORS["text"])
        self.pdf.set_font("CN", "", 9)
        self.pdf.cell(w, h, f" {text}", border=1, fill=True)

    # ── 页面结构 ──────────────────────────────────────────────────────

    def header(self):
        if self.pdf.page_no() <= 1:
            return
        self._font("CN", 8, color=_COLORS["muted"])
        self.pdf.cell(0, 6, self._thesis_title or "大纲评审报告", align="C")
        self.pdf.ln(4)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(self.pdf.l_margin, self.pdf.get_y(), self.pdf.w - self.pdf.r_margin, self.pdf.get_y())
        self.pdf.ln(4)

    def footer(self):
        if self.pdf.page_no() <= 1:
            return
        self.pdf.set_y(-15)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(self.pdf.l_margin, self.pdf.get_y(), self.pdf.w - self.pdf.r_margin, self.pdf.get_y())
        self.pdf.ln(3)
        self._font("CN", 8, color=_COLORS["muted"])
        self.pdf.cell(0, 8, str(self.pdf.page_no()), align="C")

    def page_break(self):
        self.pdf.add_page()
        return self

    # ── 封面 ──────────────────────────────────────────────────────────

    def cover_page(self, title: str, subtitle: str, meta: list[str],
                   framework: str = "more-paper-workflow — Step 2b"):
        """生成封面。

        Args:
            title: 报告标题（如 "博士论文大纲评审报告"）
            subtitle: 论文题目
            meta: 元信息行列表
            framework: 框架标识
        """
        self._thesis_title = subtitle
        self.pdf.add_page()
        self.pdf.ln(40)

        # 装饰线
        self.pdf.set_draw_color(*_COLORS["primary"])
        self.pdf.set_line_width(0.6)
        y = self.pdf.get_y()
        self.pdf.line(60, y, 150, y)
        self.pdf.ln(16)

        self._font("CN", 28, color=_COLORS["primary"])
        self.pdf.multi_cell(0, 14, title, align="C")
        self.pdf.ln(6)

        self._font("CN", 14, color=(60, 60, 60))
        self.pdf.multi_cell(0, 9, subtitle, align="C")
        self.pdf.ln(10)

        # 元信息框
        self.pdf.set_draw_color(*_COLORS["primary"])
        self.pdf.set_fill_color(245, 247, 255)
        box_x, box_w, box_h = 40, 130, max(42, 12 * len(meta) + 8)
        self.pdf.rect(box_x, self.pdf.get_y(), box_w, box_h, style="DF")
        self.pdf.set_xy(box_x + 8, self.pdf.get_y() + 8)
        self._font("CN", 11, color=(40, 40, 40))
        for m in meta:
            self.pdf.cell(box_w - 16, 9, m)
            self.pdf.set_xy(box_x + 8, self.pdf.get_y() + 9)

        self.pdf.ln(box_h + 16)
        self._font("CN", 9, color=_COLORS["muted"])
        self.pdf.cell(0, 6, f"Generated with {framework}", align="C")
        return self

    # ── 标题 ──────────────────────────────────────────────────────────

    def section_title(self, title: str, num: str = ""):
        """一级标题（蓝色左侧色条 + 深蓝文字）。"""
        self.pdf.ln(4)
        self.pdf.set_draw_color(*_COLORS["primary"])
        self.pdf.set_fill_color(*_COLORS["primary"])
        self.pdf.set_line_width(0.4)
        y = self.pdf.get_y()
        self.pdf.rect(self.pdf.l_margin, y, 3, 10, style="F")
        self.pdf.set_xy(self.pdf.l_margin + 6, y)
        self._font("CN", 14, color=_COLORS["primary"])
        label = f"{num}  {title}" if num else title
        self.pdf.cell(0, 10, label)
        self.pdf.ln(14)
        return self

    def sub_title(self, title: str):
        """二级标题。"""
        self._font("CN", 12, color=(60, 60, 60))
        self.pdf.cell(0, 8, title)
        self.pdf.ln(10)
        return self

    def sub_sub_title(self, title: str):
        """三级标题（缩进 + 加粗）。"""
        self.pdf.set_x(self.pdf.l_margin + 6)
        self._font("CN", 11, bold=True, color=_COLORS["primary"])
        self.pdf.cell(0, 7, title)
        self.pdf.ln(8)
        return self

    # ── 正文 ──────────────────────────────────────────────────────────

    def body(self, text: str, size: float = 9.5, indent: float = 0):
        """正文段落。"""
        self._font("CN", size, color=_COLORS["text"])
        x0 = self.pdf.l_margin + indent
        self.pdf.set_x(x0)
        self.pdf.multi_cell(self.pdf.w - self.pdf.r_margin - x0, 5.8, text, align="L")
        self.pdf.ln(2)
        return self

    def bullet(self, text: str, indent: float = 4, size: float = 9.5,
               color=_COLORS["text"]):
        """项目符号列表项。"""
        self._font("CN", size, color=color)
        x0 = self.pdf.l_margin + indent
        self.pdf.set_x(x0)
        self.pdf.cell(5, 5.5, "•")
        self.pdf.multi_cell(self.pdf.w - self.pdf.r_margin - x0 - 5, 5.5, text)
        self.pdf.ln(0.5)
        return self

    def annotation(self, text: str, tag: str = ""):
        """灰色注释（模拟楷体标注）。"""
        self._font("CN", 9, italic=True, color=(140, 140, 140))
        full = f"[{tag}] {text}" if tag else text
        self.pdf.set_x(self.pdf.l_margin + 12)
        self.pdf.multi_cell(self.pdf.w - self.pdf.r_margin - self.pdf.l_margin - 12, 5, full)
        self.pdf.ln(1)
        return self

    def kv(self, key: str, value: str, indent: float = 4):
        """键值对行。"""
        self._font("CN", 9.5)
        x0 = self.pdf.l_margin + indent
        self.pdf.set_x(x0)
        self.pdf.set_text_color(*_COLORS["primary"])
        kw = self.pdf.get_string_width(key) + 2
        self.pdf.cell(kw, 5.5, key)
        self.pdf.set_text_color(*_COLORS["text"])
        self.pdf.multi_cell(self.pdf.w - self.pdf.r_margin - x0 - kw, 5.5, value)
        self.pdf.ln(0.5)
        return self

    # ── 高亮框 ────────────────────────────────────────────────────────

    def box(self, text: str, severity: str = "blue"):
        """彩色信息框。

        severity: 'red' | 'orange' | 'yellow' | 'green' | 'blue' | 'grey'
        """
        key = f"box_{severity}" if f"box_{severity}" in _COLORS else "box_grey"
        self.pdf.set_fill_color(*_COLORS[key])
        self._font("CN", 9.5, color=_COLORS["text"])
        self.pdf.multi_cell(0, 5.8, text, fill=True)
        self.pdf.ln(2)
        return self

    # ── 表格 ──────────────────────────────────────────────────────────

    def table(self, headers: list[str], rows: list[list[str]],
              col_widths: list[float] | None = None, font_size: float = 8.5):
        """通用表格。

        Args:
            headers: 表头列表
            rows: 数据行列表 (每行一个 list[str])
            col_widths: 列宽列表 (mm)，默认均分
            font_size: 表内字号
        """
        if col_widths is None:
            usable = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin
            col_widths = [usable / len(headers)] * len(headers)

        # 表头
        for i, h in enumerate(headers):
            self._hdr_cell(h, col_widths[i])
        self.pdf.ln()

        # 数据行
        for ri, row in enumerate(rows):
            for i, cell in enumerate(row):
                self._data_cell(str(cell), col_widths[i], stripe=(ri % 2 == 0))
            self.pdf.ln()
        self.pdf.ln(3)
        return self

    # ── 大纲排版 ──────────────────────────────────────────────────────

    def outline_line(self, text: str, note: str = "", level: int = 1,
                     is_new: bool = False):
        """排版大纲的一行（含可选注释）。

        Args:
            text: 大纲行文本
            note: 修改注释（灰色）
            level: 1=章 / 2=节 / 3=子节
            is_new: 是否新增内容（绿色 [NEW] 标记）
        """
        sizes = {1: 11, 2: 9.5, 3: 9}
        colors_list = {1: _COLORS["primary"], 2: (60, 60, 60), 3: (80, 80, 80)}
        indents = {1: 0, 2: 6, 3: 12}
        sz = sizes.get(level, 9)
        clr = colors_list.get(level, _COLORS["text"])
        indent = indents.get(level, 0)

        self.pdf.set_x(self.pdf.l_margin + indent)
        self._font("CN", sz, bold=(level <= 2), color=clr)

        if is_new:
            self.pdf.set_text_color(0, 130, 80)
            self.pdf.cell(self.pdf.get_string_width("[NEW] ") + 1, 6, "[NEW] ")
            self.pdf.set_text_color(*clr)

        self.pdf.cell(0, 6, text)
        self.pdf.ln(6)

        if note:
            self._font("CN", 7.5, italic=True, color=(180, 100, 80))
            self.pdf.set_x(self.pdf.l_margin + indent + 6)
            self.pdf.cell(0, 4.5, note)
            self.pdf.ln(5)
        return self

    def outline_spacer(self, lines: int = 1):
        for _ in range(lines):
            self.pdf.ln(3)
        return self

    # ── 输出 ──────────────────────────────────────────────────────────

    def save(self, path: str):
        self.pdf.output(path)
        return path


# ═══════════════════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════════════════

class ReviewData:
    """大纲评审结构化数据容器。

    所有字段可选；缺失时报告中对应区块留空或跳过。
    """

    def __init__(self, data: dict):
        d = data or {}

        # ── 论文信息 ──
        thesis = d.get("thesis", {})
        self.thesis_title_cn = thesis.get("title_cn", "")
        self.thesis_title_en = thesis.get("title_en", "")
        self.thesis_author = thesis.get("author", "")
        self.thesis_status = thesis.get("status", "")
        self.thesis_keywords = thesis.get("keywords", [])

        # ── 评审信息 ──
        review = d.get("review", {})
        self.review_framework = review.get("framework", "more-paper-workflow — Step 2b")
        self.review_date = review.get("date", datetime.date.today().strftime("%Y-%m-%d"))
        self.review_weighted_score = review.get("weighted_score", None)

        # 维度列表: [{"name": "逻辑连贯性", "weight": "25%", "score": "6/10",
        #             "verdict": "递进链基本合理..."}, ...]
        self.dimensions = review.get("dimensions", [])

        # ── 章节诊断 ──
        diagnosis = d.get("diagnosis", {})
        # [{"label": "1.1 研究背景", "status": "ok|warn|err",
        #   "desc": "..."}, ...]
        self.chapters = diagnosis.get("chapters", [])

        # ── 优先级 ──
        priorities = d.get("priorities", {})
        self.p0 = priorities.get("p0", [])
        self.p1 = priorities.get("p1", [])
        self.p2 = priorities.get("p2", [])
        self.p3 = priorities.get("p3", [])

        # ── 结构平衡性 ──
        balance = d.get("balance", {})
        # [{"chapter": "Ch1 绪论", "sections": 11, "assessment": "偏长", "note": "..."}, ...]
        self.balance_rows = balance.get("rows", [])

        # ── 创新点 ──
        originality = d.get("originality", {})
        # [{"id": "1", "content": "...", "type": "方法/发现/验证",
        #   "falsifiable": True, "independent": True, "verdict": "..."}, ...]
        self.innovations = originality.get("innovations", [])
        self.originality_core_issue = originality.get("core_issue", "")
        self.originality_suggestions = originality.get("suggestions", [])

        # ── 可行性 ──
        feasibility = d.get("feasibility", {})
        # [{"check": "实验系统", "status": "ok|warn|err", "note": "..."}, ...]
        self.feasibility_checks = feasibility.get("checks", [])

        # ── 格式完备性 ──
        completeness = d.get("completeness", {})
        self.completeness_checks = completeness.get("checks", [])

        # ── 优化大纲 ──
        optimized = d.get("optimized_outline", {})
        # [{"text": "1 绪论", "note": "", "level": 1, "is_new": False}, ...]
        self.outline_lines = optimized.get("lines", [])

        # ── 自定义区块 ──
        # [{"title": "...", "body": "...", "num": "", "items": []}, ...]
        self.custom_sections = d.get("custom_sections", [])

        # ── 总结与建议 ──
        summary = d.get("summary", {})
        self.summary_urgent = summary.get("urgent", [])
        self.summary_logic = summary.get("logic", [])
        self.summary_practical = summary.get("practical", [])
        self.summary_conclusion = summary.get("conclusion", "")

    def filter_items(self, keyword_pattern: str, source: str = "p0") -> list:
        """Filter priority items by keyword match in tag or desc.

        Args:
            keyword_pattern: regex pattern to match
            source: which priority list to search ('p0'|'p1'|'p2'|'p3')
        """
        import re
        items = getattr(self, source, [])
        pat = re.compile(keyword_pattern, re.IGNORECASE)
        return [it for it in items if pat.search(it.get("tag", "") + it.get("desc", "") + it.get("location", ""))]

    def _items_p0(self, keywords: str) -> list:
        return self.filter_items(keywords, "p0")

    def _items_p1(self, keywords: str) -> list:
        return self.filter_items(keywords, "p1")


# ═══════════════════════════════════════════════════════════════════════════
# 报告生成主函数
# ═══════════════════════════════════════════════════════════════════════════

def generate_report(data: dict | ReviewData, output_path: str | None = None,
                    font_paths: dict | None = None) -> str:
    """生成大纲评审 PDF 报告。

    Args:
        data: ReviewData 实例或 dict（自动转换）
        output_path: 输出路径，默认与数据文件同目录
        font_paths: 字体路径覆盖

    Returns:
        输出文件路径
    """
    if isinstance(data, dict):
        data = ReviewData(data)

    r = ReportPDF(font_paths)
    r.pdf.set_creator("more-paper-workflow v1.0.2+")

    # ═══════════════════════════════════════════════════════════════════
    # 封面
    # ═══════════════════════════════════════════════════════════════════
    meta_lines = [
        f"评审框架：{data.review_framework}",
        "评审维度：逻辑 / 结构 / 创新 / 可行性 / 格式",
        "分析方法：五维度评审 + 逐章诊断 + 优先级排序",
        f"生成日期：{data.review_date}",
    ]
    if data.thesis_author:
        meta_lines.insert(0, f"作者：{data.thesis_author}")

    title = "博士论文大纲评审报告" if "博士" in (data.thesis_title_cn or "") else "论文大纲评审报告"
    r.cover_page(title, data.thesis_title_cn or "（论文题目未提供）", meta_lines, data.review_framework)

    # ═══════════════════════════════════════════════════════════════════
    # 评审概览
    # ═══════════════════════════════════════════════════════════════════
    r.pdf.add_page()
    r.section_title("评审概览", "")

    r.body(
        f"本报告基于 {data.review_framework} 大纲评审框架，"
        f"对论文《{data.thesis_title_cn}》的目录大纲进行系统性评估。"
        f"评审覆盖五个维度，并对每个章节进行逐节诊断。",
        size=10,
    )

    if data.thesis_title_cn:
        r.sub_title("论文基本信息")
        if data.thesis_title_cn:
            r.kv("论文题目：", data.thesis_title_cn)
        if data.thesis_title_en:
            r.kv("英文题目：", data.thesis_title_en)
        if data.thesis_author:
            r.kv("作者：", data.thesis_author)
        if data.thesis_keywords:
            r.kv("关键方向：", "、".join(data.thesis_keywords))
        if data.thesis_status:
            r.kv("当前状态：", data.thesis_status)

    # 五维度总览表
    if data.dimensions:
        r.sub_title("五维度评审结果总览")
        headers = ["维度", "权重", "评分", "结论"]
        rows = [
            [d.get("name", ""), d.get("weight", ""), d.get("score", ""), d.get("verdict", "")]
            for d in data.dimensions
        ]
        r.table(headers, rows, [38, 12, 12, 108])
        r.pdf.ln(2)
        if data.review_weighted_score is not None:
            r.body(f"加权总分：{data.review_weighted_score:.1f} / 10", size=10)

    # ═══════════════════════════════════════════════════════════════════
    # 各维度详细分析
    # ═══════════════════════════════════════════════════════════════════
    dimension_details = [
        ("逻辑连贯性详细分析", "一", data._items_p0("逻辑|过渡|综述")),
        ("结构平衡性详细分析", "二", data._items_p1("结构|平衡")),
        ("创新点评审", "三", []),
        ("工程可行性评估", "四", []),
        ("格式完备性评估", "五", []),
    ]

    for dim_idx, (title, num, items) in enumerate(dimension_details):
        dim = data.dimensions[dim_idx] if dim_idx < len(data.dimensions) else {}
        r.section_title(title, num)

        # 维度描述（来自数据）
        if dim.get("body"):
            r.body(dim["body"])

        # 关联的 P0/P1 问题
        if items:
            r.sub_title("发现的主要问题")
            for item in items:
                sev = "red" if "P0" in item.get("tag", "") else ("orange" if "P1" in item.get("tag", "") else "yellow")
                r.box(f"[{item.get('tag', '')}] {item.get('desc', '')}", sev)

        # 特殊区块
        if title == "创新点评审":
            # 创新点表格
            if data.innovations:
                hdrs = ["#", "创新点", "类型", "可证伪", "独立性", "评价"]
                irows = []
                for inv in data.innovations:
                    irows.append([
                        inv.get("id", ""),
                        inv.get("content", ""),
                        f"[!!] {inv.get('type', '')}" if inv.get("type") != "发现" else f"[OK] {inv.get('type', '')}",
                        "[OK]" if inv.get("falsifiable") else "[  ]",
                        "[OK]" if inv.get("independent") else "[!!]",
                        inv.get("verdict", ""),
                    ])
                r.table(hdrs, irows, [8, 38, 16, 14, 14, 78])

            if data.originality_core_issue:
                r.sub_title("核心问题")
                r.box(data.originality_core_issue, "red")

            if data.originality_suggestions:
                r.body("建议：")
                for s in data.originality_suggestions:
                    r.bullet(s)

        elif title == "工程可行性评估":
            if data.feasibility_checks:
                hdrs = ["检查项", "状态", "说明"]
                frows = [[c.get("check", ""), _status_icon(c.get("status", "")), c.get("note", "")] for c in data.feasibility_checks]
                r.table(hdrs, frows, [30, 16, 122])

        elif title == "格式完备性评估":
            if data.completeness_checks:
                hdrs = ["检查项", "状态", "说明"]
                crows = [[c.get("check", ""), _status_icon(c.get("status", "")), c.get("note", "")] for c in data.completeness_checks]
                r.table(hdrs, crows, [30, 14, 124])

        elif title == "结构平衡性详细分析":
            if data.balance_rows:
                r.body("以下量化各章子节数量，评估工作量分布：")
                hdrs = ["章节", "主节数", "子节数", "总计", "评估", "权重判断"]
                brows = [
                    [b.get("chapter", ""), str(b.get("main_sections", "")), str(b.get("sub_sections", "")),
                     str(b.get("total", "")), b.get("assessment", ""), b.get("note", "")]
                    for b in data.balance_rows
                ]
                r.table(hdrs, brows, [28, 13, 13, 10, 18, 86])

    # ═══════════════════════════════════════════════════════════════════
    # 逐章诊断
    # ═══════════════════════════════════════════════════════════════════
    if data.chapters:
        r.pdf.add_page()
        r.section_title("逐章诊断", "六")

        for ch in data.chapters:
            label = ch.get("label", "")
            status = ch.get("status", "ok")
            desc = ch.get("desc", "")
            icon = {"ok": "[OK]", "warn": "[!!]", "err": "[XX]"}.get(status, "[  ]")

            r._font("CN", 10, color=(40, 40, 40))
            r.pdf.cell(0, 7, f"{icon} {label}")
            r.pdf.ln(7)

            if desc:
                r._font("CN", 9, color=_COLORS["subtext"])
                r.pdf.set_x(r.pdf.l_margin + 12)
                r.pdf.multi_cell(r.pdf.w - r.pdf.r_margin - r.pdf.l_margin - 12, 5.5, desc)
                r.pdf.ln(3)

    # ═══════════════════════════════════════════════════════════════════
    # 优先级排序
    # ═══════════════════════════════════════════════════════════════════
    has_priorities = any([data.p0, data.p1, data.p2, data.p3])
    if has_priorities:
        r.pdf.add_page()
        r.section_title("优先级排序与修改建议", "七")

        priority_sections = [
            ("P0", "必须修改（影响逻辑完整性和创新区分度）", data.p0, "red"),
            ("P1", "建议修改（显著影响章节质量）", data.p1, "orange"),
            ("P2", "可优化（提升工程实用性）", data.p2, "yellow"),
            ("P3", "细节打磨", data.p3, "grey"),
        ]

        for tag, subtitle, items, severity in priority_sections:
            if not items:
                continue
            r.sub_title(f"[{tag}] {subtitle}")
            for item in items:
                r.box(
                    f"{item.get('tag', tag)} [{item.get('location', '')}] {item.get('desc', '')}",
                    severity,
                )

    # ═══════════════════════════════════════════════════════════════════
    # 优化大纲
    # ═══════════════════════════════════════════════════════════════════
    if data.outline_lines:
        r.pdf.add_page()
        r.section_title("建议的优化大纲", "八")

        r.body("以下为基于评审意见给出的优化大纲。每处修改对应上文的优先级编号。", size=10)
        r.pdf.ln(2)

        for line in data.outline_lines:
            text = line.get("text", "")
            note = line.get("note", "")
            level = line.get("level", 3)
            is_new = line.get("is_new", False)

            if not text:
                r.outline_spacer()
                continue

            r.outline_line(text, note, level, is_new)

    # ═══════════════════════════════════════════════════════════════════
    # 自定义区块
    # ═══════════════════════════════════════════════════════════════════
    for cs in data.custom_sections:
        r.pdf.add_page()
        r.section_title(cs.get("title", ""), cs.get("num", ""))
        if cs.get("body"):
            r.body(cs["body"])
        for item in cs.get("items", []):
            if isinstance(item, str):
                r.bullet(item)
            elif isinstance(item, dict):
                kind = item.get("type", "bullet")
                if kind == "box":
                    r.box(item.get("text", ""), item.get("severity", "blue"))
                elif kind == "subtitle":
                    r.sub_title(item.get("text", ""))
                elif kind == "body":
                    r.body(item.get("text", ""))

    # ═══════════════════════════════════════════════════════════════════
    # 总结
    # ═══════════════════════════════════════════════════════════════════
    if any([data.summary_urgent, data.summary_logic, data.summary_practical]):
        r.pdf.add_page()
        r.section_title("关键建议总结", "九")

        if data.summary_urgent:
            r.sub_title("最紧急（P0）—— 立即处理")
            for s in data.summary_urgent:
                r.bullet(s, color=(180, 40, 40))
        if data.summary_logic:
            r.sub_title("最影响逻辑（P1）—— 尽快修改")
            for s in data.summary_logic:
                r.bullet(s)
        if data.summary_practical:
            r.sub_title("最影响工程实用性（P2）—— 建议补充")
            for s in data.summary_practical:
                r.bullet(s)

    # ═══════════════════════════════════════════════════════════════════
    # 尾注
    # ═══════════════════════════════════════════════════════════════════
    r.pdf.ln(8)
    r.pdf.set_draw_color(*_COLORS["primary"])
    r.pdf.set_line_width(0.4)
    y = r.pdf.get_y()
    r.pdf.line(30, y, 180, y)
    r.pdf.ln(8)
    r._font("CN", 9, color=_COLORS["muted"])
    r.pdf.multi_cell(0, 5.5, data.summary_conclusion or "", align="C")

    # ═══════════════════════════════════════════════════════════════════
    # 保存
    # ═══════════════════════════════════════════════════════════════════
    if output_path is None:
        output_path = os.path.join(os.getcwd(), "大纲评审报告.pdf")
    return r.save(output_path)


# ─── helpers ─────────────────────────────────────────────────────────

def _status_icon(status: str) -> str:
    return {"ok": "[OK]", "warn": "[!!]", "err": "[XX]", "none": "[  ]"}.get(status, "[  ]")


# ═══════════════════════════════════════════════════════════════════════════
# CLI & EXAMPLE_DATA
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="大纲评审 PDF 报告生成器")
    parser.add_argument("--data", help="评审数据 JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出 PDF 路径")
    parser.add_argument("--example", action="store_true", help="打印示例数据结构并退出")
    args = parser.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE_DATA, ensure_ascii=False, indent=2))
        return

    if not args.data:
        parser.print_help()
        print("\n提示: 使用 --example 查看示例数据结构。")
        return

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    output = args.output or os.path.splitext(args.data)[0] + ".pdf"
    path = generate_report(data, output)
    print(f"PDF saved to: {path}")


EXAMPLE_DATA = {
    "thesis": {
        "title_cn": "论文中文题目",
        "title_en": "English Thesis Title",
        "author": "作者姓名",
        "status": "初稿已成，Ch5 正在补充理论计算内容",
        "keywords": ["方向一", "方向二"],
    },
    "review": {
        "framework": "more-paper-workflow — Step 2b",
        "date": "2026-06-02",
        "weighted_score": 5.85,
        "dimensions": [
            {
                "name": "逻辑连贯性 (Coherence)",
                "weight": "25%",
                "score": "6/10",
                "verdict": "递进链基本合理，但XX过渡缺失，综述与正文未对齐",
                "body": "全文遵循「背景→XX→验证」的递进结构，方向正确。",
            },
            {
                "name": "结构平衡性 (Balance)",
                "weight": "20%",
                "score": "5/10",
                "verdict": "XX章过重(13节)，XX章过弱(2节)，分布不均",
                "body": "",
            },
            {
                "name": "创新区分度 (Originality)",
                "weight": "20%",
                "score": "5/10",
                "verdict": "仅XX属于科学发现，其余偏方法或工程验证",
                "body": "",
            },
            {
                "name": "工程可行性 (Feasibility)",
                "weight": "20%",
                "score": "7/10",
                "verdict": "实验系统、方法、基线对照均明确",
                "body": "",
            },
            {
                "name": "格式完备性 (Completeness)",
                "weight": "15%",
                "score": "6/10",
                "verdict": "各章小结齐全，但附录内容未列出，技术路线图缺失",
                "body": "",
            },
        ],
    },
    "diagnosis": {
        "chapters": [
            {"label": "1.1 研究背景", "status": "warn", "desc": "1.1.3 标题与正文重叠，建议改为「研究现状与挑战」。"},
            {"label": "1.2 综述章节", "status": "ok", "desc": "双线覆盖，逻辑清晰。"},
            {"label": "Ch3 核心章节", "status": "err", "desc": "缺XX分析，需补充。"},
        ],
    },
    "priorities": {
        "p0": [
            {"tag": "P0-1", "location": "1.3 绪论", "desc": "综述缺少XX方法，与正文不对应——盲审必抓。"},
        ],
        "p1": [
            {"tag": "P1-1", "location": "Ch5", "desc": "章节过于拥挤，建议拆分。"},
        ],
        "p2": [
            {"tag": "P2-1", "location": "5.3", "desc": "缺少理论判据——建议加入XX分析。"},
        ],
        "p3": [
            {"tag": "P3-1", "location": "标题", "desc": "英文标题单复数确认。"},
        ],
    },
    "balance": {
        "rows": [
            {"chapter": "Ch1 绪论", "main_sections": 4, "sub_sections": 7, "total": 11, "assessment": "[!!] 偏长", "note": "1.1.3 与正文重叠"},
            {"chapter": "Ch2 XX", "main_sections": 4, "sub_sections": 0, "total": 4, "assessment": "[OK] 合理", "note": ""},
            {"chapter": "Ch3 XX", "main_sections": 5, "sub_sections": 8, "total": 13, "assessment": "[!!] 过重", "note": "全文重心"},
        ],
    },
    "originality": {
        "innovations": [
            {"id": "1", "content": "XX组合物配比筛选", "type": "方法", "falsifiable": True, "independent": True, "verdict": "需从方法表述升级为发现型表述"},
        ],
        "core_issue": "创新点表述需要从「做了什么」升级为「发现了什么」。",
        "suggestions": ["建议一", "建议二"],
    },
    "feasibility": {
        "checks": [
            {"check": "实验系统", "status": "ok", "note": "各章实验系统明确"},
            {"check": "理论方法", "status": "ok", "note": "方法成熟"},
        ],
    },
    "completeness": {
        "checks": [
            {"check": "绪论综述", "status": "warn", "note": "缺XX综述"},
            {"check": "各章小结", "status": "ok", "note": "Ch2-6 均有"},
        ],
    },
    "optimized_outline": {
        "lines": [
            {"text": "1 绪论", "note": "", "level": 1, "is_new": False},
            {"text": "1.1 研究背景", "note": "", "level": 2, "is_new": False},
            {"text": "1.1.3 XX关键性能挑战", "note": "← 重命名，避免与正文重叠", "level": 3, "is_new": False},
            {"text": "1.3.2 XX理论计算方法", "note": "← [NEW] 新增：MD / DFT 等", "level": 3, "is_new": True},
        ],
    },
    "summary": {
        "urgent": ["P0 项一", "P0 项二"],
        "logic": ["P1 项一"],
        "practical": ["P2 项一"],
        "conclusion": "评审框架：more-paper-workflow v1.0.2 — Step 2b 大纲评审",
    },
}


if __name__ == "__main__":
    main()
