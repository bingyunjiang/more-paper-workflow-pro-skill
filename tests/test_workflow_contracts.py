import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_contracts import (  # noqa: E402
    DownloadManifestItem,
    SearchResultRecord,
    as_chinese_papers,
    dois_from_download_items,
    load_search_records,
    normalize_doi,
    stable_source_id,
    write_workflow_json,
)


class WorkflowContractsTest(unittest.TestCase):
    def test_normalize_doi_variants(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1016/j.test.2024.01.001."),
            "10.1016/j.test.2024.01.001",
        )
        self.assertEqual(normalize_doi("doi:10.1109/TEST.2024.123"), "10.1109/TEST.2024.123")

    def test_chinese_article_url_only_routes_to_manifest(self):
        record = SearchResultRecord.from_search_result({
            "title": "薄壁管弯曲回弹研究",
            "source": "wanfang",
            "article_url": "https://www.wanfangdata.com.cn/details/detail.do?_type=perio&id=test",
            "verification_status": "VERIFIED",
        })

        self.assertTrue(record.source_id.startswith("wanfang."))
        self.assertEqual(record.download_hint, "chinese_article_url")

        item = DownloadManifestItem.from_search_record(record)
        self.assertEqual(item.status, "ready")
        self.assertTrue(item.article_url.startswith("https://www.wanfangdata.com.cn/"))

    def test_warn_reject_fields_preserved(self):
        record = SearchResultRecord.from_search_result({
            "title": "Questionable paper",
            "source": "crossref",
            "doi": "10.1234/example",
            "verification_status": "WARN",
            "verification_confidence": "low",
            "warn_class": "metadata_mismatch",
        })

        self.assertEqual(record.verification_status, "WARN")
        self.assertEqual(record.verification_confidence, "low")
        self.assertEqual(record.warn_class, "metadata_mismatch")

    def test_workflow_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            records = [
                SearchResultRecord.from_search_result({
                    "title": "A DOI paper",
                    "source": "openalex",
                    "doi": "https://doi.org/10.5555/demo",
                    "year": "2024",
                }),
                SearchResultRecord.from_search_result({
                    "title": "A CNKI paper",
                    "source": "cnki",
                    "article_url": "https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=demo",
                }),
            ]

            write_workflow_json(path, records, {"query": "demo"})
            data = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_search_records(path)

        self.assertEqual(data["schema_version"], "workflow-contracts.v1")
        self.assertEqual(data["artifact_type"], "search_results")
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].doi, "10.5555/demo")
        self.assertTrue(loaded[1].source_id.startswith("cnki."))

    def test_download_item_views(self):
        items = [
            DownloadManifestItem(title="English", doi="10.5555/demo", source="openalex"),
            DownloadManifestItem(
                title="中文",
                source="cnki",
                source_id=stable_source_id("cnki", "中文"),
                article_url="https://kns.cnki.net/kcms/detail/detail.aspx?filename=demo",
            ),
        ]

        self.assertEqual(dois_from_download_items(items), ["10.5555/demo"])
        chinese = as_chinese_papers(items)
        self.assertEqual(len(chinese), 1)
        self.assertEqual(chinese[0]["source"], "cnki")


if __name__ == "__main__":
    unittest.main()
