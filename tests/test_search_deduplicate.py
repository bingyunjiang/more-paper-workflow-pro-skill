import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from search_by_topic import deduplicate  # noqa: E402


class SearchDeduplicateTest(unittest.TestCase):
    def test_english_records_deduplicate_by_doi(self):
        rows = [
            {"source": "openalex", "doi": "10.1/demo", "title": "A", "authors": ["Smith, John"]},
            {"source": "crossref", "doi": "https://doi.org/10.1/demo", "title": "A", "authors": ["Smith, John", "Li, Ming"], "abstract": "x"},
        ]
        deduped = deduplicate(rows)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(len(deduped[0]["authors"]), 2)
        self.assertEqual(deduped[0]["abstract"], "x")

    def test_chinese_records_deduplicate_by_author_and_title(self):
        rows = [
            {"source": "cnki", "doi": "cnki.abc", "title": "多目标拓扑优化蛛网型液冷板的散热特性", "authors": ["刘欢", "郑焱"], "abstract": ""},
            {"source": "wanfang", "doi": "wanfang.xyz", "title": "多目标拓扑优化蛛网型液冷板的散热特性", "authors": ["刘欢", "郑焱"], "abstract": "摘要"},
        ]
        deduped = deduplicate(rows)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["abstract"], "摘要")

