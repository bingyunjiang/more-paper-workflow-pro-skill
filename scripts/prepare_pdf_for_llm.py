#!/usr/bin/env python3
"""
轻量 PDF -> 文本准备脚本。

目标：
1. 从 PDF 提取全文文本
2. 执行基础清洗
3. 输出 raw / clean / chunks 三层结果
4. 保留可回查锚点，供 Step 7 / 7.15 / 8 复用

这个脚本刻意保持轻量，不试图完美恢复复杂公式、表格或版面结构。
"""

from __future__ import annotations

import argparse
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

PARSER_CHOICES = ("auto", "pymupdf", "mineru-local", "mineru-api")
DEFAULT_MINERU_BACKEND = "pipeline"
DEFAULT_MINERU_API_URL = os.environ.get("MINERU_API_URL", "").strip()
PYMUPDF_FALLBACK_RISKS = [
    "line_fragmentation",
    "reading_order_risk",
    "table_damage_risk",
    "figure_caption_loss",
    "paragraph_reconstruction_needed",
]


def extract_pages_pymupdf(pdf_path: Path) -> list[str]:
    import fitz

    doc = fitz.open(pdf_path)
    pages: list[str] = []
    try:
        for page in doc:
            pages.append(page.get_text() or "")
    finally:
        doc.close()
    return pages


def run_mineru_local(pdf_path: Path, out_dir: Path, backend: str) -> tuple[list[str], dict[str, Any]]:
    mineru_bin = shutil.which("mineru")
    if not mineru_bin:
        raise RuntimeError("MinerU CLI not found on PATH")

    mineru_out = Path(tempfile.mkdtemp(prefix=f"{pdf_path.stem}.mineru-", dir=out_dir))
    cmd = [mineru_bin, "-p", str(pdf_path), "-o", str(mineru_out)]
    if backend:
        cmd.extend(["-b", backend])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "MinerU CLI failed: "
            f"exit={proc.returncode}; stdout={proc.stdout.strip()[:400]}; stderr={proc.stderr.strip()[:400]}"
        )

    text_blocks, consumed_files = _load_mineru_outputs(mineru_out)
    if not text_blocks:
        raise RuntimeError(f"MinerU CLI returned no usable markdown/text output in {mineru_out}")

    return text_blocks, {
        "mineru_output_dir": str(mineru_out),
        "mineru_backend": backend or DEFAULT_MINERU_BACKEND,
        "mineru_cli": mineru_bin,
        "mineru_consumed_files": consumed_files,
        "mineru_mode": "local",
    }


def run_mineru_api(pdf_path: Path, api_url: str, timeout: int = 300) -> tuple[list[str], dict[str, Any]]:
    if not api_url:
        raise RuntimeError("MinerU API URL is missing; set --mineru-api-url or MINERU_API_URL")

    endpoint = api_url.strip().rstrip("/")
    if not endpoint:
        raise RuntimeError("MinerU API URL is empty")
    if not endpoint.endswith("/file_parse") and not endpoint.endswith("/tasks"):
        endpoint = f"{endpoint}/file_parse"

    body, content_type = _encode_multipart(
        fields={},
        files={"file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")},
    )
    req = urllib.request.Request(endpoint, data=body, method="POST")
    req.add_header("Content-Type", content_type)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"MinerU API request failed: {exc}") from exc

    try:
        data = json.loads(payload)
    except Exception as exc:
        raise RuntimeError(f"MinerU API returned non-JSON payload: {payload[:300]}") from exc

    text_blocks = _extract_text_blocks_from_object(data)
    consumed_files: list[str] = []
    if not text_blocks:
        output_path = _find_output_path_from_object(data)
        if output_path:
            p = Path(output_path)
            if p.exists():
                text_blocks, consumed_files = _load_mineru_outputs(p)

    if not text_blocks:
        raise RuntimeError("MinerU API returned no usable markdown/text output")

    return text_blocks, {
        "mineru_api_url": endpoint,
        "mineru_mode": "api",
        "mineru_consumed_files": consumed_files,
    }


def _encode_multipart(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = "----MinerUFormBoundary" + os.urandom(8).hex()
    body = io.BytesIO()

    for key, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.write(value.encode())
        body.write(b"\r\n")

    for key, (filename, content, content_type) in files.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.write(content)
        body.write(b"\r\n")

    body.write(f"--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def _load_mineru_outputs(output_dir: Path) -> tuple[list[str], list[str]]:
    candidates: list[Path] = []
    for suffix in (".md", ".markdown", ".txt"):
        candidates.extend(sorted(output_dir.rglob(f"*{suffix}")))
    if candidates:
        text_blocks = [p.read_text(encoding="utf-8", errors="replace").strip() for p in candidates if p.is_file()]
        text_blocks = [t for t in text_blocks if t]
        return _normalize_markdown_blocks(text_blocks), [str(p) for p in candidates]

    json_candidates = sorted(output_dir.rglob("*.json"))
    text_blocks: list[str] = []
    consumed: list[str] = []
    for path in json_candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        extracted = _extract_text_blocks_from_object(data)
        if extracted:
            text_blocks.extend(extracted)
            consumed.append(str(path))
    return _normalize_markdown_blocks(text_blocks), consumed


def _normalize_markdown_blocks(blocks: list[str]) -> list[str]:
    cleaned: list[str] = []
    for block in blocks:
        text = re.sub(r"\n{3,}", "\n\n", block.strip())
        if text:
            cleaned.append(text)
    return cleaned


def _extract_text_blocks_from_object(value: Any) -> list[str]:
    blocks: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if len(text) > 40:
            blocks.append(text)
        return blocks
    if isinstance(value, list):
        for item in value:
            blocks.extend(_extract_text_blocks_from_object(item))
        return blocks
    if isinstance(value, dict):
        for key in ("markdown", "md", "content", "text", "result", "output"):
            if key in value:
                blocks.extend(_extract_text_blocks_from_object(value[key]))
        for item in value.values():
            blocks.extend(_extract_text_blocks_from_object(item))
    return blocks


def _find_output_path_from_object(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("output_path", "output", "path", "result_path"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        for item in value.values():
            candidate = _find_output_path_from_object(item)
            if candidate:
                return candidate
    if isinstance(value, list):
        for item in value:
            candidate = _find_output_path_from_object(item)
            if candidate:
                return candidate
    return ""


def normalize_line(line: str) -> str:
    line = line.replace("\u00ad", "")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def looks_like_page_number(line: str) -> bool:
    return bool(re.fullmatch(r"[0-9]{1,4}", line.strip()))


def looks_like_running_header(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 4:
        return False
    if len(stripped) > 90:
        return False
    if re.search(r"(doi|vol\.|volume|issue|copyright|received|accepted)", stripped, flags=re.I):
        return True
    upper_ratio = sum(1 for c in stripped if c.isupper()) / max(len(stripped), 1)
    return upper_ratio > 0.55 and len(stripped.split()) <= 12


def merge_lines(lines: list[str]) -> str:
    out: list[str] = []
    buffer = ""
    for raw in lines:
        line = normalize_line(raw)
        if not line:
            if buffer:
                out.append(buffer.strip())
                buffer = ""
            out.append("")
            continue
        if looks_like_page_number(line) or looks_like_running_header(line):
            continue
        if buffer and buffer.endswith("-") and line:
            buffer = buffer[:-1] + line
            continue
        if buffer and not re.search(r"[.!?;:。！？；：]$", buffer) and not re.match(r"^(#+|\[Figure|\[Equation|Table\s+\d+|Figure\s+\d+)", line):
            buffer += " " + line
        else:
            if buffer:
                out.append(buffer.strip())
            buffer = line
    if buffer:
        out.append(buffer.strip())
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def detect_risk_flags(text: str) -> list[str]:
    flags: list[str] = []
    if re.search(r"\b(eq\.?|equation)\b|\([0-9]+\)", text, flags=re.I):
        flags.append("equation")
    if re.search(r"\btable\s+[0-9]+\b", text, flags=re.I):
        flags.append("table")
    if re.search(r"\bfigure\s+[0-9]+\b|\bfig\.\s*[0-9]+\b", text, flags=re.I):
        flags.append("figure_caption")
    if re.search(r"\bappendix\b|\bsupplementary\b", text, flags=re.I):
        flags.append("appendix_detail")
    return sorted(set(flags))


def split_chunks(clean_text: str, chunk_words: int) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    chunks: list[dict[str, Any]] = []
    current: list[str] = []
    current_words = 0
    seq = 1

    for para in paragraphs:
        words = len(para.split())
        if current and current_words + words > chunk_words:
            joined = "\n\n".join(current).strip()
            chunks.append(
                {
                    "chunk_seq": seq,
                    "text": joined,
                    "risk_flags": detect_risk_flags(joined),
                }
            )
            seq += 1
            current = []
            current_words = 0
        current.append(para)
        current_words += words

    if current:
        joined = "\n\n".join(current).strip()
        chunks.append(
            {
                "chunk_seq": seq,
                "text": joined,
                "risk_flags": detect_risk_flags(joined),
            }
        )
    return chunks


def analyze_complexity(pages: list[str]) -> dict[str, Any]:
    page_count = len(pages)
    total_chars = sum(len(p or "") for p in pages)
    avg_chars = total_chars / max(page_count, 1)
    empty_pages = sum(1 for p in pages if not (p or "").strip())
    short_line_ratio_samples: list[float] = []
    marker_hits = 0

    for page in pages:
        lines = [normalize_line(line) for line in (page or "").splitlines()]
        lines = [line for line in lines if line]
        if lines:
            short = sum(1 for line in lines if len(line) < 35)
            short_line_ratio_samples.append(short / len(lines))
        marker_hits += len(re.findall(r"\b(table|figure|equation|appendix|supplementary)\b", page or "", flags=re.I))

    short_line_ratio = sum(short_line_ratio_samples) / max(len(short_line_ratio_samples), 1)
    risk_flags: list[str] = []
    if page_count >= 4 and avg_chars < 900:
        risk_flags.append("low_text_density")
    if empty_pages > 0:
        risk_flags.append("scan_or_ocr_likely")
    if short_line_ratio >= 0.45:
        risk_flags.append("multi_column_or_fragmented_layout")
    if marker_hits >= 4:
        risk_flags.append("formula_table_dense")
    if total_chars == 0:
        risk_flags.append("text_extraction_failed")

    return {
        "page_count": page_count,
        "total_chars": total_chars,
        "avg_chars_per_page": round(avg_chars, 2),
        "empty_pages": empty_pages,
        "short_line_ratio": round(short_line_ratio, 3),
        "marker_hits": marker_hits,
        "risk_flags": sorted(set(risk_flags)),
        "mineru_recommended": bool(risk_flags),
    }


def mineru_recommendation_text(risk_flags: list[str], parser_mode: str) -> str:
    if not risk_flags:
        return ""
    flags = ", ".join(risk_flags)
    if parser_mode == "auto":
        return (
            "检测到复杂 PDF，建议改用 MinerU 以获得更好的版面恢复和 OCR 结果。"
            f" 当前将继续使用轻量解析链路；风险标记：{flags}。"
            " 如可用，请重跑：`--parser mineru-local` 或 `--parser mineru-api`。"
            " 首次使用可参考 MinerU 官方仓库与文档；本地 CLI 常用命令是 `mineru -p <input_path> -o <output_path>`，"
            " 纯 CPU 场景可加 `-b pipeline`。若暂时不安装，可先试官方在线 demo 再决定是否接入。"
            " 如果你计划长期使用 MinerU API，可按官方文档自建或使用官方服务，并准备 endpoint / token 后再启用 `mineru-api`。"
        )
    return (
        "当前文档属于高风险版面，MinerU 更适合处理。"
        f" 风险标记：{flags}。"
        " 如未安装 MinerU，可先参考官方仓库的 Local Deployment / Online Experience 说明。"
        " 如果你计划长期使用 MinerU API，可按官方文档自建或使用官方服务，并准备 endpoint / token 后再启用 `mineru-api`。"
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare PDF text for Step 7/8 LLM use.")
    parser.add_argument("--pdf", required=True, help="PDF file path")
    parser.add_argument("--out-dir", default="pdf-prepared", help="Output directory")
    parser.add_argument("--parser", default="auto", choices=PARSER_CHOICES,
                        help="PDF parser backend: auto/pymupdf/mineru-local/mineru-api")
    parser.add_argument("--mineru-api-url", default=DEFAULT_MINERU_API_URL,
                        help="MinerU API endpoint or base URL (optional)")
    parser.add_argument("--mineru-backend", default=DEFAULT_MINERU_BACKEND,
                        help="MinerU local backend name (default: pipeline)")
    parser.add_argument("--paper-title", default="", help="Paper title")
    parser.add_argument("--citekey", default="", help="BibTeX citekey")
    parser.add_argument("--zotero-item-key", default="", help="Zotero item key")
    parser.add_argument("--section", default="", help="Optional section label")
    parser.add_argument("--evidence-level", default="pdf_fulltext_supported",
                        choices=["metadata_only", "notes_or_abstract_supported", "pdf_fulltext_supported"])
    parser.add_argument("--chunk-words", type=int, default=1200, help="Approximate words per chunk")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    out_dir = Path(args.out_dir).expanduser().resolve()
    stem = pdf_path.stem
    raw_path = out_dir / f"{stem}.raw.md"
    clean_path = out_dir / f"{stem}.clean.md"
    chunks_path = out_dir / f"{stem}.chunks.json"
    report_path = out_dir / f"{stem}.extraction_report.json"
    artifact_index_path = out_dir / "prepared_pdf_artifacts.json"

    parser_requested = args.parser
    parser_used = "pymupdf"
    parser_fallback_reason = ""
    parser_messages: list[str] = []
    mineru_meta: dict[str, Any] = {}

    try:
        pages = extract_pages_pymupdf(pdf_path)
    except ImportError:
        raise SystemExit("Missing dependency: PyMuPDF (fitz). Install with `pip install pymupdf`.")

    complexity = analyze_complexity(pages)
    recommendation = mineru_recommendation_text(complexity["risk_flags"], parser_requested)
    if recommendation:
        parser_messages.append(recommendation)

    text_blocks: list[str] = pages
    if parser_requested == "mineru-local":
        try:
            text_blocks, mineru_meta = run_mineru_local(pdf_path, out_dir, args.mineru_backend)
            parser_used = "mineru-local"
        except Exception as exc:
            parser_fallback_reason = str(exc)
            parser_messages.append(
                "MinerU local 不可用，已自动回退到 PyMuPDF 轻量解析链路。"
                f" 原因：{parser_fallback_reason}"
            )
            text_blocks = pages
    elif parser_requested == "mineru-api":
        try:
            text_blocks, mineru_meta = run_mineru_api(pdf_path, args.mineru_api_url)
            parser_used = "mineru-api"
        except Exception as exc:
            parser_fallback_reason = str(exc)
            parser_messages.append(
                "MinerU API 不可用，已自动回退到 PyMuPDF 轻量解析链路。"
                f" 原因：{parser_fallback_reason}"
            )
            text_blocks = pages
    else:
        if complexity["mineru_recommended"]:
            parser_messages.append(
                "当前保持默认轻量解析链路；如需更高保真版面恢复，请显式改用 MinerU。"
            )

    raw_blocks = []
    for idx, text in enumerate(text_blocks, start=1):
        raw_blocks.append(f"## Page {idx}\n\n{text.strip()}\n")
    raw_text = "\n".join(raw_blocks).strip() + "\n"

    clean_text = merge_lines(raw_text.splitlines())
    chunks = split_chunks(clean_text, args.chunk_words)
    parser_confidence = "low" if parser_used == "pymupdf" else "medium"
    parser_risk_flags = list(PYMUPDF_FALLBACK_RISKS) if parser_used == "pymupdf" else []

    chunk_payload = []
    for item in chunks:
        chunk_id = f"{stem}_{item['chunk_seq']:03d}"
        risk_flags = sorted(set(item["risk_flags"] + parser_risk_flags))
        must_check_pdf = bool(risk_flags) or parser_used == "pymupdf"
        chunk_payload.append(
            {
                "chunk_id": chunk_id,
                "paper_title": args.paper_title or stem,
                "citekey": args.citekey,
                "zotero_item_key": args.zotero_item_key,
                "source_pdf": str(pdf_path),
                "pages": "",
                "section": args.section,
                "evidence_level": args.evidence_level,
                "parser_used": parser_used,
                "parser_confidence": parser_confidence,
                "must_check_pdf": must_check_pdf,
                "risk_flags": risk_flags,
                "text": item["text"],
            }
        )

    report = {
        "source_pdf": str(pdf_path),
        "paper_title": args.paper_title or stem,
        "citekey": args.citekey,
        "zotero_item_key": args.zotero_item_key,
        "page_count": len(text_blocks),
        "chunk_count": len(chunk_payload),
        "evidence_level": args.evidence_level,
        "parser_requested": parser_requested,
        "parser_used": parser_used,
        "parser_confidence": parser_confidence,
        "parser_fallback_reason": parser_fallback_reason,
        "parser_risk_flags": parser_risk_flags,
        "complexity_assessment": complexity,
        "mineru_recommended": complexity["mineru_recommended"],
        "messages": parser_messages,
        "notes": [
            "raw.md is the direct extracted layer",
            "clean.md is the cleaned reading layer",
            "chunks.json is the LLM working layer",
            "original PDF remains the truth source for quotes, pages, equations, tables, and figure captions",
        ],
    }
    report.update(mineru_meta)

    artifact_entry = {
        "source_pdf": str(pdf_path),
        "paper_title": args.paper_title or stem,
        "citekey": args.citekey,
        "zotero_item_key": args.zotero_item_key,
        "parser_requested": parser_requested,
        "parser_used": parser_used,
        "parser_confidence": parser_confidence,
        "parser_fallback_reason": parser_fallback_reason,
        "mineru_recommended": complexity["mineru_recommended"],
        "parser_messages": parser_messages,
        "raw_md": str(raw_path),
        "clean_md": str(clean_path),
        "chunks_json": str(chunks_path),
        "extraction_report_json": str(report_path),
        "evidence_level": args.evidence_level,
        "must_check_pdf": any(chunk.get("must_check_pdf") for chunk in chunk_payload),
        "risk_flags": sorted({flag for chunk in chunk_payload for flag in chunk.get("risk_flags", [])}),
    }

    artifact_index = {"artifacts": [artifact_entry]}

    write_text(raw_path, raw_text)
    write_text(clean_path, clean_text)
    write_json(chunks_path, chunk_payload)
    write_json(report_path, report)
    write_json(artifact_index_path, artifact_index)

    print(f"RAW: {raw_path}")
    print(f"CLEAN: {clean_path}")
    print(f"CHUNKS: {chunks_path}")
    print(f"REPORT: {report_path}")
    print(f"ARTIFACT_INDEX: {artifact_index_path}")
    print(f"PARSER_REQUESTED: {parser_requested}")
    print(f"PARSER_USED: {parser_used}")
    if parser_messages:
        for msg in parser_messages:
            print(f"NOTICE: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
