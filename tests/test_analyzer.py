import math
import unittest

from engine.analyzer import summarize, summarize_pods
from engine.config import EngineConfig


class TestAnalyzerSummaries(unittest.TestCase):
    def test_empty_series_returns_explicit_no_data(self):
        result = summarize([])
        self.assertTrue(result["no_data"])
        self.assertIsNone(result.get("mean"))
        self.assertEqual(result["count"], 0)

    def test_single_sample_has_valid_statistics(self):
        result = summarize([7], min_samples=1)
        self.assertEqual((result["min"], result["mean"], result["P50"], result["P95"], result["P99"], result["max"]), (7, 7, 7, 7, 7, 7))
        self.assertFalse(result["insufficient_data"])

    def test_all_equal_samples(self):
        result = summarize([4, 4, 4, 4, 4])
        self.assertEqual(result["P95"], 4)
        self.assertEqual(result["variability"], 0)

    def test_nan_and_none_are_dropped(self):
        result = summarize([1, float("nan"), None, 3])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["dropped"], 2)
        self.assertEqual(result["mean"], 2)

    def test_all_nan_is_no_data(self):
        result = summarize([float("nan"), float("nan")])
        self.assertTrue(result["no_data"])
        self.assertEqual(result["dropped"], 2)
        self.assertNotIn("P95", result)

    def test_below_configured_minimum_is_flagged(self):
        self.assertEqual(EngineConfig().min_samples, 5)
        result = summarize([2, 3, 4], min_samples=4)
        self.assertTrue(result["insufficient_data"])

    def test_per_pod_maximum_is_not_sum(self):
        result = summarize_pods({"pod-a": [100], "pod-b": [80] }, min_samples=1)
        self.assertEqual(result["pods"], {"pod-a": 100, "pod-b": 80})
        self.assertEqual(result["max_p95"], 100)
        self.assertNotEqual(result["max_p95"], sum(result["pods"].values()))

    def test_per_pod_all_missing_reports_no_data(self):
        result = summarize_pods({"pod-a": [None, math.nan]})
        self.assertEqual(result["pods"]["pod-a"], None)
        self.assertTrue(result["no_data"])
        self.assertIsNone(result["max_p95"])


if __name__ == "__main__":
    unittest.main()
