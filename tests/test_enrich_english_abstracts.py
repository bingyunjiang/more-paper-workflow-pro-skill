import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from enrich_english_abstracts import (  # noqa: E402
    _reconstruct_abstract,
    _strip_jats,
    should_enrich,
)


class EnrichEnglishAbstractsTest(unittest.TestCase):
    def test_reconstruct_openalex_abstract(self):
        abstract = _reconstruct_abstract({"cold": [0], "plate": [1], "optimization": [2]})
        self.assertEqual(abstract, "cold plate optimization")

    def test_strip_jats_tags(self):
        self.assertEqual(_strip_jats("<jats:p>Hello <b>world</b></jats:p>"), "Hello world")

    def test_should_enrich_only_english_t1_t2_without_abstract(self):
        yes = {
            "source": "openalex",
            "paper_tier": "T2",
            "abstract": "",
        }
        no_cn = {
            "source": "cnki",
            "paper_tier": "T2",
            "abstract": "",
        }
        no_t3 = {
            "source": "crossref",
            "paper_tier": "T3",
            "abstract": "",
        }
        no_abs_needed = {
            "source": "crossref",
            "paper_tier": "T1",
            "abstract": "already here",
        }
        self.assertTrue(should_enrich(yes))
        self.assertFalse(should_enrich(no_cn))
        self.assertFalse(should_enrich(no_t3))
        self.assertFalse(should_enrich(no_abs_needed))


if __name__ == "__main__":
    unittest.main()
