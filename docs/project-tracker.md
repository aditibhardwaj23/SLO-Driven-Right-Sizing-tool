# Project Tracker

Status: Not started / In progress / Done

| # | Phase | Key tasks | Status |
|---|---|---|---|
| 1 | Learning and concepts | Kubernetes basics, requests vs limits, Prometheus, VPA, SLOs, Locust | In progress |
| 2 | Environment setup | Docker, kubectl, Kind, Helm, Python, Git repo | In progress |
| 3 | Sample app and monitoring | Flask app, Dockerfile, deploy on Kind, Prometheus + Grafana | In progress (Flask app written, not yet verified) |
| 4 | Metrics Collector | Query Prometheus for CPU, memory, throttling, latency, errors, OOM | Not started (query helpers only) |
| 5 | Resource Analyzer | Avg, P95, peaks, variability | Not started (helpers only) |
| 6 | Optimization Engine | Formulas, margins, spikes, throttling, OOM, separate limits | Not started (basic formulas only) |
| 7 | SLO Validator | Latency, error rate, availability over a proper window | Not started (basic checks only) |
| 8 | Load testing with Locust | Test at 10/50/100/500 users, before and after | Not started (starter locustfile) |
| 9 | Dashboard | Current vs recommended, savings, validation status | Not started |
| 10 | AWS deployment | EC2/EKS, repeat tests, tear down to control cost | Not started |
| 11 | Testing and refinement | Tune margins, edge cases, repeatability | Not started |
| 12 | Documentation and presentation | README, diagrams, measured results | Not started |
