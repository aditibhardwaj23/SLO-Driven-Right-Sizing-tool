"""Resource Analyzer: statistics over historical usage (Phase 5)."""
from math import isnan
from statistics import mean, pstdev

from engine.config import EngineConfig


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (pct from 0 to 100)."""
    if not values:
        raise ValueError("no values")
    data = sorted(values)
    if len(data) == 1:
        return float(data[0])
    rank = (pct / 100) * (len(data) - 1)
    low = int(rank)
    high = min(low + 1, len(data) - 1)
    return data[low] + (data[high] - data[low]) * (rank - low)


def _clean(values: list[float | None]) -> tuple[list[float], int]:
    cleaned = []
    dropped = 0
    for value in values:
        if value is None or (isinstance(value, float) and isnan(value)):
            dropped += 1
        else:
            cleaned.append(float(value))
    return cleaned, dropped


def summarize(
    values: list[float | None], pct: float = 95.0, min_samples: int | None = None
) -> dict:
    """Summarize a series, excluding missing and NaN samples."""
    cleaned, dropped = _clean(values)
    required = EngineConfig().min_samples if min_samples is None else min_samples
    count = len(cleaned)
    if not cleaned:
        return {
            "count": 0,
            "dropped": dropped,
            "no_data": True,
            "insufficient_data": True,
        }

    avg = mean(cleaned)
    deviation = pstdev(cleaned)
    p50 = percentile(cleaned, 50)
    p95 = percentile(cleaned, 95)
    p99 = percentile(cleaned, 99)
    peak = max(cleaned)
    return {
        "count": count,
        "dropped": dropped,
        "no_data": False,
        "insufficient_data": count < required,
        "min": min(cleaned),
        "mean": avg,
        "P50": p50,
        "P95": p95,
        "P99": p99,
        "max": peak,
        "peak": peak,
        # Keep the original result keys for existing callers.
        "avg": avg,
        "pct": percentile(cleaned, pct),
        "stdev": deviation,
        "variability": (deviation / avg) if avg else 0.0,
        "samples": count,
    }


def summarize_pods(
    pod_samples: dict[str, list[float | None]], min_samples: int | None = None
) -> dict:
    """Return each pod's P95 and the maximum pod P95; never aggregate by sum."""
    per_pod = {}
    for pod, values in pod_samples.items():
        result = summarize(values, min_samples=min_samples)
        per_pod[pod] = result["P95"] if not result["no_data"] else None

    available = {pod: p95 for pod, p95 in per_pod.items() if p95 is not None}
    if not available:
        return {"pods": per_pod, "max_p95": None, "max_pod": None, "no_data": True}
    max_pod = max(available, key=available.get)
    return {
        "pods": per_pod,
        "max_p95": available[max_pod],
        "max_pod": max_pod,
        "no_data": False,
    }
