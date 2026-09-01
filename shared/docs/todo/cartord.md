# Cartord TODO

## Idempotency(Completed)

- [ ] Add idempotency key / event ID tracking for order service consumers (completed)

- [ ] Persist processed event IDs (per saga ID + step) to guard against duplicate Kafka delivery

- [ ] Add idempotency check before any DB write triggered by a consumed event

## Rate Limiting

- [ ] Decide rate-limiting strategy (per-user, per-IP, per-endpoint)

- [ ] Add rate-limiting middleware/dependency to public-facing endpoints

- [ ] Define limits for auth endpoints (login/register) separately from general API limits

## Outbox Pattern (12/08/26, in progress -- Completed 18/08/26)

- [ ] Create `outbox` table per service (event payload, topic, status, created_at) (completed)

- [ ] Write business data + outbox row in the same DB transaction

- [ ] Build poller/relay process to publish unpublished outbox rows to Kafka

- [ ] Mark outbox rows as published once Kafka ack is received

## Database Per Service (Completed)

- [ ] Provision separate database per service (auth, inventory, order, payment, notification, search)

- [ ] Update each service's `settings.py` with its own `DATABASE_URL`

- [ ] Split Alembic into per-service `alembic/` directories with their own `env.py`

- [ ] Remove any direct cross-service DB/table access; replace with API calls or events

## System Design

- [ ] Finalize saga flow diagram (order → inventory → payment → notification)

- [ ] Define compensating actions for each step (e.g. inventory release, payment refund)

- [ ] Define Kafka topic and event schema conventions (event name, payload shape, saga/correlation ID)

- [ ] Document consumer group naming per service

- [ ] Add a circuit breaker between order service and inventory service when reservation is made

## AI / Agentic Layer

- [ ] Define LangGraph workflow

- [ ] Implement RAG indexing pipeline

- [ ] Implement RAG retrieval pipeline

## Observability

- [ ] Finish OpenTelemetry instrumentation (tracing across services)

- [ ] Finish centralized logging setup

- [ ] Finish Prometheus metrics instrumentation per service (Grafana dashboards already configured)

## Kubernetes / Deployment

- [ ] Finish k8s integration in dev environment

- [ ] Deploy to EC2

- [ ] Deploy to EKS

## Testing

- [ ] Create test cases for each service (auth, inventory, order, payment, notification, search, ai)

## Saga Pattern

- [ ] Finish up saga pattern implementation (ties into the compensating-actions and flow diagram work under System Design)

## Extras (Completed)

- [ ] Configure Prometheus and Grafana

- [ ] Access Token Rotation and Revoking (completed)