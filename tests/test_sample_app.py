import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sample-app"))

from app import app  # noqa: E402


class TestSampleApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        self.assertEqual(self.client.get("/health").get_json()["status"], "healthy")

    def test_fast(self):
        self.assertEqual(self.client.get("/fast").status_code, 200)

    def test_products(self):
        self.assertEqual(len(self.client.get("/api/products").get_json()), 8)

    def test_product_not_found(self):
        self.assertEqual(self.client.get("/api/products/999").status_code, 404)

    def test_work_rejects_bad_seconds(self):
        self.assertEqual(self.client.get("/work?seconds=99").status_code, 400)

    def test_cart_flow(self):
        r = self.client.post("/api/cart/items", json={"product_id": 1, "quantity": 2})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/api/cart").get_json()["item_count"], 2)

    def test_metrics_exposed(self):
        self.client.get("/fast")
        body = self.client.get("/metrics").get_data(as_text=True)
        self.assertIn("http_requests_total", body)
        self.assertIn("http_request_duration_seconds", body)


if __name__ == "__main__":
    unittest.main()
