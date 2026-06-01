#!/usr/bin/env python3
"""
批量提取 PDF 文献全文文本，供 Step 8 论文写作使用。

两种方案，根据文献量自动切换：
  方案 A（按需精读）— 逐章筛选、提取，适用于小批量（<20 篇）
  方案 B（批量预提取）— 全库一次提取，适用于大批量（≥20 篇）

Usage:
  # 方案 A: 按章节提取特定 PDF
  python3 scripts/batch_read_pdfs.py paper-temp/ --file-list chapter1_pdfs.txt --output 第1章文献.md

  # 方案 B: 全库一次提取（自动 6 进程）
  python3 scripts/batch_read_pdfs.py paper-temp/ --output 文献库全文.md

  # 自定义进程数 + 独立 .txt 输出
  python3 scripts/batch_read_pdfs.py paper-temp/ --workers 8 --txt-dir paper-txt/
"""
import sys, os, time, re, argparse
from multiprocessing import Pool, cpu_count

# Ensure scripts/ is on the path for cdp_utils import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import check_optional_dep, print_missing_deps_summary

# 默认并行数
DEFAULT_WORKERS = min(6, cpu_count())
# 方案切换阈值
BATCH_THRESHOLD = 20

def extract_text_from_pdf(args):
    """用 PyMuPDF 提取单个 PDF 的文本"""
    filepath, doi = args
    try:
        import fitz
        doc = fitz.open(filepath)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        text = "\n".join(text_parts)
        pages = len(text_parts)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return (os.path.basename(filepath), doi, text, pages, None)
    except Exception as e:
        return (os.path.basename(filepath), doi, "", 0, str(e))

def guess_doi_from_pdf(filepath):
    """从 PDF 元数据或文件名猜测 DOI"""
    try:
        import fitz
        doc = fitz.open(filepath)
        meta = doc.metadata
        doc.close()
        doi_text = meta.get("doi", "") or meta.get("subject", "") or ""
        if "10." in doi_text:
            m = re.search(r"10\.\d{4,}/[^\s,;)]+", doi_text)
            if m:
                return m.group(0)
    except:
        pass
    name = os.path.splitext(os.path.basename(filepath))[0]
    if name.startswith("10."):
        return name.replace("_", "/", 1)
    return ""

def do_extract(pdf_files, workers, output_path, txt_dir):
    """执行批量提取"""
    tasks = [(fp, guess_doi_from_pdf(fp)) for fp in pdf_files]

    t0 = time.time()
    results = []
    with Pool(workers) as pool:
        for i, result in enumerate(pool.imap_unordered(extract_text_from_pdf, tasks), 1):
            fname, doi, text, pages, error = result
            results.append(result)
            status = f"✅ {pages}p" if not error else f"❌ {error}"
            print(f"  [{i}/{len(tasks)}] {status} {fname}", flush=True)

    elapsed = time.time() - t0
    results.sort(key=lambda r: r[0])

    success = sum(1 for r in results if r[3] > 0)
    total_chars = sum(len(r[2]) for r in results)
    print(f"\n提取完成: ✅ {success} 成功, ❌ {len(results)-success} 失败", flush=True)
    print(f"总字符数: {total_chars:,}", flush=True)
    print(f"总耗时: {elapsed:.1f}s", flush=True)

    # 输出合并 Markdown
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 文献库全文\n\n")
        f.write(f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"> PDF 数: {success}/{len(results)}\n")
        f.write(f"> 总字符: {total_chars:,}\n\n")
        f.write("---\n\n")
        for r in results:
            fname, doi, text, pages, error = r
            if not text:
                continue
            f.write(f"## {fname}\n\n")
            if doi:
                f.write(f"DOI: {doi}\n\n")
            f.write(text)
            f.write(f"\n\n---\n\n")

    print(f"输出: {output_path} ({os.path.getsize(output_path)//1024}KB)", flush=True)

    if txt_dir:
        os.makedirs(txt_dir, exist_ok=True)
        for r in results:
            fname, doi, text, pages, error = r
            if not text:
                continue
            txt_path = os.path.join(txt_dir, fname.replace(".pdf", ".txt"))
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"DOI: {doi}\n\n" if doi else "")
                f.write(text)
        print(f"独立 .txt: {txt_dir}/ ({success} 个)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量提取 PDF 全文文本")
    parser.add_argument("pdf_dir", help="PDF 文件目录")
    parser.add_argument("--output", "-o", default="文献库全文.md",
                        help="输出 Markdown 文件路径")
    parser.add_argument("--txt-dir", help="独立 .txt 文件输出目录")
    parser.add_argument("--file-list", help="仅处理此文件中列出的 PDF 文件名（每行一个）")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"并行进程数（默认 {DEFAULT_WORKERS}）")
    parser.add_argument("--scheme", choices=["auto", "a", "b"], default="auto",
                        help="方案: auto=自动, a=按需精读, b=批量预提取")
    args = parser.parse_args()

    if not os.path.isdir(args.pdf_dir):
        print(f"错误: 目录不存在 {args.pdf_dir}", flush=True)
        sys.exit(1)

    # 收集 PDF 文件列表
    if args.file_list:
        with open(args.file_list) as f:
            filenames = [l.strip() for l in f if l.strip()]
        pdf_files = [os.path.join(args.pdf_dir, f) for f in filenames
                     if os.path.exists(os.path.join(args.pdf_dir, f))]
    else:
        pdf_files = [os.path.join(args.pdf_dir, f) for f in os.listdir(args.pdf_dir)
                     if f.endswith(".pdf")]
        pdf_files.sort()

    if not pdf_files:
        print("未找到 PDF 文件", flush=True)
        sys.exit(1)

    count = len(pdf_files)

    # Check optional dependencies before extraction
    if not check_optional_dep("fitz"):
        print("  ⚠ PyMuPDF 未安装，将无法提取 PDF 文本。", flush=True)
        print("  是否继续（仅预览模式）？[y/N]", flush=True)
        # Non-interactive: exit with hint
        exit(1)

    # 确定方案
    if args.scheme == "a":
        scheme = "A（按需精读）"
    elif args.scheme == "b":
        scheme = "B（批量预提取）"
    else:
        scheme = "B（批量预提取）" if count >= BATCH_THRESHOLD else "A（按需精读）"

    print(f"PDF 数量: {count}", flush=True)
    print(f"选用方案: {scheme}", flush=True)
    print(f"并行进程: {args.workers}", flush=True)
    print(f"输出文件: {args.output}", flush=True)
    print()

    if scheme.startswith("A"):
        print("方案 A — 按需精读: 适用于小批量或单章写作。")
        print("写作时逐篇引用，按需提取单篇 PDF。无需全量预处理。")
        print("直接使用 zotero_get_item_fulltext 或读取选中 PDF。")
        print(f"\n如需转为批量模式，增大文献量或指定 --scheme b\n")
        # 方案 A 实际就是直接读，这里只做一个提示
        if args.file_list:
            do_extract(pdf_files, args.workers, args.output, args.txt_dir)
    else:
        print("方案 B — 批量预提取: 全库一次提取，LLM 直接读合并文本。")
        print()
        do_extract(pdf_files, args.workers, args.output, args.txt_dir)
        print(f"\n提示: 写作时直接读取 {args.output} 即可，无需逐篇打开 PDF。")
