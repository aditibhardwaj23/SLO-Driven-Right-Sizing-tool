"""Optimization Engine: recommendation formulas (Phase 6).

These are starting heuristics, NOT VPA's algorithm and NOT guaranteed safe.
Still to design: spikes, throttling, OOM events, and limits (requests and
limits are separate values and must be recommended separately).
"""
import math

from engine.config import EngineConfig


def recommend_cpu_request_m(p95_cpu_m: float, config: EngineConfig = EngineConfig()) -> int:
    """Recommended CPU request in millicores = P95 * (1 + margin)."""
    value = p95_cpu_m * (1 + config.margins.cpu)
    return max(config.min_cpu_m, math.ceil(value))


def recommend_memory_request_mi(p95_memory_mi: float, config: EngineConfig = EngineConfig()) -> int:
    """Recommended memory request in Mi = P95 * (1 + margin)."""
    value = p95_memory_mi * (1 + config.margins.memory)
    return max(config.min_memory_mi, math.ceil(value))
