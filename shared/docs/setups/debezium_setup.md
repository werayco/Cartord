# Debezium on Kubernetes

The `k8s` Helm chart deploys Debezium Connect using the same connector image
and Kafka Connect topic configuration as Docker Compose. The REST API is
cluster-internal; use port forwarding when registering connectors from the
repository workstation.

## Deploy

```powershell
helm upgrade --install cartord k8s --namespace cartord --create-namespace -f k8s/values.yaml
```

Ensure the `cartord-secrets` Kubernetes Secret exists in the `cartord`
namespace and contains `POSTGRES_USER` and `POSTGRES_PASSWORD`. The connector
registration script reads those values from `shared/compose_files/.env.k8s`.

## Register the outbox connectors

In one terminal, forward the Connect REST API:

```powershell
make k8s-debezium-forward
```

In another terminal, register or update the five existing outbox connectors:

```powershell
make k8s-debezium-register
```

Check connector health:

```powershell
Invoke-RestMethod http://localhost:8083/connectors
Invoke-RestMethod http://localhost:8083/connectors/order-outbox-connector/status
```

The setup script defaults to Docker Compose settings and accepts overrides for
the REST URL and PostgreSQL host/port so it can be used in either environment.
