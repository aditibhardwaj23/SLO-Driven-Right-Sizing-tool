import unittest

from engine.analyzer import percentile, summarize
from engine.config import EngineConfig
from engine.optimizer import recommend_cpu_request_m, recommend_memory_request_mi
from engine.slo_validator import evaluate


class TestAnalyzer(unittest.TestCase):
    def test_percentile_median(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 50), 3)

    def test_percentile_single_value(self):
        self.assertEqual(percentile([7], 95), 7)

    def test_summarize_peak(self):
        self.assertEqual(summarize([100, 200, 300])["peak"], 300)


class TestOptimizer(unittest.TestCase):
    def test_cpu_example_from_design(self):
        # P95 600m with 20% margin -> 720m (illustrative example from the design notes)
        self.assertEqual(recommend_cpu_request_m(600), 720)

    def test_memory_example_from_design(self):
        # P95 800Mi with 25% margin -> 1000Mi
        self.assertEqual(recommend_memory_request_mi(800), 1000)

    def test_minimum_floor(self):
        self.assertEqual(recommend_cpu_request_m(1, EngineConfig()), 50)


class TestSLOValidator(unittest.TestCase):
    def test_passes(self):
        self.assertTrue(evaluate(170, 0.3, 99.95).passed)

    def test_fails_latency_and_errors(self):
        result = evaluate(350, 1.5, 99.95)
        self.assertFalse(result.passed)
        self.assertEqual(set(result.failed_checks()), {"p95_latency_ms", "error_rate_pct"})


if __name__ == "__main__":
    unittest.main()
