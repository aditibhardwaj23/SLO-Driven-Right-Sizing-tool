#!/usr/bin/env bash
# Smoke-tests the running sample app (local, Docker, or port-forwarded Kind).
# Usage: BASE_URL=http://localhost:5000 bash scripts/verify-sample-app.sh
set -u

BASE_URL="${BASE_URL:-http://localhost:5000}"
JAR="$(mktemp)"
PASS=0
FAIL=0

check() {  # check <name> <expected_status> <curl args...>
  local name="$1" expected="$2"; shift 2
  local status
  status=$(curl -s -o /tmp/verify_body -w '%{http_code}' -b "$JAR" -c "$JAR" "$@")
  if [ "$status" = "$expected" ]; then
    echo "PASS  $name ($status)"; PASS=$((PASS+1))
  else
    echo "FAIL  $name: expected $expected, got $status"; FAIL=$((FAIL+1))
  fi
}

check "home page"            200 "$BASE_URL/"
check "health"               200 "$BASE_URL/health"
check "fast"                 200 "$BASE_URL/fast"
check "list products"        200 "$BASE_URL/api/products"
check "product 1"            200 "$BASE_URL/api/products/1"
check "product 999 missing"  404 "$BASE_URL/api/products/999"
check "search"               200 "$BASE_URL/api/products?search=laptop"
check "add to cart"          200 -X POST -H 'Content-Type: application/json' \
      -d '{"product_id":1,"quantity":1}' "$BASE_URL/api/cart/items"
check "view cart"            200 "$BASE_URL/api/cart"
check "update cart"          200 -X PATCH -H 'Content-Type: application/json' \
      -d '{"quantity":2}' "$BASE_URL/api/cart/items/1"
check "checkout"             200 -X POST -H 'Content-Type: application/json' -d '{}' \
      "$BASE_URL/api/checkout"
check "checkout empty cart"  400 -X POST -H 'Content-Type: application/json' -d '{}' \
      "$BASE_URL/api/checkout"
check "work 0.2s"            200 "$BASE_URL/work?seconds=0.2"
check "work invalid"         400 "$BASE_URL/work?seconds=99"
check "metrics endpoint"     200 "$BASE_URL/metrics"

if grep -q '^http_requests_total' /tmp/verify_body \
   && grep -q 'http_request_duration_seconds' /tmp/verify_body; then
  echo "PASS  /metrics has http_requests_total and http_request_duration_seconds"
  PASS=$((PASS+1))
else
  echo "FAIL  /metrics is missing expected metric names"; FAIL=$((FAIL+1))
fi

rm -f "$JAR" /tmp/verify_body
echo "----"; echo "passed=$PASS failed=$FAIL"
[ "$FAIL" -eq 0 ]
