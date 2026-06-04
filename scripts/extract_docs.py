#!/usr/bin/env python3
"""
批量提取工程技术文档文本（.docx / .doc），供大纲优化和文档分析使用。

功能：
  1. 扫描目录中的 .docx / .doc 文件，列出大小和类型
  2. 按文件大小检测重复文件（如 (1) 副本）
  3. .docx 用 python-docx 提取段落文本
  4. .doc（旧格式）用 macOS textutil 转换后提取
  5. 清理 TOC 域代码残留
  6. 输出独立 .txt 或合并 .md（含前80行/后30行结构预览）

依赖：
  - python-docx: pip install python-docx
  - .doc 转换工具（按平台自动选择）：
    - macOS: textutil（系统内置，无需安装）
    - Windows / Linux: LibreOffice（需安装: https://www.libreoffice.org/）

Usage:
  # 仅扫描文件清单和去重提示
  python3 scripts/extract_docs.py /path/to/docs/ --scan-only

  # 提取为独立 .txt 文件
  python3 scripts/extract_docs.py /path/to/docs/ --txt-dir extracted/

  # 提取为合并 Markdown（供对话分析用）
  python3 scripts/extract_docs.py /path/to/docs/ --output combined.md

  # 跳过重复文件、设置超时
  python3 scripts/extract_docs.py /path/to/docs/ --txt-dir out/ --timeout 60
"""
import sys, os, re, argparse, subprocess, time
from pathlib import Path

# ── 常量 ─────────────────────────────────────────────────────

# 已知的 TOC 域代码模式（textutil 转换 .doc 时可能暴露未更新的域代码）
TOC_ARTIFACT_PATTERNS = [
    re.compile(r'\{\s*TOC\s+\\[^}]*\}'),        # { TOC \o "1-3" \h ... }
    re.compile(r'\{\s*HYPERLINK\s+[^}]*\}'),     # { HYPERLINK ... }
    re.compile(r'\{\* MERGEFORMAT\s*\}'),         # {* MERGEFORMAT}
]

SUPPORTED_EXTS = {'.docx', '.doc'}


# ── 文件扫描与去重 ──────────────────────────────────────────

def scan_docs(directory: str) -> list[dict]:
    """扫描目录，返回文件信息列表（按文件名排序，含去重标记）。

    Returns:
        [{name, path, ext, size_bytes, size_kb, duplicate_of: str|None}]
    """
    files = []
    for name in sorted(os.listdir(directory)):
        if name.startswith('.') or name.startswith('~$'):
            continue
        path = os.path.join(directory, name)
        ext = os.path.splitext(name)[1].lower()
        if ext not in SUPPORTED_EXTS:
            continue
        if not os.path.isfile(path):
            continue
        size = os.path.getsize(path)
        files.append({
            'name': name,
            'path': path,
            'ext': ext,
            'size_bytes': size,
            'size_kb': round(size / 1024, 1),
            'duplicate_of': None,
        })

    # 按文件大小检测疑似重复
    size_map: dict[int, str] = {}
    for f in files:
        key = f['size_bytes']
        if key in size_map:
            f['duplicate_of'] = size_map[key]
        else:
            size_map[key] = f['name']

    return files


# ── 文本提取 ─────────────────────────────────────────────────

def extract_docx_text(filepath: str) -> list[str]:
    """用 python-docx 提取 .docx 段落文本（仅保留非空行）。"""
    import docx
    doc = docx.Document(filepath)
    return [p.text for p in doc.paragraphs if p.text.strip()]


def _find_converter() -> str:
    """检测系统可用的 .doc 转换工具，返回 "textutil" | "libreoffice" | ""。"""
    import shutil
    if shutil.which("textutil"):
        return "textutil"
    if shutil.which("soffice") or shutil.which("libreoffice"):
        return "libreoffice"
    return ""


def extract_doc_text(filepath: str, timeout: int = 60) -> list[str]:
    """将旧格式 .doc 转为纯文本后提取行。

    按平台自动选择转换工具：
      - macOS: textutil（系统内置，最快）
      - Windows / Linux: LibreOffice --headless --convert-to txt
      - 若都不可用则报错
    """
    converter = _find_converter()
    if not converter:
        raise RuntimeError(
            "未找到 .doc 转换工具。macOS 已内置 textutil；"
            "Windows/Linux 请安装 LibreOffice: https://www.libreoffice.org/"
        )

    outpath = os.path.join(
        os.environ.get("TMPDIR", os.environ.get("TEMP", "/tmp")),
        f"hermes_doc_convert_{os.getpid()}.txt"
    )

    try:
        if converter == "textutil":
            result = subprocess.run(
                ["textutil", "-convert", "txt", "-output", outpath, filepath],
                capture_output=True, timeout=timeout,
            )
        else:  # libreoffice
            out_dir = os.path.dirname(outpath)
            result = subprocess.run(
                ["soffice", "--headless", "--convert-to", "txt:Text",
                 "--outdir", out_dir, filepath],
                capture_output=True, timeout=timeout,
            )
            # LibreOffice 输出文件名不同于我们指定的，需要找到它
            base = os.path.splitext(os.path.basename(filepath))[0]
            generated = os.path.join(out_dir, f"{base}.txt")
            if os.path.exists(generated) and generated != outpath:
                os.rename(generated, outpath)

        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"{converter} 返回非零退出码: {stderr}")

        with open(outpath, 'r', encoding='utf-8', errors='replace') as f:
            lines = [l.strip() for l in f if l.strip()]
        return lines
    finally:
        if os.path.exists(outpath):
            os.unlink(outpath)


def clean_toc_artifacts(lines: list[str]) -> list[str]:
    """清理 textutil 可能暴露的 TOC 域代码残留。"""
    cleaned = []
    for line in lines:
        for pattern in TOC_ARTIFACT_PATTERNS:
            line = pattern.sub('', line)
        line = line.strip()
        if line:
            cleaned.append(line)
    return cleaned


def extract_file(filepath: str, ext: str, timeout: int = 30) -> dict:
    """提取单个文件，返回结果字典。

    Returns:
        {lines: list[str], char_count: int, line_count: int,
         error: str|None, elapsed: float}
    """
    t0 = time.time()
    try:
        if ext == '.docx':
            lines = extract_docx_text(filepath)
        elif ext == '.doc':
            lines = extract_doc_text(filepath, timeout)
            lines = clean_toc_artifacts(lines)
        else:
            return _error_result(f'不支持的文件类型: {ext}', t0)

        elapsed = time.time() - t0
        return {
            'lines': lines,
            'char_count': sum(len(l) for l in lines),
            'line_count': len(lines),
            'error': None,
            'elapsed': elapsed,
        }
    except ImportError:
        return _error_result('缺少 python-docx，请执行: pip install python-docx', t0)
    except subprocess.TimeoutExpired:
        return _error_result(f'textutil 超时（>{timeout}s），文件可能过大', t0)
    except Exception as e:
        return _error_result(str(e), t0)


def _error_result(msg: str, t0: float) -> dict:
    return {
        'lines': [], 'char_count': 0, 'line_count': 0,
        'error': msg, 'elapsed': time.time() - t0,
    }


# ── 输出构建 ─────────────────────────────────────────────────

def build_markdown_block(file_info: dict, result: dict, preview_head: int = 80,
                         preview_tail: int = 30) -> str:
    """为单个文件构建 Markdown 输出块（含结构预览）。"""
    name = file_info['name']
    dup = file_info.get('duplicate_of')

    lines = [f"## {name}", ""]
    lines.append(f"- 大小: {file_info['size_kb']} KB  |  类型: {file_info['ext']}")

    if dup:
        lines.append(f"- ⚠️ 疑似重复: 与 `{dup}` 大小完全相同")

    if result['error']:
        lines.append(f"- ❌ 提取失败: {result['error']}")
        lines.extend(["", "---", ""])
        return "\n".join(lines)

    lines.append(f"- 段落数: {result['line_count']}  |  字符数: {result['char_count']:,}  |  耗时: {result['elapsed']:.1f}s")
    lines.append("")

    content = result['lines']

    # 前 N 行 — 结构目录
    lines.append(f"### 前 {preview_head} 行（结构概览）")
    lines.append("")
    for l in content[:preview_head]:
        lines.append(f"> {l[:200]}")
    lines.append("")

    if len(content) > preview_head:
        lines.append(f"> ...（省略中间 {len(content) - preview_head - preview_tail} 行）")
        lines.append("")

    # 后 N 行 — 结论/附录
    if len(content) > preview_head:
        tail_start = max(preview_head, len(content) - preview_tail)
        lines.append(f"### 后 {min(preview_tail, len(content) - preview_head)} 行（结论/附录）")
        lines.append("")
        for l in content[tail_start:]:
            lines.append(f"> {l[:200]}")
        lines.append("")

    lines.extend(["---", ""])
    return "\n".join(lines)


# ── 主流程 ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="批量提取工程技术文档文本（.docx / .doc）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s /path/to/docs/ --scan-only            # 仅扫描文件清单
  %(prog)s /path/to/docs/ --txt-dir extracted/    # 提取为独立 .txt
  %(prog)s /path/to/docs/ --output combined.md    # 提取为合并 Markdown
        """,
    )
    parser.add_argument("directory", help="包含 .docx / .doc 文件的目录")
    parser.add_argument("--output", "-o", help="合并输出 Markdown 文件路径")
    parser.add_argument("--txt-dir", help="独立 .txt 文件输出目录")
    parser.add_argument("--scan-only", action="store_true",
                        help="仅扫描文件清单和去重提示，不提取文本")
    parser.add_argument("--timeout", type=int, default=30,
                        help="单个文件提取超时秒数（默认 30）")
    parser.add_argument("--max-files", type=int, default=50,
                        help="最大提取文件数（默认 50，超出截断）")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"❌ 目录不存在: {args.directory}", flush=True)
        sys.exit(1)

    # ── Step 1: 扫描 ──

    files = scan_docs(args.directory)

    if not files:
        print(f"📭 未找到 .docx / .doc 文件: {args.directory}", flush=True)
        sys.exit(0)

    docx_n = sum(1 for f in files if f['ext'] == '.docx')
    doc_n  = sum(1 for f in files if f['ext'] == '.doc')
    dup_n  = sum(1 for f in files if f['duplicate_of'])

    print(f"📁 {args.directory}")
    print(f"   .docx: {docx_n} 个  |  .doc: {doc_n} 个", flush=True)

    if dup_n:
        print(f"   ⚠️ 疑似重复: {dup_n} 个（文件大小相同）", flush=True)
        for f in files:
            if f['duplicate_of']:
                print(f"      `{f['name']}` ↔ `{f['duplicate_of']}`", flush=True)

    # 文件清单
    print(f"\n{'文件':<45} {'大小':>8} {'类型':>6}", flush=True)
    print("-" * 62, flush=True)
    for f in files:
        flag = " ⚠️重复" if f['duplicate_of'] else ""
        print(f"{f['name']:<45} {f['size_kb']:>6.0f} KB {f['ext']:>6}{flag}", flush=True)

    if args.scan_only:
        print("\n✅ 扫描完成（--scan-only 模式，未提取文本）。", flush=True)
        if dup_n:
            print("💡 提示: 确认重复后可手动删除副本，或提取时自动跳过。", flush=True)
        return

    # ── Step 2: 提取 ──

    # 跳过疑似重复文件
    to_extract = [f for f in files if not f['duplicate_of']]
    skipped = len(files) - len(to_extract)
    if skipped:
        print(f"\n⏭ 跳过 {skipped} 个疑似重复文件", flush=True)

    if len(to_extract) > args.max_files:
        print(f"⚠️ 文件数 ({len(to_extract)}) 超过上限 ({args.max_files})，"
              f"仅处理前 {args.max_files} 个", flush=True)
        to_extract = to_extract[:args.max_files]

    print(f"\n🔧 开始提取文本（{len(to_extract)} 个文件）...\n", flush=True)

    results: dict[str, dict] = {}
    for i, f in enumerate(to_extract, 1):
        print(f"  [{i:>2}/{len(to_extract)}] {f['name']}...", end=" ", flush=True)
        result = extract_file(f['path'], f['ext'], args.timeout)
        results[f['name']] = result

        if result['error']:
            print(f"❌ {result['error']}", flush=True)
        else:
            print(f"✅ {result['line_count']} 段, {result['char_count']:,} 字, "
                  f"{result['elapsed']:.1f}s", flush=True)

    # ── Step 3: 输出 ──

    success = sum(1 for r in results.values() if not r['error'])
    fail = len(results) - success
    print(f"\n📊 提取完成: ✅ {success} 成功, ❌ {fail} 失败", flush=True)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(f"# 工程技术文档批量提取\n\n")
            f.write(f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"> 源目录: {args.directory}\n")
            f.write(f"> 提取成功: {success}/{len(to_extract)}\n\n")
            f.write("---\n\n")

            for file_info in to_extract:
                result = results.get(file_info['name'])
                if result and not result['error']:
                    f.write(build_markdown_block(file_info, result))

        size_kb = os.path.getsize(args.output) // 1024
        print(f"📄 合并输出: {args.output} ({size_kb} KB)", flush=True)

    if args.txt_dir:
        os.makedirs(args.txt_dir, exist_ok=True)
        written = 0
        for file_info in to_extract:
            result = results.get(file_info['name'])
            if result and not result['error'] and result['lines']:
                base = os.path.splitext(file_info['name'])[0]
                txt_path = os.path.join(args.txt_dir, f"{base}.txt")
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 源文件: {file_info['name']}\n")
                    f.write(f"# 大小: {file_info['size_kb']} KB\n")
                    f.write(f"# 提取时间: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
                    for line in result['lines']:
                        f.write(line + '\n')
                written += 1
        print(f"📄 独立 .txt: {args.txt_dir}/ ({written} 个)", flush=True)

    if not args.output and not args.txt_dir:
        print("💡 未指定输出方式，请使用 --output 或 --txt-dir", flush=True)
        print("   示例: python3 scripts/extract_docs.py docs/ --output combined.md", flush=True)


if __name__ == "__main__":
    main()
