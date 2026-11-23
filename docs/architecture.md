# Architecture

```
Locust (traffic) --> sample-app Pods (Kind / EKS)
                          |
                     Prometheus  <-- cAdvisor / kube-state-metrics (CPU, memory, throttling, OOM)
                          |         <-- sample-app /metrics (latency, errors, request rate)
                   Python engine: collector -> analyzer -> optimizer
                          |
                     SLO validator  <-- Locust before/after runs
                          |
                      Dashboard (Grafana + Python results)
```

## Components

- **Sample app**: Flask TechStore, served by gunicorn. Exposes `/metrics`.
- **Collector**: queries the Prometheus HTTP API.
- **Analyzer**: percentiles, peaks, variability.
- **Optimizer**: recommended CPU/memory requests (limits evaluated separately).
- **SLO validator**: pass/fail against latency, error-rate and availability targets.
- **Locust**: generates load, before and after applying candidate resources.

## Design rules

- The tool recommends; it does not modify production resources.
- CPU request, CPU limit, memory request and memory limit are four separate values.
- SLOs are checked over a meaningful window with enough requests.
