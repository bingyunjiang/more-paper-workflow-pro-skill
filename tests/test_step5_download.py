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
import auto_sd_downloader as auto_sd  # noqa: E402
import parallel_sd_download as parallel_sd  # noqa: E402
import cdp_utils  # noqa: E402
import sd_download  # noqa: E402
import batch_resolve_pii  # noqa: E402
import console_compat  # noqa: E402


class Step5DownloadTest(unittest.TestCase):
    def test_auto_sd_loader_reads_pii_map_as_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            pii_map = Path(tmp) / "sd_pii_map.json"
            out_dir = Path(tmp) / "out"
            out_dir.mkdir()
            pii_map.write_text(
                """{
                  "resolved": {
                    "paper_001": {"doi": "10.1016/j.demo.2026.01.001", "pii": "S0000000000000001"}
                  }
                }""",
                encoding="utf-8",
            )

            remaining, done = auto_sd._load_remaining_papers(str(pii_map), str(out_dir))

        self.assertEqual(done, 0)
        self.assertEqual(remaining, [("paper_001", "10.1016/j.demo.2026.01.001", "S0000000000000001")])

    def test_auto_sd_loader_recognizes_completed_key_named_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            pii_map = Path(tmp) / "sd_pii_map.json"
            out_dir = Path(tmp) / "out"
            out_dir.mkdir()
            pii_map.write_text(
                """{
                  "resolved": {
                    "S8RREAFT": {"doi": "10.1016/j.ijheatmasstransfer.2021.121612", "pii": "S0017931021007158"},
                    "WI9CIV79": {"doi": "10.1016/j.ijheatmasstransfer.2025.127378", "pii": "S0017931025007173"}
                  }
                }""",
                encoding="utf-8",
            )
            (out_dir / "S8RREAFT.pdf").write_bytes(b"%PDF-1.4\n")

            remaining, done = auto_sd._load_remaining_papers(str(pii_map), str(out_dir))

        self.assertEqual(done, 1)
        self.assertEqual(remaining, [("WI9CIV79", "10.1016/j.ijheatmasstransfer.2025.127378", "S0017931025007173")])

    def test_batch_resolve_pii_preserves_balanced_parentheses_in_old_doi(self):
        self.assertEqual(
            batch_resolve_pii._clean_doi("https://doi.org/10.1016/S0378-7753(03)00012-3)"),
            "10.1016/S0378-7753(03)00012-3",
        )
        self.assertEqual(
            batch_resolve_pii._clean_doi("10.1016/S0378-7753(03)00012-3"),
            "10.1016/S0378-7753(03)00012-3",
        )

    def test_auto_sd_worker_passes_timeout_overrides_to_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            out_dir.mkdir()
            results = {}
            papers = [("paper_001", "10.1016/j.demo.2026.01.001", "S0000000000000001")]

            with patch.object(auto_sd, "download_sd_pii", return_value=b"%PDF" + b"x" * 25000) as mock_download:
                auto_sd._worker("Chrome", 9223, papers, str(out_dir), results, auto_sd.threading.Lock(), 11, 27)
                self.assertTrue((out_dir / "paper_001.pdf").exists())

        mock_download.assert_called_once_with(9223, "S0000000000000001", timeout_a=11, timeout_b=27)

    def test_auto_sd_resolve_browsers_edge_uses_edge_only(self):
        args = auto_sd.argparse.Namespace(
            browser="edge",
            browser_path=None,
            browser_path_edge=None,
            port_chrome=9223,
            port_edge=9223,
        )
        with patch.object(auto_sd, "find_chrome_path", return_value=r"C:\Chrome\chrome.exe") as find_chrome, \
             patch.object(auto_sd, "find_edge_path", return_value=r"C:\Edge\msedge.exe"):
            browsers = auto_sd._resolve_browsers(args)

        find_chrome.assert_not_called()
        self.assertEqual(browsers, [("Edge", r"C:\Edge\msedge.exe", 9223, auto_sd.DEFAULT_PROFILES["edge"])])

    def test_run_generic_round_routes_sciencedirect_through_generic_cdp(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "10.1016_j.demo_2026.01.001.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n" + b"x" * 6000)
            with patch.object(router, "generic_download_one", return_value=(str(pdf_path), "ok", "sd_elsevier")) as download:
                downloaded, remaining, reasons = router.run_generic_round(
                    ["10.1016/j.demo.2026.01.001"], tmp, 9223
                )

        self.assertEqual(downloaded, ["10.1016/j.demo.2026.01.001"])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})
        download.assert_called_once_with(9223, "10.1016/j.demo.2026.01.001", tmp, include_si=False)

    def test_sd_download_strategy_b_uses_timeout_for_article_page_wait(self):
        with patch.object(sd_download, "_extract_pdfft_url", return_value="https://example.com/pdfft?md5=abc") as mock_extract, \
             patch.object(sd_download, "_navigate_and_capture", return_value=b"%PDFdemo") as mock_capture:
            pdf = sd_download._strategy_b(9223, "S0000000000000001", timeout=17)

        self.assertEqual(pdf, b"%PDFdemo")
        mock_extract.assert_called_once_with(9223, "S0000000000000001", render_timeout=17)
        mock_capture.assert_called_once_with(9223, "https://example.com/pdfft?md5=abc", redirect_timeout=17, capture_timeout=20)

    def test_parallel_sd_worker_passes_timeout_overrides_to_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            out_dir.mkdir()
            papers = [("paper_001", "10.1016/j.demo.2026.01.001", "S0000000000000001")]

            with patch.object(parallel_sd, "download_sd_pii", return_value=b"%PDF" + b"x" * 25000) as mock_download:
                parallel_sd.worker("Chrome", 9223, papers, str(out_dir), 9, 21)
                self.assertTrue((out_dir / "paper_001.pdf").exists())

        mock_download.assert_called_once_with(9223, "S0000000000000001", timeout_a=9, timeout_b=21)

    def test_sd_access_probe_uses_current_known_good_pii_sample(self):
        self.assertEqual(cdp_utils._SD_TEST_DOI, "10.1016/j.est.2024.113105")
        self.assertIn("S2352152X24026914", cdp_utils._SD_TEST_URL)
        self.assertTrue(cdp_utils._SD_TEST_URL.endswith("/pdfft"))

    def test_sd_access_probe_unknown_article_page_is_blocked(self):
        tabs = [{
            "id": "tab-1",
            "url": "https://www.sciencedirect.com/science/article/pii/S2352152X24026914",
            "title": "Article page - ScienceDirect",
        }]
        with patch.object(cdp_utils, "check_cdp", return_value=True), \
             patch.object(cdp_utils, "get_cdp_ws_url", return_value="ws://browser"), \
             patch.object(cdp_utils.websocket, "create_connection") as create_connection, \
             patch.object(cdp_utils, "list_tabs", return_value=tabs), \
             patch.object(cdp_utils, "close_tab") as close_tab, \
             patch.object(cdp_utils.time, "sleep", return_value=None):
            ws = create_connection.return_value
            ws.recv.return_value = '{"result":{"targetId":"tab-1"}}'

            status, reason = cdp_utils.check_sd_access(9223)

        self.assertEqual(status, "blocked")
        self.assertIn("pdf probe unknown", reason)
        close_tab.assert_called_with(9223, "tab-1")

    def test_sd_access_probe_pdf_redirect_is_ok(self):
        tabs = [{
            "id": "tab-1",
            "url": "https://pdf.sciencedirectassets.com/demo/main.pdf",
            "title": "main.pdf",
        }]
        with patch.object(cdp_utils, "check_cdp", return_value=True), \
             patch.object(cdp_utils, "get_cdp_ws_url", return_value="ws://browser"), \
             patch.object(cdp_utils.websocket, "create_connection") as create_connection, \
             patch.object(cdp_utils, "list_tabs", return_value=tabs), \
             patch.object(cdp_utils, "close_tab") as close_tab, \
             patch.object(cdp_utils.time, "sleep", return_value=None):
            ws = create_connection.return_value
            ws.recv.return_value = '{"result":{"targetId":"tab-1"}}'

            status, reason = cdp_utils.check_sd_access(9223)

        self.assertEqual((status, reason), ("ok", "pdf_probe_ok"))
        close_tab.assert_called_with(9223, "tab-1")

    def test_sd_download_diagnosis_detects_referencework_and_verification(self):
        tabs = [
            {"id": "ref", "url": "https://www.sciencedirect.com/science/chapter/referencework/abs/pii/B9780323960205000388", "title": "Book chapter - ScienceDirect"},
            {"id": "chk", "url": "https://www.sciencedirect.com/science/article/pii/S0000", "title": "请稍候…"},
        ]
        with patch.object(sd_download, "list_tabs", return_value=tabs):
            ref_state = sd_download._inspect_sd_tab_state(9223, "ref")
            chk_state = sd_download._inspect_sd_tab_state(9223, "chk")

        self.assertEqual(ref_state["kind"], "referencework_abs")
        self.assertEqual(chk_state["kind"], "manual_verification_required")

    def test_console_compat_translates_status_symbols_for_ascii_mode(self):
        with patch.dict("os.environ", {"MORE_PAPER_SYMBOLS": "ascii"}):
            self.assertEqual(console_compat.symbol("ok"), "[OK]")
            self.assertEqual(console_compat.replace_status_symbols("✅ → ❌"), "[OK] -> [FAIL]")

    def test_child_python_env_sets_utf8_backslashreplace(self):
        env = console_compat.configure_child_python_utf8_env({"EXISTING": "1"})

        self.assertEqual(env["EXISTING"], "1")
        self.assertEqual(env["PYTHONIOENCODING"], "utf-8:backslashreplace")

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

    def test_parse_doi_file_reads_one_doi_per_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dois.txt"
            path.write_text("\n".join([
                "# comment",
                "10.1016/j.test.2024.01.001",
                "",
                "10.1007/demo.2024.1",
            ]), encoding="utf-8")

            dois = router.parse_doi_file(str(path))

        self.assertEqual(dois, ["10.1016/j.test.2024.01.001", "10.1007/demo.2024.1"])

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
        self.assertIn("generic", strategies)
        self.assertIn("chinese_cdp", strategies)

    def test_sciencedirect_generic_adapter_downloads_via_sd_pii(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(gpd, "_download_sciencedirect", return_value=(str(Path(tmp) / "paper.pdf"), "ok")) as sd_adapter:
                result_path, status, pub = gpd.download_one(
                    9223, "10.1016/j.demo.2026.01.001", tmp
                )

        self.assertEqual(status, "ok")
        self.assertEqual(pub, "sd_elsevier")
        self.assertTrue(result_path.endswith("paper.pdf"))
        sd_adapter.assert_called_once_with(9223, "10.1016/j.demo.2026.01.001", tmp)

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
            downloaded, remaining, reasons = router.run_generic_round(["10.1007/demo"], "paper-temp", 9223)

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, ["10.1007/demo"])
        self.assertEqual(reasons["10.1007/demo"], "generic_failed")

    def test_generic_round_keeps_manual_required_item_for_rerun(self):
        with patch.object(router, "resolve_publisher", return_value={"strategy": "generic", "_key": "springer", "publisher_domain": "link.springer.com"}), \
             patch.object(router, "generic_download_one", return_value=(None, "manual_required", "springer")):
            downloaded, remaining, reasons = router.run_generic_round(["10.1007/demo"], "paper-temp", 9223)

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, ["10.1007/demo"])
        self.assertEqual(reasons["10.1007/demo"], "manual_confirmation_required")

    def test_english_cdp_prompts_and_retries_first_login_required_failure(self):
        first = ([], ["10.1007/demo", "10.1021/demo"], {
            "10.1007/demo": "manual_confirmation_required",
            "10.1021/demo": "generic_failed",
        })
        second = (["10.1007/demo"], [], {})

        with patch.object(router, "run_generic_round", side_effect=[first, second]) as run_generic, \
             patch.object(router, "show_english_login_gate", return_value=True) as login_gate:
            downloaded, remaining, results, reasons = router.run_english_cdp(
                ["10.1007/demo", "10.1021/demo"], "paper-temp", 9223
            )

        self.assertEqual(downloaded, ["10.1007/demo"])
        self.assertEqual(remaining, ["10.1021/demo"])
        self.assertEqual(reasons, {"10.1021/demo": "generic_failed"})
        login_gate.assert_called_once_with(["10.1007/demo"], skip_sd=False)
        self.assertEqual(run_generic.call_args_list[1].args[0], ["10.1007/demo"])
        self.assertEqual(results[-1]["round"], "Generic CDP (after login)")

    def test_generate_download_log_includes_reason_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "10.1007_demo.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n" + b"x" * 6000)
            log_path = router.generate_download_log(
                tmp,
                ["10.1007/demo", "10.1016/j.demo"],
                [{"round": "Generic CDP", "downloaded": ["10.1007/demo"]}],
                {"10.1016/j.demo": "manual_verification_required"},
            )
            text = Path(log_path).read_text(encoding="utf-8")

        self.assertIn("| # | DOI | Status | Source | Reason | Size | Path |", text)
        self.assertIn("manual_verification_required", text)


if __name__ == "__main__":
    unittest.main()
