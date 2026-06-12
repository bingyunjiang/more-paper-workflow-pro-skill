#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Target journal style profile extractor — learns writing conventions from exemplar
papers published in the target venue, then outputs a structured style profile that
guides Step 7 writing to match the journal's rhetorical patterns.

Inspired by PaperSpine's style_profile.md + exemplar_learning_dossier.md.

Usage:
  # Flash mode: 3 exemplar papers (quick, ~5 min)
  python3 learn_journal_style.py --target-journal "Applied Thermal Engineering" \\
      --pdf-dir exemplar_pdfs/ --mode flash --output research_dossier/

  # Pro mode: 6 exemplar papers (thorough, ~10 min)
  python3 learn_journal_style.py --target-journal "Nature Communications" \\
      --pdf-dir exemplar_pdfs/ --mode pro

  # Use Zotero collection as exemplar source (requires Zotero MCP)
  python3 learn_journal_style.py --target-journal "IEEE T-PAMI" \\
      --zotero-collection "TPAMI-Exemplars" --mode pro

  # Analyze from existing PDF text dumps (from batch_read_pdfs.py)
  python3 learn_journal_style.py --target-journal "Energy" \\
      --text-dir paper-txt/ --mode flash
"""
import json
import sys
import os
import re
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class StyleProfile:
    """Complete style profile for a target journal."""
    journal: str
    mode: str                     # "flash" or "pro"
    num_exemplars: int
    target_genre: str = "journal"
    target_name: str = ""
    # Formatting
    abstract_word_count: dict = field(default_factory=dict)   # {min, max, avg}
    section_heading_style: str = ""  # numbered, unnumbered, mixed
    typical_section_count: dict = field(default_factory=dict)  # {min, max, avg}
    paragraph_length: dict = field(default_factory=dict)      # {min, max, avg_sentences}
    # Typography preferences inferred from conventions
    figure_caption_style: str = ""  # "sentence-case", "title-case", "mixed"
    reference_format: str = ""     # "numbered", "author-year"
    # Structure
    section_order: list[str] = field(default_factory=list)
    typical_subsections: dict = field(default_factory=dict)   # section -> avg count
    # Citation patterns
    avg_citations_per_section: dict = field(default_factory=dict)
    total_references_range: dict = field(default_factory=dict)  # {min, max, avg}
    # Language patterns
    avg_sentence_length: float = 0.0
    passive_voice_ratio: float = 0.0   # 0-1, higher = more passive
    hedging_frequency: dict = field(default_factory=dict)      # hedging terms per 1000 words
    transition_phrases: list[str] = field(default_factory=list)  # common transitions
    sample_source: str = ""
    sample_count: int = 0
    confidence: str = "medium"
    constraints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render as style_profile.md."""
        return _render_style_profile_md(self)

    def to_schema_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "journal": self.journal,
            "target_genre": self.target_genre,
            "target_name": self.target_name or self.journal,
            "sample_source": self.sample_source,
            "sample_count": self.sample_count or self.num_exemplars,
            "confidence": self.confidence,
            "structure_rules": {
                "abstract_word_count": self.abstract_word_count,
                "section_heading_style": self.section_heading_style,
                "typical_section_count": self.typical_section_count,
                "paragraph_length": self.paragraph_length,
                "section_order": self.section_order,
                "typical_subsections": self.typical_subsections,
            },
            "language_rules": {
                "avg_sentence_length": self.avg_sentence_length,
                "passive_voice_ratio": self.passive_voice_ratio,
                "hedging_frequency": self.hedging_frequency,
                "transition_phrases": self.transition_phrases,
            },
            "citation_rules": {
                "reference_format": self.reference_format,
                "avg_citations_per_section": self.avg_citations_per_section,
                "total_references_range": self.total_references_range,
            },
            "figure_rules": {
                "figure_caption_style": self.figure_caption_style,
            },
            "constraints": self.constraints,
            "warnings": self.warnings,
        }


@dataclass
class ExemplarAnalysis:
    """Analysis of a single exemplar paper."""
    filename: str
    title: str = ""
    year: int = 0
    # Structural metrics
    sections: list[str] = field(default_factory=list)
    subsection_count: int = 0
    abstract_word_count: int = 0
    # Citation metrics
    reference_count: int = 0
    # Language metrics
    total_sentences: int = 0
    total_words: int = 0
    avg_sentence_length: float = 0.0
    passive_ratio: float = 0.0
    hedging_count: int = 0
    # Paragraph structure
    avg_paragraph_sentences: float = 0.0
    paragraphs: list[int] = field(default_factory=list)  # sentence counts per paragraph


# ── PDF Text Parsing ─────────────────────────────────────────────────────────

def analyze_pdf_text(text: str, filename: str) -> ExemplarAnalysis:
    """Analyze a single exemplar paper's full text."""
    analysis = ExemplarAnalysis(filename=filename)

    # Extract title (first non-empty line that looks like a title)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        analysis.title = lines[0]

    # Count sections (look for heading patterns)
    heading_patterns = [
        r'^\d+\.\s+\w+',           # "1. Introduction"
        r'^[IVX]+\.\s+\w+',        # "I. Introduction"
        r'^(?:Introduction|Method|Experiment|Result|Conclusion|Discussion|Related|Background|Abstract|Reference)',
    ]
    section_headings = []
    for line in lines:
        for pat in heading_patterns:
            if re.match(pat, line, re.IGNORECASE):
                section_headings.append(line)
                break
    analysis.sections = section_headings
    analysis.subsection_count = len([
        l for l in lines
        if re.match(r'^\d+\.\d+\s+', l)
    ])

    # Abstract word count (look for abstract section)
    abstract_text = _extract_abstract_section(text)
    analysis.abstract_word_count = len(abstract_text.split()) if abstract_text else 0

    # Count references
    ref_section = _extract_reference_section(text)
    if ref_section:
        # Count lines starting with [N] or N. pattern
        ref_lines = re.findall(r'(?:^\[?\d+\]?\.?\s+)', ref_section, re.MULTILINE)
        analysis.reference_count = len(ref_lines) if ref_lines else 0

    # Sentence analysis
    sentences = _split_sentences(text)
    analysis.total_sentences = len(sentences)
    words = text.split()
    analysis.total_words = len(words)
    analysis.avg_sentence_length = (
        analysis.total_words / max(analysis.total_sentences, 1)
    )

    # Passive voice ratio (heuristic: count "is/are/was/were/been + past participle")
    passive_patterns = [
        r'\b(?:is|are|was|were|been|be)\s+\w+ed\b',
        r'\b(?:is|are|was|were|been|be)\s+\w+(?:ed|en|t)\b',
    ]
    passive_count = 0
    for pat in passive_patterns:
        passive_count += len(re.findall(pat, text, re.IGNORECASE))
    analysis.passive_ratio = passive_count / max(analysis.total_sentences, 1)

    # Hedging frequency
    hedging_terms = [
        'may', 'might', 'could', 'suggest', 'indicate', 'appear',
        'seem', 'potentially', 'likely', 'probably', 'possibly',
        'tend to', 'in general', 'typically', 'often', 'usually',
    ]
    analysis.hedging_count = sum(
        len(re.findall(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE))
        for t in hedging_terms
    )

    # Paragraph structure
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 100]
    para_sentence_counts = []
    for para in paragraphs:
        para_sents = _split_sentences(para)
        if para_sents:
            para_sentence_counts.append(len(para_sents))
    analysis.paragraphs = para_sentence_counts
    analysis.avg_paragraph_sentences = (
        sum(para_sentence_counts) / max(len(para_sentence_counts), 1)
    )

    return analysis


def combine_analyses(
    journal: str, mode: str, analyses: list[ExemplarAnalysis],
) -> StyleProfile:
    """Combine individual exemplar analyses into a journal style profile."""
    if not analyses:
        return StyleProfile(journal=journal, mode=mode, num_exemplars=0)

    profile = StyleProfile(
        journal=journal,
        mode=mode,
        num_exemplars=len(analyses),
    )

    # Abstract word count
    awc = [a.abstract_word_count for a in analyses if a.abstract_word_count > 0]
    if awc:
        profile.abstract_word_count = {"min": min(awc), "max": max(awc), "avg": round(sum(awc) / len(awc))}

    # Section count
    sc = [len(a.sections) for a in analyses]
    profile.typical_section_count = {"min": min(sc), "max": max(sc), "avg": round(sum(sc) / len(sc), 1)}

    # Section heading style
    numbered = sum(1 for a in analyses if any(re.match(r'^\d', s) for s in a.sections))
    if numbered >= len(analyses) * 0.7:
        profile.section_heading_style = "numbered (e.g., '1. Introduction')"
    elif numbered <= len(analyses) * 0.3:
        profile.section_heading_style = "unnamed (descriptive headings without numbers)"
    else:
        profile.section_heading_style = "mixed"

    # Section order (most common order)
    all_section_names = []
    for a in analyses:
        names = [_normalize_section_name(s) for s in a.sections]
        all_section_names.append(names)
    profile.section_order = _most_common_order(all_section_names)

    # Typical subsections
    profile.typical_subsections = {
        "per_paper_avg": round(sum(a.subsection_count for a in analyses) / len(analyses), 1),
    }

    # Citation patterns
    refs = [a.reference_count for a in analyses if a.reference_count > 0]
    if refs:
        profile.total_references_range = {"min": min(refs), "max": max(refs), "avg": round(sum(refs) / len(refs))}

    # Language patterns
    profile.avg_sentence_length = round(
        sum(a.avg_sentence_length for a in analyses) / len(analyses), 1
    )
    profile.passive_voice_ratio = round(
        sum(a.passive_ratio for a in analyses) / len(analyses), 2
    )

    # Common transition phrases
    transition_counter = Counter()
    for a in analyses:
        for t in _find_transitions(a):
            transition_counter[t.lower()] += 1
    profile.transition_phrases = [p for p, c in transition_counter.most_common(10)]

    # Paragraph length
    all_para_counts = []
    for a in analyses:
        all_para_counts.extend(a.paragraphs)
    if all_para_counts:
        profile.paragraph_length = {
            "min": min(all_para_counts),
            "max": max(all_para_counts),
            "avg_sentences": round(sum(all_para_counts) / len(all_para_counts), 1),
        }

    return profile


# ── Report Rendering ─────────────────────────────────────────────────────────

def _render_style_profile_md(profile: StyleProfile) -> str:
    """Render style profile as Markdown."""
    md = f"""# 目标期刊风格画像

> 期刊：**{profile.journal}**
> 分析模式：{profile.mode}（{profile.num_exemplars} 篇范文）
> 生成时间：{_now()}

## 1. 格式化规范

| 维度 | 分析结果 |
|------|---------|
| **摘要字数** | {_fmt_range(profile.abstract_word_count, 'words')} |
| **章节标题风格** | {profile.section_heading_style} |
| **章节数** | {_fmt_range(profile.typical_section_count, '节')} |
| **每段句数** | {_fmt_range(profile.paragraph_length, '句')} |

## 2. 结构约定

**典型章节顺序：**
"""
    for i, section in enumerate(profile.section_order, 1):
        md += f"{i}. {section}\n"

    md += f"""
**子节密度：** 平均每篇 {profile.typical_subsections.get('per_paper_avg', 'N/A')} 个子节

## 3. 引用模式

| 维度 | 分析结果 |
|------|---------|
| **参考文献数量** | {_fmt_range(profile.total_references_range, '条')} |
| **引用风格** | {profile.reference_format or '编号引用 [N]（从范文推断）'} |

## 4. 语言风格

| 维度 | 分析结果 |
|------|---------|
| **平均句长** | {profile.avg_sentence_length:.1f} words/句 |
| **被动语态比例** | {profile.passive_voice_ratio:.0%} |
| **模糊限定频率** | ~{profile.hedging_frequency.get('per_1000_words', 'N/A')} 次/1000 词 |

**常用过渡短语：**
"""
    for phrase in profile.transition_phrases[:10]:
        md += f"- {phrase}\n"

    md += f"""
## 5. 写作建议

基于以上分析，投 {profile.journal} 时建议：

1. **摘要**控制在 {profile.abstract_word_count.get('avg', 'N/A')} 词左右，不超过 {profile.abstract_word_count.get('max', 'N/A')} 词
2. **章节结构**按以下顺序组织：{' → '.join(profile.section_order[:6])}{'...' if len(profile.section_order) > 6 else ''}
3. **句长**保持在 {profile.avg_sentence_length:.0f} 词左右，自然波动
4. **被动语态**占比约 {profile.passive_voice_ratio:.0%}——{'多用主动态' if profile.passive_voice_ratio < 0.25 else '适度使用被动态' if profile.passive_voice_ratio < 0.45 else '被动态较常见'}
5. **参考文献**控制在 {profile.total_references_range.get('min', 'N/A')}-{profile.total_references_range.get('max', 'N/A')} 条范围
6. **段落长度**平均 {profile.paragraph_length.get('avg_sentences', 'N/A')} 句，注意自然变化
"""
    return md


def _render_research_dossier(
    profile: StyleProfile,
    analyses: list[ExemplarAnalysis],
) -> str:
    """Render the complete research dossier."""
    md = f"""# 目标期刊研究档案

> 目标期刊：**{profile.journal}**
> 分析时间：{_now()}

## 范文清单

| # | 标题 | 年份 | 引用数 | 句长 |
|---|------|:---:|:-----:|:---:|
"""
    for i, a in enumerate(analyses, 1):
        md += f"| {i} | {a.title[:60]}{'...' if len(a.title) > 60 else ''} | {a.year or '?'} | {a.reference_count} | {a.avg_sentence_length:.1f} |\n"

    md += "\n---\n\n"
    md += profile.to_markdown()
    return md


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_abstract_section(text: str) -> str:
    """Extract abstract text from a paper."""
    patterns = [
        r'(?:^|\n)Abstract\s*\n(.*?)(?:\n\d+\.\s+\w+|\nIntroduction|\n\Z)',
        r'(?:^|\n)ABSTRACT\s*\n(.*?)(?:\n\d+\.\s+\w+|\nINTRODUCTION|\n\Z)',
        r'(?:^|\n)摘要\s*\n(.*?)(?:\n\d+\.\s+\w+|\n引言|\n\Z)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _extract_reference_section(text: str) -> str:
    """Extract references section."""
    patterns = [
        r'(?:^|\n)(?:References?|Bibliography|参考文献)\s*\n(.*?)(?:\n\Z)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()[:5000]  # Cap at 5000 chars
    return ""


def _split_sentences(text: str) -> list[str]:
    """Basic sentence splitter."""
    # Remove reference numbers and equation fragments
    text = re.sub(r'\[\d+(?:[,，\-\s]+\d+)*\]', '', text)
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if len(s.strip().split()) > 3]


def _normalize_section_name(name: str) -> str:
    """Normalize a section heading to a standard name."""
    name = re.sub(r'^\d+\.?\s*', '', name).strip().lower()
    mapping = {
        'introduction': 'Introduction',
        'intro': 'Introduction',
        'related work': 'Related Work',
        'background': 'Related Work',
        'literature review': 'Related Work',
        'method': 'Method',
        'methodology': 'Method',
        'methods': 'Method',
        'approach': 'Method',
        'experiment': 'Experiments',
        'experiments': 'Experiments',
        'results': 'Experiments',
        'experimental results': 'Experiments',
        'discussion': 'Discussion',
        'conclusion': 'Conclusion',
        'conclusions': 'Conclusion',
        'summary': 'Conclusion',
        'abstract': 'Abstract',
        'references': 'References',
        'bibliography': 'References',
    }
    for key, value in mapping.items():
        if key in name:
            return value
    return name.title()


def _most_common_order(all_orders: list[list[str]]) -> list[str]:
    """Find the most common section ordering across exemplars."""
    # Simple approach: count occurrences of each section, preserve typical order
    position_scores = {}
    for order in all_orders:
        for i, name in enumerate(order):
            if name not in position_scores:
                position_scores[name] = []
            position_scores[name].append(i)

    avg_positions = {
        name: sum(positions) / len(positions)
        for name, positions in position_scores.items()
    }
    return sorted(avg_positions, key=avg_positions.get)


def _find_transitions(analysis: ExemplarAnalysis) -> list[str]:
    """Extract common transition phrases. Returns empty list since this requires
    the full text which isn't stored in ExemplarAnalysis."""
    return []


def _fmt_range(d: dict, unit: str) -> str:
    """Format a min/max/avg dict."""
    if not d:
        return f"N/A {unit}"
    return f"{d.get('min', '?')}-{d.get('max', '?')} {unit}（平均 {d.get('avg', '?')}）"


def _now() -> str:
    """Current time string."""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Learn target journal style from exemplar papers",
    )
    parser.add_argument("--target-journal", required=True, help="Target journal name")
    parser.add_argument("--mode", choices=["flash", "pro"], default="flash",
                        help="flash=3 exemplars, pro=6 exemplars (default: flash)")
    parser.add_argument("--pdf-dir", help="Directory with exemplar PDF files")
    parser.add_argument("--text-dir", help="Directory with pre-extracted .txt files (from batch_read_pdfs.py)")
    parser.add_argument("--zotero-collection", help="Zotero collection name (requires Zotero MCP)")
    parser.add_argument("--output", "-o", default="research_dossier/",
                        help="Output directory (default: research_dossier/)")
    parser.add_argument("--exemplar-limit", type=int, default=0,
                        help="Max exemplars to analyze (overrides mode default)")

    args = parser.parse_args()

    # Determine exemplar limit
    if args.exemplar_limit > 0:
        limit = args.exemplar_limit
    else:
        limit = 3 if args.mode == "flash" else 6

    # Load exemplar texts
    texts = {}

    if args.text_dir and os.path.isdir(args.text_dir):
        txt_files = sorted([
            f for f in os.listdir(args.text_dir) if f.endswith('.txt')
        ])[:limit]
        for f in txt_files:
            path = os.path.join(args.text_dir, f)
            with open(path, 'r', encoding='utf-8') as fh:
                texts[f] = fh.read()
        print(f"📂 从文本目录加载 {len(texts)} 篇范文: {args.text_dir}")
    elif args.pdf_dir and os.path.isdir(args.pdf_dir):
        # Try to use PyMuPDF if available
        try:
            import fitz
            pdf_files = sorted([
                f for f in os.listdir(args.pdf_dir) if f.endswith('.pdf')
            ])[:limit]
            for f in pdf_files:
                path = os.path.join(args.pdf_dir, f)
                doc = fitz.open(path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                texts[f] = text
            print(f"📂 从 PDF 目录加载 {len(texts)} 篇范文: {args.pdf_dir}")
        except ImportError:
            print("❌ PyMuPDF (fitz) 未安装，无法直接读取 PDF。")
            print("   请先运行: pip install pymupdf")
            print("   或使用 --text-dir 指定已提取的文本目录")
            return
    elif args.zotero_collection:
        print("⚠️ Zotero 模式需要在 SKILL.md 对话中通过 Zotero MCP 工具调用。")
        print(f"   目标集合: {args.zotero_collection}")
        print("   请通过 /more-paper-workflow-pro-skill → Step 6f 触发")
        return
    else:
        print("❌ 请指定范文来源: --pdf-dir, --text-dir, 或 --zotero-collection")
        return

    if not texts:
        print("❌ 未找到范文")
        return

    # Analyze each exemplar
    print(f"🔍 分析 {len(texts)} 篇范文...")
    analyses = []
    for filename, text in texts.items():
        print(f"   {filename} ...", end=" ")
        analysis = analyze_pdf_text(text, filename)
        analyses.append(analysis)
        print(f"✅ ({analysis.total_words} 词, {analysis.total_sentences} 句, {analysis.reference_count} 条引用)")

    # Combine into style profile
    profile = combine_analyses(args.target_journal, args.mode, analyses)
    profile.target_name = args.target_journal
    profile.sample_count = len(analyses)

    # Write outputs
    os.makedirs(args.output, exist_ok=True)

    # Style profile
    style_path = os.path.join(args.output, "style_profile.md")
    with open(style_path, 'w', encoding='utf-8') as f:
        f.write(profile.to_markdown())
    print(f"✅ 风格画像: {style_path}")

    style_json_path = os.path.join(args.output, "style_profile.json")
    with open(style_json_path, 'w', encoding='utf-8') as f:
        json.dump(profile.to_schema_dict(), f, ensure_ascii=False, indent=2)
    print(f"✅ 风格画像JSON: {style_json_path}")

    # Research dossier (full analysis)
    dossier_path = os.path.join(args.output, "research_dossier.md")
    with open(dossier_path, 'w', encoding='utf-8') as f:
        f.write(_render_research_dossier(profile, analyses))
    print(f"✅ 研究档案: {dossier_path}")

    # Print summary
    print(f"\n── {args.target_journal} 风格摘要 ──")
    print(f"   摘要: {_fmt_range(profile.abstract_word_count, '词')}")
    print(f"   章节数: {_fmt_range(profile.typical_section_count, '节')}")
    print(f"   参考文献: {_fmt_range(profile.total_references_range, '条')}")
    print(f"   平均句长: {profile.avg_sentence_length:.1f} words")
    print(f"   被动语态: {profile.passive_voice_ratio:.0%}")


if __name__ == "__main__":
    main()
