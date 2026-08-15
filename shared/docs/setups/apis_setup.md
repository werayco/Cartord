# Service API Endpoint Map

This document lists the API endpoints currently exposed by the active FastAPI services in this project.

## Service Ports

The running services are configured in the Docker Compose setup:

- Auth Service: http://localhost:9068
- Inventory Service: http://localhost:9002
- Order Service: http://localhost:9004
- Search Service: http://localhost:9007

> The notification, AI, and payment services are present in the repository but are not currently active in the service compose configuration.

## Common Auth Pattern

Protected routes typically require an Authorization header:

```http
Authorization: Bearer <access_token>
```

---

## 1) Auth Service

Base URL: http://localhost:9068

### Health

- GET /api/v1/health
  - No payload

### Customer APIs

- POST /api/v1/auth/user/register
```json
{
  "email": "jane@example.com",
  "name": "Jane Doe",
  "username": "janedoe",
  "password": "Secret123!",
  "shipping_address": "123 Main Street, Springfield"
}
```

- POST /api/v1/auth/user/login
```json
{
  "username": "janedoe",
  "password": "Secret123!"
}
```

- POST /api/v1/auth/user/refresh
```json
{
  "refresh_token": "<refresh_token>"
}
```

- GET /api/v1/auth/user/me
  - No payload
  - Requires bearer token

- POST /api/v1/auth/user/change-password
```json
{
  "old_password": "Secret123!",
  "new_password": "NewSecret456!"
}
```

- PATCH /api/v1/auth/user/update
```json
{
  "email": "jane.new@example.com",
  "name": "Jane Updated",
  "username": "janedoe2",
  "shipping_address": "456 Oak Avenue, Springfield"
}
```

- DELETE /api/v1/auth/user/delete
```json
{
  "username": "janedoe",
  "password": "Secret123!"
}
```

### Employee APIs

- POST /api/v1/auth/employee/register-employee
```json
{
  "email": "employee@example.com",
  "name": "Alex Staff",
  "username": "alexstaff",
  "password": "Secret123!"
}
```

- POST /api/v1/auth/employee/register-inventory-manager
```json
{
  "email": "manager@example.com",
  "name": "Morgan Manager",
  "username": "morganmgr",
  "password": "Secret123!"
}
```

- DELETE /api/v1/auth/employee/{username}
  - Path parameter: username
  - Example: /api/v1/auth/employee/alexstaff
  - No request body

- GET /api/v1/auth/employee/employees
  - No payload
  - Requires bearer token

- GET /api/v1/auth/employee/inventory-managers
  - No payload
  - Requires bearer token

- POST /api/v1/auth/employee/login
```json
{
  "username": "alexstaff",
  "password": "Secret123!"
}
```

- POST /api/v1/auth/employee/refresh
```json
{
  "refresh_token": "<refresh_token>"
}
```

- GET /api/v1/auth/employee/me
  - No payload
  - Requires bearer token

- POST /api/v1/auth/employee/change-password
```json
{
  "old_password": "Secret123!",
  "new_password": "NewSecret456!"
}
```

---

## 2) Inventory Service

Base URL: http://localhost:9002

### Health

- GET /api/v1/health
  - No payload

### Inventory APIs

- POST /api/v1/inventory/
```json
{
  "name": "Wireless Mouse",
  "description": "Ergonomic wireless mouse",
  "unit_price": 25.5,
  "sku": "CTD001",
  "quantity": 120,
  "reserved_quantity": 0
}
```

- GET /api/v1/inventory/
  - Request body/filter example:

```json
{
  "name": "Wireless Mouse",
  "description": "Ergonomic wireless mouse",
  "unit_price": 25.5,
  "sku": "CTD001",
  "quantity": 120,
  "reserved_quantity": 0
}
```

- PUT /api/v1/inventory/
```json
{
  "name": "Wireless Mouse Pro",
  "description": "Updated ergonomic mouse",
  "unit_price": 29.99,
  "sku": "CTD001",
  "quantity": 150,
  "reserved_quantity": 10
}
```

- DELETE /api/v1/inventory/
```json
{
  "sku": "CTD001"
}
```

- PATCH /api/v1/inventory/reserve
```json
{
  "sku": "CTD001",
  "reserved_quantity": 2
}
```

---

## 3) Order Service

Base URL: http://localhost:9004

### Health

- GET /api/v1/health
  - No payload

### Order APIs

- POST /api/v1/order/place/{idempotency_key}
  - Path parameter: idempotency_key
  - Example: /api/v1/order/place/order-001
```json
{
  "sku": "CTD001",
  "quantity": 2
}
```

---

## 4) Search Service

Base URL: http://localhost:9007

### Health

- GET /api/v1/health
  - No payload

### Search APIs

- GET /api/v1/search/items
  - Query parameter: query
  - Example: /api/v1/search/items?query=mouse
  - No request body

---

## Notes

- All services expose a health check at /api/v1/health.
- Auth endpoints are split into customer and employee router groups under /api/v1/auth/user and /api/v1/auth/employee.
- Inventory and order routes use the /api/v1/\* namespace to isolate service-specific APIs.
- Search uses a keyword query parameter on /api/v1/search/items, for example: /api/v1/search/items?query=phone
- Some protected endpoints are currently implemented with request body payloads for update and deletion flows, while several read-only endpoints are auth-protected and require only a bearer token.
