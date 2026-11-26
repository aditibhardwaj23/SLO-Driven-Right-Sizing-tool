"""Metrics Collector: talks to the Prometheus HTTP API.

Phase 4. Only the generic query helpers exist so far. The PromQL for each
metric (CPU, memory, throttling, latency, errors, OOM) is still to be written.
"""
import requests

from engine.config import EngineConfig


def query(config: EngineConfig, promql: str) -> list:
    """Run an instant query and return the 'result' list."""
    resp = requests.get(
        f"{config.prometheus_url}/api/v1/query",
        params={"query": promql},
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "success":
        raise RuntimeError(f"Prometheus query failed: {payload}")
    return payload["data"]["result"]


def query_range(config: EngineConfig, promql: str, start: float, end: float, step: str = "30s") -> list:
    """Run a range query (timestamps are Unix seconds)."""
    resp = requests.get(
        f"{config.prometheus_url}/api/v1/query_range",
        params={"query": promql, "start": start, "end": end, "step": step},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "success":
        raise RuntimeError(f"Prometheus range query failed: {payload}")
    return payload["data"]["result"]
