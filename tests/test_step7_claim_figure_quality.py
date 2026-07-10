import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from citation_audit import AuditResult, CitationRef, build_claim_evidence_payload  # noqa: E402
from resolve_figure_refs import resolve_figure_refs  # noqa: E402


class Step7ClaimFigureQualityTest(unittest.TestCase):
    def test_abstract_screening_cannot_close_numeric_claim(self):
        citation = CitationRef(1, "[1]", "效率提高12%[1]。", "效率提高12%[1]。", 1, doi="10.1000/demo")
        result = AuditResult(citation, "✅ 支撑", "The abstract reports an experiment with 12% improvement.", "related")
        payload = build_claim_evidence_payload("效率提高12%[1]。", [result], [])
        record = payload["records"][0]
        self.assertEqual(record["required_evidence"], "page_or_table")
        self.assertEqual(record["support_grade"], "partial")
        self.assertTrue(record["downgrade_required"])
        self.assertEqual(payload["summary"]["unresolved_count"], 1)

    def test_zero_keyword_figure_match_is_not_inserted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "unrelated.png"
            image.write_bytes(b"image")
            draft = root / "draft.md"
            output = root / "resolved.md"
            cards = root / "cards.json"
            draft.write_text("结果如下。\n\n[图: 电池温度分布]", encoding="utf-8")
            cards.write_text(json.dumps({"records": [{
                "citekey": "author2024", "reading_depth": "full_text", "source_trace": {"image_source": "MinerU"},
                "figure_candidates": [{"figure_id": "Fig. 9", "caption": "Network architecture", "local_image_path": str(image)}],
            }]}), encoding="utf-8")
            resolve_figure_refs(draft_path=draft, cards_paths=[str(cards)], output_path=output)
            text = output.read_text(encoding="utf-8")
            report = json.loads((root / "figure_resolution_report.json").read_text(encoding="utf-8"))
        self.assertNotIn("![图", text)
        self.assertIn("manual_confirmation_required", text)
        self.assertEqual(report["unresolved_count"], 1)


if __name__ == "__main__":
    unittest.main()
