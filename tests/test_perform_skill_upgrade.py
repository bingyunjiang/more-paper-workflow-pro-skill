from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "perform_skill_upgrade.py"


class PerformSkillUpgradeTest(unittest.TestCase):
    def test_reports_continue_when_git_pull_fails(self):
        with tempfile.TemporaryDirectory() as tmpbin:
            shim = Path(tmpbin) / "git"
            shim.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"pull\" ]; then\n"
                "  echo 'fatal: unable to access remote repository' 1>&2\n"
                "  exit 1\n"
                "fi\n"
                "exec /usr/bin/git \"$@\"\n",
                encoding="utf-8",
            )
            shim.chmod(0o755)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env={"PATH": f"{tmpbin}:/usr/bin:/bin"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["upgraded"])
        self.assertTrue(payload["continue_with_current_version"])
        self.assertEqual(payload["reason"], "git_pull_failed")
        self.assertIn("继续使用当前本地版本", payload["message"])


if __name__ == "__main__":
    unittest.main()
