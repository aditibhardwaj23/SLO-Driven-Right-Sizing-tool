
from flask import Flask, render_template, jsonify, request, session, Response, g
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)
import time
import os
import uuid

app = Flask(__name__)

# All replicas must share the same SECRET_KEY (the cart lives in a session cookie).
# In Kubernetes, set it from a Secret. The fallback is for local development only.
app.secret_key = os.environ.get(
    "SECRET_KEY", "techstore-development-key"
)

# ----------------------------------
# PROMETHEUS METRICS
# ----------------------------------
# Used by the optimization engine to compute latency, error rate and
# request rate (the SLIs). CPU and memory come from the cluster, not here.

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1, 2, 5, 10),
)


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    # Skip /metrics itself and unmatched routes (avoids label explosion).
    if request.url_rule is None or request.path == "/metrics":
        return response

    endpoint = request.url_rule.rule
    elapsed = time.perf_counter() - getattr(g, "start_time", time.perf_counter())

    REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, endpoint).observe(elapsed)
    return response

PRODUCTS = [
    {
        "id": 1,
        "name": "ProBook Laptop",
        "category": "Computers",
        "price": 55000,
        "original_price": 65000,
        "emoji": "💻",
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800",
        "description": "Powerful laptop for work, study and gaming.",
        "details": "High-performance laptop with a crisp display, fast storage and a powerful processor.",
        "rating": 4.8,
        "reviews": 245,
        "stock": 15
    },
    {
        "id": 2,
        "name": "Smartphone X",
        "category": "Mobiles",
        "price": 25000,
        "original_price": 30000,
        "emoji": "📱",
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800",
        "description": "Modern smartphone with an amazing camera.",
        "details": "A stylish smartphone featuring a vibrant screen, capable camera and all-day battery.",
        "rating": 4.7,
        "reviews": 318,
        "stock": 20
    },
    {
        "id": 3,
        "name": "Wireless Headphones",
        "category": "Audio",
        "price": 3000,
        "original_price": 4500,
        "emoji": "🎧",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
        "description": "Enjoy immersive sound and wireless freedom.",
        "details": "Comfortable wireless headphones with rich sound and a stylish design.",
        "rating": 4.6,
        "reviews": 182,
        "stock": 30
    },
    {
        "id": 4,
        "name": "Smartwatch Pro",
        "category": "Wearables",
        "price": 5000,
        "original_price": 6500,
        "emoji": "⌚",
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800",
        "description": "Track your fitness and daily activity.",
        "details": "A smart wearable for activity tracking, notifications and everyday convenience.",
        "rating": 4.5,
        "reviews": 156,
        "stock": 25
    },
    {
        "id": 5,
        "name": "Gaming Console",
        "category": "Gaming",
        "price": 35000,
        "original_price": 42000,
        "emoji": "🎮",
        "image": "https://images.unsplash.com/photo-1486401899868-0e435ed85128?w=800",
        "description": "Experience next-generation gaming.",
        "details": "A powerful gaming setup for immersive entertainment and high-performance play.",
        "rating": 4.9,
        "reviews": 289,
        "stock": 10
    },
    {
        "id": 6,
        "name": "Bluetooth Speaker",
        "category": "Audio",
        "price": 2500,
        "original_price": 3500,
        "emoji": "🔊",
        "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800",
        "description": "Portable speaker with powerful audio.",
        "details": "Compact portable speaker designed for clear audio and everyday listening.",
        "rating": 4.4,
        "reviews": 112,
        "stock": 18
    },
    {
        "id": 7,
        "name": "Digital Camera",
        "category": "Photography",
        "price": 42000,
        "original_price": 50000,
        "emoji": "📷",
        "image": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800",
        "description": "Capture beautiful moments in high quality.",
        "details": "A versatile digital camera for photography, travel and creative projects.",
        "rating": 4.8,
        "reviews": 204,
        "stock": 8
    },
    {
        "id": 8,
        "name": "Tablet",
        "category": "Computers",
        "price": 18000,
        "original_price": 22000,
        "emoji": "📲",
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800",
        "description": "A versatile tablet for entertainment and work.",
        "details": "A lightweight tablet for browsing, studying, entertainment and productivity.",
        "rating": 4.6,
        "reviews": 138,
        "stock": 12
    }
]


def get_product(product_id):
    return next(
        (p for p in PRODUCTS if p["id"] == product_id),
        None
    )


def get_cart():
    return session.setdefault("cart", {})


def cart_details():
    cart = get_cart()
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = get_product(int(product_id))

        if product:
            item = {
                **product,
                "quantity": quantity,
                "subtotal": product["price"] * quantity
            }
            items.append(item)
            total += item["subtotal"]

    return {
        "items": items,
        "total": total,
        "item_count": sum(i["quantity"] for i in items)
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/products")
def products():
    search = request.args.get("search", "").strip().lower()
    category = request.args.get("category", "").strip().lower()

    result = PRODUCTS

    if search:
        result = [
            p for p in result
            if search in p["name"].lower()
            or search in p["category"].lower()
        ]

    if category and category != "all":
        result = [
            p for p in result
            if p["category"].lower() == category
        ]

    return jsonify(result)


@app.route("/api/products/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product)


@app.route("/api/cart", methods=["GET"])
def view_cart():
    return jsonify(cart_details())


@app.route("/api/cart/items", methods=["POST"])
def add_to_cart():
    data = request.get_json(silent=True) or {}

    try:
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid product or quantity"}), 400

    product = get_product(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if quantity < 1:
        return jsonify({"error": "Quantity must be positive"}), 400

    cart = get_cart()
    new_quantity = cart.get(str(product_id), 0) + quantity

    if new_quantity > product["stock"]:
        return jsonify({"error": "Not enough stock available"}), 400

    cart[str(product_id)] = new_quantity
    session.modified = True

    return jsonify({
        "message": "Product added to cart",
        "cart": cart_details()
    })


@app.route("/api/cart/items/<int:product_id>", methods=["PATCH"])
def update_cart_item(product_id):
    data = request.get_json(silent=True) or {}

    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid quantity"}), 400

    product = get_product(product_id)
    cart = get_cart()

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if quantity < 0 or quantity > product["stock"]:
        return jsonify({"error": "Invalid quantity or insufficient stock"}), 400

    if quantity == 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = quantity

    session.modified = True
    return jsonify(cart_details())


@app.route("/api/cart/items/<int:product_id>", methods=["DELETE"])
def remove_cart_item(product_id):
    cart = get_cart()
    cart.pop(str(product_id), None)
    session.modified = True

    return jsonify({
        "message": "Product removed",
        "cart": cart_details()
    })


@app.route("/api/checkout", methods=["POST"])
def checkout():
    details = cart_details()

    if not details["items"]:
        return jsonify({"error": "Your cart is empty"}), 400

    order_id = "TS-" + uuid.uuid4().hex[:8].upper()

    session["cart"] = {}

    return jsonify({
        "message": "Demo order placed successfully!",
        "order_id": order_id,
        "total": details["total"],
        "items": details["items"]
    })


@app.route("/metrics")
def metrics():
    # With several gunicorn workers each process has its own counters, so
    # they are combined through PROMETHEUS_MULTIPROC_DIR (set in the Dockerfile).
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    else:
        data = generate_latest()
    return Response(data, mimetype=CONTENT_TYPE_LATEST)


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "TechStore",
        "timestamp": time.time()
    })


@app.route("/fast")
def fast():
    return jsonify({
        "message": "Fast request completed",
        "status": "success"
    })


@app.route("/work")
def heavy_work():
    try:
        seconds = float(request.args.get("seconds", 1))
    except ValueError:
        return jsonify({"error": "Invalid seconds value"}), 400

    if not 0.1 <= seconds <= 5:
        return jsonify({
            "error": "Seconds must be between 0.1 and 5"
        }), 400

    start = time.perf_counter()
    result = 0
    iterations = 0

    while time.perf_counter() - start < seconds:
        result = (result * 31 + iterations * iterations) % 1000000007
        iterations += 1

    return jsonify({
        "message": "CPU workload completed",
        "execution_time": round(time.perf_counter() - start, 3),
        "iterations": iterations,
        "result": result
    })


if __name__ == "__main__":
    # Local development only. In Docker/Kubernetes the app runs under gunicorn.
    # Set FLASK_DEBUG=1 to turn on debug mode locally.
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )
