import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import batch_chinese_search as helper  # noqa: E402


class BatchChineseLoginTabsTest(unittest.TestCase):
    @patch.object(helper, "create_tab")
    @patch.object(helper, "list_tabs")
    def test_opens_both_missing_database_tabs(self, list_tabs, create_tab):
        list_tabs.return_value = [{"type": "page", "url": "about:blank"}]

        helper._navigate_initial_tabs(9223)

        self.assertEqual(
            [call.args[1] for call in create_tab.call_args_list],
            [helper.CNKI_URL, helper.WANFANG_URL],
        )

    @patch.object(helper, "create_tab")
    @patch.object(helper, "list_tabs")
    def test_reuses_existing_database_tabs_without_duplicates(self, list_tabs, create_tab):
        list_tabs.return_value = [
            {"type": "page", "url": "https://kns.cnki.net/kns8s/"},
            {"type": "page", "url": "https://www.wanfangdata.com.cn/"},
        ]

        helper._navigate_initial_tabs(9223)

        create_tab.assert_not_called()

    @patch.object(helper, "_navigate_initial_tabs")
    @patch.object(helper, "_ensure_chinese_cdp", return_value=True)
    def test_open_login_tabs_returns_without_waiting_for_confirmation(self, ensure_cdp, navigate):
        with patch("sys.argv", ["batch_chinese_search.py", "--open-login-tabs"]):
            result = helper.main()

        self.assertEqual(result, 0)
        ensure_cdp.assert_called_once_with(9223, "chrome")
        navigate.assert_called_once_with(9223)


if __name__ == "__main__":
    unittest.main()
