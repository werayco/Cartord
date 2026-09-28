# PromQL Queries

Reference queries for `http_requests_total` and related metrics across
`auth_service`, `inventory_service`, `order_service`, `payment_service`,
`notification_service`, and `search_service`.

## Request rate

```promql
# Raw rate, per handler/instance/method/status (noisy — many series)
rate(http_requests_total[5m])

# Request rate per service (recommended default)
sum by (job) (rate(http_requests_total[5m]))

# Request rate per service + endpoint
sum by (job, handler) (rate(http_requests_total[5m]))
```

## Error rate

```promql
# Raw error request rate (5xx) per service
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))

# Error ratio (0–1) per service
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
/
sum by (job) (rate(http_requests_total[5m]))

# 4xx (client error) rate per service
sum by (job) (rate(http_requests_total{status=~"4.."}[5m]))
```

## Success vs error breakdown

```promql
sum by (job, status) (rate(http_requests_total[5m]))
```

## Latency (requires histogram metrics, e.g. http_request_duration_seconds_bucket)

```promql
# p50 latency per service
histogram_quantile(0.50, sum by (job, le) (rate(http_request_duration_seconds_bucket[5m])))

# p95 latency per service
histogram_quantile(0.95, sum by (job, le) (rate(http_request_duration_seconds_bucket[5m])))

# p99 latency per service
histogram_quantile(0.99, sum by (job, le) (rate(http_request_duration_seconds_bucket[5m])))
```

## Health checks

```promql
# Health-check hit rate per service
sum by (job) (rate(http_requests_total{handler="/api/v1/health"}[5m]))

# Is the target up? (1 = up, 0 = down)
up{job=~"auth_service|inventory_service|order_service|payment_service|notification_service|search_service"}
```

## Traffic volume (totals, not rates)

```promql
# Total requests in the last 1h per service (increase, not rate)
sum by (job) (increase(http_requests_total[1h]))
```

## Notes
- `http_requests_created` is **not** a request count — it's an
  auto-generated timestamp gauge from `prometheus_client` Counters.
  Always use `http_requests_total` (or its `rate`/`increase`) instead.

- Swap `[5m]` for a shorter window (e.g. `[1m]`) if you want the graph
  to react faster to spikes, at the cost of a noisier line.

- Set the panel legend format to something like `{{job}} - {{status}}`
  to keep multi-series panels readable.