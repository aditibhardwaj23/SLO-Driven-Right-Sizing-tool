"""Resource Analyzer: statistics over historical usage (Phase 5)."""
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


def summarize(values: list[float], pct: float = 95.0, config: EngineConfig = EngineConfig()) -> dict:
    """Summarize a series and flag sample counts below the configured minimum."""
    if not values:
        return {
            "min": None, "mean": None, "p50": None, "p95": None,
            "p99": None, "max": None, "avg": None, "pct": None,
            "peak": None, "stdev": None, "variability": None,
            "samples": 0, "insufficient_data": True,
        }
    avg = mean(values)
    deviation = pstdev(values)
    return {
        "min": min(values),
        "mean": avg,
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "max": max(values),
        "avg": avg,
        "pct": percentile(values, pct),
        "peak": max(values),
        "stdev": deviation,
        "variability": (deviation / avg) if avg else 0.0,
        "samples": len(values),
        "insufficient_data": len(values) < config.min_samples,
    }
