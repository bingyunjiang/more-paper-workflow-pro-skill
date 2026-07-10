import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_zotero_plan import apply_duplicate_states  # noqa: E402
from validate_step6_output import validate  # noqa: E402
from zotero_operation_journal import record_operation  # noqa: E402


class Step6QualityUpgradeTest(unittest.TestCase):
    def test_duplicate_doi_is_a_candidate_not_auto_merged(self):
        records = [
            {"record_id": "r1", "doi": "10.1000/demo", "title": "A", "authors": ["One"], "year": "2024", "item_state": "planned"},
            {"record_id": "r2", "doi": "10.1000/demo", "title": "A", "authors": ["One"], "year": "2024", "item_state": "planned"},
        ]
        apply_duplicate_states(records)
        self.assertEqual(records[1]["item_state"], "duplicate_candidate")
        self.assertEqual(records[1]["duplicate_of_record_id"], "r1")

    def test_operation_journal_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            operation = {"operation_type": "create_item", "target_id": "r1", "status": "success", "checkpoint_confirmed": True}
            first = record_operation(tmp, operation)
            second = record_operation(tmp, operation)
            lines = (Path(tmp) / "zotero_write_operations.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertFalse(first["skipped"])
        self.assertTrue(second["skipped"])
        self.assertEqual(len(lines), 1)

    def test_pdf_only_direct_entry_is_plan_ready_without_step5(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_dir = root / "pdfs"
            pdf_dir.mkdir()
            (pdf_dir / "unlinked.pdf").write_bytes(b"%PDF-1.4\n<< /Type /Page >>\n" + b"x" * 6000)
            result = subprocess.run([
                sys.executable, str(SCRIPTS / "build_zotero_plan.py"),
                "--pdf-dir", str(pdf_dir),
                "--output", str(root / "文献-Zotero架构对照.json"),
                "--review", str(root / "文献-Zotero架构对照.md"),
                "--pdf-index", str(root / "pdf-附件池索引.json"),
            ], capture_output=True, text=True, check=False)
            plan = json.loads((root / "文献-Zotero架构对照.json").read_text(encoding="utf-8"))
            findings, summary = validate(root)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(plan["direct_entry"])
        self.assertEqual(plan["completion_state"], "plan_ready")
        self.assertEqual(summary["status"], "pass", findings)

    def test_records_json_direct_entry_does_not_require_bib_or_step5(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "zotero_readonly_scan.json"
            records.write_text(json.dumps({"items": [{
                "id": "ITEM0001", "title": "Direct Zotero record", "DOI": "10.1000/direct",
                "author": [{"family": "Author"}], "year": "2025",
            }]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPTS / "build_zotero_plan.py"),
                "--records-json", str(records),
                "--output", str(root / "文献-Zotero架构对照.json"),
                "--review", str(root / "文献-Zotero架构对照.md"),
                "--pdf-index", str(root / "pdf-附件池索引.json"),
            ], capture_output=True, text=True, check=False)
            plan = json.loads((root / "文献-Zotero架构对照.json").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(plan["records"][0]["item_state"], "planned")
        self.assertNotIn("文献库.bib", plan["blocking_missing"])


if __name__ == "__main__":
    unittest.main()
