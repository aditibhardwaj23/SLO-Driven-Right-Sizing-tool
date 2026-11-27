# SLO-Driven Kubernetes Right-Sizing Tool

A tool that finds over-provisioned Kubernetes workloads and recommends smaller
CPU and memory settings **without breaking performance**.

1. **Collect** CPU, memory, latency and error metrics from Prometheus.
2. **Analyse** them in Python (averages, P95, peaks, variability).
3. **Recommend** new CPU and memory requests using safety margins.
4. **Validate** with Locust load tests against SLOs (latency, error rate, availability).
5. **Display** current vs recommended resources and results on a dashboard.

The tool only *recommends*. It never changes production resources automatically.

> Numbers such as 2000m to 720m in the design notes are illustrative examples,
> not measured results. Real results go in `results/` once tests are run.

## Architecture

```
Locust --> Sample app (Kind/EKS) --> Prometheus --> Python engine --> SLO validator --> Dashboard
```

## Project structure

| Folder | Purpose |
|---|---|
| `sample-app/` | TechStore test e-commerce app (Flask), Dockerfile |
| `k8s/` | Kind config, Deployment, Service |
| `monitoring/` | Prometheus and Grafana configuration |
| `engine/` | Collector, analyzer, optimizer, SLO validator |
| `load-testing/` | Locust scripts |
| `dashboard/` | Dashboard (later phase) |
| `results/` | Measured before/after results |
| `docs/` | Architecture, algorithm notes, project tracker |
| `tests/` | Unit tests |

## Quick start

### 1. Run the sample app locally
```bash
cd sample-app
python -m venv venv
venv\Scripts\activate          # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000 and check `/health`, `/fast`, `/work?seconds=1`,
`/api/products`, `/metrics`.

### 2. Run the tests
```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

### 3. Docker
```bash
cd sample-app
docker build -t sample-app:v1 .
docker run -p 5000:5000 sample-app:v1
```

### 4. Kind (Phase 3)
```bash
kind create cluster --config k8s/kind-config.yaml
kind load docker-image sample-app:v1 --name rightsizer
kubectl create secret generic sample-app-secret --from-literal=secret-key=<choose-a-random-value>
kubectl apply -f k8s/
```
App is then at http://localhost:8080.

The `k8s/` directory is the single source for Kubernetes manifests. Its Deployment and Service
use the `app: sample-app` label, and `monitoring/sample-app-servicemonitor.yaml` selects that
Service on its named `http` port in the `default` namespace. The monitoring resources are
configured but have not been verified against a live Kind cluster.

### 5. Load test
```bash
pip install locust
locust -f load-testing/locustfile.py --host http://localhost:8080
```

## Sample app endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Storefront page |
| `GET /api/products`, `/api/products/<id>` | Product list and details |
| `GET/POST/PATCH/DELETE /api/cart...` | Cart (session cookie) |
| `POST /api/checkout` | Demo checkout |
| `GET /fast` | Cheap request |
| `GET /work?seconds=N` | CPU-heavy request (0.1 to 5 s) |
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics |

## Status

See [docs/project-tracker.md](docs/project-tracker.md).
