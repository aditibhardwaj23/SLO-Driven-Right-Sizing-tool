# Monitoring

Prometheus and Grafana are installed into the Kind cluster with Helm
(Phase 3). Planned contents:

- `prometheus-values.yaml`: Helm values (scrape config for `sample-app` `/metrics`)
- `grafana-dashboards/`: exported Grafana dashboards

CPU, memory, throttling and OOM data come from cAdvisor / kube-state-metrics.
Latency, request rate and error rate come from the app's `/metrics` endpoint.
