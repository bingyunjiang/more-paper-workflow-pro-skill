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

from deterministic_writing_diagnostics import diagnose_text  # noqa: E402
from deterministic_writing_diagnostics import merge_into_revision_ledger  # noqa: E402
from deterministic_writing_diagnostics import render_diagnostic_summary_section  # noqa: E402


SCRIPT = SCRIPT_DIR / "deterministic_writing_diagnostics.py"


class DeterministicWritingDiagnosticsTest(unittest.TestCase):
    def test_diagnose_text_returns_revision_ledger_compatible_issues(self):
        text = (
            "Moreover, it is worth noting that this method plays a crucial role in the system, "
            "highlighting the importance of scalability. Moreover, studies have shown that the effect is strong. "
            "Moreover, this sentence is written in a very similar rhythm to the next sentence. "
            "This sentence is written in a very similar rhythm to the previous sentence."
        )
        payload = diagnose_text(text, lang="en")
        self.assertEqual(payload["summary"]["readiness"], "partial")
        self.assertGreaterEqual(payload["summary"]["issue_count"], 4)
        self.assertTrue(payload["summary"]["can_continue"])

        issue = payload["issues"][0]
        for field in [
            "issue_id",
            "category",
            "issue_type",
            "severity",
            "location",
            "problem",
            "evidence_basis",
            "allowed_action",
            "proposed_revision",
            "meaning_audit_required",
            "verification",
            "final_status",
            "next_action",
            "issue_state",
            "state_reason",
            "rule_family",
            "rule_id",
            "rule_examples",
            "density_signal",
        ]:
            self.assertIn(field, issue)
        self.assertEqual(issue["issue_type"], "language_mechanical")
        self.assertEqual(payload["issues"][0]["category"], "可直接修订")

    def test_category_defaults_bind_to_expected_next_actions(self):
        text = (
            "Moreover, it is worth noting that this method plays a crucial role. "
            "Studies have shown that it works. "
            "This sentence is written with very similar rhythm to the next sentence. "
            "This sentence is written with very similar rhythm to the previous sentence. "
            "This sentence is written with very similar rhythm to the other sentence. "
            "This sentence is written with very similar rhythm to the other sentence again."
        )
        payload = diagnose_text(text, lang="en")
        by_id = {item["issue_id"]: item for item in payload["issues"]}
        self.assertEqual(by_id["ai-trace-stock-001"]["category"], "可直接修订")
        self.assertEqual(by_id["ai-trace-stock-001"]["next_action"], "保留修改")
        self.assertEqual(by_id["ai-trace-vague-001"]["category"], "当前依据不足")
        self.assertEqual(by_id["ai-trace-vague-001"]["next_action"], "return_to_step_7_citation_audit")
        self.assertEqual(by_id["ai-trace-vague-001"]["deficiency_kind"], "citation_evidence")
        self.assertEqual(by_id["ai-trace-rhythm-001"]["category"], "需作者决定")
        self.assertEqual(by_id["ai-trace-rhythm-001"]["next_action"], "转人工复核")
        self.assertGreaterEqual(payload["summary"]["citation_evidence_rollback_count"], 1)

    def test_structural_gap_defaults_to_step4_or_6_rollback(self):
        payload = diagnose_text("这里需要补文献，图表待补，[[TODO: add experiment evidence]]", lang="zh")
        by_id = {item["issue_id"]: item for item in payload["issues"]}
        self.assertIn("ai-trace-structgap-001", by_id)
        self.assertEqual(by_id["ai-trace-structgap-001"]["category"], "当前依据不足")
        self.assertEqual(by_id["ai-trace-structgap-001"]["next_action"], "return_to_step_4_or_6")
        self.assertEqual(by_id["ai-trace-structgap-001"]["deficiency_kind"], "structure_material")
        self.assertGreaterEqual(payload["summary"]["structure_material_rollback_count"], 1)

    def test_cli_json_output_is_machine_readable(self):
        text = "值得注意的是，本文方法至关重要。此外，研究表明该方法有效。此外，这里还有一个重复的机械连接。"
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            draft.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(draft), "--lang", "zh", "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("summary", payload)
        self.assertIn("issues", payload)
        self.assertGreaterEqual(payload["summary"]["issue_count"], 2)
        self.assertEqual(payload["summary"]["recommended_next_step"], "Step 8")

    def test_summary_section_render_contains_fixed_block_fields(self):
        payload = diagnose_text("值得注意的是，本文方法有效。此外，研究表明其有效。", lang="zh")
        section = render_diagnostic_summary_section(payload)
        self.assertIn("## AI 味确定性检查摘要", section)
        self.assertIn("规则族命中数量", section)
        self.assertIn("高密度章节/段落", section)
        self.assertIn("可直接修复项数量", section)
        self.assertIn("需人工复核项数量", section)
        self.assertIn("引用/证据型回退数量", section)
        self.assertIn("结构/资料缺口回退数量", section)

    def test_merge_into_revision_ledger_preserves_existing_issues(self):
        payload = diagnose_text("Moreover, it is worth noting that this method plays a crucial role.", lang="en")
        existing = {
            "issues": [
                {
                    "issue_id": "existing-001",
                    "issue_type": "citation_misalignment",
                }
            ],
            "warnings": ["existing warning"],
        }
        merged = merge_into_revision_ledger(existing, payload)
        issue_ids = [item["issue_id"] for item in merged["issues"]]
        self.assertIn("existing-001", issue_ids)
        self.assertIn("ai-trace-stock-001", issue_ids)
        self.assertIn("ai_trace_diagnostics", merged)
        self.assertIn("已并入 deterministic writing diagnostics 结果", merged["warnings"])

    def test_cli_can_write_summary_and_merged_ledger(self):
        text = "Moreover, it is worth noting that this method plays a crucial role. Moreover, studies have shown that it works."
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            ledger = Path(tmp) / "revision_ledger.json"
            summary = Path(tmp) / "diagnostic_summary_ai_trace.md"
            merged = Path(tmp) / "revision_ledger.merged.json"
            draft.write_text(text, encoding="utf-8")
            ledger.write_text(json.dumps({"issues": [], "warnings": []}, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(draft),
                    "--lang",
                    "en",
                    "--summary-output",
                    str(summary),
                    "--merge-ledger",
                    str(ledger),
                    "--merged-output",
                    str(merged),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                    text=True,
                    check=False,
                )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(summary.exists())
            self.assertTrue(merged.exists())
            self.assertIn("## AI 味确定性检查摘要", summary.read_text(encoding="utf-8"))
            merged_payload = json.loads(merged.read_text(encoding="utf-8"))
            self.assertIn("ai_trace_diagnostics", merged_payload)
            self.assertGreaterEqual(len(merged_payload["issues"]), 1)


if __name__ == "__main__":
    unittest.main()
