import unittest
from unittest.mock import Mock

import requests

from engine.analyzer import percentile, summarize
from engine.collector import PrometheusQueryError, query_range, render_query
from engine.config import EngineConfig
from engine.optimizer import recommend_cpu_request_m, recommend_memory_request_mi, recommend_resources
from engine.slo_validator import evaluate


class TestAnalyzer(unittest.TestCase):
    def test_percentile_median(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 50), 3)

    def test_percentile_single_and_equal_values(self):
        self.assertEqual(percentile([7], 95), 7)
        self.assertEqual(percentile([4, 4, 4], 99), 4)

    def test_percentile_empty(self):
        with self.assertRaises(ValueError):
            percentile([], 95)

    def test_summary_statistics_and_minimum_samples(self):
        config = EngineConfig(min_samples=3)
        summary = summarize([1, 2, 3], config=config)
        self.assertEqual((summary["min"], summary["mean"], summary["max"]), (1, 2, 3))
        self.assertEqual((summary["p50"], summary["p95"], summary["p99"]), (2, 2.9, 2.98))
        self.assertFalse(summary["insufficient_data"])
        self.assertTrue(summarize([1, 2], config=config)["insufficient_data"])

    def test_summary_empty(self):
        summary = summarize([])
        self.assertEqual(summary["samples"], 0)
        self.assertTrue(summary["insufficient_data"])


class TestCollector(unittest.TestCase):
    def setUp(self):
        self.config = EngineConfig(namespace="shop", pod="store-.*", container="web")

    def mock_response(self, payload):
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    def test_success_parses_values_and_injects_query_params(self):
        session = Mock()
        session.get.return_value = self.mock_response({"status": "success", "data": {
            "result": [{"values": [[10, "1.5"], [20, "2"]]}]}})
        result = query_range(self.config, render_query(self.config.queries.cpu, self.config), 1, 20, session=session)
        self.assertEqual(result, [[(10.0, 1.5), (20.0, 2.0)]])
        args, kwargs = session.get.call_args
        self.assertTrue(args[0].endswith("/api/v1/query_range"))
        self.assertIn('namespace="shop"', kwargs["params"]["query"])
        self.assertEqual(kwargs["params"]["step"], self.config.query_step)

    def test_empty_result(self):
        session = Mock()
        session.get.return_value = self.mock_response({"status": "success", "data": {"result": []}})
        with self.assertRaisesRegex(PrometheusQueryError, "no series"):
            query_range(self.config, "up", 1, 2, session=session)

    def test_prometheus_error_status(self):
        session = Mock()
        session.get.return_value = self.mock_response({"status": "error", "error": "bad query"})
        with self.assertRaisesRegex(PrometheusQueryError, "bad query"):
            query_range(self.config, "bad", 1, 2, session=session)

    def test_timeout(self):
        session = Mock()
        session.get.side_effect = requests.Timeout("slow")
        with self.assertRaisesRegex(PrometheusQueryError, "timed out"):
            query_range(self.config, "up", 1, 2, session=session)

    def test_http_error(self):
        session = Mock()
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("503")
        session.get.return_value = response
        with self.assertRaisesRegex(PrometheusQueryError, "HTTP request failed"):
            query_range(self.config, "up", 1, 2, session=session)


class TestOptimizer(unittest.TestCase):
    def test_request_formulas_and_floors(self):
        self.assertEqual(recommend_cpu_request_m(600), 720)
        self.assertEqual(recommend_memory_request_mi(800), 1000)
        self.assertEqual(recommend_cpu_request_m(1), 50)
        self.assertEqual(recommend_memory_request_mi(1), 64)

    def test_separate_limits_and_memory_peak(self):
        result = recommend_resources(600, 800, peak_memory_mi=1200, oomkill_count=1)
        self.assertEqual(result.cpu_request_m, 720)
        self.assertEqual(result.memory_request_mi, 1200)
        self.assertNotEqual(result.cpu_limit_m, result.cpu_request_m)
        self.assertNotEqual(result.memory_limit_mi, result.memory_request_mi)
        self.assertTrue(any("OOMKill" in warning for warning in result.warnings))
        self.assertIn("peak_memory_mi", result.inputs)


class TestSLOValidator(unittest.TestCase):
    def test_passes_only_at_trusted_volume(self):
        result = evaluate(170, 0.3, 99.95, request_count=1000)
        self.assertEqual(result.status, "passed")
        self.assertTrue(result.passed)
        self.assertTrue(all("actual" in check and "target" in check for check in result.checks.values()))

    def test_fails_each_slo_target(self):
        cases = [(250, 0.2, 99.95, "p95_latency_ms"),
                 (100, 1.2, 99.95, "error_rate_pct"),
                 (100, 0.2, 99.0, "availability_pct")]
        for latency, errors, availability, name in cases:
            with self.subTest(name=name):
                result = evaluate(latency, errors, availability, request_count=1000)
                self.assertEqual(result.status, "failed")
                self.assertFalse(result.checks[name]["passed"])

    def test_low_volume_is_inconclusive_even_if_metrics_pass(self):
        result = evaluate(100, 0.1, 100, request_count=999)
        self.assertEqual(result.status, "inconclusive")
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
