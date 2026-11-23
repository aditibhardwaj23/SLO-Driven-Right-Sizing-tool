"""Resource Analyzer: statistics over historical usage (Phase 5)."""
from statistics import mean, pstdev


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


def summarize(values: list[float], pct: float = 95.0) -> dict:
    """Average, percentile, peak and variability of a usage series."""
    avg = mean(values)
    return {
        "avg": avg,
        "pct": percentile(values, pct),
        "peak": max(values),
        "stdev": pstdev(values),
        "variability": (pstdev(values) / avg) if avg else 0.0,
        "samples": len(values),
    }
