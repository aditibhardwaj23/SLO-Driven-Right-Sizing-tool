"""SLO Validator: pass/fail against the targets (Phase 7).

Results are only meaningful over a long enough window with enough requests.
"""
from dataclasses import dataclass

from engine.config import SLOTargets


@dataclass
class SLOResult:
    passed: bool
    checks: dict      # name -> (passed, actual, target)

    def failed_checks(self) -> list[str]:
        return [name for name, (ok, _, _) in self.checks.items() if not ok]


def evaluate(p95_latency_ms: float, error_rate_pct: float, availability_pct: float,
             targets: SLOTargets = SLOTargets()) -> SLOResult:
    checks = {
        "p95_latency_ms": (p95_latency_ms < targets.p95_latency_ms, p95_latency_ms, targets.p95_latency_ms),
        "error_rate_pct": (error_rate_pct < targets.error_rate_pct, error_rate_pct, targets.error_rate_pct),
        "availability_pct": (availability_pct >= targets.availability_pct, availability_pct, targets.availability_pct),
    }
    return SLOResult(passed=all(ok for ok, _, _ in checks.values()), checks=checks)
