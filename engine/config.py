"""All tunable values live here.

Numeric defaults are starting heuristics, not measured values.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Margins:
    # Starting heuristics, not measured: 1.20x P95 CPU and 1.25x P95 memory.
    cpu: float = 0.20
    memory: float = 0.25


@dataclass(frozen=True)
class ResourceLimits:
    """Independent limit multipliers; starting heuristics, not measured."""
    cpu_multiplier: float = 2.0
    memory_multiplier: float = 2.0


@dataclass(frozen=True)
class SLOTargets:
    # Starting SLO targets, not measured.
    p95_latency_ms: float = 200.0
    error_rate_pct: float = 1.0
    availability_pct: float = 99.9


@dataclass(frozen=True)
class PrometheusQueries:
    """Query templates based on monitoring/README.md; label values are parameters."""
    request_rate: str = 'sum(rate(http_requests_total{namespace="{namespace}",pod=~"{pod}"}[{window}]))'
    p95_latency: str = (
        'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket'
        '{{namespace="{namespace}",pod=~"{pod}"}}[{window}])) by (le))'
    )
    cpu: str = (
        'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}",'
        'pod=~"{pod}",container="{container}"}}[{window}]))'
    )
    memory: str = (
        'container_memory_working_set_bytes{{namespace="{namespace}",'
        'pod=~"{pod}",container="{container}"}}'
    )


@dataclass(frozen=True)
class EngineConfig:
    # Window and threshold defaults below are starting heuristics, not measured.
    prometheus_url: str = "http://localhost:9090"
    namespace: str = "default"
    pod: str = "sample-app.*"
    container: str = "sample-app"
    query_window: str = "5m"
    query_step: str = "15s"
    margins: Margins = field(default_factory=Margins)
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    slo: SLOTargets = field(default_factory=SLOTargets)
    queries: PrometheusQueries = field(default_factory=PrometheusQueries)
    percentile: float = 95.0
    min_cpu_m: int = 50
    min_memory_mi: int = 64
    min_samples: int = 20
    min_requests: int = 1000
