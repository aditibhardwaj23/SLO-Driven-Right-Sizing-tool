# Local monitoring on Kind

The files here configure the `kube-prometheus-stack` Helm chart and tell Prometheus to scrape the sample app. The values and ServiceMonitor are prepared but have **not** been installed or verified against a running Kind cluster yet.

## Install

From the repository root, with Kind and Helm available and the `rightsizer` cluster running:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml
kubectl apply -f monitoring/sample-app-servicemonitor.yaml
kubectl -n monitoring get svc
kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open Prometheus at <http://localhost:9090> and check **Status > Targets** for the `sample-app` target. The ServiceMonitor selects the `app: sample-app` Service label, uses its `http` named port, and looks in the `default` namespace. These match the current `k8s/service.yaml`.

## Queries to verify

Run these in the Prometheus expression browser after generating requests to the app. The selectors use the container name `sample-app` from `k8s/deployment.yaml`.

```promql
sum(rate(http_requests_total[1m])) by (endpoint)
```

```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le, endpoint))
```

```promql
sum(rate(container_cpu_usage_seconds_total{pod=~"sample-app.*", container="sample-app"}[1m]))
```

```promql
container_memory_working_set_bytes{pod=~"sample-app.*", container="sample-app"}
```

The app exports request rate and latency histogram metrics. CPU and memory metrics are supplied by Kubernetes/cAdvisor. These queries are documented for later collector work; query results have not yet been observed on a live cluster.

## Grafana

Grafana is installed by the same chart. The generated admin password is stored in the `monitoring-grafana` Secret; do not commit the password or other credentials.
