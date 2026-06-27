import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_step7_output.py"


class ValidateStep7OutputTest(unittest.TestCase):
    def run_validator(self, output_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(output_dir)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_fails_when_draft_skips_step7_artifact_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "journal_paper_draft.md").write_text(
                "# 受力与变形特征\n\n这里直接写正文，但没有工件链。\n",
                encoding="utf-8",
            )
            result = self.run_validator(out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_execution_card", result.stdout)
        self.assertIn("missing_citation_audit", result.stdout)
        self.assertIn("missing_figure_gate", result.stdout)
        self.assertIn("missing_mechanism_decision", result.stdout)

    def test_passes_when_required_step7_artifacts_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "journal_paper_draft.md").write_text(
                "# 受力与变形特征\n\n正文采用编号引文[1]（已读全文）。\n",
                encoding="utf-8",
            )
            (out / "step7_execution_card.md").write_text(
                "\n".join([
                    "# Step 7 Execution Card",
                    "- mechanism_trigger_decision: enter_mechanism_analysis",
                    "- figure_mode: skip",
                ]),
                encoding="utf-8",
            )
            (out / "evidence_matrix.md").write_text("# Evidence\n", encoding="utf-8")
            (out / "citation_audit.md").write_text("# Citation Audit\n", encoding="utf-8")
            (out / "figure_asset_check.md").write_text("# Figure Asset Check\n", encoding="utf-8")
            (out / "mechanism_cards.md").write_text("# Mechanism Cards\n", encoding="utf-8")
            (out / "mechanism_argument_plan.md").write_text("# Mechanism Argument Plan\n", encoding="utf-8")
            (out / "mechanism_claim_audit.md").write_text("# Mechanism Claim Audit\n", encoding="utf-8")
            result = self.run_validator(out)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("STEP7_VALIDATION: pass", result.stdout)

    def test_fails_on_raw_zotero_key_citations(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.write_minimum_artifacts(out)
            (out / "journal_paper_draft.md").write_text(
                "# 受力与变形特征\n\n壁厚减薄受相对弯曲半径影响 `99QWSQ5K`（已读全文）。\n",
                encoding="utf-8",
            )
            result = self.run_validator(out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw_zotero_key_citations", result.stdout)
        self.assertIn("missing_submission_style_citations", result.stdout)

    def test_fails_when_mineru_assets_exist_without_figure_index_or_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.write_minimum_artifacts(out, figure_mode="post_write")
            (out / "figure_asset_check.md").write_text(
                "# Figure Asset Check\n\n- figure_mode: post_write\n- mineru_zip: available\n",
                encoding="utf-8",
            )
            (out / "journal_paper_draft.md").write_text(
                "# 受力与变形特征\n\n正文采用编号引文[1]（已读全文），但没有图位。\n",
                encoding="utf-8",
            )
            result = self.run_validator(out)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_figure_index", result.stdout)
        self.assertIn("missing_figure_marker", result.stdout)

    def test_passes_with_mineru_assets_figure_index_and_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.write_minimum_artifacts(out, figure_mode="post_write")
            (out / "figure_asset_check.md").write_text(
                "# Figure Asset Check\n\n- figure_mode: post_write\n- mineru_zip: available\n",
                encoding="utf-8",
            )
            (out / "figure_index.json").write_text('{"records": []}\n', encoding="utf-8")
            (out / "journal_paper_draft.md").write_text(
                "# 受力与变形特征\n\n正文采用编号引文[1]（已读全文）。\n\n[[FIGURE:wall_thinning|source=99QWSQ5K|status=post_write]]\n",
                encoding="utf-8",
            )
            result = self.run_validator(out)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def write_minimum_artifacts(self, out: Path, figure_mode: str = "skip") -> None:
        (out / "step7_execution_card.md").write_text(
            "\n".join([
                "# Step 7 Execution Card",
                "- mechanism_trigger_decision: enter_mechanism_analysis",
                f"- figure_mode: {figure_mode}",
            ]),
            encoding="utf-8",
        )
        (out / "evidence_matrix.md").write_text("# Evidence\n", encoding="utf-8")
        (out / "citation_audit.md").write_text("# Citation Audit\n", encoding="utf-8")
        (out / "figure_asset_check.md").write_text(f"# Figure Asset Check\n\n- figure_mode: {figure_mode}\n", encoding="utf-8")
        (out / "mechanism_cards.md").write_text("# Mechanism Cards\n", encoding="utf-8")
        (out / "mechanism_argument_plan.md").write_text("# Mechanism Argument Plan\n", encoding="utf-8")
        (out / "mechanism_claim_audit.md").write_text("# Mechanism Claim Audit\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
