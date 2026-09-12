# Jaeger tracing

All seven services send OTLP/gRPC traces to http://otel-collector:4317.
The existing collector forwards traces to jaeger:4317.
Open http://localhost:16686 and select a service to search its traces.

## Shared environment

In shared/compose_files/.env:

```dotenv
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_RESOURCE_ATTRIBUTES=service.namespace=cartord,deployment.environment.name=development
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0
OTEL_PROPAGATORS=tracecontext,baggage
```

Sampling 1.0 captures all new root traces for local development. Set 0.1
for 10% root sampling. Downstream spans follow their parent sampling decision.
Sentry sampling is configured separately.

Each application has its own OTEL_SERVICE_NAME in services.docker-compose.yml:
ai_service, auth_service, inventory_service, search_service,
notification_service, order_service, payment_service.
Each telemetry.py uses settings.OTEL_SERVICE_NAME. The Settings model reads the environment variable and defaults to the original service name.
No per-service DSN is needed for Jaeger.

Apply environment changes from the repository root:

```powershell
docker compose --env-file shared/compose_files/.env -f shared/compose_files/services.docker-compose.yml up -d
```

## Scope

FastAPI instrumentation produces incoming request spans. Existing database,
Redis, aiohttp, and Elasticsearch instrumentation adds spans where configured.
Applications must initialize successfully to produce normal request traces.
Only instrumented outgoing clients propagate HTTP trace context automatically.
Kafka message trace propagation is not configured by these environment values.

The setup check emits cartord-otel-connection-test from each container using
the application's provider setup and verifies retrieval through Jaeger's API.
This checks the trace pipeline independently of application startup.

Reference: https://opentelemetry.io/docs/languages/sdk-configuration/general/