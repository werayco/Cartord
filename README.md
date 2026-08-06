# Cartord: Event-Driven Ordering Platform

A mini ordering system built to demonstrate production-grade backend
architecture: event-driven microservices, resilience patterns, and
full observability, deployed on Kubernetes.

## Microservices
- **Auth Service** - registration, login, JWT issuing/validation
- **Inventory Service** - product catalog and stock, source of truth (Postgres)
- **Order Service** - order lifecycle, orchestrates stock reservation
- **Search Service** - read-optimized product search (Elasticsearch)
- **Notification Service** - consumes events, sends customer notifications

## Architecture Patterns
- **Event-driven communication** - Kafka, domain-partitioned topics
  (`order`, `inventory`, `user`, `notification`)
- **Idempotency keys** - prevents duplicate order creation on client retries
- **Circuit breakers** - protects synchronous calls (Order → Inventory)
  from cascading failure
- **Retry with exponential backoff** - Tenacity, tuned differently for
  sync HTTP calls vs. async Kafka consumers
- **Dead Letter Queue** - captures events that exhaust retries instead
  of silently dropping them

## Observability
- **OpenTelemetry** - distributed tracing across services
- **GlitchTip** - error tracking / exception reporting
- **Langfuse** - LLM observability

## Infrastructure
- **PostgreSQL** - per-service transactional storage
- **Redis** - idempotency key store
- **Elasticsearch** - search index
- **Kubernetes** - deployment, StatefulSets for stateful workloads
- **Docker Compose** - local development

# System architecture

This project is a small event driven ordering platform built around several backend services. Each service has a focused job, and they communicate through HTTP and Kafka rather than one large monolithic app.

## Main idea

The system is designed to handle order flow in a way that is resilient and easy to scale. The order service coordinates the main business flow, while other services react to events and handle their own responsibilities.

## Services

- Auth service handles user registration, login, and token related work.
- User service manages user profile data.
- Inventory service owns product stock and acts as the source of truth for inventory.
- Order service manages the order lifecycle and coordinates stock reservation.
- Search service provides read optimized search support for product and order related data.
- Notification service listens for events and sends updates to users.

## Communication style

The platform uses an event driven approach.

- Services communicate synchronously when they need an immediate response.
- They also publish domain events to Kafka when important changes happen.
- Other services subscribe to those events and react independently.

This makes the system more flexible and helps reduce tight coupling between services.

## Example flow

A typical order flow looks like this:

1. The client sends a request to the order service.
2. The order service validates the request and starts the order process.
3. It checks inventory and reserves what is needed.
4. It publishes an event for the order or inventory change.
5. Other services, such as search and notification, consume the event and update their own view of the data.

## Data and storage

The project uses a distributed setup with service specific storage.

- PostgreSQL is used for transactional data in services.
- Redis is used for idempotency and short lived state.
- Elasticsearch is used for search related read models.
- Kafka is used for event streaming between services.

## Reliability patterns

The architecture includes a few patterns that help the system stay stable under load or failure.

- Idempotency keys prevent duplicate order creation when requests are retried.
- Circuit breakers protect service to service calls from cascading failures.
- Retries with backoff help recover from temporary issues.
- Dead letter queues capture failed events so they do not disappear silently.

## Deployment
The project is prepared for container based deployment.

- Docker Compose is used for local development.
- Kubernetes manifests are included for deployment in a cluster.
- The services are packaged as separate containers and can be scaled independently.

## Summary

In short, this project is a microservice based ordering platform with event driven communication, service specific data ownership, and read models built for scale and resilience.
