# End-to-end: Deploy Cartord on Amazon EKS (with AWS Secrets Manager)

This guide takes Cartord from source to a working cluster on **Amazon EKS**, using the Helm umbrella chart in `k8s/` and the Makefile targets already in the repo. Secrets live in **AWS Secrets Manager** and are synced into the cluster by the **External Secrets Operator (ESO)**, so no secret file is ever applied by hand.

It covers:

1. AWS and local tooling
2. EKS cluster and add-ons
3. Container images in ECR
4. S3 for product images (the chart does not deploy MinIO)
5. Secrets Manager + External Secrets Operator
6. Public URLs, Ingress, and the `values-eks.yaml` overlay
7. Helm install
8. Seed, Kafka topics, and Debezium
9. DNS and TLS
10. Smoke checks
11. Hardening, upgrade, teardown, common failures

Local Docker Compose remains the day-to-day development path. This document is for running the same platform on EKS.

---

## Architecture on EKS

| Layer | What Cartord uses on EKS |
| --- | --- |
| Apps | `auth`, `inventory`, `order`, `payment`, `search`, `notification`, `ai`, `frontend` |
| Data plane (in-cluster via Helm) | Postgres StatefulSet, Redis, Kafka, Elasticsearch, Debezium Connect |
| Object storage | AWS S3 |
| Secrets | AWS Secrets Manager, synced to the Kubernetes Secret `cartord-secrets` by ESO |
| Observability (optional, chart toggles) | Prometheus, Grafana, Jaeger, OTel Collector, GlitchTip |
| Ingress | AWS Load Balancer Controller + one shared ALB |

### Why ESO needs no chart changes

Every workload in the chart already reads a Kubernetes Secret named `cartord-secrets`:

- all 8 app charts (`envFrom` and `secretKeyRef`)
- the Postgres StatefulSet (`secretName: cartord-secrets`)
- GlitchTip (`existingSecret`) and Elasticsearch (`ELASTIC_PASSWORD`)
- the `seed-and-topics` and `debezium-register` Jobs

ESO creates and keeps that one Secret in sync with a single JSON secret in Secrets Manager. Nothing in `k8s/charts/` changes.

The umbrella chart is `k8s/Chart.yaml`. Install with:

```bash
make k8s
# helm upgrade --install cartord ./k8s --namespace cartord -f ./k8s/values.yaml --create-namespace
```

> **Note:** The default chart runs Kafka with a single broker and replication factor `1`. That is fine for a first EKS environment. Raise broker count and replication before production traffic.

---

## 0. Prerequisites

### Tools on your machine

- AWS CLI v2, configured (`aws sts get-caller-identity`)
- `kubectl`
- `eksctl`
- Helm 3.14+
- Docker
- `make`
- Python 3.10+ with `python-dotenv` (`pip install python-dotenv`), used once to convert `.env.k8s` into the JSON secret

### AWS permissions

You need rights to create and manage:

- EKS clusters and node groups
- ECR repositories
- VPC, subnets, security groups
- IAM roles and policies, including roles for service accounts (IRSA)
- S3 buckets and CORS
- **Secrets Manager secrets**
- ACM certificates (for HTTPS)
- Elastic Load Balancing (ALB)

### Suggested sizing (first cluster)

| Workload | Suggested starting point |
| --- | --- |
| Node group | 3x `m5.xlarge` or `m6i.xlarge` (larger if you enable the full observability stack) |
| Disk | gp3, at least 100 GiB root; Postgres / ES / Kafka need PersistentVolumes |
| Region | Pick one and keep ECR, EKS, S3, Secrets Manager, and ACM in it |

Postgres, Kafka, and Elasticsearch in the default chart are stateful. Use the cluster's default StorageClass (EBS CSI).

### Shell variables used throughout

```bash
export AWS_REGION=eu-west-1
export CLUSTER_NAME=cartord-eks
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

---

## 1. Create the EKS cluster

Pick a Kubernetes version that is currently offered. List what your account can create today:

```bash
aws eks describe-cluster-versions --query 'clusterVersions[].[clusterVersion,status]' --output table
```

Use a version in standard support with plenty of runway (as of November 2026 that means 1.35 or newer; 1.34 leaves standard support on December 2, 2026). Do not copy an old version number from older guides.

```bash
export K8S_VERSION=1.36   # confirm against the command above

eksctl create cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --version "$K8S_VERSION" \
  --with-oidc \
  --nodegroup-name cartord-nodes \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 6 \
  --managed
```

`--with-oidc` is required: IRSA (used by ESO and, later, S3) depends on it.

Confirm access:

```bash
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION"
kubectl get nodes
```

### Required cluster add-ons

Install (or confirm) these before Cartord:

1. **Amazon EBS CSI driver**: PersistentVolumes for Postgres / Kafka / Elasticsearch
2. **AWS Load Balancer Controller**: ALB Ingress
3. **metrics-server**: HPA (the charts include HPA templates)
4. **External Secrets Operator**: installed in section 5

Verify the first three before moving on:

```bash
kubectl get sc                                   # a default StorageClass backed by ebs.csi.aws.com
kubectl get deploy -n kube-system aws-load-balancer-controller metrics-server
```

---

## 2. Create ECR repositories and push images

Cartord images are tagged as `$(IMAGE_REPO)/<service>:latest` (default `IMAGE_REPO=werayco` in the Makefile). On AWS, point that at your account's ECR.

```bash
export ECR="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
export IMAGE_REPO="$ECR/cartord"

for name in \
  auth-service inventory-service notification-service order-service \
  search-service payment-service ai-service frontend-service cartord-init
do
  aws ecr describe-repositories --repository-names "cartord/$name" 2>/dev/null \
    || aws ecr create-repository --repository-name "cartord/$name"
done

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR"
```

Build and push. The nodes are x86_64, so build `linux/amd64` images (matters if you build on an ARM machine):

```bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64

# App services (Makefile)
make build-all IMAGE_REPO="$IMAGE_REPO"
make push-all IMAGE_REPO="$IMAGE_REPO"

# Frontend (not in build-all or push-all today)
docker build -t "$IMAGE_REPO/frontend-service:latest" ./services/frontend-service
docker push "$IMAGE_REPO/frontend-service:latest"
```

`make push-all` already pushes `cartord-init`, but `build-all` does not build it, so build it first:

```bash
docker build -t "$IMAGE_REPO/cartord-init:latest" -f shared/init_scripts/Dockerfile .
docker push "$IMAGE_REPO/cartord-init:latest"
```

Managed node groups can pull from ECR in the same account through the node IAM role, so no image pull secret is needed.

---

## 3. Provision S3 for product images

Kubernetes does **not** deploy MinIO. Inventory talks to S3 through `boto3`.

```bash
export BUCKET=cartord-product-images-$AWS_ACCOUNT_ID

aws s3 mb "s3://$BUCKET" --region "$AWS_REGION"

# Public reads for product image URLs (tighten if you use CloudFront + signed URLs later)
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false
```

Public reads also need a bucket policy that allows `s3:GetObject` on `arn:aws:s3:::$BUCKET/*`. Add one, or serve images through CloudFront instead.

### CORS

Browsers upload with a presigned PUT from the frontend origin. Set bucket CORS to that exact origin:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "HEAD"],
    "AllowedOrigins": ["https://shop.example.com"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

```bash
aws s3api put-bucket-cors --bucket "$BUCKET" --cors-configuration file://cors.json
```

### IAM user for the first deploy

The inventory service currently passes `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` explicitly to `boto3`, so for the first deploy create a dedicated IAM user limited to this bucket (`s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`), create an access key for it, and store the key pair in Secrets Manager in the next section. Moving to IRSA later needs a small code change so the keys become optional and `boto3` falls back to its default credential chain.

---

## 4. Frontend and backend URLs (decide this before secrets)

Several secret values depend on the final hostnames (`ALLOW_ORIGINS`, `MINIO_CORS_ORIGINS`, `MINIO_PUBLIC_ENDPOINT`), so settle them first.

The services serve their routes at the root of their own host (for example `/api/v1/health`) and do not use a path prefix. The ALB does not rewrite paths, so **give each backend its own hostname** instead of `api.example.com/auth`:

| Service | Public host |
| --- | --- |
| frontend | `shop.example.com` |
| auth | `auth.api.example.com` |
| inventory | `inventory.api.example.com` |
| order | `order.api.example.com` |
| payment | `payment.api.example.com` |
| search | `search.api.example.com` |
| ai (HTTP + WebSocket) | `ai.api.example.com` |

One wildcard ACM certificate, `*.api.example.com`, plus `shop.example.com`, covers all of them.

Set `ALLOW_ORIGINS` (a secret key) to `https://shop.example.com`.

---

## 5. Secrets Manager + External Secrets Operator

### 5.1 Build the secret values

Copy the example env and fill it for in-cluster DNS names:

```bash
cp shared/compose_files/.env.example shared/compose_files/.env.k8s
```

`.env.k8s` is git-ignored. It is only a staging file: after step 5.3 it should be deleted from disk.

Typical changes from Compose:

| Key | Local Compose | EKS |
| --- | --- | --- |
| Postgres host in every `*_DATABASE_URL`, `DATABASE_URL` | `postgres` | `cartord-postgres` (the chart service name) |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | `cartord-kafka:9092` |
| `REDIS_HOST` | `redis` | `cartord-redis-master` |
| `ELASTICSEARCH_HOST` | `elasticsearch` | `elasticsearch-master` |
| `DEBEZIUM_URL` | compose host | `http://debezium-connect:8083` |
| Service-to-service URLs (`PAYMENT_BASE_URL`, `AUTH_BASE_URL`, ...) | `*_service:900x` | `http://payment-service:9005/api/v1` style cluster DNS |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | local MinIO | the S3 IAM user key pair from section 3 |
| `MINIO_PUBLIC_ENDPOINT` | local | `https://<bucket>.s3.<region>.amazonaws.com` |
| `MINIO_CORS_ORIGINS`, `ALLOW_ORIGINS` | localhost | `https://shop.example.com` |
| `EMAIL_PROVIDER` | Mailpit | `resend` or `smtp` with real credentials (there is no Mailpit on EKS) |

Confirm the real names against `.env.example` and the `k8s/charts/*/values.yaml` files before you assume the table is complete.

**Two keys the chart needs that are easy to miss:**

- `ELASTICSEARCH_PASSWORD`: `k8s/values.yaml` sets `ELASTIC_PASSWORD` from this key. It is not in `.env.example`. If it is missing from the secret, the Elasticsearch pod fails with `CreateContainerConfigError`. Security is disabled in the chart, so any non-empty value works.
- `SECRET_KEY` and `DATABASE_URL`: GlitchTip reads both from `cartord-secrets`. `DATABASE_URL` must point at a database GlitchTip can use.

Generate fresh values rather than reusing Compose ones:

```bash
# JWT_PRIVATE_KEY, SECRET_KEY, SERVICE_SHARED_KEY: run once per key
make gen-secret

# MFA_ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# AI_AGENT_SECRET, AI_AGENT_SECRET_HASH, AUTH_DELEGATION_SECRET (prints three KEY=value lines)
python shared/init_scripts/gen_ai_secrets.py
```

`gen_ai_secrets.py` only prints; paste its three lines into `.env.k8s` yourself. (The earlier version of this guide referenced `generate_ai_agent_secret --write-env`, which does not exist in the repo.)

### 5.2 Store them in Secrets Manager as one JSON secret

One secret holding every key keeps the setup simple and cheap, and stays well under the 64 KB secret size limit.

```bash
export SECRET_ID=cartord/prod/app

umask 077
TMP=$(mktemp)

python - "$TMP" <<'PY'
import json, sys
from dotenv import dotenv_values

vals = dotenv_values("shared/compose_files/.env.k8s", interpolate=False)
vals = {k: v for k, v in vals.items() if v is not None}
with open(sys.argv[1], "w") as f:
    json.dump(vals, f)
print(f"{len(vals)} keys")
PY

aws secretsmanager create-secret \
  --name "$SECRET_ID" \
  --secret-string "file://$TMP" \
  --region "$AWS_REGION"

shred -u "$TMP" 2>/dev/null || rm -f "$TMP"
```

Notes:

- Always pass the value with `file://`, never inline, so it does not land in your shell history or process list.
- To change values later, run the same script and replace `create-secret` with `put-secret-value --secret-id "$SECRET_ID"`.
- Every value is stored as a string, which is what the Kubernetes Secret needs.

### 5.3 IAM policy and service account for ESO

ESO's controller reads the secret through IRSA, scoped to the `cartord/*` prefix only.

```bash
cat > eso-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:cartord/*"
    }
  ]
}
EOF

export ESO_POLICY_ARN=$(aws iam create-policy \
  --policy-name cartord-eso-read \
  --policy-document file://eso-policy.json \
  --query Policy.Arn --output text)

kubectl create namespace external-secrets --dry-run=client -o yaml | kubectl apply -f -

eksctl create iamserviceaccount \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --namespace external-secrets \
  --name external-secrets-sa \
  --attach-policy-arn "$ESO_POLICY_ARN" \
  --approve
```

If you use a customer-managed KMS key on the secret, also allow `kms:Decrypt` on that key. The default `aws/secretsmanager` key needs nothing extra.

### 5.4 Install ESO

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --set installCRDs=true \
  --set serviceAccount.create=false \
  --set serviceAccount.name=external-secrets-sa

kubectl rollout status deploy/external-secrets -n external-secrets --timeout=5m
```

### 5.5 Connect ESO to Secrets Manager and create `cartord-secrets`

Keep these two manifests outside the Helm chart (the umbrella chart only packages `k8s/templates/`), for example in `k8s/external-secrets/`.

`k8s/external-secrets/cluster-secret-store.yaml`:

```yaml
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-west-1   # same as $AWS_REGION
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
```

`k8s/external-secrets/cartord-secrets.yaml`:

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: cartord-secrets
  namespace: cartord
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: cartord-secrets      # the name every chart already expects
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: cartord/prod/app  # every JSON property becomes a key in the Secret
```

Apply them. The `cartord` namespace must exist first:

```bash
kubectl create namespace cartord --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f k8s/external-secrets/cluster-secret-store.yaml
kubectl apply -f k8s/external-secrets/cartord-secrets.yaml

kubectl wait --for=condition=Ready externalsecret/cartord-secrets -n cartord --timeout=120s
```

Verify the Secret has the expected keys (this prints key names only, not values):

```bash
kubectl get secret cartord-secrets -n cartord -o json | python -c "import json,sys; print(sorted(json.load(sys.stdin)['data']))"
```

If `kubectl apply` says `no matches for kind ... in version external-secrets.io/v1`, your ESO release serves an older API. Check with `kubectl api-resources --api-group=external-secrets.io` and use `external-secrets.io/v1beta1` instead.

> **Do not run `make k8s-secret` on EKS.** That target builds `cartord-secrets` from a local file for minikube. If you already ran it, delete the Secret first (`kubectl delete secret cartord-secrets -n cartord`) so ESO can own it.

### 5.6 Changing or rotating a secret

1. Update the value in Secrets Manager (step 5.2 with `put-secret-value`).
2. Force a sync, or wait up to `refreshInterval`:

   ```bash
   kubectl annotate externalsecret cartord-secrets -n cartord force-sync=$(date +%s) --overwrite
   ```

3. Restart the workloads. Environment variables are read at container start, so running pods keep the old values until restarted:

   ```bash
   kubectl rollout restart deployment -n cartord
   ```

Cautions specific to Cartord:

- The Postgres password exists twice: as `POSTGRES_PASSWORD` and inside every `*_DATABASE_URL`. Change both together, and remember the in-cluster Postgres only reads `POSTGRES_PASSWORD` on first initialization, so rotating it needs an `ALTER ROLE` as well.
- Do not rotate `JWT_PRIVATE_KEY` casually: every issued token becomes invalid.
- Do not rotate `MFA_ENCRYPTION_KEY` without a migration: enrolled MFA secrets become unreadable.

Secrets Manager costs roughly $0.40 per secret per month plus API calls (check current pricing). One JSON secret keeps that negligible.

---

## 6. Public URLs, Ingress, and the `values-eks.yaml` overlay

Create `k8s/values-eks.yaml`. Subchart values are keyed by the subchart name from `k8s/Chart.yaml`.

```yaml
# ---- images (repeat the block for every app) ----
auth-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/auth-service
    tag: "latest"
    pullPolicy: Always
  ingress:
    enabled: true
    className: alb
    annotations: &alb
      alb.ingress.kubernetes.io/group.name: cartord
      alb.ingress.kubernetes.io/scheme: internet-facing
      alb.ingress.kubernetes.io/target-type: ip
      alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
      alb.ingress.kubernetes.io/ssl-redirect: "443"
      alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:eu-west-1:123456789012:certificate/REPLACE_ME
      alb.ingress.kubernetes.io/healthcheck-path: /api/v1/health
    hosts:
      - host: auth.api.example.com
        paths:
          - path: /
            pathType: Prefix

inventory-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/inventory-service
    tag: "latest"
    pullPolicy: Always
  productImages:
    endpoint: "https://s3.eu-west-1.amazonaws.com"
    publicEndpoint: "https://cartord-product-images-123456789012.s3.eu-west-1.amazonaws.com"
    bucket: "cartord-product-images-123456789012"
    corsOrigins: "https://shop.example.com"
  ingress:
    enabled: true
    className: alb
    annotations: *alb
    hosts:
      - host: inventory.api.example.com
        paths:
          - path: /
            pathType: Prefix

order-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/order-service
    tag: "latest"
    pullPolicy: Always
  ingress:
    enabled: true
    className: alb
    annotations: *alb
    hosts:
      - host: order.api.example.com
        paths:
          - path: /
            pathType: Prefix

payment-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/payment-service
    tag: "latest"
    pullPolicy: Always
  ingress:
    enabled: true
    className: alb
    annotations: *alb
    hosts:
      - host: payment.api.example.com
        paths:
          - path: /
            pathType: Prefix

search-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/search-service
    tag: "latest"
    pullPolicy: Always
  ingress:
    enabled: true
    className: alb
    annotations: *alb
    hosts:
      - host: search.api.example.com
        paths:
          - path: /
            pathType: Prefix

ai-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/ai-service
    tag: "latest"
    pullPolicy: Always
  ingress:
    enabled: true
    className: alb
    annotations:
      <<: *alb
      alb.ingress.kubernetes.io/load-balancer-attributes: idle_timeout.timeout_seconds=300
    hosts:
      - host: ai.api.example.com
        paths:
          - path: /
            pathType: Prefix

notification-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/notification-service
    tag: "latest"
    pullPolicy: Always
  # internal only: no ingress

frontend-service:
  image:
    repository: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/cartord/frontend-service
    tag: "latest"
    pullPolicy: Always
  ingress:
    enabled: true
    className: alb
    annotations:
      <<: *alb
      alb.ingress.kubernetes.io/healthcheck-path: /   # the frontend has no /api/v1/health
    hosts:
      - host: shop.example.com
        paths:
          - path: /
            pathType: Prefix
  env:
    - name: VITE_AUTH_SERVICE_URL
      value: "https://auth.api.example.com"
    - name: VITE_INVENTORY_SERVICE_URL
      value: "https://inventory.api.example.com"
    - name: VITE_ORDER_SERVICE_URL
      value: "https://order.api.example.com"
    - name: VITE_PAYMENT_SERVICE_URL
      value: "https://payment.api.example.com"
    - name: VITE_SEARCH_SERVICE_URL
      value: "https://search.api.example.com"
    - name: VITE_AI_SERVICE_URL
      value: "https://ai.api.example.com"
    - name: VITE_AI_WS_URL
      value: "wss://ai.api.example.com/api/v1/ws/chat"
    - name: VITE_AI_WS_MESSAGE_FIELD
      value: "content"
    - name: VITE_CURRENCY
      value: "NGN"

# ---- GlitchTip: the default values target Traefik + cert-manager, which EKS does not have ----
glitchtip:
  glitchtip:
    domain: "https://errors.example.com"   # only used for links; adjust or leave
  ingress:
    enabled: false   # reach it with: kubectl port-forward svc/<glitchtip-web> 8080:80 -n cartord
```

Notes:

- `group.name: cartord` makes every Ingress share **one** ALB instead of creating eight.
- The frontend `env` list **replaces** the chart default, so keep every `VITE_*` entry.
- The `&alb` / `*alb` YAML anchors work because they sit in the same file. If your tooling rejects anchors, repeat the annotations.
- Replace the `123456789012` account ID, region, certificate ARN, and bucket name everywhere.
- The default `k8s/values.yaml` already sets the Kafka, Redis, Elasticsearch, and Postgres service names the secret values in section 5.1 rely on.

---

## 7. Install Cartord with Helm

Make sure `cartord-secrets` exists (section 5) before installing, otherwise Postgres, Elasticsearch, and the apps sit in `CreateContainerConfigError`.

```bash
kubectl get secret cartord-secrets -n cartord

helm dependency update ./k8s

helm upgrade --install cartord ./k8s \
  --namespace cartord \
  --create-namespace \
  -f ./k8s/values.yaml \
  -f ./k8s/values-eks.yaml
```

`make k8s` only passes `values.yaml`, so use the command above (or add `-f ./k8s/values-eks.yaml` to the Makefile target).

Watch the rollout:

```bash
kubectl get pods -n cartord -w
kubectl get pvc -n cartord
kubectl get ingress -n cartord
```

Wait until core deployments are Ready before seeding and registering Debezium:

```bash
for d in order inventory payment ai auth search debezium-connect; do
  kubectl rollout status deployment/${d}$([ "$d" != "debezium-connect" ] && echo -service) -n cartord --timeout=10m
done
```

---

## 8. Seed data, Kafka topics, and Debezium

### Seed inventory and create topics

The Job reads `INVENTORY_DATABASE_URL` from `cartord-secrets` and talks to `cartord-kafka:9092`. Its image is currently `cartord-init:latest` with no registry, which only works on minikube. Point it at ECR for this run, without editing the tracked file:

```bash
sed "s|image: cartord-init:latest|image: $IMAGE_REPO/cartord-init:latest|; s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|" \
  k8s/jobs/seed-and-topics.yaml | kubectl create -f -

kubectl get jobs -n cartord -w
kubectl logs -n cartord job/<seed-job-name>
```

Do not use `make k8s-init` on EKS: it builds and loads the image into minikube and registers Debezium before the apps are ready.

### Register Debezium connectors

Outbox tables are created when order, inventory, payment, and AI start, so register connectors only after those deployments are Ready:

```bash
sed "s|image: werayco/cartord-init:latest|image: $IMAGE_REPO/cartord-init:latest|" \
  k8s/jobs/debezium-register.yaml | kubectl create -f -

kubectl get jobs -n cartord -w
kubectl logs -n cartord job/<debezium-register-job-name>
```

(Note the two Job files reference the init image differently: `seed-and-topics.yaml` uses `cartord-init:latest`, while `debezium-register.yaml` uses `werayco/cartord-init:latest`, which would pull from Docker Hub. Hence the two different `sed` patterns.) The Job talks to `debezium-connect` and Postgres through cluster DNS and reads `POSTGRES_USER` / `POSTGRES_PASSWORD` from `cartord-secrets`.

Optional local debug:

```bash
make k8s-debezium-forward   # kubectl port-forward -n cartord svc/debezium-connect 8083:8083
curl http://localhost:8083/connectors
```

---

## 9. DNS and TLS

1. Request an ACM certificate in the **same region as the ALB** covering `shop.example.com` and `*.api.example.com`, and validate it through DNS.
2. Put its ARN in `values-eks.yaml` (`certificate-arn`) and re-run the Helm upgrade.
3. Find the ALB hostname: `kubectl get ingress -n cartord`.
4. Create Route 53 alias records (or CNAMEs) for `shop.example.com` and each `*.api.example.com` host pointing at that ALB.
5. Confirm HTTPS on the frontend and `wss://` on the AI host.
6. Keep S3 CORS origins and the `ALLOW_ORIGINS` secret aligned with the final frontend origin.

---

## 10. Smoke test

```bash
curl -fsS https://auth.api.example.com/api/v1/health
curl -fsS https://search.api.example.com/api/v1/search/items/all
curl -fsSI https://shop.example.com
```

In the browser:

1. Open `https://shop.example.com`
2. Sign up / sign in as a buyer
3. Browse the shop (paginated catalogue)
4. Open the AI assistant and send a message (WebSocket)
5. As a seller, create a product and upload an image (presigned PUT to S3)
6. Place an order and confirm wallet and stock behaviour

Check the event path end to end: place an order, then confirm the payment event arrived and the order moved out of `PENDING`:

```bash
kubectl logs -n cartord deploy/order-service --tail=50
kubectl logs -n cartord deploy/payment-service --tail=50
```

Observability (if enabled in values):

| UI | How to reach it |
| --- | --- |
| Grafana | `kubectl port-forward svc/grafana 3000:80 -n cartord` |
| Prometheus | `kubectl port-forward svc/prometheus 9090:80 -n cartord` |
| Jaeger | port-forward the `jaeger` query service |
| GlitchTip | port-forward (Ingress is disabled in `values-eks.yaml`) |

Prometheus and Grafana storage is disabled and Jaeger uses in-memory storage in the default values, so their data is lost when those pods restart.

---

## 11. Production hardening checklist

- [ ] Kafka brokers 3 or more, replication factor 2 or more, multi-AZ node groups
- [ ] Postgres: prefer Amazon RDS / Aurora. Debezium needs logical replication, so set `rds.logical_replication = 1` in the parameter group and grant the replication role; update all `*_DATABASE_URL` keys in the secret
- [ ] Redis: prefer ElastiCache; point `REDIS_HOST` at it
- [ ] Elasticsearch: prefer Amazon OpenSearch; update search service config
- [ ] Pin image tags to digests or semver, not `latest`
- [ ] IRSA for S3 on the inventory service account (needs the small `boto3` code change in section 3), then remove the static S3 keys from the secret
- [ ] Restrict the ESO IAM policy to the exact secret ARN once the secret name is final
- [ ] Add a Secrets Manager resource policy or SCP so only the ESO role can read `cartord/*`
- [ ] Enable CloudTrail data events for Secrets Manager reads, and alert on unexpected `GetSecretValue` callers
- [ ] NetworkPolicies / security groups: only the ALB reaches app pods
- [ ] Resource requests and limits tuned; HPA enabled with real metrics
- [ ] Backups for Postgres (and ES if still in-cluster)
- [ ] Keep GlitchTip and Grafana off the public internet, or put them behind SSO
- [ ] Add a Reloader (or a CI step) to roll deployments when `cartord-secrets` changes

---

## 12. Upgrade and teardown

### Upgrade

```bash
# Build and push new images with a new tag, update the tag in values-eks.yaml, then:
helm upgrade cartord ./k8s -n cartord -f ./k8s/values.yaml -f ./k8s/values-eks.yaml
kubectl rollout status deployment/frontend-service -n cartord
```

### Tear down

Delete the ingresses first so the ALB controller removes the load balancer, then the release, then everything around it:

```bash
helm uninstall cartord -n cartord
kubectl delete pvc --all -n cartord
kubectl delete externalsecret cartord-secrets -n cartord
kubectl delete namespace cartord

helm uninstall external-secrets -n external-secrets
eksctl delete iamserviceaccount --cluster "$CLUSTER_NAME" --region "$AWS_REGION" \
  --namespace external-secrets --name external-secrets-sa
aws iam delete-policy --policy-arn "$ESO_POLICY_ARN"

# Secrets Manager keeps a deleted secret for a recovery window (billed) unless you force it
aws secretsmanager delete-secret --secret-id "$SECRET_ID" --force-delete-without-recovery --region "$AWS_REGION"

# Optional: delete the cluster
eksctl delete cluster --name "$CLUSTER_NAME" --region "$AWS_REGION"
```

Empty and delete the S3 bucket, the S3 IAM user, and the ECR repositories when you no longer need them. A running cluster bills continuously (control plane, nodes, NAT gateway, ALB, EBS), so tear it down when you are done testing.

---

## 13. Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ExternalSecret` stuck `SecretSyncedError` | ESO cannot read the secret | `kubectl describe externalsecret cartord-secrets -n cartord`; check the IAM policy ARN, the region in the store, and the secret name |
| `AccessDeniedException` in the ESO logs | Service account not annotated for IRSA, or policy scope wrong | `kubectl get sa external-secrets-sa -n external-secrets -o yaml` should show `eks.amazonaws.com/role-arn`; restart the ESO deployment after fixing |
| `no matches for kind "ExternalSecret"` | CRDs missing or older API version | Install with `installCRDs=true`; try `external-secrets.io/v1beta1` |
| Pods `CreateContainerConfigError` ("secret not found" or "key not found") | `cartord-secrets` missing, or a key is absent | Confirm the ExternalSecret is Ready and list the keys (section 5.5); Elasticsearch needs `ELASTICSEARCH_PASSWORD` |
| Changed a secret but apps behave the same | Env vars are read at start | `kubectl rollout restart deployment -n cartord` |
| ESO will not overwrite `cartord-secrets` | A Secret created by `make k8s-secret` already exists | Delete it, then re-apply the ExternalSecret |
| ImagePullBackOff | Wrong ECR path or no pull auth | Check repository names; confirm the node role can pull from ECR |
| PVC Pending | EBS CSI / StorageClass missing | Install EBS CSI; check `kubectl get sc` |
| Frontend loads but APIs fail | Vite env still points at localhost, or CORS origin mismatch | Set public URLs in `frontend-service.env`; align the `ALLOW_ORIGINS` secret |
| API host returns 404 from the ALB | Path-based routing used, services have no path prefix | Use one hostname per service (section 4) |
| Chat WebSocket drops | ALB idle timeout, or `ws://` on an HTTPS page | Raise idle timeout; use `wss://` |
| Image upload 403 from the browser | S3 CORS, bucket policy, or wrong public endpoint | Align CORS origin; check `productImages.publicEndpoint` and the bucket policy |
| Debezium register Job fails | App pods not Ready, bad DB URL, or no logical replication | Wait for rollouts; verify the secret's DB hosts; with RDS set `rds.logical_replication` |
| `make k8s-init` fails or hangs on EKS | The target loads the image into minikube | Use the `sed` + `kubectl create` commands in section 8 |
| Orders return 409 | Insufficient free stock | Check inventory `available_quantity` vs `reserved_quantity` |

---

## Quick command index

```bash
# Cluster
aws eks update-kubeconfig --name cartord-eks --region "$AWS_REGION"

# Secrets (once, then ESO keeps them synced)
aws secretsmanager create-secret --name cartord/prod/app --secret-string file://secrets.json
kubectl apply -f k8s/external-secrets/cluster-secret-store.yaml
kubectl apply -f k8s/external-secrets/cartord-secrets.yaml
kubectl wait --for=condition=Ready externalsecret/cartord-secrets -n cartord --timeout=120s

# Install
helm dependency update ./k8s
helm upgrade --install cartord ./k8s -n cartord --create-namespace \
  -f ./k8s/values.yaml -f ./k8s/values-eks.yaml

# Post-install (see section 8 for the ECR image substitution)
kubectl create -f k8s/jobs/seed-and-topics.yaml
kubectl create -f k8s/jobs/debezium-register.yaml

# Status
kubectl get pods,svc,ingress,pvc -n cartord
kubectl get externalsecret -n cartord
kubectl logs -n cartord deploy/ai-service --tail=100
```

Related docs in this repo:

- `README.md`: Kubernetes section
- `shared/docs/setups/debezium_setup.md`: connector details
- `shared/docs/setups/apis_setup.md`: service ports and routes
- `shared/docs/cheatsheet/k8s_cheatsheet.md`: kubectl reference
- `Makefile`: `k8s`, `k8s-secret` (minikube only), `k8s-init` (minikube only), `k8s-debezium-register`, `build-all`, `push-all`