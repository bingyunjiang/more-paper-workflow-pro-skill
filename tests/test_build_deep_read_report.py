import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_deep_read_report.py"


class BuildDeepReadReportTest(unittest.TestCase):
    def test_cli_builds_report_with_mineru_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = root / "mapping.json"
            cards = root / "deep_read_cards.json"
            figure_index = root / "figure_index.json"
            mineru_zip = root / "mineru.zip"
            figures_dir = root / "figures"
            report_md = root / "deep_read_report.md"

            mapping.write_text(json.dumps({
                "records": [{
                    "title": "Example Paper",
                    "authors": ["Alice", "Bob"],
                    "publication_title": "Journal of Testing",
                    "date": "2026-01-02",
                    "doi": "10.1234/example",
                    "pdf_path": str(root / "example.pdf"),
                }]
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            cards.write_text(json.dumps({
                "schema_version": "deep-read-cards.v1",
                "metadata": {"entry_mode": "deep_read_refine"},
                "records": [{
                    "title": "Example Paper",
                    "claim_summary": "The paper validates a coupled model.",
                    "method_summary": "A surrogate model is trained.",
                    "experiment_summary": "The model matches experiment results.",
                    "figure_candidates": [{
                        "figure_id": "Fig. 1",
                        "page": "1",
                        "caption": "Method overview",
                        "source_image_path": str(figures_dir / "fig-1.jpg"),
                        "local_image_path": str(figures_dir / "fig-1.jpg"),
                    }],
                }]
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            figure_index.write_text(json.dumps({
                "schema_version": "figure-index.v1",
                "records": [{
                    "figure_id": "Fig. 1",
                    "caption": "Method overview",
                    "local_image_path": str(figures_dir / "fig-1.jpg"),
                    "source_image_path": "images/fig-1.jpg",
                }]
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            figures_dir.mkdir()
            (figures_dir / "fig-1.jpg").write_bytes(b"fake-image")
            with zipfile.ZipFile(mineru_zip, "w") as zf:
                zf.writestr("full.md", "Abstract\n\nThe paper validates a coupled model.")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mapping-json",
                    str(mapping),
                    "--cards-json",
                    str(cards),
                    "--figure-index-json",
                    str(figure_index),
                    "--mineru-zip",
                    str(mineru_zip),
                    "--output-md",
                    str(report_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            markdown = report_md.read_text(encoding="utf-8")

        self.assertIn("论文精读报告：Example Paper", markdown)
        self.assertIn("Method overview", markdown)
        self.assertIn("## 7. 创新点逐条拆解", markdown)

    def test_cli_builds_pdf_only_report_without_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = root / "mapping.json"
            cards = root / "deep_read_cards.json"
            report_md = root / "deep_read_report.pdfonly.md"

            mapping.write_text(json.dumps({
                "records": [{
                    "title": "Example Paper",
                    "authors": ["Alice", "Bob"],
                    "publication_title": "Journal of Testing",
                    "date": "2026-01-02",
                    "doi": "10.1234/example",
                    "pdf_path": str(root / "example.pdf"),
                }]
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            cards.write_text(json.dumps({
                "schema_version": "deep-read-cards.v1",
                "metadata": {"entry_mode": "deep_read_refine"},
                "records": [{
                    "title": "Example Paper",
                    "claim_summary": "The paper validates a coupled model.",
                    "method_summary": "A surrogate model is trained.",
                    "experiment_summary": "The model matches experiment results.",
                    "figure_candidates": [],
                }]
            }, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mapping-json",
                    str(mapping),
                    "--cards-json",
                    str(cards),
                    "--output-md",
                    str(report_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            markdown = report_md.read_text(encoding="utf-8")

        self.assertIn("论文精读报告：Example Paper", markdown)
        self.assertIn("## 11. 完整性自检", markdown)
        self.assertNotIn("![](", markdown)


if __name__ == "__main__":
    unittest.main()
