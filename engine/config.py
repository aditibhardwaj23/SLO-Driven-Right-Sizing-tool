"""All tunable numbers live here. Do not hardcode them elsewhere."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Margins:
    cpu: float = 0.20       # +20% over P95 CPU
    memory: float = 0.25    # +25% over P95 memory


@dataclass(frozen=True)
class SLOTargets:
    p95_latency_ms: float = 200.0     # must stay below
    error_rate_pct: float = 1.0       # must stay below
    availability_pct: float = 99.9    # must stay at or above


@dataclass(frozen=True)
class EngineConfig:
    prometheus_url: str = "http://localhost:9090"
    namespace: str = "default"
    margins: Margins = field(default_factory=Margins)
    slo: SLOTargets = field(default_factory=SLOTargets)
    percentile: float = 95.0
    min_cpu_m: int = 50          # never recommend below this
    min_memory_mi: int = 64
