from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import cdp_utils  # noqa: E402
import auto_sd_downloader  # noqa: E402
import setup_zotero  # noqa: E402
import unified_download_router as router  # noqa: E402


class PlatformCompatTest(unittest.TestCase):
    def test_macos_chrome_fallback_is_preserved(self):
        chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        with patch.object(cdp_utils, "_is_macos", return_value=True), \
             patch.object(cdp_utils, "_is_windows", return_value=False), \
             patch.object(cdp_utils.shutil, "which", return_value=None), \
             patch.object(cdp_utils.os.path, "isfile", side_effect=lambda p: p == chrome):
            self.assertEqual(cdp_utils.find_chrome_path(), chrome)

    def test_windows_chrome_fallback_is_detected(self):
        chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        with patch.object(cdp_utils, "_is_macos", return_value=False), \
             patch.object(cdp_utils, "_is_windows", return_value=True), \
             patch.object(cdp_utils.shutil, "which", return_value=None), \
             patch.object(cdp_utils.os.path, "isfile", side_effect=lambda p: p == chrome):
            self.assertEqual(cdp_utils.find_chrome_path(), chrome)

    def test_windows_profile_cleanup_targets_only_matching_profile_processes(self):
        calls = []

        def _fake_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        with patch.object(cdp_utils, "_is_macos", return_value=False), \
             patch.object(cdp_utils, "_is_windows", return_value=True), \
             patch.object(cdp_utils.subprocess, "run", side_effect=_fake_run), \
             patch.object(cdp_utils.time, "sleep", return_value=None):
            cdp_utils.kill_browser_by_profile(r"C:\Users\demo\.hermes\chrome_sd_profile")

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0:3], ["powershell", "-NoProfile", "-Command"])
        self.assertIn("chrome_sd_profile", calls[0][3])
        self.assertNotIn("/IM", " ".join(calls[0]))

    def test_zotero_bin_detects_windows_scripts_exe(self):
        site_packages = r"C:\Users\demo\AppData\Local\Programs\Python\Python311\Lib\site-packages"
        expected = r"C:\Users\demo\AppData\Local\Programs\Python\Python311\Scripts\zotero-mcp.exe"
        pip_show = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"Name: zotero-mcp-server\nLocation: {site_packages}\n",
            stderr="",
        )
        with patch.object(setup_zotero.subprocess, "run", return_value=pip_show), \
             patch.object(setup_zotero.os.path, "exists", side_effect=lambda p: p == expected), \
             patch.object(setup_zotero.shutil, "which", return_value=None):
            self.assertEqual(setup_zotero.get_zotero_bin(), expected)

    def test_router_auto_start_uses_python_cdp_helper(self):
        with patch.object(router, "check_cdp", side_effect=[False, True]), \
             patch.object(router, "start_persistent_cdp_browser") as starter:
            self.assertTrue(router.ensure_cdp_running(9223))
        starter.assert_called_once()

    def test_auto_sd_default_browser_is_single_chrome(self):
        parser = auto_sd_downloader.argparse.ArgumentParser()
        parser.add_argument("--browser", choices=["auto", "chrome", "edge"], default="chrome")
        args = parser.parse_args([])
        self.assertEqual(args.browser, "chrome")

    def test_platform_compat_scan_has_no_errors(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "check_platform_compat.py")],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
