"""SLO Validator: pass/fail against the targets (Phase 7).

Results are only meaningful over a long enough window with enough requests.
"""
from dataclasses import dataclass

from engine.config import EngineConfig, SLOTargets


@dataclass
class SLOResult:
    status: str
    request_count: int
    checks: dict      # name -> {passed, actual, target}

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    def failed_checks(self) -> list[str]:
        return [name for name, check in self.checks.items() if not check["passed"]]


def evaluate(p95_latency_ms: float, error_rate_pct: float, availability_pct: float,
             targets: SLOTargets = SLOTargets(), request_count: int | None = None,
             config: EngineConfig = EngineConfig()) -> SLOResult:
    checks = {
        "p95_latency_ms": {"passed": p95_latency_ms < targets.p95_latency_ms,
                            "actual": p95_latency_ms, "target": targets.p95_latency_ms},
        "error_rate_pct": {"passed": error_rate_pct < targets.error_rate_pct,
                            "actual": error_rate_pct, "target": targets.error_rate_pct},
        "availability_pct": {"passed": availability_pct >= targets.availability_pct,
                              "actual": availability_pct, "target": targets.availability_pct},
    }
    count = request_count if request_count is not None else 0
    status = "inconclusive" if count < config.min_requests else (
        "passed" if all(check["passed"] for check in checks.values()) else "failed"
    )
    return SLOResult(status=status, request_count=count, checks=checks)
