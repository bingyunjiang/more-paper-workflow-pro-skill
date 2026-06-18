import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from manage_step4_intermediate import collect_intermediate_files  # noqa: E402


class ManageStep4IntermediateTest(unittest.TestCase):
    def test_collect_intermediate_files_skips_protected_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workflow_search_results.cnki_demo.json").write_text("{}", encoding="utf-8")
            (root / "wanfang_demo.bib").write_text("", encoding="utf-8")
            (root / "workflow_search_results.json").write_text("{}", encoding="utf-8")
            (root / "文献库.bib").write_text("", encoding="utf-8")

            files = collect_intermediate_files(root)
            names = {p.name for p in files}

        self.assertIn("workflow_search_results.cnki_demo.json", names)
        self.assertIn("wanfang_demo.bib", names)
        self.assertNotIn("workflow_search_results.json", names)
        self.assertNotIn("文献库.bib", names)


if __name__ == "__main__":
    unittest.main()
