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
