import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import unified_download_router as router  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
