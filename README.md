
 # FastAPI Observability

 ![Monitoring](https://img.shields.io/badge/Monitoring-Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
 ![Visualization](https://img.shields.io/badge/Visualization-Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)
 ![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)

 Short project used to practice instrumentation, Prometheus scraping, Grafana dashboards and lightweight stress testing with Locust. This repository contains the code and configuration used during the exercise — only the items actually implemented are documented here.

 **Scope implemented**
 - Instrumented FastAPI app exposing `/metrics` using `prometheus_client` and `prometheus-fastapi-instrumentator`.
 - Docker Compose stack including: the FastAPI app (`api`), PostgreSQL (`db`), Prometheus and Grafana.
 - Fixed runtime issues that prevented the API from starting (missing packages and service port binding).
 - Upgraded database driver to `psycopg` (psycopg v3) for Python 3.14 compatibility.
 - Basic stress testing with `locust` and adjustments to stress volume to avoid overloading the endpoint during tests.

 Why this project exists: learning and practising observability patterns (metrics, scraping, dashboards) and how to verify through load tests.

 **Repository layout (relevant parts)**

 - `app/` — FastAPI app, database config and routes.
 - `docs/` — Brief and watch notes about PromQL and observability used for the exercise.
 - `prometheus/` — Prometheus configuration used to scrape the API.
 - `screenshots/` — Verification screenshots (check `screenshots/` for examples of dashboards and test results).
 - `docker-compose.yml` — Local compose stack used for testing and verification.

 **Quick architecture**

 ```mermaid
 flowchart LR
   A[FastAPI app] -->|HTTP /metrics| B(Prometheus)
   A -->|Reads/Writes| C[(Postgres DB)]
   B --> D[Grafana]
   E[Locust] -->|Load| A
 ```

 ---

 ## How the issues were resolved (concise)

 1. First startup failure: missing packages & wrong binding

 - Cause: Some required packages were not installed in the environment and the app/uvicorn process was not binding to the expected interface/port inside its container.
 - Fix applied: Installed missing dependencies (via `uv sync`) and ensured the server binds to `0.0.0.0:3030` so Docker and Prometheus can reach it.

 2. Scraping / connection errors during stress tests

 - Cause: psycopg2 incompatibility with Python 3.14 caused the app to crash in some environments; in other cases, under heavy locust load the endpoint became unresponsive.
 - Fix applied: Upgraded to `psycopg` (psycopg v3) and reduced stress volume (fewer concurrent users / slower spawn rate) to keep the endpoint responsive during verification.

 ---

 ## Reproduce (minimal)

 1. Install project dependencies (this project uses `uv` to manage dependencies):

 ```bash
 # in project root
 uv sync
 ```

 2. Start the stack (Docker Compose):

 ```bash
 docker compose up -d
 ```

 3. Verify endpoints:

 ```bash
 # API metrics
 curl http://localhost:3030/metrics

 # Prometheus UI
 open http://localhost:9090/targets

 # Grafana UI
 open http://localhost:4040
 ```

 Notes:
 - If you run heavy load tests, reduce `--users` and `--spawn-rate` for `locust` to avoid overwhelming the single-node test environment. Example used for verification: `locust -f locustfile.py --host http://localhost:3030 --users 50 --spawn-rate 5`.

 ---

 ## Files of interest

 - `app/database.py` — contains `DATABASE_URL` (uses `postgresql+psycopg://...` after the upgrade).
 - `pyproject.toml` — project deps, updated to use `psycopg>=3.1.0`.
 - `docker-compose.yml` — compose stack used in tests.
 - `prometheus/prometheus.yml` — scrape configuration for the API.

## Verification & Results (embedded screenshots & observations)

Below are the verification images, embedded inline as thumbnails for quick inspection. Click any thumbnail to open the full-size image in the `screenshots/` folder.

### Prometheus & metrics

<div style="display:flex; gap:12px; flex-wrap:wrap;">
  <figure style="width:220px; text-align:center;">
    <a href="screenshots/prometheus%20fastapi%20up.png"><img src="screenshots/prometheus%20fastapi%20up.png" alt="Prometheus target up" width="200"/></a>
    <figcaption><strong>Prometheus target UP</strong><br/>Prometheus scrapes `/metrics` (Phase 2).</figcaption>
  </figure>

  <figure style="width:220px; text-align:center;">
    <a href="screenshots/metrics%20endpoint.png"><img src="screenshots/metrics%20endpoint.png" alt="metrics endpoint" width="200"/></a>
    <figcaption><strong>Metrics endpoint</strong><br/>Raw counters/histograms exposed by app (used for PromQL).</figcaption>
  </figure>

  <figure style="width:220px; text-align:center;">
    <a href="screenshots/items_created_total.png"><img src="screenshots/items_created_total.png" alt="items_created_total" width="200"/></a>
    <figcaption><strong>items_created_total</strong><br/>Custom counter for `rate()`/`increase()` tests.</figcaption>
  </figure>

  <figure style="width:220px; text-align:center;">
    <a href="screenshots/http_request_total_by_method.png"><img src="screenshots/http_request_total_by_method.png" alt="http request by method" width="200"/></a>
    <figcaption><strong>HTTP by method</strong><br/>Label filtering and aggregation example (Mission 1 Q2).</figcaption>
  </figure>

  <figure style="width:220px; text-align:center;">
    <a href="screenshots/all_CRUD_operations.png"><img src="screenshots/all_CRUD_operations.png" alt="CRUD operations" width="200"/></a>
    <figcaption><strong>CRUD operations</strong><br/>Business counters used for dashboards (Mission 2).</figcaption>
  </figure>
</div>

---

### Troubleshooting evidence (errors that were fixed)

<div style="display:flex; gap:12px; flex-wrap:wrap;">
  <figure style="width:320px; text-align:center;">
    <a href="screenshots/api%20error%201.png"><img src="screenshots/api%20error%201.png" alt="API error 1" width="300"/></a>
    <figcaption><strong>API error 1</strong><br/>Startup failure (missing deps / binding); fixed by `uv sync` & bind `0.0.0.0:3030`.</figcaption>
  </figure>

  <figure style="width:320px; text-align:center;">
    <a href="screenshots/api%20error%202.png"><img src="screenshots/api%20error%202.png" alt="API error 2" width="300"/></a>
    <figcaption><strong>API error 2</strong><br/>Driver incompatibility (psycopg2) — upgraded to `psycopg` v3.</figcaption>
  </figure>
</div>

---

### Stress tests (Locust) — observations and conclusions

<div style="display:flex; gap:12px; flex-wrap:wrap;">
  <figure style="width:260px; text-align:center;">
    <a href="screenshots/users%2050%20spawn%20rate%2010.png"><img src="screenshots/users%2050%20spawn%20rate%2010.png" alt="Locust 50 users" width="240"/></a>
    <figcaption><strong>Light — 50 users</strong><br/>Stable RPS and low P95 latency; no notable errors (baseline smoke test).</figcaption>
  </figure>

  <figure style="width:260px; text-align:center;">
    <a href="screenshots/users%20100%20spawn%20rate%2010.png"><img src="screenshots/users%20100%20spawn%20rate%2010.png" alt="Locust 100 users" width="240"/></a>
    <figcaption><strong>Medium — 100 users</strong><br/>Higher latency and occasional errors; indicates emerging contention under load.</figcaption>
  </figure>

  <figure style="width:260px; text-align:center;">
    <a href="screenshots/users%201000%20spawn%20rate%2020.png"><img src="screenshots/users%201000%20spawn%20rate%2020.png" alt="Locust 1000 users" width="240"/></a>
    <figcaption><strong>Heavy — 1000 users</strong><br/>High error rate and timeouts; system overwhelmed, informs safe test limits.</figcaption>
  </figure>
</div>

**Summary of how these results answer the brief**

- <strong>Mission 1 (PromQL)</strong> — `metrics endpoint` and `items_created_total` provide raw metrics to practise `rate()` and `increase()`; `http_request_total_by_method` shows label filtering.
- <strong>Mission 2 (Dashboards)</strong> — `all_CRUD_operations` demonstrates dashboard-ready aggregations and metric naming for Phase 3 panels.
- <strong>Phase 4 (Stress Testing)</strong> — The Locust tests demonstrate baseline → contention → overload and were used to set safe test limits.

> For background on the PromQL functions and label matchers used to build these queries, see `docs/OBSERVABILITY_WATCH.md` (Mission 1 & 2 theories and examples).
> Note: For PromQL examples and conceptual answers used during the exercises, see `docs/OBSERVABILITY_WATCH.md` (Mission 1 & 2 explanations). The watch file explains `rate()` vs `increase()`, label matching, and `histogram_quantile()` which were used to build the dashboard panels and queries above.

---

 Project maintained for learning purposes — not intended as production-grade monitoring scaffolding. Use as a starting point for instrumenting FastAPI apps and practising Prometheus + Grafana workflows.

