# Prometheus RED Metrics Setup

This document describes how Prometheus metrics were added to the FastAPI services using the RED framework:

- **Rate**: number of requests handled over time
- **Errors**: requests returning error status codes
- **Duration**: request latency

## Instrumentation

Each service uses `prometheus-fastapi-instrumentator==7.1.0`. The dependency is listed in every service's `requirements.txt`.

The existing telemetry setup for each service now also creates a Prometheus instrumentator:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(
    app,
    endpoint="/api/v1/metrics",
    include_in_schema=False,
)
```

This was added to the following files:

- `services/ai_service/app/services/telemetry.py`
- `services/auth_service/app/services/telemetry.py`
- `services/inventory_service/app/services/telemetry.py`
- `services/notification_service/app/services/telemetry.py`
- `services/order_service/app/services/telemetry.py`
- `services/payment_service/app/services/telemetry.py`
- `services/search_service/app/services/telemetry.py`

The metrics endpoint is hidden from the generated OpenAPI schema but remains available to Prometheus.

## Service Metrics Endpoints

Every service exposes metrics at `/api/v1/metrics`:

| Service      | Metrics target                             |
| ------------ | ------------------------------------------ |
| AI           | `ai_service:9000/api/v1/metrics`           |
| Auth         | `auth_service:9001/api/v1/metrics`         |
| Inventory    | `inventory_service:9002/api/v1/metrics`    |
| Notification | `notification_service:9003/api/v1/metrics` |
| Order        | `order_service:9004/api/v1/metrics`        |
| Payment      | `payment_service:9005/api/v1/metrics`      |
| Search       | `search_service:9007/api/v1/metrics`       |

## Prometheus Scraping

Prometheus is configured in `shared/bind_volumes/prometheus.yml` with a 20-second scrape and evaluation interval. Each service has a separate scrape job using the Docker service name and internal port.

The service containers and Prometheus must share the external Docker network named `mynet`. This is configured in both compose files:

- `shared/compose_files/docker-compose.yml`
- `shared/compose_files/services.docker-compose.yml`

## Starting the Stack

Create the external network once if it does not exist:

```powershell
docker network create mynet
```

Start infrastructure services first:

```powershell
docker compose -f shared/compose_files/docker-compose.yml up -d
```

Build and start the application services so the new Python dependency is installed:

```powershell
docker compose -f shared/compose_files/services.docker-compose.yml up --build -d
```

Prometheus is available at:

```text
http://localhost:9090
```

## Checking Metrics

Check a service endpoint directly from the host when its port is published:

```powershell
Invoke-WebRequest http://localhost:9000/api/v1/metrics
```

From inside the Docker network, use the service name instead:

```text
http://ai_service:9000/api/v1/metrics
```

In the Prometheus UI, open **Status > Targets** and confirm that all seven service targets are `UP`.

## RED Queries

Request rate across all services:

```promql
sum by (job) (rate(http_requests_total[5m]))
```

Request rate for one service:

```promql
sum(rate(http_requests_total{job="ai_service"}[5m]))
```

Server error rate:

```promql
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
```

Error percentage:

```promql
100 * sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
  / sum by (job) (rate(http_requests_total[5m]))
```

Request duration at the 95th percentile:

```promql
histogram_quantile(
  0.95,
  sum by (job, le) (rate(http_request_duration_seconds_bucket[5m]))
)
```

The instrumentator also exports request-in-progress and request/response size metrics. Use the labels such as `job`, `handler`, `method`, and `status` to filter dashboards and alerts.

## Troubleshooting

### Target is down

Check that both compose projects are running and that their containers are attached to `mynet`:

```powershell
docker network inspect mynet
docker ps
```

A service hostname such as `kafka`, `postgres`, or `otel-collector` will not resolve if the infrastructure compose stack is stopped.

### Metrics package changes are not visible

Rebuild the service image after changing `requirements.txt`:

```powershell
docker compose -f shared/compose_files/services.docker-compose.yml up --build -d ai_service
```

Repeat for the service being updated.
