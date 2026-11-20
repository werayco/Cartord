# Cartord frontend-service

React + TypeScript + Vite + Tailwind frontend for the Cartord microservices backend. It is a separate, independently deployable app that talks to the existing services over their documented HTTP/WebSocket APIs. It does not add any backend logic.

Contract source: `shared/docs/setups/apis_setup.md` in [werayco/Cartord](https://github.com/werayco/Cartord). Everything wired to a real endpoint below comes from that file. Anything the file doesn't cover is listed under **Integration gaps** and is not faked.

## Run it

```bash
npm install
cp .env.example .env     # point the URLs at your services
npm run dev              # http://localhost:5173
npm run build            # production bundle in dist/
npm run typecheck        # tsc --noEmit
```

**CORS:** the browser calls each service directly, so every FastAPI service must allow this app's origin (`CORSMiddleware`, `allow_origins=["http://localhost:5173", ...]`, `allow_headers=["*"]`). If sign-in shows "Can't reach the auth service" while `curl` works, this is almost certainly why.

With kubefwd running, use the service names in `.env` (`http://auth-service:9001`, ...).

### Docker / Kubernetes

```bash
docker build -t cartord/frontend-service .
docker run -p 8080:80 \
  -e VITE_AUTH_SERVICE_URL=http://host.docker.internal:9001 \
  -e VITE_INVENTORY_SERVICE_URL=http://host.docker.internal:9002 \
  -e VITE_ORDER_SERVICE_URL=http://host.docker.internal:9004 \
  -e VITE_PAYMENT_SERVICE_URL=http://host.docker.internal:9005 \
  -e VITE_SEARCH_SERVICE_URL=http://host.docker.internal:9007 \
  -e VITE_AI_SERVICE_URL=http://host.docker.internal:9000 \
  cartord/frontend-service
```

The container writes `/config.js` from those environment variables at start, so one image works in every environment. In Kubernetes set the same variables on the Deployment. The URLs must be reachable **from the user's browser** (public ingress hosts, e.g. via Traefik), not cluster-internal DNS.

## Structure

```
src/
  config/env.ts        service URLs (runtime config.js, then VITE_*, then defaults)
  api/                 centralized client + one module per service
    http.ts            fetch wrapper: bearer token, single-flight refresh on 401, error normalisation
    auth.ts inventory.ts search.ts orders.ts payments.ts ai.ts (WebSocket)
    types.ts           Product/Wallet/User + tolerant response normalisers
  context/             AuthContext (session, roles), ShopContext (cart/wishlist/recent, local)
  routes/RequireAuth   protected routes + role-based redirects
  components/          ui/ primitives, layout/ (public, auth, dashboard), ProductCard, DataBlock
  pages/               Landing, auth/, buyer/, seller/, admin/, chat/, shared/
```

Business rules stay in the backend. The UI validates input shape only; stock, price and payment are decided by the services.

## Screens and the endpoints they use

| Area | Screens | Endpoints |
|---|---|---|
| Public | Landing, Shop, Product detail | `GET /search/items`, `GET /search/items/all` (these require a token, so product browsing is sign-in only) |
| Auth | Sign in, Sign up | `POST /auth/{buyer,seller}/login`, `POST /auth/{buyer,seller}/register`, `GET /auth/{buyer,seller}/me`, `POST /auth/{buyer,seller}/refresh` |
| Buyer | Dashboard, Cart/checkout, Orders, Wishlist, Wallet, Profile | `POST /order/place/{key}`, `GET /order/summary`, `GET /wallets/buyer`, `PATCH /auth/buyer/update`, `POST /auth/buyer/change-password` |
| Seller | Overview, Products (create/edit/delete and image management), Inventory, Wallet, Profile | `GET/POST/PUT/DELETE /inventory/`, `POST /inventory/{sku}/images/{upload-url,complete}`, `DELETE /inventory/{sku}/images/{image_id}`, `GET /wallets/seller`, `POST /auth/seller/change-password` |
| Admin | Overview, Users, Products, Orders | `GET /auth/admin/users/count`, `GET /auth/admin/customers/statistics`, `GET /inventory/admin/{summary,low-stock,out-of-stock}`, `GET /order/admin/{statistics,failed-statistics}` |
| AI chat | Conversation UI with product cards | `WS /api/v1/ws/chat?token=` |

Checkout places **one order per cart line** (the backend expects an array of order items, so each line is sent as a one-item array) and reuses each line's idempotency key on retry, so a double submit can't create duplicates. The local order list uses the order ID and price returned by the service.

The admin and buyer/seller areas have separate layouts, navigation and colour accents. Routes are protected by role; a buyer who opens `/admin` is redirected to `/buyer`.

## Integration gaps

These are marked in the UI with an amber "Backend integration gap" notice. Nothing here calls an invented endpoint.

| Needed by the brief | Status |
|---|---|
| Password recovery, account verification, MFA | No endpoints. Screens exist and say so. |
| Admin login | No admin login route is documented. The Admin tab uses the buyer login and requires the token's role claim to be admin/employee. Confirm how admin accounts sign in. |
| Admin `me` | None. Admin identity is read from the JWT claims. |
| Product categories, attributes, status | Product images are supported through the inventory service and MinIO. Category chips on the landing page are search shortcuts. |
| Get product by id | None. Detail page finds the SKU in `search/items/all`. |
| Public product browsing | Search endpoints require a bearer token. |
| Cart, wishlist, recently viewed | No endpoints. Stored in `localStorage` per username. |
| Order history and status | The buyer summary endpoint returns aggregate text, but no individual records or live status. Buyer "My orders" keeps a local record alongside that summary. Seller orders: none. |
| Seller update, store profile (name, logo, address) | Only `change-password` exists for sellers. Read-only profile. |
| Buyer phone number, profile picture | Not in the auth schema. |
| Admin: user lists/actions, payments, categories, reports, individual orders, moderation | Only the aggregate endpoints above. |
| In-app notifications | Notification service has no HTTP routes (email only). |
| Chat history | No endpoint. Conversations are stored in the browser. |
| Seller revenue / sales analytics | Wallet balance is the only figure. |

## Assumptions to verify (response shapes aren't documented)

All guesses are isolated in `src/api/` so a fix is one edit.

1. **Login response**: expects `access_token` (also accepts `token`, `accessToken`) and optional `refresh_token`. `tokenStore.extractTokens`.
2. **Role claim**: read from the JWT (`role`, `roles`, `user_type`, `type`, `account_type`). `lib/jwt.ts`. Falls back to the chosen tab.
3. **Product shape**: the documented request fields; also accepts `price`/`quantity` aliases, bare arrays or `{items|data|results|products|response|hits}` wrappers. `api/types.ts`.
4. **Wallet**: `current_balance`, `balance`, `available_balance` or `amount`.
5. **AI WebSocket**: outgoing JSON `{ "content": "<text>", "message_id": "<uuid>", "conversation_id": "<uuid>" }`; `conversation_id` is omitted for the first message. Incoming `ack` and `done` frames control request state, and streamed `token` deltas are combined into one reply. Errors and questions are shown as assistant messages. `VITE_AI_WS_MESSAGE_FIELD` changes the content field; `api/ai.ts`.
6. **Admin statistics**: rendered generically by `DataBlock` (numbers become cards, arrays become tables). The `period` query is free text, default `all`.
7. **Inventory SKU**: the service generates SKUs on create; updates and deletes identify products by SKU.
8. **Seller product list**: assumed `GET /inventory/` returns the seller's own items. If it returns everything, the backend should filter by token.

## Security notes

Tokens are kept in `localStorage` for simplicity, which is readable by any XSS. For production consider httpOnly cookies set by the auth service. The AI WebSocket passes the token as a query parameter because the backend requires it; make sure proxies don't log full URLs.
