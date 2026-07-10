import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from search_by_topic import score_results  # noqa: E402


class SearchScoringTest(unittest.TestCase):
    @patch("search_by_topic.time.gmtime")
    def test_scoring_uses_documented_weights_and_exposes_uncertainty(self, gmtime):
        gmtime.return_value.tm_year = 2026
        records = [{
            "doi": "10.1/demo",
            "title": "Cold plate topology optimization",
            "abstract": "Experimental validation against a baseline demonstrates topology performance.",
            "venue": "Journal of Thermal Engineering",
            "source": "openalex",
            "year": 2024,
            "citations": 30,
        }]
        score_results(records, ["cold plate", "topology optimization"])
        record = records[0]

        self.assertEqual(record["_score_weights"]["topic_match"], 0.35)
        self.assertEqual(set(record["_score_dimensions"]), {
            "topic_match", "method_rigor", "source_quality", "recency", "impact",
        })
        self.assertEqual(record["_score_confidence"], "high")
        self.assertGreaterEqual(record["_weighted_score"], 20)
        self.assertEqual(record["_tier"], "Tier 1")

    def test_missing_abstract_cannot_become_high_confidence_tier1(self):
        records = [{
            "doi": "10.1/missing",
            "title": "Cold plate topology optimization",
            "abstract": "",
            "venue": "Known Venue",
            "source": "crossref",
            "year": 2025,
            "citations": 100,
        }]
        score_results(records, ["cold plate", "topology optimization"])
        record = records[0]

        self.assertIn("no_abstract_uncertain", record["_uncertainty_flags"])
        self.assertIn("method_rigor_unavailable", record["_uncertainty_flags"])
        self.assertNotEqual(record["_tier"], "Tier 1")


if __name__ == "__main__":
    unittest.main()
