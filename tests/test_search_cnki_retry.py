import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import search_by_topic as topic  # noqa: E402


class SearchCnkiRetryTest(unittest.TestCase):
    @patch.object(topic, "_cache_get", return_value=None)
    @patch.object(topic, "_cache_set")
    @patch.object(topic.time, "sleep")
    def test_search_cnki_retries_until_success(self, sleep_mock, cache_set_mock, _cache_get_mock):
        with patch.object(topic, "_try_cnki_cdp", side_effect=[[], [], [{"title": "充电桩", "doi": "cnki.demo"}]]):
            results = topic.search_cnki("充电桩", limit=10, use_cache=False, language="zh")

        self.assertEqual(len(results), 1)
        self.assertEqual(sleep_mock.call_count, 2)
        cache_set_mock.assert_not_called()

    @patch.object(topic, "_cache_get", return_value=None)
    @patch.object(topic, "_cache_set")
    @patch.object(topic.time, "sleep")
    def test_search_cnki_stops_after_three_empty_attempts(self, sleep_mock, cache_set_mock, _cache_get_mock):
        with patch.object(topic, "_try_cnki_cdp", side_effect=[[], [], []]) as try_mock:
            results = topic.search_cnki("充电桩", limit=10, use_cache=False, language="zh")

        self.assertEqual(results, [])
        self.assertEqual(try_mock.call_count, topic.CNKI_CDP_MAX_ATTEMPTS)
        self.assertEqual(sleep_mock.call_count, topic.CNKI_CDP_MAX_ATTEMPTS - 1)
        cache_set_mock.assert_not_called()

    @patch.object(topic, "_cache_get", return_value=None)
    @patch.object(topic, "_cache_set")
    @patch.object(topic.time, "sleep")
    def test_search_cnki_does_not_retry_none_failure(self, sleep_mock, cache_set_mock, _cache_get_mock):
        with patch.object(topic, "_try_cnki_cdp", return_value=None) as try_mock:
            results = topic.search_cnki("充电桩", limit=10, use_cache=False, language="zh")

        self.assertEqual(results, [])
        self.assertEqual(try_mock.call_count, 1)
        sleep_mock.assert_not_called()
        cache_set_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
