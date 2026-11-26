# Project Tracker

Status: Not started / In progress / Done

| # | Phase | Key tasks | Status |
|---|---|---|---|
| 1 | Learning and concepts | Kubernetes basics, requests vs limits, Prometheus, VPA, SLOs, Locust | In progress |
| 2 | Environment setup | Docker, kubectl, Kind, Helm, Python, Git repo | In progress |
| 3 | Sample app and monitoring | Flask app, Dockerfile, deploy on Kind, Prometheus + Grafana | In progress (local smoke verified; Docker, Kind, and live Prometheus remain open) |
| 4 | Metrics Collector | Query Prometheus for CPU, memory, throttling, latency, errors, OOM | Partially implemented: request rate (`http_requests_total`), P95 latency (`http_request_duration_seconds_bucket`), CPU (`container_cpu_usage_seconds_total`), and memory (`container_memory_working_set_bytes`) range queries are configured. Missing: CPU throttling, error-rate, availability, and OOMKill queries. Mock-tested only; live Prometheus verification open |
| 5 | Resource Analyzer | Avg, P95, peaks, variability | Implemented and unit-tested against mock data only |
| 6 | Optimization Engine | Formulas, margins, spikes, throttling, OOM, separate limits | Implemented and unit-tested against mock data only; starting heuristics, not measured |
| 7 | SLO Validator | Latency, error rate, availability over a proper window | Partially implemented and mock-tested: evaluates P95 latency, error rate, availability, and request-count sufficiency when supplied. Collector currently supplies P95 latency and request rate, but not failed-request counts/error rate, total request counts for the SLO window, or availability/uptime; those inputs must be added before end-to-end SLO verdicts. Live validation open |
| 8 | Load testing with Locust | Test at 10/50/100/500 users, before and after | Not started (starter locustfile) |
| 9 | Dashboard | Current vs recommended, savings, validation status | Not started |
| 10 | AWS deployment | EC2/EKS, repeat tests, tear down to control cost | Not started |
| 11 | Testing and refinement | Tune margins, edge cases, repeatability | Not started |
| 12 | Documentation and presentation | README, diagrams, measured results | Not started |

Engine pieces (collector, analyzer, optimizer, and SLO validator) have only been
unit-tested with mocked data. They have not been verified against live Prometheus.
The previous `codex-task-brief-verify-deploy-monitor.md` Tasks 2–4 (Docker, Kind,
and Prometheus/Grafana deployment and validation) remain open. The `results/`
directory contains no measured data.
