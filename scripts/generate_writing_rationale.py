#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Writing rationale matrix generator — produces a unit-by-unit rationale document
that explains what each writing unit does, how it serves the confirmed motivation,
and what evidence supports it. This is the "central artifact" borrowed from
PaperSpine's writing_rationale_matrix.md.

Usage:
  python3 generate_writing_rationale.py section_blueprints.md \\
      style_profile.md --output research_dossier/writing_rationale_matrix.md
"""
import sys
import os
import re
import json
from dataclasses import dataclass, field


@dataclass
class UnitRationale:
    """Rationale for one writing unit (section or paragraph-level unit)."""
    unit_id: str                # e.g., "§3.2" or "§3.2-¶3"
    parent_section_id: str      # e.g., "3.2"
    unit_name: str              # Descriptive name
    what_it_does: str           # What this unit does in the paper
    motivation_link: str        # How it serves the confirmed motivation
    claim_binding: list[str]    # Which claims it serves
    evidence_used: list[str]    # What evidence supports this unit
    sota_reference: str         # How this was informed by SOTA/target-journal examples
    quality_check: str          # What to check before considering this unit done
    risk_notes: list[str] = field(default_factory=list)

    def to_schema_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "unit_id": self.unit_id,
            "parent_section_id": self.parent_section_id,
            "unit_name": self.unit_name,
            "what_it_does": self.what_it_does,
            "motivation_link": self.motivation_link,
            "claim_binding": self.claim_binding,
            "evidence_used": self.evidence_used,
            "quality_check": self.quality_check,
            "risk_notes": self.risk_notes,
        }


# ── Rationale Generation ─────────────────────────────────────────────────────

def generate_rationale_matrix(
    blueprints_path: str,
    style_profile_path: str = "",
) -> list[UnitRationale]:
    """Generate unit-by-unit writing rationale from blueprints."""

    # Parse blueprints
    sections = _parse_blueprint_sections(blueprints_path)

    # Load style notes if available
    style_notes = ""
    if style_profile_path and os.path.exists(style_profile_path):
        with open(style_profile_path, 'r', encoding='utf-8') as f:
            style_notes = f.read()

    units = []
    for section in sections:
        # Generate 2-4 units per section
        section_units = _generate_section_units(section, style_notes)
        units.extend(section_units)

    return units


def render_rationale_md(units: list[UnitRationale]) -> str:
    """Render rationale matrix as Markdown."""
    current_section = ""
    md = f"""# 写作逻辑矩阵

> 逐单元解释：每个写作单元做什么、如何服务于核心论点、用到了哪些证据。
> 每一段正文在写之前，先对照本矩阵确认"我为什么写这一段"——没有理由的段落应删除。

## 矩阵速查

| 单元 | 做什么 | 服务论点？ | 证据 |
|------|--------|:---:|------|
"""
    for u in units:
        evidence_brief = "; ".join(u.evidence_used[:2]) if u.evidence_used else "—"
        if len(u.evidence_used) > 2:
            evidence_brief += f" ...（共{len(u.evidence_used)}条）"
        md += f"| {u.unit_id} | {u.what_it_does[:40]}... | {u.motivation_link[:40]}... | {evidence_brief[:40]} |\n"

    md += "\n---\n\n## 逐单元详述\n\n"

    for u in units:
        # Section header
        section_id = u.unit_id.split('-')[0]
        if section_id != current_section:
            current_section = section_id
            md += f"### {current_section}\n\n"

        md += f"""#### {u.unit_id}: {u.unit_name}

**做什么：** {u.what_it_does}

**服务于核心论点：** {u.motivation_link}

**证据支撑：**
"""
        for ev in u.evidence_used:
            md += f"- {ev}\n"

        if u.sota_reference:
            md += f"\n**SOTA/目标期刊参考：** {u.sota_reference}\n"

        md += f"\n**质量检查：** {u.quality_check}\n\n---\n\n"

    return md


# ── Parsers ──────────────────────────────────────────────────────────────────

def _parse_blueprint_sections(path: str) -> list[dict]:
    """Parse sections from section_blueprints.md."""
    sections = []
    if path.endswith(".json"):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            sections.append({
                "number": item.get("section_id", ""),
                "name": item.get("section_title", ""),
                "section_function": item.get("section_function", ""),
                "claims": item.get("key_claims", []),
                "risks": item.get("risk_flags", []),
            })
        return sections
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match blueprint section headers: "### 1 Introduction"
    pattern = re.compile(
        r'###\s*(\d+(?:\.\d+)?)\s+(.+?)\n\n\*\*用途：\*\*\s*(.+?)\n',
    )
    for match in pattern.finditer(content):
        sections.append({
            "number": match.group(1),
            "name": match.group(2).strip(),
            "section_function": match.group(3).strip(),
            "claims": [],
            "risks": [],
        })

    return sections


def _generate_section_units(
    section: dict,
    style_notes: str,
) -> list[UnitRationale]:
    """Generate writing units for one section."""

    name = section["name"].lower()
    num = section["number"]
    section_function = section.get("section_function", "")
    units = []

    # Each section typically has 2-4 natural writing units
    if any(w in name for w in ['intro', '引言', '绪论']):
        units = [
            UnitRationale(
                unit_id=f"§{num}-¶1", unit_name="背景段落",
                parent_section_id=num,
                what_it_does="建立宏观背景，说明研究领域的重要性和当前面临的核心挑战",
                motivation_link="回答'为什么读者需要关心这个问题'——设置论文的 stakes",
                claim_binding=section.get("claims", []),
                evidence_used=["行业报告/权威数据（如有）", "高引经典论文（综述类）"],
                sota_reference="范文绪论第一段的背景铺陈方式",
                quality_check="读完这段后，非同领域的读者能理解为什么这个问题值得研究吗？",
                risk_notes=section.get("risks", []),
            ),
            UnitRationale(
                unit_id=f"§{num}-¶2", unit_name="Gap 识别段落",
                parent_section_id=num,
                what_it_does="综述已有工作的不足，明确指出研究空白（gap）",
                motivation_link="回答'已有方法为什么不够'——为本文贡献建立必要性",
                claim_binding=section.get("claims", []),
                evidence_used=["已有方法的关键局限（来自综述矩阵）"],
                sota_reference="范文如何批评已有工作但不贬低",
                quality_check="gap 是否具体到可验证的程度？不是'fill a gap'空话",
                risk_notes=section.get("risks", []),
            ),
            UnitRationale(
                unit_id=f"§{num}-¶3", unit_name="贡献声明段落",
                parent_section_id=num,
                what_it_does="列出本文 3-5 条具体贡献，每条标注对应章节",
                motivation_link="核心——回答'本文做了什么、与已有方法有何不同'",
                claim_binding=section.get("claims", []),
                evidence_used=["逐条贡献对应后文章节的证据"],
                sota_reference="范文贡献列表的格式和密度",
                quality_check="每一条贡献是否都有对应章节可以验证？贡献之间是否独立？",
                risk_notes=section.get("risks", []),
            ),
        ]
    elif any(w in name for w in ['method', '方法', '方案']):
        units = [
            UnitRationale(
                unit_id=f"§{num}-¶1", unit_name="方法总览段落",
                parent_section_id=num,
                what_it_does="给出方法的顶层框架/系统架构，定义核心概念和符号",
                motivation_link="读者需要先建立心智模型再理解细节",
                claim_binding=section.get("claims", []),
                evidence_used=["系统/方法框架图"],
                sota_reference="范文方法章节开头如何做高层次概述",
                quality_check="画个架构图——新手看完能理解方法的主要组件吗？",
                risk_notes=section.get("risks", []),
            ),
            UnitRationale(
                unit_id=f"§{num}-¶2", unit_name="方法细节展开",
                parent_section_id=num,
                what_it_does="按逻辑顺序展开各组件，先符号后公式，公式旁有直觉解释",
                motivation_link="核心创新体现在方法的设计细节中",
                claim_binding=section.get("claims", []),
                evidence_used=["公式推导的数学基础", "设计选择的动机/理由"],
                sota_reference="范文如何处理公式密度和直觉解释的平衡",
                quality_check="每个公式是否能被同领域研究者复现？参数来源是否标注？",
                risk_notes=section.get("risks", []),
            ),
        ]
    elif any(w in name for w in ['experiment', '实验', '结果']):
        units = [
            UnitRationale(
                unit_id=f"§{num}-¶1", unit_name="实验设置段落",
                parent_section_id=num,
                what_it_does="明确实验回答的研究问题、实验条件、对比基线",
                motivation_link="证明实验设计的合理性——回答读者'我凭什么信你的结果'",
                claim_binding=section.get("claims", []),
                evidence_used=["实验设备/数据集描述", "基线方法来源"],
                sota_reference="范文如何处理实验设置表格和条件描述",
                quality_check="读者能仅凭此段复现你的实验设置吗？",
                risk_notes=section.get("risks", []),
            ),
            UnitRationale(
                unit_id=f"§{num}-¶2", unit_name="核心结果展示",
                parent_section_id=num,
                what_it_does="展示核心对比结果，数据→分析→解释三层递进",
                motivation_link="用数据证明方法有效——这是论文的'胜负手'",
                claim_binding=section.get("claims", []),
                evidence_used=["实验结果数据（表格/图表）"],
                sota_reference="范文的结果段落如何做到图表自包含",
                quality_check="每个图表不看正文能看懂吗？caption写全了吗？",
                risk_notes=section.get("risks", []),
            ),
            UnitRationale(
                unit_id=f"§{num}-¶3", unit_name="消融与分析",
                parent_section_id=num,
                what_it_does="消融实验/深入分析验证各组件的贡献",
                motivation_link="回答'为什么方法有效'而不仅是'方法有效吗'",
                claim_binding=section.get("claims", []),
                evidence_used=["消融实验数据", "参数敏感性分析"],
                sota_reference="范文如何处理消融实验和深入分析",
                quality_check="消融实验是否覆盖了每个声称的创新组件？",
                risk_notes=section.get("risks", []),
            ),
        ]
    elif any(w in name for w in ['conclusion', '结论']):
        units = [
            UnitRationale(
                unit_id=f"§{num}-¶1", unit_name="贡献总结段落",
                parent_section_id=num,
                what_it_does="与引言贡献条目一一对应，总结而非重述全文",
                motivation_link="给读者留下最终印象——本文到底贡献了什么",
                claim_binding=section.get("claims", []),
                evidence_used=["各章节核心发现的浓缩"],
                sota_reference="范文结论如何避免成为摘要的复读",
                quality_check="结论中出现的贡献是否都在引言中声明过？",
                risk_notes=section.get("risks", []),
            ),
            UnitRationale(
                unit_id=f"§{num}-¶2", unit_name="局限与未来方向",
                parent_section_id=num,
                what_it_does="诚实列出 2-3 条局限性，提出具体未来方向",
                motivation_link="建立可信度——承认局限比假装完美更令人信服",
                claim_binding=section.get("claims", []),
                evidence_used=["未解决的问题清单（来自 Step 7f 评审）"],
                sota_reference="范文局限部分的坦诚度和具体程度",
                quality_check="未来方向是否具体（有方法名/有场景）而非空话？",
                risk_notes=section.get("risks", []),
            ),
        ]
    else:
        # Generic section
        units = [
            UnitRationale(
                unit_id=f"§{num}-¶1", unit_name=f"{name} 段落",
                parent_section_id=num,
                what_it_does=f"展开论述 {section['name']} 的核心内容",
                motivation_link="支持论文的整体论证链",
                claim_binding=section.get("claims", []),
                evidence_used=["相关文献（来自综述矩阵）"],
                sota_reference="目標期刊范文对应章节的结构和密度",
                quality_check="该节内容是否与前后章节形成逻辑递进？",
                risk_notes=section.get("risks", []),
            ),
        ]

    return units


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate unit-by-unit writing rationale matrix",
    )
    parser.add_argument("blueprints", help="Path to section_blueprints.md")
    parser.add_argument("--style-profile", help="Path to style_profile.md")
    parser.add_argument("--output", "-o", default="research_dossier/writing_rationale_matrix.md",
                        help="Output path")
    parser.add_argument("--journal", help="Target journal name")

    args = parser.parse_args()

    print(f"📝 生成写作逻辑矩阵...")
    units = generate_rationale_matrix(args.blueprints, args.style_profile or "")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    md = render_rationale_md(units)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"✅ 写作逻辑矩阵: {args.output}")

    json_output = os.path.splitext(args.output)[0] + ".json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump([u.to_schema_dict() for u in units], f, ensure_ascii=False, indent=2)
    print(f"✅ 写作逻辑矩阵JSON: {json_output}")
    print(f"   共 {len(units)} 个写作单元")


if __name__ == "__main__":
    main()
