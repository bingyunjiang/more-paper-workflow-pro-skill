from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_step8_ai_trace.py"


class RunStep8AiTraceTest(unittest.TestCase):
    def test_runner_uses_default_artifact_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "值得注意的是，本文方法有效。此外，研究表明该方法有效。此外，还存在一个机械连接。",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            diagnostics_json = root / ".skill-state" / "ai_trace_diagnostics.json"
            diagnostic_summary = root / "diagnostic_summary.md"
            revision_ledger = root / "revision_ledger.json"
            revision_ledger_md = root / "revision_ledger.md"
            polish_quality_report = root / "润色质量报告.md"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(diagnostics_json.exists())
            self.assertTrue(diagnostic_summary.exists())
            self.assertTrue(revision_ledger.exists())
            self.assertTrue(revision_ledger_md.exists())
            self.assertTrue(polish_quality_report.exists())

            summary_text = diagnostic_summary.read_text(encoding="utf-8")
            self.assertIn("## AI 味确定性检查摘要", summary_text)
            self.assertIn("引用/证据型回退数量", summary_text)
            self.assertIn("结构/资料缺口回退数量", summary_text)
            self.assertIn("### Step 8 总判断", summary_text)
            self.assertIn("Overall Status", summary_text)
            self.assertIn("Next Action", summary_text)
            self.assertIn("### 统一状态契约", summary_text)
            self.assertIn("readiness", summary_text)
            self.assertIn("can_continue", summary_text)
            self.assertIn("recommended_next_step", summary_text)

            ledger = json.loads(revision_ledger.read_text(encoding="utf-8"))
            self.assertIn("ai_trace_diagnostics", ledger)
            self.assertGreaterEqual(len(ledger.get("issues", [])), 1)
            self.assertIn("step8_decision", ledger["ai_trace_diagnostics"])
            self.assertIn("status_contract", ledger["ai_trace_diagnostics"])
            ledger_md_text = revision_ledger_md.read_text(encoding="utf-8")
            self.assertIn("## Step 8 问题闭环摘要", ledger_md_text)
            self.assertIn("## 问题分流", ledger_md_text)
            self.assertIn("### 可直接修订", ledger_md_text)
            self.assertIn("### 需作者决定", ledger_md_text)
            self.assertIn("### 当前依据不足", ledger_md_text)
            self.assertIn("- default_next_action: `保留修改`", ledger_md_text)
            self.assertIn("- default_next_action: `转人工复核`", ledger_md_text)
            self.assertIn("- default_next_action: `return_to_step_7_citation_audit / return_to_step_4_or_6`", ledger_md_text)
            self.assertIn("- overall_status: `ready_with_warnings`", ledger_md_text)
            self.assertIn("- readiness: `partial`", ledger_md_text)
            self.assertIn("- can_continue: `True`", ledger_md_text)
            self.assertIn("- recommended_next_step: `Step 7`", ledger_md_text)
            report_text = polish_quality_report.read_text(encoding="utf-8")
            self.assertIn("## AI 味检查结果", report_text)
            self.assertIn("引用/证据型回退数量", report_text)
            self.assertIn("结构/资料缺口回退数量", report_text)
            self.assertIn("Overall Status", report_text)
            self.assertIn("Next Action", report_text)
            self.assertIn("### 统一状态契约", report_text)

    def test_runner_replaces_existing_summary_block_and_preserves_other_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "Moreover, it is worth noting that this method plays a crucial role. Moreover, studies have shown that it works.",
                encoding="utf-8",
            )
            (root / "diagnostic_summary.md").write_text(
                "# diagnostic_summary\n\n## AI 味确定性检查摘要\n\n旧内容\n\n## 其他问题\n\n保留内容\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root), "--lang", "en"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (root / "diagnostic_summary.md").read_text(encoding="utf-8")
            self.assertIn("## AI 味确定性检查摘要", text)
            self.assertIn("## 其他问题", text)
            self.assertNotIn("旧内容", text)

    def test_runner_replaces_existing_polish_quality_report_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "值得注意的是，本文方法有效。此外，研究表明该方法有效。",
                encoding="utf-8",
            )
            (root / "润色质量报告.md").write_text(
                "# 润色质量报告\n\n## AI 味检查结果\n\n旧区块\n\n## 降级说明\n\n保留内容\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (root / "润色质量报告.md").read_text(encoding="utf-8")
            self.assertIn("## AI 味检查结果", text)
            self.assertIn("## 降级说明", text)
            self.assertNotIn("旧区块", text)

    def test_runner_groups_revision_ledger_md_by_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "值得注意的是，本文方法有效。此外，研究表明该方法有效。"
                "Moreover, it is worth noting that this method plays a crucial role.",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            ledger_md = (root / "revision_ledger.md").read_text(encoding="utf-8")
            self.assertIn("### 可直接修订", ledger_md)
            self.assertIn("### 需作者决定", ledger_md)
            self.assertIn("### 当前依据不足", ledger_md)
            self.assertIn("#### ai-trace-stock-001", ledger_md)
            self.assertIn("#### ai-trace-vague-001", ledger_md)
            self.assertIn("- next_action: `保留修改`", ledger_md)
            self.assertIn("- next_action: `return_to_step_7_citation_audit`", ledger_md)

    def test_runner_splits_currently_insufficient_by_deficiency_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "研究表明该方法有效。这里需要补文献，图表待补。"
                "Moreover, it is worth noting that this method plays a crucial role.",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            ledger_md = (root / "revision_ledger.md").read_text(encoding="utf-8")
            self.assertIn("#### 引用/证据型回退", ledger_md)
            self.assertIn("#### 结构/资料缺口回退", ledger_md)
            self.assertIn("##### ai-trace-vague-001", ledger_md)
            self.assertIn("##### ai-trace-structgap-001", ledger_md)
            self.assertIn("- deficiency_kind: `citation_evidence`", ledger_md)
            self.assertIn("- deficiency_kind: `structure_material`", ledger_md)
            self.assertIn("- next_action: `return_to_step_4_or_6`", ledger_md)

    def test_runner_marks_structure_material_gap_as_not_ready_requires_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "这里需要补文献，图表待补，[[TODO: add experiment evidence]]",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            summary_text = (root / "diagnostic_summary.md").read_text(encoding="utf-8")
            report_text = (root / "润色质量报告.md").read_text(encoding="utf-8")
            ledger = json.loads((root / "revision_ledger.json").read_text(encoding="utf-8"))
            self.assertIn("`not_ready_requires_rollback`", summary_text)
            self.assertIn("`return_to_step_4_or_6`", summary_text)
            self.assertIn("`not_ready_requires_rollback`", report_text)
            self.assertIn("`return_to_step_4_or_6`", report_text)
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["step8_decision"]["overall_status"],
                "not_ready_requires_rollback",
            )
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["status_contract"]["readiness"],
                "blocked",
            )
            self.assertFalse(ledger["ai_trace_diagnostics"]["status_contract"]["can_continue"])
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["status_contract"]["recommended_next_step"],
                "Step 4/6",
            )

    def test_runner_marks_direct_fix_only_case_as_ready_to_polish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "值得注意的是，本文方法有效。此外，另外，首先，其次，更重要的是，这里反复使用连接词。",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = json.loads((root / "revision_ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["step8_decision"]["overall_status"],
                "ready_to_polish",
            )
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["step8_decision"]["next_action"],
                "apply_polish_and_verify",
            )
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["status_contract"]["readiness"],
                "partial",
            )
            self.assertTrue(ledger["ai_trace_diagnostics"]["status_contract"]["can_continue"])
            self.assertFalse((root / "论文润色稿.md").exists())
            self.assertTrue(ledger["ai_trace_diagnostics"]["status_contract"]["warnings"])
            self.assertEqual(
                ledger["ai_trace_diagnostics"]["status_contract"]["recommended_next_step"],
                "Step 8",
            )

    def test_runner_only_finalizes_existing_polished_draft_after_fidelity_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text(
                "值得注意的是，在25 °C条件下，该方法可能使效率提高12%[3]。",
                encoding="utf-8",
            )
            (root / "论文润色稿.md").write_text(
                "在25 °C条件下，该方法可能将效率提高12%[3]。",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            ledger = json.loads((root / "revision_ledger.json").read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(ledger["ai_trace_diagnostics"]["step8_decision"]["overall_status"], "ready_for_finalize")
        self.assertEqual(ledger["ai_trace_diagnostics"]["status_contract"]["readiness"], "complete")
        self.assertEqual(ledger["ai_trace_diagnostics"]["polish_fidelity"]["status"], "pass")

    def test_runner_blocks_polished_draft_when_fidelity_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            (root / "论文初稿.md").write_text("在25 °C条件下，效率可能提高12%[3]。", encoding="utf-8")
            (root / "论文润色稿.md").write_text("效率证明提高15%[3]。", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            ledger = json.loads((root / "revision_ledger.json").read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(ledger["ai_trace_diagnostics"]["step8_decision"]["overall_status"], "not_ready_requires_rollback")
        self.assertEqual(ledger["ai_trace_diagnostics"]["status_contract"]["recommended_next_step"], "Step 8")
        self.assertTrue(ledger["ai_trace_diagnostics"]["status_contract"]["blocking"])

    def test_runner_inherits_unresolved_structured_step7_evidence_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".skill-state").mkdir()
            draft = "在25 °C条件下，该方法可能使效率提高12%[3]。"
            (root / "论文初稿.md").write_text(draft, encoding="utf-8")
            (root / "论文润色稿.md").write_text("在25 °C条件下，该方法可能将效率提高12%[3]。", encoding="utf-8")
            import hashlib
            (root / "claim_evidence_audit.json").write_text(json.dumps({
                "schema_version": "claim-evidence-audit.v1",
                "draft_sha256": hashlib.sha256(draft.encode("utf-8")).hexdigest(),
                "summary": {"unresolved_count": 1},
                "records": [],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            ledger = json.loads((root / "revision_ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        diagnostics = ledger["ai_trace_diagnostics"]
        self.assertEqual(diagnostics["step7_evidence_gate"]["status"], "unresolved")
        self.assertEqual(diagnostics["step8_decision"]["overall_status"], "not_ready_requires_rollback")
        self.assertEqual(diagnostics["status_contract"]["recommended_next_step"], "Step 7")


if __name__ == "__main__":
    unittest.main()
