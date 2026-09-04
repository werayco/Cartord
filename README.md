<div align="center">
 <img src="shared/images/cartord-logo-1.png" alt="Cartord Logo" width="700"/>

 <br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-005571?style=flat-square&logo=elasticsearch&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat-square&logo=grafana&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-000000?style=flat-square&logo=opentelemetry&logoColor=white)

![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white)
![Jaeger](https://img.shields.io/badge/Jaeger-66CFE3?style=flat-square&logo=jaeger&logoColor=white)
![Debezium](https://img.shields.io/badge/Debezium-EE3A43?style=flat-square&logoColor=white)
![GlitchTip](https://img.shields.io/badge/GlitchTip-8B5CF6?style=flat-square&logoColor=white)
![Saga Pattern](https://img.shields.io/badge/Saga_Pattern-6E56CF?style=flat-square&logoColor=white)
![Circuit Breaker](https://img.shields.io/badge/Circuit_Breaker-D97706?style=flat-square&logoColor=white)
![Microservices](https://img.shields.io/badge/Microservices-0EA5E9?style=flat-square&logoColor=white)
![Makefile](https://img.shields.io/badge/Makefile-427819?style=flat-square&logoColor=white)

</div>
<br/>

# Cartord: Event-Driven Ordering Platform

A mini e-commerce ordering system built to demonstrate production-grade backend
architecture: event-driven microservices, resilience patterns, an AI shopping
assistant, and full observability, deployed on Docker Compose or Kubernetes.

## Microservices

| Service                  | Port   | Responsibility                                                                                                                                                     |
| ------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **AI Service**           | `9000` | Conversational shopping assistant - RAG pipeline over product docs, an agent with tool-calling nodes, websocket chat, and document ingestion/embeddings (pgvector) |
| **Auth Service**         | `9001` | Registration, login, JWT issuing/validation for buyers, sellers, and admin/employee accounts                                                                       |
| **Inventory Service**    | `9002` | Product catalog and stock, source of truth (Postgres)                                                                                                              |
| **Notification Service** | `9003` | Consumes events and emails customers (pluggable provider: Resend, SMTP, or Mailpit for local dev)                                                                  |
| **Order Service**        | `9004` | Order lifecycle, orchestrates stock reservation, idempotent order placement                                                                                        |
| **Payment Service**      | `9005` | Buyer/seller wallets and payment processing                                                                                                                        |
| **Search Service**       | `9007` | Read-optimized product search (Elasticsearch)                                                                                                                      |

## Architecture Patterns

- **Event-driven communication** - Kafka, domain-partitioned topics
  (`order`, `inventory`, `payment`, `auth`, `chat`, plus a `.dlq` topic per domain)
- **Outbox + CDC** - each service writes to a local outbox table; Debezium
  tails the Postgres WAL and republishes those rows to Kafka, so DB writes
  and event publication stay atomic
- **Idempotency keys** - prevents duplicate order creation on client retries
- **Circuit breakers** - protects synchronous calls (Order → Inventory)
  from cascading failure
- **Retry with exponential backoff** - Tenacity, tuned differently for
  sync HTTP calls vs. async Kafka consumers
- **Dead Letter Queue** - captures events that exhaust retries instead
  of silently dropping them

## Observability

- **OpenTelemetry** - distributed tracing across services, exported via an
  otel-collector to **Jaeger**
- **Prometheus + Grafana** - metrics collection and dashboards
- **GlitchTip** - self-hosted, Sentry-SDK-compatible error tracking

## Infrastructure

- **PostgreSQL** (pgvector) - per-service transactional storage, plus vector
  storage for the AI service
- **Redis** - idempotency key store and caching
- **Elasticsearch** - search index
- **Kafka + Debezium** - event streaming and CDC-based outbox relay
- **Kubernetes** - deployment, StatefulSets for stateful workloads
- **Docker Compose** - local development

# System Architecture

Cartord is a small event-driven ordering platform built around several
backend services. Each service has a focused job, and they communicate
through HTTP and Kafka rather than one large monolithic app.

## Main idea

The system is designed to handle order flow in a way that is resilient and
easy to scale. The order service coordinates the main business flow, while
other services react to events and handle their own responsibilities.

## Communication style

The platform uses an event-driven approach.

- Services communicate synchronously (HTTP, behind a circuit breaker) when
  they need an immediate response - for example, Order calling Inventory to
  reserve stock.
- They also publish domain events to Kafka when important changes happen,
  via the outbox/CDC pattern described above.
- Other services subscribe to those events and react independently - Search
  reindexes on inventory changes, Notification emails customers on payment
  events, and so on.

This makes the system more flexible and helps reduce tight coupling between
services.

## Example flow

A typical order flow looks like this:

1. The client sends a request to the Order service.
2. Order validates the request and calls Inventory synchronously to reserve
   stock, rolling the reservation back if anything downstream fails.
3. Order writes the order row and an outbox event in the same transaction.
4. Debezium picks up the outbox row and publishes it to Kafka.
5. Payment consumes the order event and processes the wallet transaction.
6. Search and Notification consume the relevant events and update their own
   view of the data (search index, customer email).

## Data and storage

The project uses a distributed setup with service-specific storage.

- PostgreSQL is used for transactional data in every service.
- Redis is used for idempotency and short-lived state.
- Elasticsearch is used for search-related read models.
- Kafka is used for event streaming between services.

## Deployment

The project is prepared for container-based deployment.

- Docker Compose is used for local development.
- Kubernetes manifests (`k8s/base`, `k8s/overlays`) are included for
  cluster deployment.
- Services are packaged as separate containers and can be scaled
  independently.

---

# Running the Project

## Prerequisites

- Docker + Docker Compose
- `make`
- Python 3.10+ (only needed on the host to run the one-off init scripts)
- `openssl` is not required for JWT generation anymore because the project uses a shared HS256 secret

## 1. Create the Docker network

The compose files expect an external network named `mynet`, so create it
once before bringing anything up:

```bash
docker network create mynet
```

## 2. Configure environment variables

Copy the example env file into the location the compose files read from
and fill in real values:

```bash
cp shared/.env.example shared/compose_files/.env
```

`shared/compose_files/.env` is git-ignored - it holds the actual secrets
(DB credentials, admin bootstrap user, JWT keys, etc.) used by every
service.

## 3. Generate the JWT signing secret

Auth (and every service that verifies tokens) uses HS256 with a shared
secret. Generate one and copy it into `shared/compose_files/.env`:

```bash
make gen-secret
```

This prints a secure random secret that should be assigned to
`JWT_PRIVATE_KEY` in `shared/compose_files/.env`.

## 4. Start the stack

```bash
make run
```

This is equivalent to:

```bash
docker-compose -f shared/compose_files/docker-compose.yml up -d
docker-compose -f shared/compose_files/services.docker-compose.yml up -d
```

The first file brings up infrastructure (Postgres, Kafka, Debezium,
Elasticsearch, Redis, Prometheus, Grafana, Jaeger, otel-collector,
GlitchTip, Mailpit). The second builds and starts all seven application
services on top of it.

## 5. Initialize the platform

Once the stack is healthy, register the Debezium connectors, seed
inventory data, and create the Kafka topics:

```bash
make init
```

This is equivalent to running, in order:

```bash
python -m shared.init_scripts.debezium_setup   # registers the outbox CDC connectors in Debezium
python -m shared.init_scripts.seed             # seeds shared/inventory.json into inventory_db
python -m shared.init_scripts.create_topics    # creates the order/inventory/payment/auth/chat topics + DLQs
```

> These scripts run against `localhost`, so they're meant to be run on the
> host after `make run`, not inside a container. They need
> `shared/requirements.txt` installed, plus `python-dotenv` and `requests`.

## 6. Verify

Each service exposes a health check and interactive OpenAPI docs:

```bash
curl http://localhost:9001/api/v1/health   # auth_service
```

Swagger UI is available per service at `http://localhost:<port>/docs`
(e.g. `http://localhost:9001/docs`).

Other useful UIs once the stack is up: Kafka UI on `:8090`, Grafana on
`:3000`, Jaeger on `:16686`, GlitchTip on `:8080`, Mailpit on `:8025`.

## Other Make targets

| Command                                                                                            | What it does                                                  |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `make <service>` (e.g. `make auth`, `make order`, `make payment`, `make ai`, `make db`, `make kf`) | Tail logs for that container                                  |
| `make build-all` / `make build-<service>-service`                                                  | Build Docker images (tagged `$(IMAGE_REPO)/<service>:latest`) |
| `make push-all`                                                                                    | Push all built images                                         |
| `make services-all`                                                                                | Rebuild and start all application services                    |
| `make rebuild SERVICE_NAME=<service>`                                                              | Rebuild and restart a single service                          |
| `make recreate-all`                                                                                | Force-recreate infra + services (needed after `.env` changes) |
| `make recreate SERVICE_NAME=<service>`                                                             | Force-recreate a single service                               |
| `make stop`                                                                                        | Stop everything                                               |
| `make stop-v`                                                                                      | Stop everything and remove volumes                            |

---

# API Documentation

Full endpoint reference - base URLs, request/response payloads, and the
bearer-token auth pattern - is maintained in
[`shared/docs/setups/apis_setup.md`](shared/docs/setups/apis_setup.md).
Check that file for the current, per-service API contract rather than
relying on this README, since it's kept up to date as routes change.
