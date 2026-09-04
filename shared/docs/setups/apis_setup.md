# Service API Endpoint Map

This document lists the API endpoints currently exposed by the FastAPI services in this project.

## Service Ports

The running services are configured in `shared/compose_files/services.docker-compose.yml`:

- AI Service: http://localhost:9000
- Auth Service: http://localhost:9001
- Inventory Service: http://localhost:9002
- Notification Service: http://localhost:9003
- Order Service: http://localhost:9004
- Payment Service: http://localhost:9005
- Search Service: http://localhost:9007

## Common Auth Pattern

Protected HTTP routes require an Authorization header:

```http
Authorization: Bearer <access_token>
```

The AI WebSocket uses the token query parameter instead:

```text
ws://localhost:9000/api/v1/ws/chat?token=<access_token>
```

---

## 1) AI Service

Base URL: http://localhost:9000

### Health

- GET `/api/v1/health`
  - No payload

### Documents

- POST `/api/v1/documents/upload`
  - Requires an admin bearer token
  - Multipart form field: `file`

- GET `/api/v1/documents/query/{question}`
  - Requires a bearer token
  - Path parameter: `question`
  - Example: `/api/v1/documents/query/how do I return an item`

### Chat

- WebSocket `/api/v1/ws/chat?token=<access_token>`
  - Requires an access token query parameter
  - Receives JSON messages and returns JSON responses

---

## 2) Auth Service

Base URL: http://localhost:9001

### Health

- GET `/api/v1/health`
  - No payload

### Buyer APIs

- POST `/api/v1/auth/buyer/register`

```json
{
  "email": "jane@example.com",
  "name": "Jane Doe",
  "username": "janedoe",
  "password": "Secret123!",
  "shipping_address": "123 Main Street, Springfield"
}
```

- POST `/api/v1/auth/buyer/login`

```json
{
  "username": "janedoe",
  "password": "Secret123!"
}
```

- POST `/api/v1/auth/buyer/refresh`
  - Requires a bearer token

```json
{
  "refresh_token": "<refresh_token>"
}
```

- GET `/api/v1/auth/buyer/me`
  - Requires a bearer token

- POST `/api/v1/auth/buyer/change-password`
  - Requires a bearer token

```json
{
  "old_password": "Secret123!",
  "new_password": "NewSecret456!"
}
```

- PATCH `/api/v1/auth/buyer/update`
  - Requires a bearer token
  - All fields are optional

```json
{
  "email": "jane.new@example.com",
  "name": "Jane Updated",
  "username": "janedoe2",
  "shipping_address": "456 Oak Avenue, Springfield"
}
```

- DELETE `/api/v1/auth/buyer/delete`
  - Requires a bearer token

```json
{
  "username": "janedoe",
  "password": "Secret123!"
}
```

### Seller APIs

- POST `/api/v1/auth/seller/register`

```json
{
  "email": "seller@example.com",
  "name": "Alex Seller",
  "username": "alexseller",
  "password": "Secret123!"
}
```

- DELETE `/api/v1/auth/seller/{username}`
  - Requires a seller bearer token
  - Example: `/api/v1/auth/seller/alexseller`
  - No request body

- GET `/api/v1/auth/seller/sellers`
  - Requires a seller bearer token

- POST `/api/v1/auth/seller/login`
  - Same payload as buyer login

- POST `/api/v1/auth/seller/refresh`
  - Requires a seller bearer token
  - Same payload as buyer refresh

- GET `/api/v1/auth/seller/me`
  - Requires a seller bearer token

- POST `/api/v1/auth/seller/change-password`
  - Requires a seller bearer token
  - Same payload as buyer change-password

### Admin APIs

- GET `/api/v1/auth/admin/users/count`
  - Requires an admin bearer token

- GET `/api/v1/auth/admin/customers/statistics?period=all`
  - Requires an admin bearer token
  - Query parameter: `period` (default: `all`)

---

## 3) Inventory Service

Base URL: http://localhost:9002

### Health

- GET `/api/v1/health`
  - No payload

### Inventory APIs

- POST `/api/v1/inventory/`
  - Requires a bearer token
- PUT `/api/v1/inventory/`
  - Requires a bearer token
- DELETE `/api/v1/inventory/`
  - Requires a bearer token
  - Request body uses the inventory schema; `sku` identifies the item

```json
{
  "name": "Wireless Mouse",
  "description": "Ergonomic wireless mouse",
  "unit_price": 25.5,
  "sku": "CTD001",
  "available_quantity": 120,
  "reserved_quantity": 0
}
```

- GET `/api/v1/inventory/`
  - Requires a bearer token
  - No request body

- PATCH `/api/v1/inventory/reserve`
  - No bearer dependency in the route

```json
{
  "sku": "CTD001",
  "reserved_quantity": 2
}
```

### Admin APIs

All admin endpoints require an admin bearer token:

- GET `/api/v1/inventory/admin/low-stock`
- GET `/api/v1/inventory/admin/out-of-stock`
- GET `/api/v1/inventory/admin/summary`

---

## 4) Notification Service

Base URL: http://localhost:9003

### Health

- GET `/api/v1/health`
  - No payload

The service currently exposes no additional HTTP routes.

---

## 5) Order Service

Base URL: http://localhost:9004

### Health

- GET `/api/v1/health`
  - No payload

### Order APIs

- POST `/api/v1/order/place/{idempotency_key}`
  - Requires a bearer token
  - Path parameter: `idempotency_key`
  - Example: `/api/v1/order/place/order-001`

```json
{
  "sku": "CTD001",
  "quantity": 2
}
```

### Admin APIs

All admin endpoints require an admin bearer token:

- GET `/api/v1/order/admin/statistics?period=all`
- GET `/api/v1/order/admin/failed-statistics?period=all`

Both endpoints accept the optional `period` query parameter, which defaults to `all`.

---

## 6) Payment Service

Base URL: http://localhost:9005

### Health

- GET `/api/v1/health`
  - No payload

### Wallet APIs

- GET `/api/v1/wallets/seller`
  - Requires a bearer token

- GET `/api/v1/wallets/buyer`
  - Requires a bearer token

---

## 7) Search Service

Base URL: http://localhost:9007

### Health

- GET `/api/v1/health`
  - No payload

### Search APIs

- GET `/api/v1/search/items?query=mouse`
  - Requires a bearer token
  - Query parameter: `query`
  - No request body

---

## Notes

- All seven services are enabled in the service compose configuration.
- Every service exposes a health check at `/api/v1/health`.
- Auth routes are split into buyer, seller, and admin groups.
- Inventory and order admin routes require an admin role.
- The AI chat endpoint is a WebSocket and authenticates with `?token=`.
