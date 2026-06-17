from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import unified_download_router as router  # noqa: E402


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
             patch("subprocess.run") as run_cmd:
            self.assertTrue(router.ensure_cdp_running(9223))
        run_cmd.assert_called_once()

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


if __name__ == "__main__":
    unittest.main()
