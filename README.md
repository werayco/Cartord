<div align="center">
 <img src="shared/images/cartord-logo-1.png" alt="Screenbond Logo" width="700"/>

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
