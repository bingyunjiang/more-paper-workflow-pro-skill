import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from search_by_topic import _effective_hits, build_query, deduplicate, search_crossref, search_openalex, verify_search_results  # noqa: E402


class _Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class Step4SearchExecutionQualityTest(unittest.TestCase):
    @patch("search_by_topic.urllib.request.urlopen")
    def test_openalex_receives_strategy_filter_and_sort(self, urlopen):
        urlopen.return_value = _Response({"results": []})
        search_openalex("thermal management", use_cache=False, query_params={
            "search": "thermal management", "filter": "title.search:thermal", "sort": "cited_by_count:desc",
        })
        url = urlopen.call_args.args[0].full_url
        self.assertIn("sort=cited_by_count%3Adesc", url)
        self.assertIn("filter=title.search%3Athermal", url)

    @patch("search_by_topic.urllib.request.urlopen")
    def test_crossref_receives_strategy_sort(self, urlopen):
        urlopen.return_value = _Response({"message": {"items": []}})
        search_crossref("thermal management", use_cache=False, query_params={
            "query.title": "thermal management", "sort": "published", "order": "desc",
        })
        self.assertIn("sort=published", urlopen.call_args.args[0].full_url)

    def test_source_specific_strategy_compilation(self):
        blocks = [{"concept": "thermal management", "synonyms": []}]
        self.assertEqual(build_query(blocks, "crossref", "recent")["sort"], "published")
        self.assertEqual(build_query(blocks, "crossref", "cited")["sort"], "is-referenced-by-count")
        self.assertTrue(build_query(blocks, "semantic_scholar", "recent")["strategy_degraded"])

    def test_effective_hits_use_deduplicated_relevant_identified_records(self):
        records = [
            {"doi": "10.1/a", "title": "Thermal management", "source": "openalex"},
            {"doi": "10.1/a", "title": "Thermal management", "source": "crossref"},
            {"doi": "10.1/b", "title": "Unrelated education", "source": "openalex"},
            {"title": "Thermal management without identifier", "source": "unknown"},
        ]
        self.assertEqual(len(_effective_hits(records, ["thermal"])), 1)

    def test_deduplicate_preserves_discovered_and_metadata_sources(self):
        records = deduplicate([
            {"doi": "10.1/a", "title": "A", "source": "crossref"},
            {"doi": "10.1/a", "title": "A", "abstract": "richer abstract", "source": "openalex"},
        ])
        self.assertEqual(set(records[0]["discovered_sources"]), {"crossref", "openalex"})
        self.assertEqual(records[0]["metadata_sources"]["abstract"], "openalex")

    def test_metadata_verification_distinguishes_states(self):
        responses = {
            "10.1/good": (True, {"title": "Thermal management method"}),
            "10.1/bad": (True, {"title": "Completely unrelated education"}),
            "10.1/down": (False, {}),
        }
        records = [{"doi": doi, "title": "Thermal management method", "source": "openalex"} for doi in responses]
        verify_search_results(records, verifier=lambda doi: responses[doi])
        self.assertEqual(records[0]["verification_status"], "VERIFIED")
        self.assertEqual(records[1]["warn_class"], "metadata_mismatch")
        self.assertEqual(records[2]["warn_class"], "doi_verification_unavailable")


if __name__ == "__main__":
    unittest.main()
