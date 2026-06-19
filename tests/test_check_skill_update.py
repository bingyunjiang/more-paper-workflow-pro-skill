from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_skill_update.py"


class CheckSkillUpdateScriptTest(unittest.TestCase):
    def test_json_mode_reports_soft_prompt_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"XDG_CACHE_HOME": tmp}
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", "--force", "--no-network"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env={**env, "PATH": "/usr/bin:/bin"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["enabled"])
        self.assertFalse(payload["skipped"])
        self.assertIn("update_available", payload)
        self.assertIn("should_prompt", payload)
        self.assertIn("suggested_action", payload)
        self.assertIn("messages", payload)
        self.assertEqual(payload["suggested_action"], "continue")
        self.assertFalse(payload["should_prompt"])
        self.assertEqual(payload["prompt_options"], [])
        self.assertEqual(payload["skill_version"], "v1.0.14-20260618")

    def test_record_choice_snoozes_matching_remote_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"XDG_CACHE_HOME": tmp, "PATH": "/usr/bin:/bin"}
            first = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", "--force", "--record-choice", "snooze_today"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            first_payload = json.loads(first.stdout)
            remote_head = first_payload.get("remote_head")

            if not remote_head or not first_payload.get("remote_update_available"):
                self.skipTest("remote HEAD not available in this environment")

            second = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", "--force"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            second_payload = json.loads(second.stdout)
            self.assertTrue(second_payload["suppressed"])
            self.assertEqual(second_payload["suppress_reason"], "snoozed_for_today")
            self.assertFalse(second_payload["should_prompt"])


if __name__ == "__main__":
    unittest.main()
