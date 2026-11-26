# AGENTS.md

Guidance for AI coding assistants (Claude, ChatGPT, Copilot, etc.) working in this repository.
Read this file first. It describes the project, the current folder structure and the rules to follow.

## 1. Project in one paragraph

An **SLO-driven Kubernetes right-sizing tool**. A Python engine reads CPU, memory and
application metrics from Prometheus, calculates recommended CPU/memory requests using
statistics and safety margins, and validates each recommendation with Locust load tests
against SLOs (P95 latency, error rate, availability). Results are shown on a dashboard.
The tool **recommends only**. It never changes production resources automatically.

## 2. IMPORTANT: the structure was reorganized

Earlier versions of this repo (and earlier AI chats) used a different layout. Use the layout below.

| Old (do not use) | New (use this) |
|---|---|
| `testing-app/` | `sample-app/` |
| Flask `debug=True` always on | Debug off by default; set `FLASK_DEBUG=1` locally only |
| App run with `python app.py` in containers | Run with **gunicorn** (`gunicorn.conf.py`) |
| No metrics endpoint | `GET /metrics` (prometheus-client) |
| Sample endpoints `/products` | `/api/products`, `/api/products/<id>`, `/api/cart/...`, `/api/checkout` |
| Everything loose in the root | Separate folders per module (below) |

If an older instruction, chat or file mentions `testing-app`, `/products`, or a plain
`python app.py` Dockerfile, treat it as outdated and map it to the new structure.

## 3. Folder structure

```
SLO-Driven-Right-Sizing-tool/
├── README.md              Project overview and quick start
├── AGENTS.md              This file
├── .gitignore
├── requirements-dev.txt   Installs everything for development and tests
├── docs/                  architecture.md, algorithm.md, project-tracker.md
├── sample-app/            TechStore test app (Flask + gunicorn)
│   ├── app.py             Routes, session cart, /health /fast /work /metrics
│   ├── gunicorn.conf.py   Workers/threads, Prometheus multiprocess cleanup
│   ├── Dockerfile
│   ├── requirements.txt   Flask, gunicorn, prometheus-client
│   ├── templates/index.html
│   └── static/style.css, script.js
├── k8s/                   kind-config.yaml, deployment.yaml, service.yaml
├── monitoring/            Prometheus/Grafana config (Helm values, dashboards)
├── engine/                Python optimization engine
│   ├── config.py          ALL tunable numbers (margins, SLO targets, floors)
│   ├── collector.py       Prometheus HTTP API queries
│   ├── analyzer.py        percentile, summarize
│   ├── optimizer.py       recommendation formulas
│   ├── slo_validator.py   pass/fail against SLO targets
│   └── requirements.txt
├── load-testing/          locustfile.py
├── dashboard/             (empty until Phase 9)
├── results/               Measured before/after data (CSV/JSON ignored by git)
├── scripts/               Helper scripts
└── tests/                 test_engine.py, test_sample_app.py
```

## 4. Sample app facts

- Endpoints: `/`, `/api/products`, `/api/products/<id>`, `/api/cart` (GET), `/api/cart/items` (POST),
  `/api/cart/items/<id>` (PATCH, DELETE), `/api/checkout` (POST), `/fast`, `/work?seconds=0.1..5`,
  `/health`, `/metrics`.
- The cart is stored in a **signed session cookie**, so all replicas must share the same
  `SECRET_KEY` (env var; from a Kubernetes Secret in the cluster).
- `/work` burns CPU for the requested number of seconds (busy loop). It is the main CPU-load generator.
- Metrics exposed: `http_requests_total{method,endpoint,status}` and
  `http_request_duration_seconds{method,endpoint}` (histogram). CPU and memory come from the cluster
  (cAdvisor / kube-state-metrics), not from the app.
- gunicorn uses several worker processes, so `PROMETHEUS_MULTIPROC_DIR` is set in the Dockerfile.
  Do not remove it, or `/metrics` will show only one worker's data.
- One Python process uses about 1 CPU core (GIL). `WORKERS` and `THREADS` env vars decide how much
  CPU the app can consume. Treat them as experiment variables and record the values used in `results/`.

## 5. Engine facts

- Starting heuristics (not VPA's algorithm, not guaranteed safe):
  CPU request = P95 CPU x 1.20, memory request = P95 memory x 1.25.
- CPU request, CPU limit, memory request and memory limit are **four separate values**.
  Do not set limits equal to requests automatically.
- SLO targets (defaults in `engine/config.py`): P95 latency below 200 ms, error rate below 1%,
  availability at least 99.9%.
- Validate SLOs over a meaningful window with enough requests. A short test cannot prove availability.
- Memory needs extra caution (OOMKill risk): consider peak usage and OOM events.

## 6. Rules for AI assistants

1. **Keep the structure.** Put code in the folder it belongs to. Do not create parallel folders
   (for example a second `testing-app`).
2. **No hardcoded thresholds.** Margins, SLO targets and floors go in `engine/config.py`.
3. **Illustrative is not measured.** Numbers like 2000m to 720m or 150 ms to 170 ms are examples from
   design notes. Never present them as real results. Only data in `results/` is measured.
4. **Recommend, don't apply.** Do not add code that patches live Deployments unless explicitly asked.
5. **Never commit secrets** (AWS keys, tokens, `.env`, kubeconfig). `.gitignore` covers common cases.
6. **Keep `main` runnable.** Work on a branch per module (for example `feature/dockerize-app`).
7. **Small, clear commits**, one per finished step, with descriptive messages.
8. **Update docs with code.** If you change endpoints, folders or config, update `README.md`, this file
   and `docs/project-tracker.md` in the same change.
9. **Add or update tests** in `tests/` for engine logic and app endpoints.
10. **Do not jump ahead.** Follow the phase order in `docs/project-tracker.md`. Explain changes simply:
    the project owner is learning Kubernetes, Prometheus and the engine step by step.
11. **Control AWS cost.** Develop locally on Kind first. Any AWS resource created must have a teardown step.
12. **Say what you could not verify.** If you did not run something, state that plainly.

## 7. Common commands

```bash
# Run app locally
cd sample-app && pip install -r requirements.txt && python app.py

# Tests (from repo root)
pip install -r requirements-dev.txt
python -m pytest tests

# Docker
cd sample-app && docker build -t sample-app:v1 . && docker run -p 5000:5000 sample-app:v1

# Kind
kind create cluster --config k8s/kind-config.yaml
kind load docker-image sample-app:v1 --name rightsizer
kubectl create secret generic sample-app-secret --from-literal=secret-key=<random>
kubectl apply -f k8s/

# Load test
locust -f load-testing/locustfile.py --host http://localhost:8080
```

## 8. Current status (update as work progresses)

- Done: concepts and design notes; Flask TechStore app written; folder structure; starter engine
  helpers, Dockerfile, Kind/Kubernetes YAML, starter Locust file. The app starts locally and the
  test suite passes. The smoke script could not be run because Bash/WSL is unavailable.
- Dockerfile, Kind manifests and monitoring files are written and statically reviewed, but have
  NOT been run (Docker is unavailable here). Docker build, Kind deployment, Prometheus/Grafana
  installation and live query checks remain open. Do not mark Phase 3 done yet.
- On a machine with Docker, Kind, kubectl and Helm, from the repository root run:

  ```bash
  docker build -t sample-app:v1 ./sample-app
  kind create cluster --config k8s/kind-config.yaml
  kind load docker-image sample-app:v1 --name rightsizer
  kubectl create secret generic sample-app-secret --from-literal=secret-key="$(python -c 'import secrets; print(secrets.token_hex(32))')"
  kubectl apply -f k8s/
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  helm install monitoring prometheus-community/kube-prometheus-stack \
    -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml
  kubectl apply -f monitoring/sample-app-servicemonitor.yaml
  kubectl -n monitoring get svc
  kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
  ```

- The requested `docs/codex-task-brief-verify-deploy-monitor.md` was not present on the backup
  branch; commands above are taken from the repo's current Kubernetes and monitoring instructions.
- Full phase list: `docs/project-tracker.md`.
