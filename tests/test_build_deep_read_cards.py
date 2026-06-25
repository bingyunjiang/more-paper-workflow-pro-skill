import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_deep_read_cards.py"


class BuildDeepReadCardsTest(unittest.TestCase):
    def test_cli_prefers_mineru_over_fulltext_and_preserves_existing_reading_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = root / "文献-Zotero架构对照.json"
            out_json = root / "deep_read_cards.json"
            out_md = root / "deep_read_cards.md"
            fulltext = root / "fulltext.json"
            mineru_zip = root / "LLM-for-Zotero-MinerU-cache-ABC123.zip"

            mapping.write_text(json.dumps({
                "records": [
                    {
                        "record_id": "stable-001",
                        "citekey": "wang2024example",
                        "title": "Example Paper",
                        "chapter_id": "2.1",
                        "pdf_path": str(root / "example.pdf"),
                        "zotero_item_key": "ITEM123",
                        "abstract": "Abstract only text should not win when MinerU exists.",
                        "paper_card": {
                            "evidence_role": "method",
                            "primary_claim": "提出一个热管理控制方法",
                            "main_methods_or_baselines": ["simulation-assisted framework"],
                            "reading_depth": "abstract_only",
                            "content_fit": "direct",
                            "usable_for": ["方法综述"],
                            "not_usable_for": ["强结论"],
                        },
                    }
                ]
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            fulltext.write_text(json.dumps({
                "records": [
                    {"citekey": "wang2024example", "text": "Fulltext fallback should lose to MinerU."}
                ]
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            with zipfile.ZipFile(mineru_zip, "w") as zf:
                zf.writestr("_llm_source.json", json.dumps({
                    "parentItemKey": "ITEM123",
                    "attachmentKey": "ABC123",
                    "sourceFilename": "example.pdf",
                }))
                zf.writestr("full.md", "# Example\n\nThe method uses MinerU text as the preferred source. Experiments improve efficiency by 12 percent.")
                zf.writestr("manifest.json", json.dumps({
                    "sections": [
                        {
                            "heading": "Results",
                            "figures": [
                                {"label": "Figure 1", "path": "images/fig-1.jpg", "caption": "Demo figure", "page": 1}
                            ],
                        }
                    ]
                }))
                zf.writestr("images/fig-1.jpg", b"fake-image")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mapping-json",
                    str(mapping),
                    "--section-id",
                    "2.1",
                    "--section-title",
                    "热管理方法",
                    "--fulltext-json",
                    str(fulltext),
                    "--mineru-zip",
                    str(mineru_zip),
                    "--output-json",
                    str(out_json),
                    "--output-md",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            data = json.loads(out_json.read_text(encoding="utf-8"))

        self.assertIn("SELECTED_RECORDS: 1", result.stdout)
        self.assertEqual(data["schema_version"], "deep-read-cards.v1")
        self.assertEqual(data["records"][0]["source_trace"]["text_source"], "zotero_mineru")
        self.assertEqual(data["records"][0]["source_trace"]["image_source"], "MinerU ZIP / Zotero 图文资产")
        self.assertEqual(data["records"][0]["figure_candidates"][0]["figure_id"], "Figure 1")
        self.assertIn("images/fig-1.jpg", data["records"][0]["figure_candidates"][0]["source_image_path"])
        self.assertEqual(data["records"][0]["reading_depth"], "abstract_only")
        self.assertIn("提出一个热管理控制方法", data["records"][0]["claim_summary"])

    def test_cli_falls_back_to_prepared_chunks_and_preview_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = root / "文献-Zotero架构对照.json"
            prepared = root / "prepared_pdf_artifacts.json"
            chunks = root / "example.chunks.json"
            figure_index = root / "figure_index.json"
            out_json = root / "deep_read_cards.json"
            out_md = root / "deep_read_cards.md"

            mapping.write_text(json.dumps({
                "records": [
                    {
                        "record_id": "stable-002",
                        "citekey": "liu2025demo",
                        "title": "Prepared Example",
                        "chapter_id": "3.2",
                        "pdf_path": str(root / "prepared.pdf"),
                        "abstract": "",
                        "paper_card": {
                            "evidence_role": "experiment",
                            "content_fit": "adjacent",
                            "usable_for": ["实验综述"],
                            "not_usable_for": ["机制强结论"],
                        },
                    }
                ]
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            chunks.write_text(json.dumps([
                {
                    "chunk_id": "prepared_001",
                    "text": "Method section describes a simulation workflow. Results show cooling efficiency improves by 8 percent."
                }
            ], ensure_ascii=False, indent=2), encoding="utf-8")

            prepared.write_text(json.dumps({
                "artifacts": [
                    {
                        "citekey": "liu2025demo",
                        "source_pdf": str(root / "prepared.pdf"),
                        "chunks_json": str(chunks),
                        "evidence_level": "pdf_fulltext_supported",
                        "risk_flags": ["table_damage_risk"],
                    }
                ]
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            figure_index.write_text(json.dumps({
                "records": [
                    {
                        "figure_id": "page-001-preview",
                        "page": "1",
                        "caption": "Preview only",
                        "source_image_path": "figures/page-001-preview.png",
                        "local_image_path": "",
                        "source_item_key": "",
                    }
                ]
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mapping-json",
                    str(mapping),
                    "--section-id",
                    "3.2",
                    "--section-title",
                    "结果验证",
                    "--prepared-pdf-artifacts",
                    str(prepared),
                    "--figure-index",
                    str(figure_index),
                    "--output-json",
                    str(out_json),
                    "--output-md",
                    str(out_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            data = json.loads(out_json.read_text(encoding="utf-8"))
            markdown = out_md.read_text(encoding="utf-8")

        self.assertEqual(data["records"][0]["source_trace"]["text_source"], "PyMuPDF/pdfplumber")
        self.assertEqual(data["records"][0]["source_trace"]["image_source"], "preview fallback")
        self.assertEqual(data["records"][0]["reading_depth"], "full_text")
        self.assertIn("table_damage_risk", data["records"][0]["risk_flags"])
        self.assertIn("Method section describes a simulation workflow", markdown)


if __name__ == "__main__":
    unittest.main()
