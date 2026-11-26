"""Prometheus range-query collector with explicit failure reporting."""
from datetime import datetime, timedelta, timezone
from typing import Callable

import requests

from engine.config import EngineConfig


class PrometheusQueryError(RuntimeError):
    """Raised when Prometheus cannot provide a usable time series."""


def render_query(template: str, config: EngineConfig, window: str | None = None) -> str:
    """Fill configured namespace/pod/container labels and range window."""
    return template.format(
        namespace=config.namespace,
        pod=config.pod,
        container=config.container,
        window=window or config.query_window,
    )


def _get_response(url: str, params: dict, timeout: int, session=None):
    client = session or requests
    getter = client.get if hasattr(client, "get") else client
    return getter(url, params=params, timeout=timeout)


def query_range(
    config: EngineConfig,
    promql: str,
    start: float,
    end: float,
    step: str | None = None,
    session=None,
) -> list[list[tuple[float, float]]]:
    """Return each matching series as a list of ``(timestamp, value)`` pairs."""
    try:
        response = _get_response(
            f"{config.prometheus_url}/api/v1/query_range",
            {"query": promql, "start": start, "end": end, "step": step or config.query_step},
            timeout=30,
            session=session,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise PrometheusQueryError("Prometheus range query timed out") from exc
    except requests.RequestException as exc:
        raise PrometheusQueryError(f"Prometheus HTTP request failed: {exc}") from exc
    except (ValueError, TypeError) as exc:
        raise PrometheusQueryError(f"Invalid Prometheus response: {exc}") from exc

    if payload.get("status") != "success":
        raise PrometheusQueryError(f"Prometheus query status was not success: {payload.get('error', payload)}")

    try:
        result = payload["data"]["result"]
        if not result:
            raise PrometheusQueryError("Prometheus query returned no series")
        series = []
        for item in result:
            values = item.get("values", [])
            parsed = [(float(timestamp), float(value)) for timestamp, value in values]
            if parsed:
                series.append(parsed)
        if not series:
            raise PrometheusQueryError("Prometheus query returned no samples")
        return series
    except (KeyError, TypeError, ValueError) as exc:
        raise PrometheusQueryError(f"Malformed Prometheus range result: {exc}") from exc


def collect_metrics(
    config: EngineConfig,
    window: str | None = None,
    step: str | None = None,
    end: float | None = None,
    session=None,
) -> dict[str, list[list[tuple[float, float]]]]:
    """Query configured request-rate, latency, CPU and memory expressions."""
    end = end if end is not None else datetime.now(timezone.utc).timestamp()
    # Default query window is a Prometheus duration, handled by config values used
    # in the range expressions. Convert common duration strings to a start time.
    duration = window or config.query_window
    seconds = _duration_seconds(duration)
    start = end - seconds
    queries = {
        name: render_query(getattr(config.queries, name), config, duration)
        for name in ("request_rate", "p95_latency", "cpu", "memory")
    }
    return {
        name: query_range(config, expression, start, end, step=step, session=session)
        for name, expression in queries.items()
    }


def _duration_seconds(duration: str) -> int:
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(duration[:-1]) * units[duration[-1]]
    except (ValueError, KeyError, IndexError) as exc:
        raise ValueError(f"Unsupported Prometheus duration: {duration}") from exc


def query(config: EngineConfig, promql: str, session=None) -> list:
    """Run an instant query and return Prometheus result series."""
    try:
        response = _get_response(
            f"{config.prometheus_url}/api/v1/query",
            {"query": promql},
            timeout=10,
            session=session,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise PrometheusQueryError(f"Prometheus instant query failed: {exc}") from exc
    if payload.get("status") != "success":
        raise PrometheusQueryError(f"Prometheus query status was not success: {payload.get('error', payload)}")
    result = payload.get("data", {}).get("result", [])
    if not result:
        raise PrometheusQueryError("Prometheus query returned no series")
    return result
