#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
通用中文 PDF 分析报告生成器。

基于 fpdf2 + 系统中文字体，将结构化 JSON 数据渲染为带页眉/页脚/表格/
页码的中文 A4 PDF 报告。适用于：文档分析报告、技术评审报告、大纲评审报告、
文献检索结果汇总等场景。

字体方案（按平台自动选择）：
  - macOS: STHeiti Medium / PingFang（系统内置，无需安装）
  - Windows: 微软雅黑 / 黑体 / 宋体（系统内置，无需安装）
  - Linux: Noto Sans CJK / 文泉驿（需安装 fonts-noto-cjk 或 wqy-zenhei）
  - 回退: Helvetica（仅 ASCII，中文将显示为空白）

依赖：
  - fpdf2 >= 2.5.1: pip install fpdf2  （注意：>=2.5.1 的 add_font 已废弃 uni 参数）

Usage:
  # 从 JSON 文件生成 PDF
  python3 scripts/generate_report_pdf.py report_data.json -o report.pdf -t "分析报告"

  # 从 stdin 传入 JSON（管道）
  echo '{"title":"测试","sections":[...]}' | python3 scripts/generate_report_pdf.py - -o report.pdf

  # 输出示例 JSON 模板（方便快速构建输入数据）
  python3 scripts/generate_report_pdf.py --example > template.json

JSON 输入格式:
  {
    "title": "报告标题",
    "subtitle": "副标题（可选）",
    "sections": [
      {
        "heading": "一、章节标题",
        "level": 1,
        "text": "正文段落内容...",
        "table": {
          "headers": ["列1", "列2", "列3"],
          "rows": [["a1", "a2", "a3"], ["b1", "b2", "b3"]],
          "col_widths": [60, 60, 60],
          "aligns": ["L", "C", "C"]
        }
      }
    ]
  }
"""
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import sys, os, json, argparse, time, platform


# ── 字体自动检测 ────────────────────────────────────────────

def find_chinese_font():
    """自动查找可用的中文字体，返回 (font_name, font_path)。

    按平台遍历常见中文字体路径，返回第一个找到的。
    macOS → Linux → Windows，均支持。
    """
    system = platform.system()

    candidates = []

    if system == "Darwin":
        candidates = [
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
    elif system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        candidates = [
            f"{windir}\\Fonts\\msyh.ttc",     # 微软雅黑
            f"{windir}\\Fonts\\msyhbd.ttc",    # 微软雅黑 粗体
            f"{windir}\\Fonts\\simhei.ttf",    # 黑体
            f"{windir}\\Fonts\\simsun.ttc",    # 宋体
            f"{windir}\\Fonts\\simkai.ttf",    # 楷体
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ]

    # 追加：跨平台通用字体（用户可能安装了另一平台的字体）
    extra = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in extra:
        if fp not in candidates:
            candidates.append(fp)

    for fp in candidates:
        if os.path.exists(fp):
            name = os.path.splitext(os.path.basename(fp))[0]
            # 去掉 " Medium" / " Light" 等后缀，方便 fpdf2 使用
            name = name.replace(" Medium", "").replace(" Light", "")
            return name, fp

    return None, None


# ── ReportPDF 类 ────────────────────────────────────────────

class ReportPDF:
    """中文 A4 PDF 报告生成器。

    封装了 fpdf2 的中文字体注册、页眉/页脚、表格渲染等常用操作。
    使用者只需调用 add_heading / add_text / add_table，最后 output()。

    使用示例:
        pdf = ReportPDF("分析报告", subtitle="副标题")
        pdf.add_cover()
        pdf.add_heading("一、概览")
        pdf.add_text("正文内容...")
        pdf.add_table(headers=["名称","值"], rows=[["A","1"]], col_widths=[80,80])
        pdf.output("report.pdf")
    """

    def __init__(self, title: str, subtitle: str = "",
                 font_size_body: float = 10):
        from fpdf import FPDF

        self.pdf = FPDF()
        self.title = title
        self.subtitle = subtitle
        self.font_size_body = font_size_body
        self._setup_font()
        self._setup_page()

    # ── 内部设置 ──────────────────────────────────

    def _setup_font(self):
        """注册中文字体（自动检测可用字体）。"""
        font_name, font_path = find_chinese_font()

        if font_path:
            try:
                # fpdf2 >= 2.5.1: uni 参数已废弃
                self.pdf.add_font(font_name, "", font_path)
                self.pdf.add_font(font_name, "B", font_path)
                self.font_name = font_name
                self._has_chinese = True
                return
            except Exception as e:
                print(f"⚠️ 字体加载失败 ({font_path}): {e}", flush=True)

        # 回退：无中文字体时使用 Helvetica（中文将无法渲染）
        self.font_name = "Helvetica"
        self._has_chinese = False
        print("⚠️ 未找到中文字体，PDF 中中文可能无法正常显示。", flush=True)
        print("   macOS: STHeiti 为系统内置字体，通常无需额外安装。", flush=True)
        print("   Linux: sudo apt install fonts-noto-cjk", flush=True)
        print("   继续生成（ASCII 内容正常，中文内容将为空白）。", flush=True)

    def _setup_page(self):
        """设置自动分页 + 页眉/页脚回调。"""
        self.pdf.set_auto_page_break(auto=True, margin=18)
        self.pdf.add_page()
        self.pdf.header = self._header
        self.pdf.footer = self._footer

    def _header(self):
        """每页页眉：标题靠左 + 页码靠右 + 分隔线。封面不显示。"""
        if self.pdf.page_no() == 1:
            return

        self.pdf.set_font(self.font_name, "", 8)
        self.pdf.set_text_color(128, 128, 128)
        # 标题靠左
        self.pdf.cell(0, 6, self.title[:50], align="L")
        # 页码靠右
        self.pdf.cell(0, 6, f"第 {self.pdf.page_no()} 页", align="R",
                      new_x="LMARGIN", new_y="NEXT")

        # 浅灰分隔线
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(10, self.pdf.get_y(), 200, self.pdf.get_y())
        self.pdf.ln(4)

    def _footer(self):
        """每页页脚：居中页码。"""
        self.pdf.set_y(-15)
        self.pdf.set_font(self.font_name, "", 7)
        self.pdf.set_text_color(160, 160, 160)
        self.pdf.cell(0, 10, f"{self.pdf.page_no()}/{{nb}}", align="C")

    # ── 公开方法 ──────────────────────────────────

    def add_cover(self):
        """在首页写入封面信息（标题、副标题、生成时间）。"""
        self.pdf.ln(40)
        self.pdf.set_font(self.font_name, "B", 22)
        self.pdf.set_text_color(30, 60, 120)
        self.pdf.multi_cell(0, 14, self.title, align="C")

        if self.subtitle:
            self.pdf.ln(8)
            self.pdf.set_font(self.font_name, "", 12)
            self.pdf.set_text_color(100, 100, 100)
            self.pdf.multi_cell(0, 8, self.subtitle, align="C")

        self.pdf.ln(20)
        self.pdf.set_font(self.font_name, "", 9)
        self.pdf.set_text_color(140, 140, 140)
        self.pdf.cell(0, 8, f"生成时间: {time.strftime('%Y-%m-%d %H:%M')}",
                      align="C")
        self.pdf.ln(8)
        self.pdf.set_font(self.font_name, "", 8)
        self.pdf.set_text_color(160, 160, 160)
        self.pdf.cell(0, 6, "由 Dr. Jiang 的 more-paper-workflow 生成",
                      align="C")

    def add_heading(self, text: str, level: int = 1):
        """添加章节标题。

        Args:
            text: 标题文本
            level: 1=一级标题(15pt), 2=二级(12pt), 3=三级(10.5pt)
        """
        sizes = {1: 15, 2: 12, 3: 10.5}
        prefixes = {1: "", 2: "", 3: "▸ "}

        self.pdf.ln(4)
        self.pdf.set_font(self.font_name, "B", sizes.get(level, 10))
        self.pdf.set_text_color(30, 60, 120)
        prefix = prefixes.get(level, "")
        self.pdf.cell(0, 8, f"{prefix}{text}", new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(2)

    def add_text(self, text: str):
        """添加正文段落（自动换行）。"""
        self.pdf.set_font(self.font_name, "", self.font_size_body)
        self.pdf.set_text_color(50, 50, 50)
        self.pdf.multi_cell(0, 6, text)
        self.pdf.ln(2)

    def add_table(self, headers: list[str], rows: list[list],
                  col_widths: list[float] = None,
                  aligns: list[str] = None):
        """添加带格式的数据表格。

        表头：深蓝底色 + 白色加粗字
        数据行：交替浅蓝底色

        Args:
            headers: 表头列名列表
            rows: 数据行列表，每行一个 list
            col_widths: 列宽列表（mm），None 则等宽
            aligns: 对齐方式列表（L/C/R），默认全部 C
        """
        if not rows and not headers:
            return

        n_cols = len(headers)
        available = 190  # A4 可用宽度 mm

        if col_widths is None:
            col_widths = [available / n_cols] * n_cols
        if aligns is None:
            aligns = ["C"] * n_cols

        # ── 表头 ──
        self.pdf.set_font(self.font_name, "B", 9)
        self.pdf.set_fill_color(30, 60, 120)
        self.pdf.set_text_color(255, 255, 255)

        for header, w in zip(headers, col_widths):
            self.pdf.cell(w, 8, str(header), border=1, fill=True, align="C")
        self.pdf.ln()

        # ── 数据行 ──
        self.pdf.set_font(self.font_name, "", 8.5)

        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 1:
                self.pdf.set_fill_color(240, 245, 255)
                fill = True
            else:
                fill = False

            self.pdf.set_text_color(40, 40, 40)

            for i, (cell, w) in enumerate(zip(row, col_widths)):
                a = aligns[i] if i < len(aligns) else "C"
                text = str(cell) if cell is not None else ""
                self.pdf.cell(w, 7, text[:80], border=1, align=a, fill=fill)
            self.pdf.ln()

        self.pdf.ln(3)

    def add_page_break(self):
        """手动分页。"""
        self.pdf.add_page()

    def output(self, path: str) -> str:
        """保存 PDF 到指定路径，返回文件路径。"""
        self.pdf.output(path)
        return path


# ── 从 JSON 生成完整 PDF ────────────────────────────────────

def generate_from_json(data: dict, output_path: str):
    """从结构化 JSON 数据生成完整 PDF 报告。

    遍历 data["sections"]，按 heading → text → table 顺序渲染。
    """
    title = data.get("title", "分析报告")
    subtitle = data.get("subtitle", "")

    pdf = ReportPDF(title, subtitle)
    pdf.add_cover()

    for i, section in enumerate(data.get("sections", [])):
        heading = section.get("heading", "")
        text = section.get("text", "")
        table = section.get("table")
        level = section.get("level", 1)

        if heading:
            if i > 0:
                pass  # 章节间自然间距
            pdf.add_heading(heading, level)
        if text:
            pdf.add_text(text)
        if table:
            pdf.add_table(
                headers=table.get("headers", []),
                rows=table.get("rows", []),
                col_widths=table.get("col_widths"),
                aligns=table.get("aligns"),
            )

    filepath = pdf.output(output_path)
    size_kb = os.path.getsize(filepath) // 1024
    page_count = pdf.pdf.page_no()
    print(f"✅ PDF 已生成: {filepath} ({size_kb} KB, {page_count} 页)",
          flush=True)
    return filepath


# ── CLI ──────────────────────────────────────────────────────

def get_example_data() -> dict:
    """返回示例 JSON 数据结构，供用户参考。"""
    return {
        "title": "分析报告示例",
        "subtitle": "基于工程文档的提取分析",
        "sections": [
            {
                "heading": "一、文档概览",
                "level": 1,
                "text": "本次共分析 7 份技术文档，涵盖设计计算、试验验证、改进迭代等类型。"
                       "以下为各文档基本信息汇总。",
                "table": {
                    "headers": ["文档名称", "类型", "大小", "段落数"],
                    "rows": [
                        ["设计计算报告.docx", "设计报告", "2.5 MB", "156"],
                        ["试验总结报告.docx", "试验报告", "8.3 MB", "342"],
                        ["专项技术说明书.doc", "专题说明", "1.2 MB", "89"],
                    ],
                    "col_widths": [70, 30, 25, 25],
                    "aligns": ["L", "C", "C", "C"],
                },
            },
            {
                "heading": "二、技术路线提取",
                "level": 1,
                "text": "从文档中识别出以下核心技术路线及其定量数据。",
                "table": {
                    "headers": ["路线", "方法", "关键参数", "定量结果"],
                    "rows": [
                        ["A", "方法A", "参数1, 参数2", "结果描述A"],
                        ["B", "方法B", "参数3, 参数4", "结果描述B"],
                        ["C", "方法C", "参数5", "结果描述C"],
                    ],
                    "col_widths": [20, 50, 60, 60],
                    "aligns": ["C", "L", "C", "C"],
                },
            },
            {
                "heading": "三、注意事项",
                "level": 1,
                "text": "1. 以上数据均从工程文档中提取，建议与原始文档核对后再使用。\n"
                       "2. 文档中存在重复文件时已标注，提取时自动跳过。\n"
                       "3. .doc 旧格式通过 textutil 转换，TOC 域代码已清理。",
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="通用中文 PDF 分析报告生成器（fpdf2 + 系统中文字体）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s report_data.json -o report.pdf -t "分析报告"
  echo '{"title":"测试","sections":[...]}' | %(prog)s - -o report.pdf
  %(prog)s --example > template.json   # 输出示例 JSON 模板
        """,
    )
    parser.add_argument(
        "input", nargs="?", default="-",
        help="JSON 数据文件路径（- 或省略表示从 stdin 读取）",
    )
    parser.add_argument("--output", "-o", default="report.pdf",
                        help="输出 PDF 文件路径（默认: report.pdf）")
    parser.add_argument("--title", "-t",
                        help="覆盖 JSON 中的报告标题")
    parser.add_argument("--example", action="store_true",
                        help="输出示例 JSON 模板到 stdout 并退出")
    args = parser.parse_args()

    # --example 模式
    if args.example:
        print(json.dumps(get_example_data(), ensure_ascii=False, indent=2))
        return

    # 加载 JSON 数据
    if args.input == "-" or not args.input:
        text = sys.stdin.read()
    else:
        if not os.path.exists(args.input):
            print(f"❌ 文件不存在: {args.input}", flush=True)
            sys.exit(1)
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}", flush=True)
        sys.exit(1)

    if args.title:
        data["title"] = args.title

    # 检查 fpdf2
    try:
        import fpdf
    except ImportError:
        print("❌ 缺少 fpdf2，请执行: pip install fpdf2", flush=True)
        sys.exit(1)

    generate_from_json(data, args.output)


if __name__ == "__main__":
    main()
