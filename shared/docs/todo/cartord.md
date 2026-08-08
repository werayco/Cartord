# Cartord TODO

## Idempotency
- [ ] Add idempotency key / event ID tracking for order service consumers
- [ ] Persist processed event IDs (per saga ID + step) to guard against duplicate Kafka delivery
- [ ] Add idempotency check before any DB write triggered by a consumed event

## Rate Limiting
- [ ] Decide rate-limiting strategy (per-user, per-IP, per-endpoint)
- [ ] Add rate-limiting middleware/dependency to public-facing endpoints
- [ ] Define limits for auth endpoints (login/register) separately from general API limits

## Outbox Pattern
- [ ] Create `outbox` table per service (event payload, topic, status, created_at)
- [ ] Write business data + outbox row in the same DB transaction
- [ ] Build poller/relay process to publish unpublished outbox rows to Kafka
- [ ] Mark outbox rows as published once Kafka ack is received

## Database Per Service (Completed)
- [ ] Provision separate database per service (auth, inventory, order, payment, notification, search)
- [ ] Update each service's `settings.py` with its own `DATABASE_URL`
- [ ] Split Alembic into per-service `alembic/` directories with their own `env.py`
- [ ] Remove any direct cross-service DB/table access; replace with API calls or events

## README
- [ ] Write project overview and architecture summary
- [ ] Document services list and responsibilities
- [ ] Document local setup (docker-compose, env vars, migrations)
- [ ] Document event/topic naming conventions and saga flow

## System Design
- [ ] Finalize saga flow diagram (order → inventory → payment → notification)
- [ ] Define compensating actions for each step (e.g. inventory release, payment refund)
- [ ] Define Kafka topic and event schema conventions (event name, payload shape, saga/correlation ID)
- [ ] Document consumer group naming per service
- [ ] Add a circuit breaker between order service and inventory service when reservation is made

## Extras (Completed)
- [ ] Configure Prometheus and Grafana
- [ ] Access Token Rotation and Revoking

