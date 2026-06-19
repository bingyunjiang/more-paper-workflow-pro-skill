from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import unified_download_router as router  # noqa: E402
import generic_publisher_downloader as gpd  # noqa: E402


class Step5DownloadTest(unittest.TestCase):
    def test_parse_chinese_papers_from_markdown_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chinese.md"
            path.write_text(
                "\n".join([
                    "| 来源 | 标题 | DOI | 文章链接 |",
                    "|---|---|---|---|",
                    "| cnki | 薄壁管弯曲回弹研究 | cnki.demo | https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=test |",
                    "| wanfang | 无链接条目 | wanfang.demo |  |",
                ]),
                encoding="utf-8",
            )

            papers = router.parse_chinese_papers(str(path))

        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0]["source"], "cnki")
        self.assertTrue(papers[0]["article_url"].startswith("https://kns.cnki.net/"))
        self.assertEqual(papers[0]["doi"], "cnki.demo")
        self.assertEqual(papers[1]["source"], "wanfang")
        self.assertEqual(papers[1]["article_url"], "")

    def test_parse_chinese_papers_from_json_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chinese.json"
            path.write_text(
                """[
                  {"title": "万方论文", "source": "wanfang", "article_url": "https://www.wanfangdata.com.cn/details/detail.do?_type=perio&id=test", "source_id": "wanfang.test"}
                ]""",
                encoding="utf-8",
            )

            papers = router.parse_chinese_papers(str(path))

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["source"], "wanfang")
        self.assertIn("wanfangdata.com.cn", papers[0]["article_url"])
        self.assertEqual(papers[0]["doi"], "wanfang.test")

    def test_show_chinese_login_gate_accepts_confirmed_login(self):
        papers = [{
            "title": "CNKI demo",
            "source": "cnki",
            "article_url": "https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=test",
        }]

        with patch("builtins.input", return_value="已登录"):
            self.assertTrue(router.show_chinese_login_gate(papers))

    def test_show_english_login_gate_lists_cdp_publishers(self):
        dois = [
            "10.1016/j.test.2024.01.001",
            "10.1038/s41467-2024-00001",
        ]

        with patch("builtins.input", return_value="已登录"):
            self.assertTrue(router.show_english_login_gate(dois))

    def test_ensure_cdp_running_reuses_existing_browser(self):
        with patch.object(router, "check_cdp", return_value=True):
            self.assertTrue(router.ensure_cdp_running(9223))

    def test_ensure_cdp_running_auto_starts_browser(self):
        with patch.object(router, "check_cdp", side_effect=[False, True]), \
             patch.object(router, "start_persistent_cdp_browser") as starter:
            self.assertTrue(router.ensure_cdp_running(9223))
        starter.assert_called_once()

    def test_dry_run_classification_includes_chinese_and_english_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            chinese_path = Path(tmp) / "chinese.json"
            chinese_path.write_text(
                """[
                  {"title": "中文论文", "source": "cnki", "article_url": "https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=test", "doi": "cnki.test"}
                ]""",
                encoding="utf-8",
            )

            chinese_papers = router.parse_chinese_papers(str(chinese_path))
            classified = [router.classify_doi("10.1016/j.test.2024.01.001")]
            for paper in chinese_papers:
                c = router.classify_doi(paper.get("doi", ""))
                c["strategy"] = "chinese_cdp"
                c["publisher"] = paper["source"]
                classified.append(c)

        strategies = {item["strategy"] for item in classified}
        self.assertIn("sd_cdp", strategies)
        self.assertIn("chinese_cdp", strategies)

    def test_article_page_login_wall_keeps_tab_open_for_manual_login(self):
        publisher = {
            "_key": "springer",
            "selectors": ["a.pdf-link"],
            "article_url_template": "https://example.com/{doi}",
        }

        with patch.object(gpd, "_build_article_url", return_value="https://example.com/article"), \
             patch.object(gpd, "create_tab", return_value=(None, "tab-1")), \
             patch.object(gpd, "_detect_access_barrier", return_value=("login_wall", "title matched")), \
             patch.object(gpd, "_extract_pdf_url_from_dom", return_value="LOGIN_REQUIRED"), \
             patch.object(gpd, "close_tab") as close_tab:
            result = gpd._strategy_article_page(9223, "10.1007/demo", publisher, timeout=1)

        self.assertEqual(result, "MANUAL_REQUIRED")
        close_tab.assert_not_called()

    def test_download_one_returns_manual_required_for_login_wall(self):
        with patch.object(gpd, "resolve_publisher", return_value={"strategy": "generic", "_key": "springer"}), \
             patch.object(gpd, "_strategy_direct_pdf", return_value=None), \
             patch.object(gpd, "_strategy_article_page", return_value="MANUAL_REQUIRED"):
            path, status, pub = gpd.download_one(9223, "10.1007/demo", "paper-temp")

        self.assertIsNone(path)
        self.assertEqual(status, "manual_required")
        self.assertEqual(pub, "springer")

    def test_springer_institutional_login_entry_is_documented(self):
        matrix = (ROOT / "references" / "publisher-access-matrix.md").read_text(encoding="utf-8")
        step5 = (ROOT / "agents" / "step_5_download.md").read_text(encoding="utf-8")

        self.assertIn("https://idp.springer.com/authorize?response_type=cookie&client_id=springerlink", matrix)
        self.assertIn("https://wayf.springernature.com/?redirect_uri=https%3A%2F%2Flink.springer.com%2F", matrix)
        self.assertIn("https://idp.springer.com/authorize?response_type=cookie&client_id=springerlink", step5)
        self.assertIn("skip", step5)
        self.assertIn("支持弹窗/结构化交互", matrix)
        self.assertIn("若宿主支持弹窗/结构化选项", step5)

    def test_login_gates_allow_skip_without_fatal_stop(self):
        with patch("builtins.input", return_value="2"):
            self.assertFalse(router.show_english_login_gate(["10.1007/demo"]))

    def test_login_gate_prompts_offer_three_choices(self):
        with patch("builtins.input", return_value="3") as inp:
            self.assertFalse(router.show_chinese_login_gate([{"source": "cnki", "article_url": "https://kns.cnki.net", "title": "x"}]))
        self.assertTrue(inp.called)

    def test_generic_round_recovers_from_single_item_exception(self):
        with patch.object(router, "resolve_publisher", return_value={"strategy": "generic", "_key": "springer", "publisher_domain": "link.springer.com"}), \
             patch.object(router, "generic_download_one", side_effect=RuntimeError("502") ), \
             patch.object(router, "ensure_cdp_running", return_value=True):
            downloaded, remaining = router.run_generic_round(["10.1007/demo"], "paper-temp", 9223)

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, ["10.1007/demo"])

    def test_generic_round_keeps_manual_required_item_for_rerun(self):
        with patch.object(router, "resolve_publisher", return_value={"strategy": "generic", "_key": "springer", "publisher_domain": "link.springer.com"}), \
             patch.object(router, "generic_download_one", return_value=(None, "manual_required", "springer")):
            downloaded, remaining = router.run_generic_round(["10.1007/demo"], "paper-temp", 9223)

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, ["10.1007/demo"])


if __name__ == "__main__":
    unittest.main()
