import subprocess
import sys
import tempfile
import json
import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_step7_output.py"


class ValidateStep7OutputTest(unittest.TestCase):
    def run_validator(self, output_dir: Path, target_state: str | None = None) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(SCRIPT), str(output_dir)]
        if target_state:
            command.extend(["--target-state", target_state])
        return subprocess.run(
            command,
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
            result = self.run_validator(out, "evidence_closed")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_execution_card", result.stdout)
        self.assertIn("missing_citation_audit", result.stdout)
        self.assertIn("missing_figure_gate", result.stdout)
        self.assertIn("missing_mechanism_decision", result.stdout)

    def test_draft_ready_direct_entry_does_not_require_evidence_closure_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "journal_paper_draft.md").write_text(
                "# 方法草稿\n\n当前段落仍需补充正式引文。\n",
                encoding="utf-8",
            )
            (out / "step7_execution_card.md").write_text(
                "# Step 7 Execution Card\n\n- target_state: draft_ready\n- figure_mode: skip\n- risk_status: citations_pending\n",
                encoding="utf-8",
            )
            result = self.run_validator(out, "draft_ready")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("completion_state: draft_ready", result.stdout)
        self.assertIn("draft_without_submission_style_citations", result.stdout)
        self.assertNotIn("missing_reviewer_scorecard", result.stdout)
        self.assertNotIn("missing_evidence_mapping", result.stdout)
        self.assertNotIn("missing_citation_audit", result.stdout)

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
                    "- risk_status: citations_checked",
                ]),
                encoding="utf-8",
            )
            (out / "evidence_matrix.md").write_text("# Evidence\n", encoding="utf-8")
            (out / "citation_audit.md").write_text("# Citation Audit\n", encoding="utf-8")
            (out / "figure_asset_check.md").write_text("# Figure Asset Check\n", encoding="utf-8")
            (out / "mechanism_cards.md").write_text("# Mechanism Cards\n", encoding="utf-8")
            (out / "mechanism_argument_plan.md").write_text("# Mechanism Argument Plan\n", encoding="utf-8")
            (out / "mechanism_claim_audit.md").write_text("# Mechanism Claim Audit\n", encoding="utf-8")
            self.write_reviewer_scorecard(out)
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
        self.assertIn("draft_without_submission_style_citations", result.stdout)

    def test_fails_on_raw_zotero_key_after_first_5000_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.write_minimum_artifacts(out)
            long_body = "背景说明。" * 1200
            (out / "journal_paper_draft.md").write_text(
                f"# 长章节\n\n正文采用编号引文[1]（已读全文）。\n\n{long_body}\n\n"
                "后文误留原始条目键 `99QWSQ5K`（已读全文）。\n",
                encoding="utf-8",
            )
            result = self.run_validator(out, "evidence_closed")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw_zotero_key_citations", result.stdout)

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
                "- risk_status: citations_checked",
            ]),
            encoding="utf-8",
        )
        (out / "evidence_matrix.md").write_text("# Evidence\n", encoding="utf-8")
        (out / "citation_audit.md").write_text("# Citation Audit\n", encoding="utf-8")
        (out / "figure_asset_check.md").write_text(f"# Figure Asset Check\n\n- figure_mode: {figure_mode}\n", encoding="utf-8")
        (out / "mechanism_cards.md").write_text("# Mechanism Cards\n", encoding="utf-8")
        (out / "mechanism_argument_plan.md").write_text("# Mechanism Argument Plan\n", encoding="utf-8")
        (out / "mechanism_claim_audit.md").write_text("# Mechanism Claim Audit\n", encoding="utf-8")
        self.write_reviewer_scorecard(out)

    def write_reviewer_scorecard(self, out: Path, technical_soundness: int = 4) -> None:
        scores = {}
        for axis, score in {
            "originality": 3,
            "importance": 3,
            "technical_soundness": technical_soundness,
            "evidence_adequacy": 4,
            "readability_structure": 3,
        }.items():
            scores[axis] = {
                "score": score,
                "evidence_locations": ["full_document"],
                "reason": f"{axis} assessed against the anchored rubric",
            }
        (out / "reviewer_scorecard.json").write_text(
            json.dumps({
                "schema_version": "reviewer-scorecard.v1",
                "assessment_boundary": "full_document",
                "scores": scores,
                "critical_issues": [],
            }),
            encoding="utf-8",
        )

    def test_fails_when_reviewer_score_is_below_anchored_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.write_minimum_artifacts(out)
            self.write_reviewer_scorecard(out, technical_soundness=3)
            (out / "journal_paper_draft.md").write_text(
                "# 方法\n\n正文采用编号引文[1]（已读全文）。\n",
                encoding="utf-8",
            )
            result = self.run_validator(out, "evidence_closed")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewer_score_below_gate_technical_soundness", result.stdout)

    def test_evidence_closed_requires_current_hash_and_zero_unresolved_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.write_minimum_artifacts(out)
            draft = "# 方法\n\n正文采用编号引文[1]（已读全文）。\n"
            (out / "journal_paper_draft.md").write_text(draft, encoding="utf-8")
            digest = hashlib.sha256(draft.encode("utf-8")).hexdigest()
            scorecard_path = out / "reviewer_scorecard.json"
            scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
            scorecard["draft_sha256"] = digest
            scorecard_path.write_text(json.dumps(scorecard), encoding="utf-8")
            (out / "claim_evidence_audit.json").write_text(json.dumps({
                "schema_version": "claim-evidence-audit.v1",
                "draft_sha256": digest,
                "summary": {"unresolved_count": 0},
                "records": [{
                    "claim_segment_id": "S001", "claim_text": "正文", "claim_strength": "background",
                    "required_evidence": "abstract_ok", "support_grade": "background", "reading_depth": "full_text",
                    "evidence_anchor": "page:1", "downgrade_required": False, "recommended_action": "retain",
                    "resolution_status": "closed",
                }],
            }), encoding="utf-8")
            passed = self.run_validator(out, "evidence_closed")
            (out / "journal_paper_draft.md").write_text(draft + "新增句子。\n", encoding="utf-8")
            stale = self.run_validator(out, "evidence_closed")
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        self.assertIn("completion_state: evidence_closed", passed.stdout)
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("stale_claim_evidence_audit", stale.stdout)


if __name__ == "__main__":
    unittest.main()
