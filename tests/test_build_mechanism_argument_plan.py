import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_mechanism_argument_plan.py"
AUDIT_SCRIPT = ROOT / "scripts" / "audit_mechanism_claims.py"
PARAGRAPH_AUDIT_SCRIPT = ROOT / "scripts" / "audit_mechanism_paragraphs.py"


def _write_cards(path: Path, *, reading_depth: str = "full_text", records=None):
    payload_records = records if records is not None else [
        {
            "record_id": "stable-001",
            "citekey": "liu2024mechanism",
            "title": "AA2196 continuous dynamic recrystallization mechanism",
            "section_id": "1.1",
            "section_title": "热变形机理",
            "reading_depth": reading_depth,
            "claim_summary": "热变形诱发动态再结晶。",
            "mechanism_hints": {
                "phenomenon": "热变形过程中晶粒细化",
                "state_variables": ["temperature", "strain rate", "dislocation density", "CDRX"],
                "causal_chain": ["温度和应变速率改变位错累积，从而影响动态再结晶。"],
                "governing_model": ["Zener-Hollomon parameter links temperature and strain rate."],
                "boundary_conditions": ["适用于给定温度和应变速率窗口。"],
                "validation_path": ["EBSD maps validate recrystallized fraction."],
                "evidence_anchor": [{"type": "pdf", "value": "paper.pdf", "page": ""}],
                "claim_limit": "可进入 mechanism_argument_plan。",
            },
            "figure_candidates": [],
            "source_trace": {
                "text_source": "zotero_fulltext" if reading_depth == "full_text" else "abstract_only",
                "source_pdf": "paper.pdf",
                "zotero_item_key": "ITEM123",
                "chunks_json": "",
            },
        }
    ]
    path.write_text(json.dumps({
        "schema_version": "deep-read-cards.v1",
        "metadata": {"entry_mode": "deep_read_refine", "section_id": "1.1"},
        "records": payload_records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


class BuildMechanismArgumentPlanTest(unittest.TestCase):
    def test_no_mineru_keeps_writing_allowed_but_forbids_visual_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cards = root / "deep_read_cards.json"
            _write_cards(cards)

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--cards-json",
                    str(cards),
                    "--output-dir",
                    str(root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            plan = json.loads((root / "mechanism_argument_plan.json").read_text(encoding="utf-8"))
            audit = json.loads((root / "mechanism_claim_audit.json").read_text(encoding="utf-8"))
            gap_md = (root / "evidence_gap_list.md").read_text(encoding="utf-8")

        claim = plan["claims"][0]
        self.assertEqual(claim["figure_evidence_status"], "unavailable_without_mineru_or_manual_pdf_check")
        self.assertEqual(claim["evidence_level"], "pdf_fulltext_no_page")
        self.assertIn("CDRX", claim["mechanism_type"])
        self.assertIn("DDRX", claim["discriminates_against"])
        self.assertIn("不得自动写", " ".join(claim["not_allowed_claims"]))
        self.assertEqual(audit["findings"][0]["severity"], "pass")
        self.assertIn("未发现必须降级", gap_md)

    def test_figure_index_upgrades_to_mineru_figure_anchor_and_binds_panels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cards = root / "deep_read_cards.json"
            figure_index = root / "figure_index.json"
            _write_cards(cards)
            figure_index.write_text(json.dumps({
                "schema_version": "figure-index.v1",
                "records": [
                    {
                        "item_key": "ITEM123",
                        "figure_id": "Figure 3",
                        "page": "7",
                        "caption": "Fig. 3. (a) EBSD maps of recrystallized grains; (b) boundary migration path.",
                        "source_type": "caption_plus_text",
                        "source_image_path": "LLM-for-Zotero-MinerU-cache-ABC.zip::images/fig3.jpg",
                    }
                ],
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--cards-json",
                    str(cards),
                    "--figure-index",
                    str(figure_index),
                    "--output-dir",
                    str(root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            plan = json.loads((root / "mechanism_argument_plan.json").read_text(encoding="utf-8"))
            cards_out = json.loads((root / "mechanism_cards.json").read_text(encoding="utf-8"))

        record = cards_out["records"][0]
        self.assertEqual(record["evidence_level"], "mineru_figure_anchor")
        self.assertEqual(record["figure_evidence_status"], "available_with_mineru_or_figure_index")
        self.assertIn("Figure 3", json.dumps(record["evidence_anchor"], ensure_ascii=False))
        self.assertEqual(record["evidence_anchor"][1]["panel_candidates"], ["a", "b"])
        self.assertEqual(plan["claims"][0]["figure_claim_binding"][0]["claim_binding"], plan["claims"][0]["claim_id"])

    def test_cross_material_transfer_risk_is_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cards = root / "deep_read_cards.json"
            _write_cards(cards, records=[
                {
                    "record_id": "stable-001",
                    "citekey": "liu2024mechanism",
                    "title": "AA2196 continuous dynamic recrystallization mechanism",
                    "section_id": "1.1",
                    "section_title": "热变形机理",
                    "reading_depth": "full_text",
                    "claim_summary": "AA2196 合金中的 CDRX 机理。",
                    "mechanism_hints": {
                        "phenomenon": "AA2196 合金晶粒细化",
                        "state_variables": ["CDRX", "dislocation density"],
                        "causal_chain": ["位错累积诱导亚晶旋转。"],
                        "boundary_conditions": ["铝合金热变形窗口。"],
                        "validation_path": ["EBSD validation."],
                        "evidence_anchor": [{"type": "pdf", "value": "aa.pdf"}],
                    },
                    "source_trace": {"source_pdf": "aa.pdf", "zotero_item_key": "ITEM123"},
                },
                {
                    "record_id": "stable-002",
                    "citekey": "chen2026ddrx",
                    "title": "Nickel-based superalloy discontinuous dynamic recrystallization framework",
                    "section_id": "1.1",
                    "section_title": "热变形机理",
                    "reading_depth": "full_text",
                    "claim_summary": "镍基高温合金 DDRX 建模。",
                    "mechanism_hints": {
                        "phenomenon": "nickel-based superalloy DDRX",
                        "state_variables": ["DDRX", "grain boundary migration"],
                        "causal_chain": ["局部形核触发软化反馈。"],
                        "boundary_conditions": ["镍基高温合金周期边界条件。"],
                        "validation_path": ["simulation validation."],
                        "evidence_anchor": [{"type": "pdf", "value": "ni.pdf"}],
                    },
                    "source_trace": {"source_pdf": "ni.pdf", "zotero_item_key": "ITEM456"},
                },
            ])

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--cards-json",
                    str(cards),
                    "--output-dir",
                    str(root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            mechanism_cards = json.loads((root / "mechanism_cards.json").read_text(encoding="utf-8"))

        risks = {record["citekey"]: record["transfer_risk"] for record in mechanism_cards["records"]}
        self.assertEqual(risks["liu2024mechanism"], "same_material")
        self.assertEqual(risks["chen2026ddrx"], "cross_material_requires_boundary")

    def test_abstract_only_is_downgraded_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cards = root / "deep_read_cards.json"
            _write_cards(
                cards,
                reading_depth="abstract_only",
                records=[
                    {
                        "record_id": "stable-001",
                        "citekey": "liu2024mechanism",
                        "title": "Mechanism Paper",
                        "section_id": "1.1",
                        "section_title": "热变形机理",
                        "reading_depth": "abstract_only",
                        "claim_summary": "热变形诱发动态再结晶。",
                        "mechanism_hints": {
                            "phenomenon": "热变形过程中晶粒细化",
                            "state_variables": ["temperature"],
                            "causal_chain": [],
                            "boundary_conditions": [],
                            "validation_path": [],
                            "evidence_anchor": [],
                            "claim_limit": "摘要级候选解释。",
                        },
                        "figure_candidates": [],
                        "source_trace": {
                            "text_source": "abstract_only",
                            "source_pdf": "paper.pdf",
                            "zotero_item_key": "ITEM123",
                            "chunks_json": "",
                        },
                    }
                ],
            )

            subprocess.run(
                [
                    sys.executable,
                    str(BUILD_SCRIPT),
                    "--cards-json",
                    str(cards),
                    "--output-dir",
                    str(root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            plan = json.loads((root / "mechanism_argument_plan.json").read_text(encoding="utf-8"))
            gap_md = (root / "evidence_gap_list.md").read_text(encoding="utf-8")

        claim = plan["claims"][0]
        self.assertEqual(claim["confirmation_status"], "downgraded_to_background_or_candidate")
        self.assertIn("full_text_evidence", gap_md)
        self.assertIn("不得写成已证明", " ".join(claim["not_allowed_claims"]))

    def test_standalone_audit_accepts_existing_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "mechanism_argument_plan.json"
            out_json = root / "audit.json"
            out_md = root / "audit.md"
            plan.write_text(json.dumps({
                "schema_version": "mechanism-argument-plan.v2",
                "claims": [
                    {
                        "claim_id": "mech-x",
                        "source_citekey": "x2024",
                        "mechanism_type": ["DDRX"],
                        "causal_chain": [],
                        "boundary_conditions": [],
                        "validation_path": [],
                        "evidence_anchor": [],
                        "evidence_level": "abstract_or_metadata",
                        "transfer_risk": "cross_material_requires_boundary",
                    }
                ],
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_SCRIPT),
                    "--plan-json",
                    str(plan),
                    "--output-json",
                    str(out_json),
                    "--output-md",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            audit = json.loads(out_json.read_text(encoding="utf-8"))

        self.assertEqual(audit["findings"][0]["severity"], "downgrade_required")
        self.assertIn("causal_chain", audit["findings"][0]["missing"])
        self.assertIn("transfer_boundary", audit["findings"][0]["missing"])

    def test_paragraph_audit_flags_cross_material_without_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "draft.md"
            plan = root / "mechanism_argument_plan.json"
            out_json = root / "paragraph_audit.json"
            out_md = root / "paragraph_audit.md"
            draft.write_text(
                "# Draft\n\n"
                "Chen 等证明镍基高温合金的 DDRX 机制可以直接解释铝合金热变形过程。\n\n"
                "该机制如图所示可以导致局部应力松弛。\n",
                encoding="utf-8",
            )
            plan.write_text(json.dumps({
                "schema_version": "mechanism-argument-plan.v2",
                "claims": [
                    {
                        "claim_id": "mech-chen",
                        "source_citekey": "Chen2026",
                        "mechanism_type": ["DDRX"],
                        "discriminates_against": ["CDRX"],
                        "transfer_risk": "cross_material_requires_boundary",
                        "confirmation_status": "usable_with_cautious_wording",
                    }
                ],
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(PARAGRAPH_AUDIT_SCRIPT),
                    "--draft-md",
                    str(draft),
                    "--plan-json",
                    str(plan),
                    "--output-json",
                    str(out_json),
                    "--output-md",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            audit = json.loads(out_json.read_text(encoding="utf-8"))

        issues = [issue for finding in audit["findings"] for issue in finding["issues"]]
        self.assertIn("cross_material_claim_missing_boundary", issues)
        self.assertIn("visual_reference_without_figure_id", issues)


if __name__ == "__main__":
    unittest.main()
