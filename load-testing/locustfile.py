"""Locust load test for the TechStore sample app.

Run (app reachable on http://localhost:8080 via Kind):
    pip install locust
    locust -f load-testing/locustfile.py --host http://localhost:8080

Headless example (50 users, 2 minutes):
    locust -f load-testing/locustfile.py --host http://localhost:8080 \
        --headless -u 50 -r 5 -t 2m --csv results/run1
"""
import random

from locust import HttpUser, between, task


class Shopper(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def browse_products(self):
        self.client.get("/api/products", name="/api/products")

    @task(3)
    def view_product(self):
        product_id = random.randint(1, 8)
        self.client.get(f"/api/products/{product_id}", name="/api/products/[id]")

    @task(2)
    def fast_endpoint(self):
        self.client.get("/fast")

    @task(2)
    def add_to_cart(self):
        self.client.post(
            "/api/cart/items",
            json={"product_id": random.randint(1, 8), "quantity": 1},
            name="/api/cart/items",
        )

    @task(1)
    def checkout(self):
        product_id = random.randint(1, 8)
        self.client.post(
            "/api/cart/items",
            json={"product_id": product_id, "quantity": 1},
            name="/api/cart/items (checkout setup)",
        )
        self.client.post("/api/checkout", json={})

    @task(1)
    def cpu_work(self):
        # CPU-heavy request: burns CPU for ~0.2 s
        self.client.get("/work?seconds=0.2", name="/work")
