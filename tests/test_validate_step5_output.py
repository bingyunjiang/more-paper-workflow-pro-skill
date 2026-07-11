import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import unified_download_router as router  # noqa: E402
from workflow_contracts import append_jsonl_durable, atomic_write_json  # noqa: E402
from validate_step5_output import validate  # noqa: E402


class ValidateStep5OutputTest(unittest.TestCase):
    @staticmethod
    def valid_pdf() -> bytes:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Page >>\nendobj\n" + b"x" * 6000

    def test_verified_manifest_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "10.1007_demo.pdf"
            pdf.write_bytes(self.valid_pdf())
            router.write_step5_outputs(tmp, [{"id": "10.1007/demo", "doi": "10.1007/demo"}], ["10.1007/demo"], [], [{"round": "Sci-Hub", "downloaded": ["10.1007/demo"]}], {})
            findings, summary = validate(Path(tmp))
        self.assertEqual(summary["status"], "pass", findings)

    def test_invalid_pdf_cannot_be_downloaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "10.1007_demo.pdf"
            pdf.write_bytes(b"<html>login</html>" + b"x" * 6000)
            paths = router.write_step5_outputs(tmp, [{"id": "10.1007/demo", "doi": "10.1007/demo"}], ["10.1007/demo"], [], [{"round": "Sci-Hub", "downloaded": ["10.1007/demo"]}], {})
            manifest = json.loads(Path(paths["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["items"][0]["status"], "invalid_pdf")
        self.assertEqual(manifest["readiness"], "blocked")

    def test_attempt_log_is_appended(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "10.1007_demo.pdf"
            pdf.write_bytes(self.valid_pdf())
            args = (tmp, [{"id": "10.1007/demo", "doi": "10.1007/demo"}], ["10.1007/demo"], [], [{"round": "Sci-Hub", "downloaded": ["10.1007/demo"]}], {})
            router.write_step5_outputs(*args)
            first = (Path(tmp) / "download_attempts.jsonl").read_text(encoding="utf-8").splitlines()
            router.write_step5_outputs(*args)
            second = (Path(tmp) / "download_attempts.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(second), len(first) * 2)

    def test_attempt_journal_skips_duplicate_attempt_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "download_attempts.jsonl"
            row = {"attempt_id": "same", "run_id": "run", "item_id": "item"}
            self.assertEqual(append_jsonl_durable(path, [row]), 1)
            self.assertEqual(append_jsonl_durable(path, [row]), 0)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_atomic_json_write_preserves_old_file_if_replace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text('{"old": true}', encoding="utf-8")
            with patch("workflow_contracts.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    atomic_write_json(path, {"new": True})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"old": True})

    def test_resolved_checkpoint_is_closed_but_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "login_checkpoint.json"
            path.write_text(json.dumps({"status": "pending_user_login", "items": [{"doi": "10.1/a"}]}), encoding="utf-8")
            router.resolve_login_checkpoint(path, downloaded=["10.1/a"], remaining=[])
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "resolved")
        self.assertEqual(payload["resolved_items"], ["10.1/a"])

    def test_checkpoint_stays_pending_when_items_remain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "login_checkpoint.json"
            path.write_text(json.dumps({"status": "pending_user_login"}), encoding="utf-8")
            router.resolve_login_checkpoint(path, downloaded=[], remaining=["10.1/a"])
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "pending_user_login")

    def test_validator_checks_captcha_checkpoint_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            router.write_step5_outputs(
                tmp, [{"id": "cnki.demo", "source_id": "cnki.demo", "title": "Demo"}],
                [], ["cnki.demo"], [], {"cnki.demo": "captcha_required"},
            )
            (root / "chinese_login_checkpoint.json").write_text(json.dumps({
                "status": "pending_captcha_verification",
                "items": [{"source_id": "cnki.demo"}, {"source_id": "cnki.demo"}],
            }), encoding="utf-8")
            findings, summary = validate(root)
        self.assertEqual(summary["status"], "fail")
        self.assertTrue(any(item.code == "duplicate_checkpoint_item" for item in findings))


if __name__ == "__main__":
    unittest.main()
