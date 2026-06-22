from pathlib import Path
import io
import json
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
    def _valid_pdf_bytes(self):
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Page >>\nendobj\n" + b"x" * 6000

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

    def test_english_pipeline_old_doi_scihub_success_skips_oa_and_cdp(self):
        with patch.object(router, "run_scihub_round", return_value=(["10.1016/j.demo.2020.01.001"], [])) as scihub, \
             patch.object(router, "run_oa_fast_round") as oa_fast, \
             patch.object(router, "run_generic_round") as generic:
            downloaded, remaining, results, reasons = router.run_english_pipeline(
                ["10.1016/j.demo.2020.01.001"], "paper-temp", 9223
            )

        self.assertEqual(downloaded, ["10.1016/j.demo.2020.01.001"])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})
        self.assertEqual(results, [{"round": "Sci-Hub", "downloaded": ["10.1016/j.demo.2020.01.001"]}])
        scihub.assert_called_once()
        oa_fast.assert_not_called()
        generic.assert_not_called()

    def test_english_pipeline_old_doi_scihub_failure_then_oa_success_skips_cdp(self):
        doi = "10.1016/j.demo.2020.01.001"
        with patch.object(router, "run_scihub_round", return_value=([], [doi])) as scihub, \
             patch.object(router, "run_oa_fast_round", return_value=([doi], [], {})) as oa_fast, \
             patch.object(router, "run_generic_round") as generic:
            downloaded, remaining, results, reasons = router.run_english_pipeline(
                [doi], "paper-temp", 9223
            )

        self.assertEqual(downloaded, [doi])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})
        self.assertEqual(results[-1]["round"], "OA fast (public_pdf_verified)")
        scihub.assert_called_once()
        oa_fast.assert_called_once()
        generic.assert_not_called()

    def test_english_pipeline_2024_doi_skips_scihub_and_starts_oa_fast(self):
        doi = "10.1016/j.demo.2024.01.001"
        with patch.object(router, "run_scihub_round") as scihub, \
             patch.object(router, "run_oa_fast_round", return_value=([doi], [], {})) as oa_fast, \
             patch.object(router, "run_generic_round") as generic:
            downloaded, remaining, results, reasons = router.run_english_pipeline(
                [doi], "paper-temp", 9223
            )

        self.assertEqual(downloaded, [doi])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})
        scihub.assert_not_called()
        oa_fast.assert_called_once()
        generic.assert_not_called()

    def test_english_pipeline_skip_scihub_sends_old_doi_to_oa_fast(self):
        doi = "10.1016/j.demo.2020.01.001"
        with patch.object(router, "run_scihub_round") as scihub, \
             patch.object(router, "run_oa_fast_round", return_value=([doi], [], {})) as oa_fast:
            downloaded, remaining, results, reasons = router.run_english_pipeline(
                [doi], "paper-temp", 9223, skip_scihub=True
            )

        self.assertEqual(downloaded, [doi])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})
        scihub.assert_not_called()
        oa_fast.assert_called_once()

    def test_english_pipeline_skip_oa_fast_goes_to_generic_cdp(self):
        doi = "10.1016/j.demo.2024.01.001"
        with patch.object(router, "run_scihub_round") as scihub, \
             patch.object(router, "run_oa_fast_round") as oa_fast, \
             patch.object(router, "run_generic_round", return_value=([doi], [], {})) as generic:
            downloaded, remaining, results, reasons = router.run_english_pipeline(
                [doi], "paper-temp", 9223, skip_oa_fast=True
            )

        self.assertEqual(downloaded, [doi])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})
        scihub.assert_not_called()
        oa_fast.assert_not_called()
        generic.assert_called_once()

    def test_oa_fast_invalid_html_candidate_continues_to_cdp(self):
        doi = "10.1016/j.demo.2024.01.001"
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(router, "_fetch_url_bytes", return_value=(b"<html>not a pdf</html>" + b"x" * 6000, "text/html")):
            downloaded, remaining, reasons = router.run_oa_fast_round(
                [doi],
                tmp,
                oa_hints={doi: {"oa_pdf_url": "https://example.org/demo.pdf"}},
                use_resolver=False,
            )

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, [doi])
        self.assertEqual(reasons[doi], "invalid_pdf_candidate")

    def test_oa_fast_valid_public_pdf_downloads_and_marks_verified(self):
        doi = "10.1016/j.demo.2024.01.001"
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(router, "_fetch_url_bytes", return_value=(self._valid_pdf_bytes(), "application/pdf")):
            downloaded, remaining, reasons = router.run_oa_fast_round(
                [doi],
                tmp,
                oa_hints={doi: {"oa_pdf_url": "https://example.org/demo.pdf"}},
                use_resolver=False,
            )
            pdf_path = Path(tmp) / "10.1016_j.demo.2024.01.001.pdf"

            self.assertTrue(pdf_path.exists())

        self.assertEqual(downloaded, [doi])
        self.assertEqual(remaining, [])
        self.assertEqual(reasons, {})

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

    def test_parse_bibtex_chinese_papers_extracts_cnki_doi_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.bib"
            path.write_text("""
@article{english,
  title = {Battery Thermal Management},
  doi = {10.1016/j.est.2025.117285},
  langid = {english}
}

@article{cnki,
  title = {电动汽车充电桩电源模块热仿真分析},
  doi = {10.16638/j.cnki.1671-7988.2022.011.001},
  langid = {chinese}
}
""", encoding="utf-8")

            papers = router.parse_bibtex_chinese_papers(str(path))

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["source"], "cnki")
        self.assertEqual(papers[0]["doi"], "10.16638/j.cnki.1671-7988.2022.011.001")

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

    def test_show_english_login_gate_noninteractive_returns_none(self):
        self.assertIsNone(
            router.show_english_login_gate(
                ["10.1016/j.test.2024.01.001"],
                interactive=False,
            )
        )

    def test_show_english_login_gate_eoferror_returns_none(self):
        with patch("builtins.input", side_effect=EOFError):
            self.assertIsNone(router.show_english_login_gate(["10.1016/j.test.2024.01.001"]))

    def test_ensure_cdp_running_reuses_existing_browser(self):
        with patch.object(router, "check_cdp", return_value=True), \
             patch.object(router, "cdp_browser_matches", return_value=True):
            self.assertTrue(router.ensure_cdp_running(9223))

    def test_ensure_cdp_running_auto_starts_browser(self):
        with patch.object(router, "check_cdp", side_effect=[False, True]), \
             patch.object(router, "cdp_browser_matches", return_value=True), \
             patch.object(router, "start_persistent_cdp_browser") as starter:
            self.assertTrue(router.ensure_cdp_running(9223))
        starter.assert_called_once()

    def test_ensure_cdp_running_restarts_when_existing_browser_mismatches(self):
        with patch.object(router, "check_cdp", side_effect=[True, True]), \
             patch.object(router, "cdp_browser_matches", side_effect=[False, True]), \
             patch.object(router, "get_cdp_browser_product", return_value="Microsoft Edge/125.0"), \
             patch.object(router, "start_persistent_cdp_browser") as starter:
            self.assertTrue(router.ensure_cdp_running(9223, browser="chrome"))

        starter.assert_called_once_with(
            port=9223,
            browser="chrome",
            urls=["https://www.sciencedirect.com/"],
        )

    def test_cdp_browser_matches_distinguishes_chrome_from_edge(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def read(self):
                return self.payload.encode("utf-8")

        with patch.object(cdp_utils.urllib.request, "urlopen", return_value=FakeResponse('{"Browser":"Microsoft Edge/125.0"}')):
            self.assertTrue(cdp_utils.cdp_browser_matches(9223, "edge"))
            self.assertFalse(cdp_utils.cdp_browser_matches(9223, "chrome"))

        with patch.object(cdp_utils.urllib.request, "urlopen", return_value=FakeResponse('{"Browser":"Chrome/125.0"}')):
            self.assertTrue(cdp_utils.cdp_browser_matches(9223, "chrome"))
            self.assertFalse(cdp_utils.cdp_browser_matches(9223, "edge"))

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

    def test_sciencedirect_generic_adapter_downloads_via_generic_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(gpd, "_navigate_and_capture_pdf", return_value=b"%PDF" + b"x" * 25000) as capture, \
                 patch("batch_resolve_pii._resolve_pii_from_crossref", return_value="S0000000000000001"):
                result_path, status = gpd._download_sciencedirect(
                    9223, "10.1016/j.demo.2026.01.001", tmp
                )

            self.assertEqual(status, "ok")
            self.assertTrue(Path(result_path).exists())
            capture.assert_called_once_with(
                9223,
                "https://www.sciencedirect.com/science/article/pii/S0000000000000001/pdfft",
                referrer="https://www.sciencedirect.com/science/article/pii/S0000000000000001",
                timeout=gpd.DEFAULT_TIMEOUT,
            )

    def test_sciencedirect_article_page_only_prompts_login_retry(self):
        with patch.object(gpd, "_navigate_and_capture_pdf", return_value=None), \
             patch("batch_resolve_pii._resolve_pii_from_crossref", return_value="S0000000000000001"), \
             patch("sd_download.diagnose_sd_pii", return_value={"kind": "article_page_only"}):
            result_path, status = gpd._download_sciencedirect(
                9223, "10.1016/j.demo.2026.01.001", "paper-temp"
            )

        self.assertIsNone(result_path)
        self.assertEqual(status, "pdf_probe_unknown")

    def test_sciencedirect_download_one_routes_through_generic_adapter(self):
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

        self.assertEqual(result, "LOGIN_REQUIRED")
        close_tab.assert_not_called()

    def test_download_one_returns_manual_required_for_login_wall(self):
        with patch.object(gpd, "resolve_publisher", return_value={"strategy": "generic", "_key": "springer"}), \
             patch.object(gpd, "_strategy_direct_pdf", return_value=None), \
             patch.object(gpd, "_strategy_article_page", return_value="MANUAL_REQUIRED"):
            path, status, pub = gpd.download_one(9223, "10.1007/demo", "paper-temp")

        self.assertIsNone(path)
        self.assertEqual(status, "manual_required")
        self.assertEqual(pub, "springer")

    def test_download_one_uses_ieee_generic_fallback_after_a_b_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(gpd, "resolve_publisher", return_value={"strategy": "generic", "_key": "ieee"}), \
                 patch.object(gpd, "_strategy_direct_pdf", return_value=None), \
                 patch.object(gpd, "_strategy_article_page", return_value=None), \
                 patch.object(gpd, "_download_ieee_via_generic_fallback", return_value=str(Path(tmp) / "ieee.pdf")) as fallback:
                path, status, pub = gpd.download_one(9223, "10.1109/tvt.2018.2880138", tmp)

        self.assertEqual(status, "ok")
        self.assertEqual(pub, "ieee")
        self.assertTrue(path.endswith("ieee.pdf"))
        fallback.assert_called_once()

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
        self.assertEqual(reasons["10.1007/demo"], "manual_required")

    def test_generic_round_keeps_captcha_reason_for_rerun(self):
        with patch.object(router, "resolve_publisher", return_value={"strategy": "generic", "_key": "wiley", "publisher_domain": "onlinelibrary.wiley.com"}), \
             patch.object(router, "generic_download_one", return_value=(None, "captcha_required", "wiley")):
            downloaded, remaining, reasons = router.run_generic_round(["10.1002/demo"], "paper-temp", 9223)

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, ["10.1002/demo"])
        self.assertEqual(reasons["10.1002/demo"], "captcha_required")

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
        login_gate.assert_called_once_with(["10.1007/demo"], skip_sd=False, interactive=False)
        self.assertEqual(run_generic.call_args_list[1].args[0], ["10.1007/demo"])
        self.assertEqual(results[-1]["round"], "Generic CDP (after login)")

    def test_english_cdp_noninteractive_writes_login_checkpoint_and_marks_pending(self):
        first = ([], ["10.1007/demo", "10.1021/demo"], {
            "10.1007/demo": "manual_confirmation_required",
            "10.1021/demo": "generic_failed",
        })

        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(router, "run_generic_round", return_value=first), \
             patch.object(router, "show_english_login_gate", return_value=None):
            downloaded, remaining, results, reasons = router.run_english_cdp(
                ["10.1007/demo", "10.1021/demo"], tmp, 9223
            )
            checkpoint = json.loads((Path(tmp) / "login_checkpoint.json").read_text(encoding="utf-8"))

        self.assertEqual(downloaded, [])
        self.assertEqual(remaining, ["10.1007/demo", "10.1021/demo"])
        self.assertEqual(reasons["10.1007/demo"], "pending_user_login")
        self.assertEqual(reasons["10.1021/demo"], "generic_failed")
        self.assertEqual(checkpoint["status"], "pending_user_login")
        self.assertEqual(checkpoint["items"][0]["doi"], "10.1007/demo")
        self.assertEqual(results, [{"round": "Generic CDP", "downloaded": []}])

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

    def test_write_failed_doi_sidecar_writes_structured_retry_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            sidecar = router.write_failed_doi_sidecar(
                tmp,
                ["10.1002/er.7775"],
                {"10.1002/er.7775": "captcha_required"},
            )
            data = json.loads(Path(sidecar).read_text(encoding="utf-8"))

        self.assertEqual(data["items"][0]["doi"], "10.1002/er.7775")
        self.assertEqual(data["items"][0]["failure_reason"], "captcha_required")
        self.assertIn("--papers", data["items"][0]["retry_hint"])

    def test_write_login_checkpoint_writes_pending_login_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = router.write_login_checkpoint(
                tmp,
                stage="english_cdp_retry",
                dois=["10.1016/j.ecmx.2026.101960"],
                failure_reasons={"10.1016/j.ecmx.2026.101960": "institution_login_required"},
            )
            data = json.loads(Path(checkpoint).read_text(encoding="utf-8"))

        self.assertEqual(data["status"], "pending_user_login")
        self.assertEqual(data["items"][0]["failure_reason"], "institution_login_required")
        self.assertIn("--resume-login-checkpoint", data["rerun_hint"])

    def test_resume_from_login_checkpoint_retries_only_pending_english_dois(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = {
                "checkpoint_type": "publisher_login",
                "status": "pending_user_login",
                "stage": "english_cdp_retry",
                "items": [
                    {"doi": "10.1007/demo", "failure_reason": "pending_user_login"},
                    {"doi": "10.1016/j.demo.2026.01.001", "failure_reason": "pending_user_login"},
                ],
            }
            checkpoint_path = Path(tmp) / "login_checkpoint.json"
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            resumed = (["10.1007/demo"], ["10.1016/j.demo.2026.01.001"], {
                "10.1016/j.demo.2026.01.001": "generic_failed",
            })

            with patch.object(router, "run_generic_round", return_value=resumed) as run_generic:
                downloaded, remaining, results, reasons = router.resume_from_login_checkpoint(
                    str(checkpoint_path), tmp, 9223
                )

        self.assertEqual(downloaded, ["10.1007/demo"])
        self.assertEqual(remaining, ["10.1016/j.demo.2026.01.001"])
        self.assertEqual(reasons, {"10.1016/j.demo.2026.01.001": "generic_failed"})
        self.assertEqual(results[-1]["round"], "Generic CDP (resume login checkpoint)")
        run_generic.assert_called_once_with(
            ["10.1007/demo", "10.1016/j.demo.2026.01.001"], tmp, 9223, include_si=False
        )

    def test_check_all_sessions_reports_weak_cookie_probe(self):
        with patch.object(router, "_PUBLISHER_CONFIGS", {"sd_elsevier": {"publisher_domain": "www.sciencedirect.com", "strategy": "generic", "_key": "sd_elsevier"}}), \
             patch.object(router, "describe_publisher_session", return_value={
                 "publisher": "sd_elsevier",
                 "domain": "www.sciencedirect.com",
                 "strategy": "generic",
                 "has_session": False,
                 "cookie_count": 0,
                 "signal_strength": "pdf_probe",
                 "probe_status": "blocked",
                 "probe_reason": "pdf probe unknown",
             }), \
             patch.object(router, "check_cdp", return_value=True), \
             patch("sys.stdout", new_callable=io.StringIO) as stdout:
            router.check_all_sessions(9223)

        text = stdout.getvalue()
        self.assertIn("pdf_probe (0)", text)
        self.assertIn("weak signal", text.lower() if "weak signal" in text.lower() else "cookie count is a weak signal")
        self.assertIn("需要先人工登录/验证", text)

    def test_check_all_sessions_prints_three_state_readiness_labels(self):
        signals = iter([
            {
                "publisher": "wiley",
                "domain": "onlinelibrary.wiley.com",
                "strategy": "generic",
                "has_session": True,
                "cookie_count": 0,
                "signal_strength": "article_probe",
                "probe_status": "ok",
                "probe_reason": "pdf_link_present",
            },
            {
                "publisher": "springer",
                "domain": "link.springer.com",
                "strategy": "generic",
                "has_session": False,
                "cookie_count": 0,
                "signal_strength": "weak_cookie_probe",
                "probe_status": "unknown",
                "probe_reason": "cookie probe only",
            },
        ])
        with patch.object(router, "_PUBLISHER_CONFIGS", {
            "wiley": {"publisher_domain": "onlinelibrary.wiley.com", "strategy": "generic", "_key": "wiley"},
            "springer": {"publisher_domain": "link.springer.com", "strategy": "generic", "_key": "springer"},
        }), \
             patch.object(router, "describe_publisher_session", side_effect=lambda port, cfg: next(signals)), \
             patch.object(router, "check_cdp", return_value=True), \
             patch("sys.stdout", new_callable=io.StringIO) as stdout:
            router.check_all_sessions(9223)

        text = stdout.getvalue()
        self.assertIn("可直接尝试下载", text)
        self.assertIn("信号不足，需实际下载验证", text)

    def test_check_wiley_access_reports_pdf_link_present(self):
        publisher = {
            "_key": "wiley",
            "selectors": ['a[href*="pdfdirect"]'],
            "publisher_domain": "onlinelibrary.wiley.com",
        }
        with patch.object(gpd, "check_cdp", return_value=True), \
             patch.object(gpd, "create_tab", return_value=(None, "tab-1")), \
             patch.object(gpd, "_detect_access_barrier", return_value=(None, "")), \
             patch.object(gpd, "_extract_pdf_url_from_dom", return_value="https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/ente.202301205"), \
             patch.object(gpd, "close_tab"), \
             patch.object(gpd.time, "sleep", return_value=None):
            status, reason = gpd.check_wiley_access(9223, publisher)

        self.assertEqual(status, "ok")
        self.assertIn("pdf_link_present", reason)

    def test_describe_publisher_session_uses_wiley_article_probe(self):
        publisher = {
            "_key": "wiley",
            "publisher_domain": "onlinelibrary.wiley.com",
            "strategy": "generic",
            "selectors": ['a[href*="pdfdirect"]'],
        }
        with patch.object(gpd, "check_publisher_session", return_value=(False, 0)), \
             patch.object(gpd, "check_wiley_access", return_value=("ok", "pdf_link_present")):
            signal = gpd.describe_publisher_session(9223, publisher)

        self.assertEqual(signal["signal_strength"], "article_probe")
        self.assertEqual(signal["probe_status"], "ok")
        self.assertTrue(signal["has_session"])


if __name__ == "__main__":
    unittest.main()
