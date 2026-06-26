import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_mechanism_argument_plan.py"
AUDIT_SCRIPT = ROOT / "scripts" / "audit_mechanism_claims.py"


def _write_cards(path: Path, *, reading_depth: str = "full_text", figure_candidates=None, hints=None):
    path.write_text(json.dumps({
        "schema_version": "deep-read-cards.v1",
        "metadata": {"entry_mode": "deep_read_refine", "section_id": "1.1"},
        "records": [
            {
                "record_id": "stable-001",
                "citekey": "liu2024mechanism",
                "title": "Mechanism Paper",
                "section_id": "1.1",
                "section_title": "热变形机理",
                "reading_depth": reading_depth,
                "claim_summary": "热变形诱发动态再结晶。",
                "mechanism_hints": hints if hints is not None else {
                    "phenomenon": "热变形过程中晶粒细化",
                    "state_variables": ["temperature", "strain rate", "dislocation density"],
                    "causal_chain": ["温度和应变速率改变位错累积，从而影响动态再结晶。"],
                    "governing_model": ["Zener-Hollomon parameter links temperature and strain rate."],
                    "boundary_conditions": ["适用于给定温度和应变速率窗口。"],
                    "validation_path": ["EBSD maps validate recrystallized fraction."],
                    "evidence_anchor": [{"type": "pdf", "value": "paper.pdf", "page": ""}],
                    "claim_limit": "可进入 mechanism_argument_plan。",
                },
                "figure_candidates": figure_candidates or [],
                "source_trace": {
                    "text_source": "zotero_fulltext" if reading_depth == "full_text" else "abstract_only",
                    "source_pdf": "paper.pdf",
                    "zotero_item_key": "ITEM123",
                    "chunks_json": "",
                },
            }
        ],
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
        self.assertIn("不得自动写", " ".join(claim["not_allowed_claims"]))
        self.assertEqual(audit["findings"][0]["severity"], "pass")
        self.assertIn("未发现必须降级", gap_md)

    def test_figure_index_upgrades_to_mineru_figure_anchor(self):
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
                        "caption": "EBSD maps of recrystallized grains.",
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

            cards_out = json.loads((root / "mechanism_cards.json").read_text(encoding="utf-8"))

        record = cards_out["records"][0]
        self.assertEqual(record["evidence_level"], "mineru_figure_anchor")
        self.assertEqual(record["figure_evidence_status"], "available_with_mineru_or_figure_index")
        self.assertIn("Figure 3", json.dumps(record["evidence_anchor"], ensure_ascii=False))

    def test_abstract_only_is_downgraded_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cards = root / "deep_read_cards.json"
            _write_cards(
                cards,
                reading_depth="abstract_only",
                hints={
                    "phenomenon": "热变形过程中晶粒细化",
                    "state_variables": ["temperature"],
                    "causal_chain": [],
                    "boundary_conditions": [],
                    "validation_path": [],
                    "evidence_anchor": [],
                    "claim_limit": "摘要级候选解释。",
                },
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
                "schema_version": "mechanism-argument-plan.v1",
                "claims": [
                    {
                        "claim_id": "mech-x",
                        "source_citekey": "x2024",
                        "causal_chain": [],
                        "boundary_conditions": [],
                        "validation_path": [],
                        "evidence_anchor": [],
                        "evidence_level": "abstract_or_metadata",
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


if __name__ == "__main__":
    unittest.main()
