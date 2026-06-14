from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from config_registry import (  # noqa: E402
    get_output_template,
    get_source_config,
    is_chinese_source,
    load_source_registry,
    source_label,
    source_requires_cdp,
    source_status_note,
)
from generate_search_report import (  # noqa: E402
    _build_source_routing_table,
    _build_strategy_text,
    build_report,
)
from generic_publisher_downloader import resolve_publisher  # noqa: E402


class ConfigRegistryTest(unittest.TestCase):
    def test_source_registry_reads_core_sources(self):
        registry = load_source_registry()

        for key in ["cnki", "wanfang", "openalex", "crossref", "semantic_scholar"]:
            self.assertIn(key, registry)
            self.assertEqual(get_source_config(key)["key"], key)

        self.assertEqual(source_label("wanfang"), "万方")
        self.assertTrue(is_chinese_source("cnki"))
        self.assertTrue(source_requires_cdp("wanfang"))
        self.assertEqual(get_source_config("cnki")["default_language"], "zh")
        self.assertEqual(source_status_note("semantic_scholar", "429"), "HTTP 429 已跳过")

    def test_missing_config_dir_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = load_source_registry(tmp)
            template = get_output_template("search_report", tmp)

        self.assertEqual(registry["openalex"]["report_label"], "OpenAlex")
        self.assertEqual(registry["cnki"]["default_language"], "zh")
        self.assertEqual(template["title"], "文献检索报告")

    def test_output_template_metadata_is_available(self):
        template = get_output_template("search_report")
        self.assertEqual(template["title"], "文献检索报告")
        self.assertEqual(template["default_filename"], "检索报告.md")
        self.assertIn("检索概览", template["sections"])

    def test_provider_config_still_matches_router_resolution(self):
        sd = resolve_publisher("10.1016/j.test.2024.01.001")
        ieee = resolve_publisher("10.1109/TEST.2024.123")
        mdpi = resolve_publisher("10.3390/test123")

        self.assertEqual(sd["strategy"], "sd_cdp")
        self.assertEqual(sd["provider_label"], "ScienceDirect / Elsevier")
        self.assertEqual(ieee["strategy"], "generic")
        self.assertEqual(ieee["provider_label"], "IEEE Xplore")
        self.assertEqual(mdpi["strategy"], "skip")
        self.assertTrue(mdpi["manual_required"])

    def test_generate_search_report_uses_registry_labels(self):
        meta = {
            "source_status": {
                "openalex": "ok",
                "crossref": "ok",
                "semantic_scholar": "429",
                "cnki": "carsi_logged_in",
                "wanfang": "attempted_failed",
            },
            "wanfang_fail_reason": "登录失败",
        }

        strategy = _build_strategy_text(meta)
        table = "\n".join(_build_source_routing_table(meta, "standard"))

        self.assertIn("OpenAlex + Crossref", strategy)
        self.assertIn("Semantic Scholar HTTP 429 已跳过", strategy)
        self.assertIn("万方 已尝试但登录失败", strategy)
        self.assertIn("| L1 (中) | CNKI |", table)
        self.assertIn("| L2 (中) | 万方 |", table)
        self.assertIn("CARSI 登录", table)

    def test_report_title_falls_through_template_metadata(self):
        rows = [{
            "doi": "10.5555/demo",
            "title": "Demo",
            "year": "2024",
            "source": "openalex",
            "tier": "T1",
            "score": "22",
        }]
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "检索文献表.md"
            md_path.write_text("检索日期: 2026-06-14\n", encoding="utf-8")
            report = build_report(rows, str(md_path), metadata={"source_status": {"openalex": "ok"}})
        self.assertTrue(report.startswith("# 文献检索报告"))
        self.assertIn("OpenAlex", report)

    def test_cnki_wanfang_regression_rules_remain_documented(self):
        step5 = (ROOT / "agents" / "step_5_download.md").read_text(encoding="utf-8")
        search = (ROOT / "scripts" / "search_by_topic.py").read_text(encoding="utf-8")
        router = (ROOT / "scripts" / "unified_download_router.py").read_text(encoding="utf-8")

        self.assertIn("默认串行可靠", step5)
        self.assertIn("language='zh'", search)
        self.assertIn("CHINESE_PUBLISHERS = {\"cnki\", \"wanfang\"}", router)


if __name__ == "__main__":
    unittest.main()
