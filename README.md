<div align="center">
 <img src="shared/images/cartord-logo-ii-nbg.png" alt="Cartord Logo" width="900"/>

 <sub>The Cartord logo was designed by me using Adobe Illustrator. Click <a href="shared/images/cartord-logo.ai">here</a> to view the editable file.</sub>

 <br/>

![Status](https://img.shields.io/badge/status-Work%20In%20Progress-orange?style=flat-square)

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

## Table of Contents

- [Microservices](#microservices)
- [Architecture Patterns](#architecture-patterns)
- [Observability](#observability)
- [Infrastructure](#infrastructure)
- [System Architecture](#system-architecture)
- [Running with Docker Compose](#running-with-docker-compose)
- [Running on Kubernetes](#running-on-kubernetes)
- [Accessing Kubernetes Services with kubefwd](#accessing-kubernetes-services-with-kubefwd)
- [Other Make Targets](#other-make-targets)
- [API Documentation](#api-documentation)

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

---

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

# Running with Docker Compose

## Prerequisites

- Docker + Docker Compose
- `make`
- Python 3.10+ (only needed on the host to run the one-off init scripts)
- No `openssl` needed for JWT generation: the project uses a shared HS256 secret

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

## 6. Verify

Each service exposes a health check and interactive OpenAPI docs:

```bash
curl http://localhost:9001/api/v1/health   # auth_service
```

Swagger UI is available per service at `http://localhost:<port>/docs`
(e.g. `http://localhost:9001/docs`).

Other useful UIs once the stack is up:

| UI       | URL                      |
| -------- | ------------------------ |
| Kafka UI | `http://localhost:8090`  |
| Grafana  | `http://localhost:3000`  |
| Jaeger   | `http://localhost:16686` |
| GlitchTip| `http://localhost:8080`  |
| Mailpit  | `http://localhost:8025`  |

---

# Running on Kubernetes

## 1. Create the secrets and install the Helm chart

Create or update the `cartord-secrets` Secret from
`shared/compose_files/.env.k8s`, then install or upgrade the Helm chart:

```bash
make k8s-secret
make k8s
```

> **Note:** the chart runs Kafka with a single broker, so its internal topic
> replication settings are set to `1`.

## 2. Seed inventory and create Kafka topics

Run the Kubernetes Job to seed inventory and create the Kafka topics:

```bash
make k8s-init
kubectl get jobs -n cartord -w
```

The Job reads `INVENTORY_DATABASE_URL` from the `cartord-secrets` Secret and
connects to the in-cluster Kafka Service. Find its generated name with
`kubectl get jobs -n cartord`, then inspect its output:

```bash
kubectl logs -n cartord job/<generated-job-name>
```

## 3. Register the Debezium connectors

The order, inventory, payment, and AI services create their outbox tables
during startup, so wait until they are ready before registering the
connectors:

```bash
kubectl rollout status deployment/order-service -n cartord --timeout=5m
kubectl rollout status deployment/inventory-service -n cartord --timeout=5m
kubectl rollout status deployment/payment-service -n cartord --timeout=5m
kubectl rollout status deployment/ai-service -n cartord --timeout=5m
kubectl rollout status deployment/debezium-connect -n cartord --timeout=5m
make k8s-debezium-register
kubectl get jobs -n cartord -w
```

The connector-registration Job uses the `debezium-connect` and
`cartord-postgres` Kubernetes Services and reads PostgreSQL credentials from
`cartord-secrets`. Job logs are available with:

```bash
kubectl logs -n cartord job/<generated-job-name>
```

---

# Accessing Kubernetes Services with kubefwd

[kubefwd](https://github.com/txn2/kubefwd) forwards every service in a
namespace to your local machine at once, so you can reach them by their
Kubernetes service names instead of juggling one `kubectl port-forward` per
service.

## 1. Install kubefwd

### Ubuntu

```bash
# Set the architecture (amd64 for most machines, arm64 for ARM)
ARCH=$(dpkg --print-architecture)

# Get the latest version tag
VERSION=$(curl -s https://api.github.com/repos/txn2/kubefwd/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')

# Download and install
wget https://github.com/txn2/kubefwd/releases/download/v${VERSION}/kubefwd_${ARCH}.deb
sudo dpkg -i kubefwd_${ARCH}.deb
```

Run `kubefwd` to confirm it installed successfully. It should print its usage
and available commands:

```bash
kubefwd
```

> If the `.deb` filename differs, check the exact asset name on the
> [releases page](https://github.com/txn2/kubefwd/releases) and adjust the
> `wget` line. Other install options (Homebrew, binary tarball) are listed there too.

### Windows

Using [Scoop](https://scoop.sh):

```powershell
scoop install kubefwd
```

Or download the Windows `.zip` from the
[releases page](https://github.com/txn2/kubefwd/releases), extract
`kubefwd.exe`, and add its folder to your `PATH`.

Then run `kubefwd` in PowerShell to confirm it installed successfully.

> **Tip:** run kubefwd on the same OS where your cluster runs. If minikube runs
> on Windows, use the Windows install. A WSL terminal has its own kubeconfig
> and cannot reach a Windows minikube by default.

## 2. Forward all Cartord services

Make sure the stack is up first (`kubectl get pods -n cartord`).

### Ubuntu

```bash
sudo -E kubefwd svc -n cartord
```

kubefwd needs root because it edits `/etc/hosts` and adds loopback IP
aliases. `-E` preserves your environment so `sudo` can find your
`KUBECONFIG`. If you use a non-default kubeconfig or context, pass them
explicitly (use an absolute path, not `~`):

```bash
sudo -E kubefwd svc -n cartord --kubeconfig /home/<user>/.kube/config --context <context-name>
```

Leave it running in its own terminal. Each service in the `cartord`
namespace is now reachable by its service name (see
[Service URLs](#service-urls) below), for example:

```bash
curl http://auth-service:9001/api/v1/health
```

### Windows

Open **PowerShell as Administrator** (right-click PowerShell, then
**Run as administrator**) and run:

```powershell
kubefwd svc -n cartord
```

Leave it running. Services are then reachable by name from Windows apps and
browsers. They will not resolve inside WSL, which has its own `/etc/hosts`.

## Service URLs

While kubefwd is running, these URLs work from your machine.

**Application services**

| Service                | URL                             |
| ---------------------- | ------------------------------- |
| `ai-service`           | `http://ai-service:9000`        |
| `auth-service`         | `http://auth-service:9001`      |
| `inventory-service`    | `http://inventory-service:9002` |
| `notification-service` | `http://notification-service:9003` |
| `order-service`        | `http://order-service:9004`     |
| `payment-service`      | `http://payment-service:9005`   |
| `search-service`       | `http://search-service:9007`    |

Swagger UI is available per service at `/docs`
(e.g. `http://auth-service:9001/docs`).

**Infrastructure**

| Component     | URL / address                          |
| ------------- | -------------------------------------- |
| Grafana       | `http://grafana` (port 80)             |
| Prometheus    | `http://prometheus`                    |
| Jaeger UI     | `http://jaeger-query:16686`            |
| GlitchTip     | `https://errors.devrayco.name.ng`     |
| Elasticsearch | `http://elasticsearch-master:9200`     |
| Debezium      | `http://debezium-connect:8083`         |
| Postgres      | `cartord-postgres:5432`                |
| Kafka         | `cartord-kafka:9092`                   |
| Redis         | `cartord-redis-master:6379`            |

## What kubefwd changes on your machine

kubefwd edits your real hosts file in place (`/etc/hosts` on Linux,
`C:\Windows\System32\drivers\etc\hosts` on Windows); it does not create a
separate temporary hosts file.

- **On start**, it adds an entry for each forwarded service, mapping the
  service name to a loopback IP (like `127.1.27.1`), and brings up those
  loopback aliases on your machine.
- **On exit** (`Ctrl+C` or a normal termination), it removes those entries,
  so the changes are temporary.
- **Backup**: it also saves a copy of your original hosts file as
  `hosts.original` in the home directory of the user running it, which is why
  it needs root.

## Troubleshooting

- **Stale entries after a crash.** If kubefwd is killed abruptly (`kill -9`,
  crash, power loss), cleanup may not run and its lines can remain in
  `/etc/hosts`. Delete just those lines by hand. Restore the backup only if
  you have made no other `/etc/hosts` changes since kubefwd started:

  ```bash
  sudo cp ~/hosts.original /etc/hosts
  ```

- **Can't find the kubeconfig under `sudo`.** Pass `--kubeconfig` with an
  absolute path, and confirm `kubectl get svc -n cartord` works without sudo.
- **Running on minikube.** Make sure the cluster is running
  (`minikube status`) before starting kubefwd.

---

# Other Make Targets

| Command                                                                                             | What it does                                                   |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `make <service>` (e.g. `make auth`, `make order`, `make payment`, `make ai`, `make db`, `make kf`) | Tail logs for that container                                   |
| `make build-all` / `make build-<service>-service`                                                   | Build Docker images (tagged `$(IMAGE_REPO)/<service>:latest`)  |
| `make push-all`                                                                                     | Push all built images                                          |
| `make services-all`                                                                                 | Rebuild and start all application services                     |
| `make rebuild SERVICE_NAME=<service>`                                                               | Rebuild and restart a single service                           |
| `make recreate-all`                                                                                 | Force-recreate infra + services (needed after `.env` changes)  |
| `make recreate SERVICE_NAME=<service>`                                                              | Force-recreate a single service                                |
| `make stop`                                                                                         | Stop everything                                                |
| `make stop-v`                                                                                       | Stop everything and remove volumes                             |

---

# API Documentation

Full endpoint reference - base URLs, request/response payloads, and the
bearer-token auth pattern - is maintained in
[`shared/docs/setups/apis_setup.md`](shared/docs/setups/apis_setup.md).
Check that file for the current, per-service API contract rather than
relying on this README, since it's kept up to date as routes change.