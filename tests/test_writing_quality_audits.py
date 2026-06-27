from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from audit_engineering_claims import audit_text as audit_engineering_text  # noqa: E402
from audit_scientific_writing_quality import audit_text as audit_quality_text  # noqa: E402


QUALITY_SCRIPT = SCRIPT_DIR / "audit_scientific_writing_quality.py"
ENGINEERING_SCRIPT = SCRIPT_DIR / "audit_engineering_claims.py"


class WritingQualityAuditsTest(unittest.TestCase):
    def test_scientific_quality_audit_detects_abstract_missing_moves(self):
        payload = audit_quality_text(
            "# 摘要\n\n本文提出一种充电桩能量管理方法，具有重要意义。",
            section_type="abstract",
        )
        self.assertEqual(payload["summary"]["section_type"], "abstract")
        issue_ids = {item["issue_id"] for item in payload["issues"]}
        self.assertIn("abstract-missing-problem", issue_ids)
        self.assertIn("abstract-missing-result", issue_ids)
        self.assertIn("abstract-missing-boundary", issue_ids)
        self.assertEqual(payload["summary"]["recommended_next_step"], "Step 7")

    def test_scientific_quality_audit_detects_figure_without_id_and_overclaim(self):
        payload = audit_quality_text(
            "# 讨论\n\n如图所示，该方法证明了系统性能提升，并具有重要意义。",
            section_type="discussion",
        )
        rule_ids = {item["rule_id"] for item in payload["issues"]}
        self.assertIn("figure_first_argument_plan.figure_or_table_id", rule_ids)
        self.assertIn("phrasebank_guardrail.claim_strength", rule_ids)

    def test_engineering_claim_audit_detects_power_energy_defects(self):
        text = (
            "该V2G策略提升电网稳定性并带来显著收益。"
            "系统效率较高。"
            "EMS优化显著降低运行成本。"
            "无线充电效率较高。"
            "本文首次提出该拓扑。"
        )
        payload = audit_engineering_text(text)
        defect_ids = {item["defect_id"] for item in payload["findings"]}
        self.assertIn("v2g_benefit_without_degradation_or_user_constraint", defect_ids)
        self.assertIn("efficiency_without_test_conditions", defect_ids)
        self.assertIn("ems_optimization_without_constraints", defect_ids)
        self.assertIn("wireless_charging_without_misalignment_or_emc", defect_ids)
        self.assertIn("first_claim_without_search_coverage", defect_ids)
        self.assertTrue(payload["summary"]["domain_detected"])
        self.assertEqual(payload["summary"]["recommended_next_step"], "Step 7")

    def test_cli_outputs_json_and_markdown_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "draft.md"
            quality_json = root / "quality.json"
            quality_md = root / "quality.md"
            engineering_json = root / "engineering.json"
            engineering_md = root / "engineering.md"
            draft.write_text("# 摘要\n\n本文提出一种EMS优化方法。系统效率较高。", encoding="utf-8")

            quality = subprocess.run(
                [
                    sys.executable,
                    str(QUALITY_SCRIPT),
                    str(draft),
                    "--section-type",
                    "abstract",
                    "--output-json",
                    str(quality_json),
                    "--output-md",
                    str(quality_md),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            engineering = subprocess.run(
                [
                    sys.executable,
                    str(ENGINEERING_SCRIPT),
                    str(draft),
                    "--output-json",
                    str(engineering_json),
                    "--output-md",
                    str(engineering_md),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(quality.returncode, 0, quality.stderr)
            self.assertEqual(engineering.returncode, 0, engineering.stderr)
            self.assertTrue(quality_json.exists())
            self.assertTrue(quality_md.exists())
            self.assertTrue(engineering_json.exists())
            self.assertTrue(engineering_md.exists())
            self.assertIn("Scientific Writing Quality Audit", quality_md.read_text(encoding="utf-8"))
            self.assertIn("Engineering Claim Audit", engineering_md.read_text(encoding="utf-8"))
            self.assertIn("summary", json.loads(quality.stdout))
            self.assertIn("findings", json.loads(engineering.stdout))


if __name__ == "__main__":
    unittest.main()
