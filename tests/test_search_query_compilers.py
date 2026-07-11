import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.search_query_compilers import compile_source_query
from scripts.search_by_topic import SOURCE_FUNCTIONS, search_semantic_scholar_bulk


BLOCKS = [
    {"name": "object", "terms": ["cold plate", "liquid cooling"]},
    {"name": "method", "terms": ["topology optimization", "shape optimization"]},
]
EXCLUSIONS = ["phase change material"]


class SearchQueryCompilerTest(unittest.TestCase):
    def test_capability_registry_covers_every_compiler(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "config" / "search_source_capabilities.json").read_text(encoding="utf-8"))
        expected = {"openalex", "crossref", "semantic_scholar", "semantic_scholar_bulk", "pubmed", "arxiv", "cnki", "wanfang"}
        self.assertTrue(expected.issubset(registry["sources"]))
        self.assertEqual(registry["verified_at"], "2026-07-11")

    def test_openalex_preserves_boolean_semantics(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "openalex")
        self.assertEqual(result["compile_status"], "exact")
        self.assertIn('("cold plate" OR "liquid cooling")', result["query"])
        self.assertIn(" NOT ", result["query"])
        self.assertFalse(result["post_filter_required"])

    def test_crossref_is_explicitly_degraded(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "crossref")
        self.assertEqual(result["compile_status"], "degraded")
        self.assertTrue(result["post_filter_required"])
        self.assertNotIn(" AND ", result["query"])
        self.assertIn("between_block_and", result["dropped_semantics"])

    def test_semantic_scholar_regular_search_has_no_special_syntax(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "semantic_scholar")
        self.assertEqual(result["compile_status"], "degraded")
        self.assertNotIn(" OR ", result["query"])
        self.assertNotIn(" NOT ", result["query"])
        self.assertEqual(result["request"]["endpoint"], "/paper/search")

    def test_semantic_scholar_bulk_uses_documented_operators(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "semantic_scholar_bulk")
        self.assertEqual(result["compile_status"], "exact")
        self.assertIn(" | ", result["query"])
        self.assertIn(" + ", result["query"])
        self.assertIn('-"phase change material"', result["query"])

    def test_pubmed_uses_field_tags(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "pubmed")
        self.assertEqual(result["compile_status"], "exact")
        self.assertIn('"cold plate"[tiab]', result["query"])
        self.assertIn(" NOT ", result["query"])

    def test_arxiv_uses_andnot_and_field_prefix(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "arxiv")
        self.assertEqual(result["compile_status"], "exact")
        self.assertIn('all:"cold plate"', result["query"])
        self.assertIn(" ANDNOT ", result["query"])

    def test_chinese_web_adapters_are_not_claimed_exact(self):
        for source in ("cnki", "wanfang"):
            result = compile_source_query(BLOCKS, EXCLUSIONS, source)
            self.assertEqual(result["compile_status"], "manual_required")

    def test_unknown_source_is_invalid(self):
        result = compile_source_query(BLOCKS, EXCLUSIONS, "unknown")
        self.assertEqual(result["compile_status"], "invalid")

    def test_semantic_bulk_executor_is_registered_and_parses_results(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"data": [{
                    "title": "Cold plate optimization", "year": 2025, "venue": "Demo",
                    "authors": [{"name": "Author"}], "externalIds": {"DOI": "10.1/demo"},
                    "citationCount": 3, "abstract": "demo",
                }]}).encode()

        with patch("scripts.search_by_topic.urllib.request.urlopen", return_value=Response()), patch(
            "scripts.search_by_topic._throttle_semantic_scholar_if_anonymous"
        ):
            records = search_semantic_scholar_bulk("cold + plate", limit=5, use_cache=False)
        self.assertIn("semantic_scholar_bulk", SOURCE_FUNCTIONS)
        self.assertEqual(records[0]["doi"], "10.1/demo")
        self.assertEqual(records[0]["source"], "semantic_scholar_bulk")


if __name__ == "__main__":
    unittest.main()
