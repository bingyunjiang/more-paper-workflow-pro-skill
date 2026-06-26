import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_contracts import (  # noqa: E402
    ARTIFACT_PASSPORT_SCHEMA,
    build_artifact_passport,
    load_artifact_passport,
    validate_artifact_passport,
    write_artifact_passport,
)


def readiness_by_step(passport):
    return {item.step: item for item in passport.readiness}


class ArtifactPassportTest(unittest.TestCase):
    def test_only_bibliography_enables_step5_and_step6_without_forcing_backtrack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "文献库.bib").write_text("@article{demo,title={Demo}}", encoding="utf-8")
            passport = build_artifact_passport(root, [root / "文献库.bib"])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.schema_version, ARTIFACT_PASSPORT_SCHEMA)
        self.assertEqual(passport.recommended_step, "Step 6")
        self.assertTrue(readiness["Step 5"].ready)
        self.assertTrue(readiness["Step 6"].ready)
        self.assertIn("plan-from-bib", readiness["Step 6"].allowed_modes)
        self.assertEqual(readiness["Step 6"].route_mode, "plan-only")

    def test_only_draft_enables_step8_and_step7_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "论文初稿.md"
            draft.write_text("正文", encoding="utf-8")
            passport = build_artifact_passport(root, [draft])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.recommended_step, "Step 8")
        self.assertTrue(readiness["Step 8"].ready)
        self.assertTrue(readiness["Step 7"].ready)
        self.assertIn("continue-existing", readiness["Step 7"].allowed_modes)
        self.assertIn("local-polish", readiness["Step 8"].allowed_modes)

    def test_step8_status_contract_can_block_passport_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "论文初稿.md"
            draft.write_text("正文", encoding="utf-8")
            skill_state = root / ".skill-state"
            skill_state.mkdir()
            ai_trace = skill_state / "ai_trace_diagnostics.json"
            ai_trace.write_text(
                json.dumps(
                    {
                        "status_contract": {
                            "readiness": "blocked",
                            "can_continue": False,
                            "blocking": ["存在待补文献/图表/实验材料，占位提示尚未闭环"],
                            "warnings": [],
                            "recommended_next_step": "Step 4/6",
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            passport = build_artifact_passport(root, [draft, ai_trace])
            readiness = readiness_by_step(passport)

        self.assertFalse(readiness["Step 8"].ready)
        self.assertEqual(readiness["Step 8"].recommended_next_step, "Step 4/6")
        self.assertIn("待补文献/图表/实验材料", readiness["Step 8"].blocked_reason)

    def test_step8_status_contract_can_redirect_to_step7_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft = root / "论文初稿.md"
            draft.write_text("正文", encoding="utf-8")
            skill_state = root / ".skill-state"
            skill_state.mkdir()
            ai_trace = skill_state / "ai_trace_diagnostics.json"
            ai_trace.write_text(
                json.dumps(
                    {
                        "status_contract": {
                            "readiness": "partial",
                            "can_continue": True,
                            "blocking": [],
                            "warnings": ["存在引用/证据型回退项，建议回到 Step 7 做引用审计或原文确认"],
                            "recommended_next_step": "Step 7",
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            passport = build_artifact_passport(root, [draft, ai_trace])
            readiness = readiness_by_step(passport)

        self.assertTrue(readiness["Step 8"].ready)
        self.assertEqual(readiness["Step 8"].recommended_next_step, "Step 7")
        self.assertIn("引用/证据型回退项", " ".join(readiness["Step 8"].risks))

    def test_pdf_directory_enables_step6_plan_only_with_risk_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_pool = root / "paper-temp"
            pdf_pool.mkdir()
            passport = build_artifact_passport(root, [pdf_pool])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.recommended_step, "Step 6")
        self.assertTrue(readiness["Step 6"].ready)
        self.assertEqual(readiness["Step 6"].route_mode, "plan-only")
        self.assertIn("Zotero mode: local/cloud/skip", readiness["Step 6"].missing_optional)

    def test_step5_direct_entry_from_doi_list_builds_download_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doi_list = root / "doi-list.txt"
            doi_list.write_text("10.1109/demo.2024.1\n", encoding="utf-8")
            passport = build_artifact_passport(root, [doi_list], entry_step="step5")
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.current_step, "Step 5")
        self.assertTrue(readiness["Step 5"].ready)
        self.assertIn("manifest-from-any-input", readiness["Step 5"].allowed_modes)
        self.assertTrue(any(node.node_type == "download_item" for node in passport.nodes))
        self.assertEqual(validate_artifact_passport(passport), [])

    def test_step5_direct_entry_from_pdf_pool_keeps_unlinked_pdf_nonblocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_pool = root / "PDFs"
            pdf_pool.mkdir()
            passport = build_artifact_passport(root, [pdf_pool], entry_step="step5")
            readiness = readiness_by_step(passport)

        self.assertTrue(readiness["Step 5"].ready)
        self.assertIn("reconcile-existing-pdf", readiness["Step 5"].allowed_modes)
        self.assertTrue(any("unlinked_pdf" in node.risk_flags for node in passport.nodes))
        self.assertTrue(any("unlinked" in gap for gap in passport.gaps))

    def test_step6_direct_entry_from_bib_does_not_require_step4_or_step5(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bib = root / "文献库.bib"
            bib.write_text("@article{demo,title={Demo}}", encoding="utf-8")
            passport = build_artifact_passport(root, [bib], entry_step="step6")
            readiness = readiness_by_step(passport)

        self.assertTrue(passport.direct_entry.direct_entry_friendly)
        self.assertFalse(passport.direct_entry.missing_prior_steps_block)
        self.assertTrue(readiness["Step 6"].ready)
        self.assertIn("plan-from-bib", readiness["Step 6"].allowed_modes)

    def test_workflow_json_routes_to_step5_manifest_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "workflow_search_results.json"
            workflow.write_text(json.dumps({"records": []}), encoding="utf-8")
            passport = build_artifact_passport(root, [workflow])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.recommended_step, "Step 5")
        self.assertTrue(readiness["Step 5"].ready)
        self.assertIn("manifest-from-any-input", readiness["Step 5"].allowed_modes)

    def test_zotero_mapping_routes_to_step7_and_plan_from_zotero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = root / "文献-Zotero架构对照.json"
            mapping.write_text("{}", encoding="utf-8")
            passport = build_artifact_passport(root, [mapping])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.recommended_step, "Step 7")
        self.assertTrue(readiness["Step 6"].ready)
        self.assertTrue(readiness["Step 7"].ready)
        self.assertIn("plan-from-zotero", readiness["Step 6"].allowed_modes)
        self.assertIn("pre-review", readiness["Step 7"].allowed_modes)

    def test_capability_index_routes_to_step7_and_keeps_step6_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capability = root / "capability_index.json"
            capability.write_text(json.dumps({"schema_version": "capability-index.v1"}), encoding="utf-8")
            passport = build_artifact_passport(root, [capability])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.recommended_step, "Step 7")
        self.assertTrue(readiness["Step 6"].ready)
        self.assertTrue(readiness["Step 7"].ready)
        self.assertIn("plan-from-zotero", readiness["Step 6"].allowed_modes)
        self.assertIn("pre-review", readiness["Step 7"].allowed_modes)
        self.assertEqual(passport.artifacts[0].kind, "capability_index")

    def test_local_evidence_pack_routes_to_step7_without_zotero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "实验报告.md"
            data = root / "results.csv"
            report.write_text("实验结论", encoding="utf-8")
            data.write_text("x,y\n1,2\n", encoding="utf-8")
            passport = build_artifact_passport(root, [report, data])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.recommended_step, "Step 7")
        self.assertTrue(readiness["Step 7"].ready)
        self.assertIn("evidence_pack", readiness["Step 7"].allowed_modes)

    def test_step7_direct_entry_from_evidence_pack_registers_evidence_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence_pack.json"
            evidence.write_text(json.dumps({"records": []}), encoding="utf-8")
            passport = build_artifact_passport(root, [evidence], entry_step="step7")
            readiness = readiness_by_step(passport)

        self.assertTrue(readiness["Step 7"].ready)
        self.assertIn("evidence_pack", readiness["Step 7"].allowed_modes)
        self.assertTrue(any(node.node_type == "evidence_item" for node in passport.nodes))
        self.assertEqual(validate_artifact_passport(passport), [])

    def test_mineru_zip_routes_to_step7_as_evidence_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mineru_zip = root / "LLM-for-Zotero-MinerU-cache-ABC123.zip"
            mineru_zip.write_bytes(b"not inspected by passport")
            passport = build_artifact_passport(root, [mineru_zip])
            readiness = readiness_by_step(passport)

        self.assertEqual(passport.artifacts[0].kind, "mineru_zip")
        self.assertEqual(passport.recommended_step, "Step 7")
        self.assertIn("evidence_pack", readiness["Step 7"].allowed_modes)

    def test_passport_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bib = root / "文献库.bib"
            bib.write_text("@article{demo,title={Demo}}", encoding="utf-8")
            output = root / ".skill-state" / "artifact_passport.json"
            output.parent.mkdir()

            passport = build_artifact_passport(root, [bib])
            write_artifact_passport(output, passport)
            loaded = load_artifact_passport(output)

        self.assertEqual(loaded.schema_version, ARTIFACT_PASSPORT_SCHEMA)
        self.assertEqual(loaded.recommended_step, "Step 6")
        self.assertEqual(loaded.artifacts[0].kind, "bibliography")
        self.assertTrue(loaded.nodes)

    def test_cli_scan_writes_runtime_passport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "论文初稿.md").write_text("正文", encoding="utf-8")
            output = root / ".skill-state" / "artifact_passport.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "artifact_passport.py"),
                    "--project-root",
                    str(root),
                    "--scan",
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertIn("recommended_step: Step 8", result.stdout)
        self.assertEqual(data["schema_version"], ARTIFACT_PASSPORT_SCHEMA)
        self.assertEqual(data["recommended_step"], "Step 8")

    def test_static_docs_define_passport_as_non_locking_route_layer(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        step7 = (ROOT / "agents" / "step_7_entry.md").read_text(encoding="utf-8")
        step8 = (ROOT / "agents" / "step_8_entry.md").read_text(encoding="utf-8")

        self.assertIn("artifact_passport.json", skill)
        self.assertIn("route_mode", skill)
        self.assertIn("不是线性流程锁", skill)
        self.assertIn("不覆盖本文件的 Step 7 `mode`", step7)
        self.assertIn("不覆盖 Step 8 的 `revision_scope / target_genre`", step8)


if __name__ == "__main__":
    unittest.main()
