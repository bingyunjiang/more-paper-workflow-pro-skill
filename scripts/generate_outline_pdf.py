#!/usr/bin/env python3
"""
生成优化版论文大纲 PDF（含修改注释和附录修改对照表）。

功能匹配 generate_outline_docx.py，输出 PDF 而非 .docx：
  1. 读取原始大纲 Markdown + 修改记录 JSON → 生成 A4 PDF
  2. 封面页（标题 + 版本 + 生成时间）
  3. 正文：逐章逐节排版，修改处标注优先级
  4. 附录：修改对照表（彩色表格）
  5. 无修改记录时仅格式化大纲

依赖：
  - fpdf2 >= 2.5.1: pip install fpdf2

Usage:
  # 完整模式：大纲 + 修改记录 → 优化版 PDF
  python3 scripts/generate_outline_pdf.py 大纲关键词.md \\
      --changes changes.json --output outline_v2.pdf

  # 仅格式化模式：无修改注释，纯大纲输出
  python3 scripts/generate_outline_pdf.py 大纲关键词.md --output outline.pdf

  # 输出示例 changes.json 模板
  python3 scripts/generate_outline_pdf.py --example-changes > changes.json
"""
import sys, os, json, argparse, re, time, importlib.util
from pathlib import Path

# ── 颜色常量和辅助函数 ──────────────────────────────────────

PRIORITY_COLORS_RGB = {
    "P0": (200, 40, 40),
    "P1": (220, 140, 40),
    "P2": (180, 150, 50),
    "P3": (100, 160, 100),
}

PRIORITY_LABELS = {
    "P0": "🔴 P0 必须修改",
    "P1": "🟠 P1 建议修改",
    "P2": "🟡 P2 可优化",
    "P3": "🟢 P3 细节打磨",
}

TYPE_LABELS = {"modified": "修改", "added": "新增",
               "deleted": "删除", "restructured": "重构"}


def find_font():
    """找中文字体（macOS 优先 STHeiti）。"""
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            name = os.path.splitext(os.path.basename(fp))[0]
            name = name.replace(" Medium", "").replace(" Light", "")
            return name, fp
    return None, None


# ── PDF 生成器 ──────────────────────────────────────────────

def generate_outline_pdf(chapters, changes_data, output_path):
    from fpdf import FPDF

    font_name, font_path = find_font()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)

    if font_path:
        try:
            pdf.add_font(font_name, "", font_path)
            pdf.add_font(font_name, "B", font_path)
            FN = font_name
        except Exception:
            FN = "Helvetica"
    else:
        FN = "Helvetica"
        print("⚠️ 未找到中文字体，中文可能无法正常渲染。", flush=True)

    title = changes_data.get("paper_title", "论文大纲")
    version = changes_data.get("version", "")
    changes = changes_data.get("changes", [])
    summary = changes_data.get("summary", {})

    # ── 封面 ──
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font(FN, "B", 22)
    pdf.set_text_color(30, 60, 120)
    pdf.multi_cell(0, 14, title, align="C")
    pdf.ln(6)
    if version:
        pdf.set_font(FN, "", 11)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 8, f"优化版 {version}", align="C")
        pdf.ln(20)
    pdf.set_font(FN, "", 9)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(0, 8, f'生成时间: {time.strftime("%Y-%m-%d %H:%M")}', align="C")

    # ── 变更摘要（如有） ──
    if summary:
        pdf.add_page()
        pdf.set_font(FN, "B", 15)
        pdf.set_text_color(30, 60, 120)
        pdf.cell(0, 10, "变更摘要", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        for k, v in [
            ("原大纲子节数", str(summary.get("total_sections_before", "—"))),
            ("优化后子节数", str(summary.get("total_sections_after", "—"))),
            ("P0（必须修改）", str(summary.get("p0_changes", 0))),
            ("P1（建议修改）", str(summary.get("p1_changes", 0))),
            ("P2（可优化）", str(summary.get("p2_changes", 0))),
            ("P3（细节打磨）", str(summary.get("p3_changes", 0))),
        ]:
            pdf.set_font(FN, "", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 7, f"  {k}: {v}", new_x="LMARGIN", new_y="NEXT")

    # ── 正文 ──
    pdf.add_page()
    pdf.set_font(FN, "B", 14)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 10, "优化版大纲", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 构建修改索引: {(章标题, 节标题): change}
    change_index = {}
    for c in changes:
        change_index[(c.get("chapter", ""), c.get("section", ""))] = c

    for ch in chapters:
        # 可能触发分页
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.set_font(FN, "B", 13)
        pdf.set_text_color(30, 60, 120)
        pdf.cell(0, 9, ch["title"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for sec in ch.get("sections", []):
            if pdf.get_y() > 255:
                pdf.add_page()
            # 子节标题
            pdf.set_font(FN, "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 7, sec["title"], new_x="LMARGIN", new_y="NEXT")

            # 是否有修改注释
            change = change_index.get((ch["title"], sec["title"]))
            if change:
                priority = change.get("priority", "P2")
                original = change.get("original", "")
                updated = change.get("updated", "")
                reason = change.get("reason", "")
                note = f"  [{PRIORITY_LABELS.get(priority, priority)}] 原: {original}  →  改: {updated}"
                pdf.set_font(FN, "", 7.5)
                pcolor = PRIORITY_COLORS_RGB.get(priority, (128, 128, 128))
                pdf.set_text_color(*pcolor)
                pdf.cell(0, 5, note, new_x="LMARGIN", new_y="NEXT")
                if reason:
                    pdf.set_text_color(128, 128, 128)
                    pdf.cell(0, 5, f"  理由: {reason}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)

            # 内容
            if sec.get("content"):
                pdf.set_font(FN, "", 9)
                pdf.set_text_color(50, 50, 50)
                pdf.multi_cell(0, 5.5, sec["content"])
                pdf.ln(1)

            # 列表项
            for item in sec.get("items", []):
                pdf.set_font(FN, "", 8.5)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(4)
                pdf.multi_cell(0, 5, f"  - {item}")
                pdf.ln(0.5)

    # ── 附录：修改对照表 ──
    if not changes:
        pdf.output(output_path)
        size = os.path.getsize(output_path) // 1024
        print(f"✅ 大纲 PDF 已生成（无修改记录，跳过附录）: {output_path} ({size} KB)", flush=True)
        return output_path

    pdf.add_page()
    pdf.set_font(FN, "B", 14)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 10, "附录：修改对照表", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FN, "", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 7, f"原版 v1.0 vs 优化版 {version or 'v2.0'}  共 {len(changes)} 项变更",
           new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    headers = ["位置", "类型", "原版", "优化版", "修改理由", "优先级"]
    col_widths = [30, 10, 42, 42, 58, 10]
    pdf.set_font(FN, "B", 6.5)
    pdf.set_fill_color(30, 60, 120)
    pdf.set_text_color(255, 255, 255)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, h, border=1, fill=True, align="C")
    pdf.ln()

    for idx, chg in enumerate(changes):
        priority = chg.get("priority", "P2")
        loc = f'{chg.get("chapter","")} → {chg.get("section","")[:12]}'
        vals = [
            loc,
            TYPE_LABELS.get(chg.get("type", "modified"), chg.get("type", "")),
            chg.get("original", "")[:50],
            chg.get("updated", "")[:50],
            chg.get("reason", "")[:55],
            priority,
        ]
        pdf.set_font(FN, "", 6.5)
        pcolor = PRIORITY_COLORS_RGB.get(priority, (40, 40, 40))
        pdf.set_text_color(*pcolor)
        if idx % 2 == 1:
            pdf.set_fill_color(240, 245, 255)
            fill = True
        else:
            fill = False
        for v, w in zip(vals, col_widths):
            align = "C" if v in ("新增","修改","删除","重构","P0","P1","P2","P3") else "L"
            pdf.cell(w, 6, str(v)[:60], border=1, fill=fill, align=align)
        pdf.ln()

    pdf.output(output_path)
    size = os.path.getsize(output_path) // 1024
    print(f"✅ 大纲 PDF 已生成: {output_path} ({size} KB)", flush=True)
    print(f"   含 {len(changes)} 条修改注释 + 附录修改对照表", flush=True)
    return output_path


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="生成优化版论文大纲 PDF（fpdf2 + 系统中文字体）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 大纲关键词.md --changes changes.json -o outline_v2.pdf
  %(prog)s 大纲关键词.md -o outline.pdf
  %(prog)s --example-changes > changes.json
        """,
    )
    parser.add_argument("outline_md", nargs="?", help="大纲 Markdown 文件路径")
    parser.add_argument("--changes", "-c", help="修改记录 JSON 文件路径")
    parser.add_argument("--output", "-o", default="outline_v2.pdf",
                        help="输出 .pdf 文件路径（默认: outline_v2.pdf）")
    parser.add_argument("--example-changes", action="store_true",
                        help="输出示例 changes.json 模板")
    args = parser.parse_args()

    if args.example_changes:
        # 从 generate_outline_docx.py 获取示例数据
        import importlib.util
        docx_path = Path(__file__).parent / "generate_outline_docx.py"
        spec = importlib.util.spec_from_file_location("_docx_mod", docx_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(json.dumps(mod.get_example_changes(), ensure_ascii=False, indent=2))
        return

    if not args.outline_md:
        parser.print_help()
        print("\n❌ 请指定大纲 Markdown 文件路径", flush=True)
        sys.exit(1)

    if not os.path.exists(args.outline_md):
        print(f"❌ 文件不存在: {args.outline_md}", flush=True)
        sys.exit(1)

    try:
        from fpdf import FPDF
    except ImportError:
        print("❌ 缺少 fpdf2，请执行: pip install fpdf2", flush=True)
        sys.exit(1)

    # 解析大纲
    import importlib.util
    docx_path = Path(__file__).parent / "generate_outline_docx.py"
    spec = importlib.util.spec_from_file_location("_docx_mod", docx_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    chapters = mod.parse_outline_md(args.outline_md)

    if not chapters:
        print("⚠️ 未能从大纲文件中解析出章节结构。", flush=True)
        sys.exit(1)

    print(f"📖 解析到 {len(chapters)} 个章节:", flush=True)
    for ch in chapters:
        sec_count = len(ch.get("sections", []))
        print(f"   {ch['title']} ({sec_count} 子节)", flush=True)

    # 加载修改记录
    changes_data = {}
    if args.changes:
        if os.path.exists(args.changes):
            with open(args.changes, "r", encoding="utf-8") as f:
                changes_data = json.load(f)
            n = len(changes_data.get("changes", []))
            print(f"📝 加载 {n} 条修改记录", flush=True)

    # 生成 PDF
    generate_outline_pdf(chapters, changes_data, args.output)


if __name__ == "__main__":
    main()
