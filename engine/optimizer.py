"""Optimization Engine: recommendation formulas (Phase 6).

These are starting heuristics, NOT VPA's algorithm and NOT guaranteed safe.
Still to design: spikes, throttling, OOM events, and limits (requests and
limits are separate values and must be recommended separately).
"""
import math
from dataclasses import dataclass, field

from engine.config import EngineConfig


@dataclass(frozen=True)
class Recommendation:
    cpu_request_m: int
    memory_request_mi: int
    cpu_limit_m: int
    memory_limit_mi: int
    inputs: dict
    formula_parameters: dict
    warnings: list[str] = field(default_factory=list)


def recommend_cpu_request_m(p95_cpu_m: float, config: EngineConfig = EngineConfig()) -> int:
    """Recommended CPU request in millicores = P95 * (1 + margin)."""
    value = p95_cpu_m * (1 + config.margins.cpu)
    return max(config.min_cpu_m, math.ceil(value))


def recommend_memory_request_mi(p95_memory_mi: float, config: EngineConfig = EngineConfig()) -> int:
    """Recommended memory request in Mi = P95 * (1 + margin)."""
    value = p95_memory_mi * (1 + config.margins.memory)
    return max(config.min_memory_mi, math.ceil(value))


def recommend_resources(
    p95_cpu_m: float,
    p95_memory_mi: float,
    peak_memory_mi: float | None = None,
    oomkill_count: int | None = None,
    config: EngineConfig = EngineConfig(),
) -> Recommendation:
    """Return a recommendation only; this function never applies resources."""
    peak = peak_memory_mi if peak_memory_mi is not None else p95_memory_mi
    memory_request = max(recommend_memory_request_mi(p95_memory_mi, config), math.ceil(peak))
    cpu_request = recommend_cpu_request_m(p95_cpu_m, config)
    # Limits use independent settings, not values copied from requests.
    cpu_limit = max(config.min_cpu_m, math.ceil(p95_cpu_m * config.limits.cpu_multiplier))
    memory_limit = max(config.min_memory_mi, math.ceil(peak * config.limits.memory_multiplier))
    warnings = ["Starting heuristic, not measured; validate with representative load and SLO data."]
    if peak_memory_mi is not None and peak_memory_mi > p95_memory_mi:
        warnings.append("Memory request is raised to observed peak usage.")
    if oomkill_count:
        warnings.append(f"Observed {oomkill_count} OOMKill event(s); inspect memory sizing before use.")
    if memory_limit <= memory_request:
        warnings.append("Configured memory limit multiplier does not place the limit above the request.")
    if cpu_limit <= cpu_request:
        warnings.append("Configured CPU limit multiplier does not place the limit above the request.")
    return Recommendation(
        cpu_request_m=cpu_request,
        memory_request_mi=memory_request,
        cpu_limit_m=cpu_limit,
        memory_limit_mi=memory_limit,
        inputs={"p95_cpu_m": p95_cpu_m, "p95_memory_mi": p95_memory_mi,
                "peak_memory_mi": peak_memory_mi, "oomkill_count": oomkill_count},
        formula_parameters={"cpu_request_margin": config.margins.cpu,
                            "memory_request_margin": config.margins.memory,
                            "cpu_limit_multiplier": config.limits.cpu_multiplier,
                            "memory_limit_multiplier": config.limits.memory_multiplier},
        warnings=warnings,
    )
