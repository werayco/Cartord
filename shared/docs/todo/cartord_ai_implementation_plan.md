# Cartord AI Implementation Plan

## Overview

This plan merges two pieces of design work into one build order:

1. **The real-time transport layer** — how a message gets from an open WebSocket, through a transactional outbox, Debezium CDC, Kafka, and back to the client as a streamed reply. This is the plumbing everything else runs on top of.
2. **The Cartord AI feature roadmap** — tool-calling agents for orders, products, admin analytics, and fraud detection, all sitting behind that transport layer.

The ordering matters: nothing in the feature roadmap works reliably until the transport layer underneath it can durably accept a message, guarantee it isn't lost, and route a streamed reply back to the correct client. So this plan starts at **Phase 0 — transport**, then layers the tool-calling agent (Phase 1) and the rest of the original roadmap (Phases 2–7) on top of it.

```text
Phase 0   Real-time transport (WebSocket + outbox + Debezium CDC + Kafka + streaming)
Phase 1   Tool-calling foundation (AI gateway, auth, tool registry, conversation state)
Phase 2   Order assistant
Phase 3   Product intelligence
Phase 4   Transactional AI (make_order, reorder, returns)
Phase 5   Admin AI analytics
Phase 6   Fraud detection
Phase 7   AI business intelligence
```

Each later phase assumes the AI worker described in Phase 0 is the same process that Phase 1 turns into a tool-calling agent — you are not building two separate systems, you're adding capability to one.

---

# Phase 0 — Real-Time Transport Foundation

## Goal

Get a message from an open WebSocket connection into the database durably, acknowledge it to the client immediately, and have Debezium CDC carry it downstream to an AI worker — without the client ever waiting on Kafka, Debezium, or the LLM.

## Why this comes first

Every later phase (order assistant, product search, admin analytics) is just "more tools the AI worker can call." None of that matters if the transport layer drops messages, blocks on downstream infra, or can't route a streamed reply back to the right socket when you're running more than one gateway pod. Build this once, correctly, before adding agent logic on top.

## Architecture

```text
Client
  |
  | WebSocket message
  v
Gateway pod (WS handler)
  |
  | single DB transaction:
  |   insert into messages
  |   insert into outbox_events
  v
PostgreSQL  ------------------->  ack frame sent back to client immediately
  |                                  (conversation_id + message_id, no waiting)
  | WAL
  v
Debezium CDC  (reads WAL directly, no polling, no locking)
  |
  v
Kafka topic: chat.messages   (keyed by conversation_id, preserves order)
  |
  v
AI worker (consumer)
  |
  +--> loads conversation history
  +--> calls LLM, streams tokens
  +--> publishes tokens to Redis pub/sub channel: conversation:{id}
  +--> persists final assistant message to `messages` on completion
  |
  v
Redis pub/sub
  |
  v
Whichever gateway pod is subscribed to conversation:{id}
  |
  v
Client receives streamed reply over its open socket
```

Only the DB transaction and the ack sit on the client's critical path. Everything from Debezium onward is fully asynchronous.

## Key design decisions

- **One DB transaction, not two writes.** The message row and the outbox row are inserted together and committed together. If they aren't atomic, you can end up with a message that was saved but never announced downstream, or an outbox event pointing at a message that doesn't exist.
- **Respond the instant the transaction commits.** Do not wait for Debezium, Kafka, or the AI worker to do anything before sending the ack. The client's `conversation_id` comes from this commit, not from any downstream step.
- **Debezium CDC, not a polling worker.** Since this is log-based CDC reading the Postgres WAL directly, there's only one reader — no race conditions, so no `claimed_by` / `claimed_at` locking columns are needed on the outbox table. Keep a `published_at` timestamp purely for observability and cleanup, not coordination.
- **Redis pub/sub solves cross-pod routing.** The AI worker that generates a reply is a different process from whichever gateway pod is holding the client's actual socket. Each gateway pod subscribes to a `conversation:{id}` channel the moment a socket for that conversation opens, and unsubscribes on disconnect. The AI worker just publishes to the channel — it never needs to know which pod holds the connection.
- **The database is the source of truth, not the stream.** Tokens are streamed live for UX, but the assistant's full reply is only considered durable once it's written to `messages`. A client that disconnects mid-generation loses nothing — on reconnect it does a plain `GET /conversations/{id}/messages` to catch up.
- **Idempotency via client-generated message IDs.** Every user message carries a UUID generated on the client before it's sent. If Kafka redelivers an event (e.g. the AI worker crashed mid-stream), check whether a reply already exists for that `message_id` before generating a second one.
- **Dead-letter on repeated failure.** If the AI worker can't produce a reply after a bounded number of retries (LLM timeout, provider error), route to a dead-letter topic and surface a fallback message rather than retrying forever or failing silently.

## Schema

**conversations**

| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | generated server-side on first message |
| user_id | uuid, FK | owner |
| created_at | timestamptz | |
| title | text, nullable | can be backfilled by the AI worker after first reply |

**messages**

| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | client-generated for user messages — enables idempotency checks |
| conversation_id | uuid, FK | indexed |
| role | enum | `user` / `assistant` / `system` |
| content | text | |
| created_at | timestamptz | |

**outbox_events**

| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| event_type | text | e.g. `message_created` |
| conversation_id | uuid | used as the Kafka partition key |
| payload | jsonb | event body Debezium/Kafka Connect forwards |
| created_at | timestamptz | |
| published_at | timestamptz, nullable | observability only |

## Deliverables

- [ ] WebSocket gateway service with connection registry per pod
- [ ] `conversations`, `messages`, `outbox_events` tables + migrations
- [ ] Transactional write path (message + outbox insert, single transaction)
- [ ] Ack frame sent on commit
- [ ] Debezium connector configured against the outbox table, publishing to `chat.messages`
- [ ] AI worker skeleton: consumes `chat.messages`, loads history, calls LLM (stubbed response is fine at this stage), persists reply
- [ ] Redis pub/sub wiring: gateway subscribe/unsubscribe on connect/disconnect, AI worker publish on token
- [ ] Reconnect/catch-up REST endpoint: `GET /conversations/{id}/messages`
- [ ] Dead-letter topic + basic retry policy for the AI worker

## Exit criteria

A client can open a socket, send a message, get an immediate ack with a `conversation_id`, and receive a streamed (even if canned/stubbed) reply — correctly, even if the gateway pod that sent the ack is different from the one that ends up delivering the reply. Killing the AI worker mid-stream and restarting it should not produce a duplicate reply.

---

# Phase 1 — Tool-Calling Foundation

## Goal

Turn the AI worker from Phase 0 into an actual tool-calling agent, with authentication, authorization, and a registry of typed tools it's allowed to call — instead of a bare LLM wrapper.

## Deliverables
- [ ] AI gateway layer sitting in front of the LLM call inside the AI worker.
- [ ] Authentication context threaded through from the WebSocket connection into every tool call (the LLM never gets to decide who a user is).
- [ ] Tool registry: strongly typed tool definitions, each mapped to a real Cartord service call.
- [ ] Per-tool authorization checks (ownership, role, order state) enforced in the tool implementation, never inferred by the LLM.
- [ ] Conversation state management (message history windowing/summarization as conversations grow long).
- [ ] Structured tool response contracts (the LLM explains structured data, it doesn't invent it).
- [ ] Confirmation step for any destructive tool call (cancel, create, refund, modify).
## Guardrails carried over from the roadmap

```text
User A
  |
  | "Cancel ORD-999"
  v
AI worker
  |
  v
cancel_order()
  |
  +--> Authenticate user
  +--> Verify ownership
  +--> Validate order state
  +--> Execute cancellation
```

Never:

```text
LLM  --->  Raw SQL  --->  Production DB
```

The LLM calls tools. The tools enforce the rules. This applies to every phase from here on.

## Exit criteria
The AI worker can call at least one real tool end-to-end (e.g. `faq()` against a knowledge base) with full auth context, and refuses to call any tool the authenticated user isn't allowed to invoke.

---

# Phase 2 — Order Assistant

## Goal

Customer-facing order tools, built on the tool-calling foundation from Phase 1.

## Tools

```text
get_order(order_id)
track_order(order_id)
cancel_order(order_id)
order_failure_details(order_id)
get_order_history(user_id)
faq(query)
```

## Notes

- `cancel_order` never lets the LLM decide cancellability — the order service checks ownership, order state, and refund rules.
- `order_failure_details` returns structured failure data (`reason_code`, `retryable`, etc.); the LLM converts it to a human-readable explanation, it doesn't guess at reasons.
- `faq` is backed by a knowledge base / RAG lookup against real policy docs — not the model's own assumptions about Cartord's policies.

## Exit criteria

A user can ask "where's my order," "cancel my order," and "why did my order fail" in natural language and get correct, authorized, tool-backed answers.

---

# Phase 3 — Product Intelligence

## Goal

Give the assistant real understanding of the product catalog.

## Tools

```text
search_products(query, filters)
compare_products(product_ids)
recommend_products(user_id, context)
find_similar_products(product_id)
check_product_stock(product_id)
```

## Architecture

```text
User query
    |
    v
LLM
    |
    +--> structured filters
    |
    +--> embedding
             |
             v
        pgvector
             |
             v
      candidate products
             |
             v
        ranking layer
             |
             v
          results
```

## Notes

- Add PostgreSQL + pgvector for embedding-based semantic search and similarity lookups.
- Stock checks always hit live inventory — never rely on the model's memory of a prior answer in the conversation.

## Exit criteria

Natural-language product queries ("laptop under ₦1.2M with 16GB RAM") resolve to a correctly filtered, ranked result set.

---

# Phase 4 — Transactional AI

## Goal

Let the assistant actually create and modify orders — the highest-risk phase, so it leans hardest on the confirmation and idempotency work from Phase 0/1.

## Tools

```text
make_order(product_id, quantity, ...)
reorder(order_id)
check_return_eligibility(order_id)
create_return_request(order_id, item_id, reason)
get_refund_status(order_id)
change_delivery_address(order_id, address_id)
change_order_quantity(order_id, item_id, quantity)
```

## Flow example

```text
User: "Buy 2 MX Keys"
  |
  v
AI: search_product()
  |
  v
Product Service: product + price + stock
  |
  v
AI: "I found 2 available at ₦X. Confirm?"
  |
  v
User: "Yes"
  |
  v
make_order()
```

## Notes

- Every destructive/transactional tool requires explicit user confirmation before execution.
- `reorder` re-validates current stock and current prices — it never blindly replays a past order.
- Idempotency keys (reusing the Phase 0 `message_id` pattern) prevent a retried tool call from double-charging or double-creating an order.

## Exit criteria

A full "search → confirm → order" flow works end-to-end, and replaying the same tool call (simulated network retry) does not create a duplicate order.

---

# Phase 5 — Admin AI Analytics

## Goal

Give admin users a natural-language interface over safe, predefined analytics tools — never direct SQL access.

## Tools

```text
get_user_count()
get_top_products(limit, period)
get_revenue(period)
get_order_statistics(period)
get_customer_statistics(period)
get_product_performance(product_id, period)
get_low_stock_products()
get_out_of_stock_products()
get_inventory_summary()
get_sales_trends(period, granularity)
get_revenue_breakdown(period, dimension)
get_failed_order_statistics(period)
get_customer_segments()
```

## Notes

- Admin authorization is enforced before any tool in this set executes — same pattern as customer-facing tools, different role check.
- The backend computes real metrics; the LLM only explains and summarizes them. Numbers never come from the model.

## Exit criteria

An admin can ask "how much revenue did we make this month" or "which products are almost out of stock" and get accurate, tool-sourced answers with no hallucinated figures.

---

# Phase 6 — Fraud Detection

## Goal

A dedicated risk/fraud service that the AI layer can query and explain, not something the LLM scores itself.

## Architecture

```text
Order
  |
  v
Risk Service
  |
  +--> feature extraction
  +--> ML model
  +--> rules engine
  |
  v
Risk score --> LOW / MEDIUM / HIGH
```

## Tools

```text
get_high_risk_orders()
get_order_risk(order_id)
get_user_risk_profile(user_id)
```

## Notes

- Risk scores and their explanations come from the risk service's actual model features — the LLM narrates them, it doesn't invent contributing factors.
- Example explanation format the service should return, for the LLM to summarize:

```text
High-risk factors:
- Order value is significantly above the user's normal spending.
- Multiple payment attempts occurred within a short period.
- Billing and shipping information do not match.
```

## Exit criteria

Admins can pull today's high-risk orders and get a correct, explainable summary of why each one was flagged.

---

# Phase 7 — AI Business Intelligence

## Goal

The most advanced layer: proactive, cross-metric insight generation for admins.

## Deliverables

- [ ] Automated business insights ("what should I be worried about in the store?")
- [ ] Anomaly detection across revenue, orders, and inventory metrics
- [ ] Sales forecasting
- [ ] Customer segmentation (potentially ML clustering)
- [ ] Inventory demand forecasting
- [ ] AI-generated daily/weekly reports

## Example

The analytics system feeds the LLM structured deltas:

```text
Revenue: -14%
Orders: -8%
Failed payments: +31%
Inventory stockouts: +18%
Returning customers: +2%
```

The LLM produces something like:

> "The biggest issue appears to be payment failures, which increased 31% this period. Stockouts are also increasing and may be contributing to the decline in orders."

The LLM explains the data — it never manufactures the metrics.

## Exit criteria

A weekly digest is generated automatically, summarizing real metric movements with correct, traceable explanations.

---

# Cross-Cutting Security Rules (apply to every phase)

- The AI layer never bypasses normal Cartord authorization — every tool call re-checks ownership/role/state itself, regardless of what the LLM "believes."
- The LLM never gets raw SQL access, in any phase.
- Destructive operations (cancel, create, refund, modify) always require explicit user confirmation.
- All monetary figures, risk scores, and analytics numbers are computed by backend services — the LLM's job is explanation, never computation.

---

# Final Feature Set

### Transport (Phase 0)
- [ ] WebSocket gateway with per-pod connection registry
- [ ] Transactional outbox
- [ ] Debezium CDC → Kafka
- [ ] AI worker with streaming
- [ ] Redis pub/sub cross-pod routing
- [ ] Reconnect/catch-up endpoint

### Customer AI
- [ ] FAQ assistant
- [ ] Semantic product search
- [ ] Product recommendations
- [ ] Product comparison
- [ ] Product availability lookup
- [ ] Order tracking
- [ ] Order history
- [ ] Order failure explanations
- [ ] Order cancellation
- [ ] Make order through natural language
- [ ] Reorder previous purchases
- [ ] Return/refund assistant
- [ ] Change eligible order details
- [ ] General customer support agent

### Risk / Fraud AI
- [ ] Transaction risk scoring
- [ ] Fraud classification
- [ ] Risk explanations
- [ ] High-risk order detection
- [ ] User risk profiles
- [ ] Fraud investigation tools
- [ ] Anomaly detection

### Admin AI
- [ ] User count
- [ ] New/active user statistics
- [ ] Total orders, success/failure rate
- [ ] Revenue, average order value
- [ ] Best-selling products
- [ ] Product performance
- [ ] Low-stock / out-of-stock products
- [ ] Sales trends
- [ ] Revenue breakdown
- [ ] Failed-order analysis
- [ ] Customer segmentation and retention
- [ ] AI business insights
- [ ] Automated daily/weekly reports
- [ ] Sales forecasting
- [ ] Demand forecasting

---

# Portfolio Framing

Not:

> "I added ChatGPT to Cartord."

Instead:

> **AI-powered commerce infrastructure with tool-calling agents, event-driven real-time delivery, semantic search, recommendation systems, fraud detection, and natural-language business analytics.**

That framing spans:

```text
Real-time systems (WebSockets, transactional outbox, Debezium CDC, Kafka)
     +
LLM / Agents (tool-calling, structured responses)
     +
RAG / Vector Search (pgvector)
     +
Traditional ML (fraud scoring, forecasting, segmentation)
     +
Backend Architecture (services, authorization, idempotency)
     +
Event-Driven Systems
     +
Observability
     +
Analytics
     +
Payments / Risk
```

The end state: an AI agent that can safely move between chat, products, orders, payments, and analytics, with every action executed through strongly typed, authorized Cartord tools — sitting on a transport layer that never loses a message and never blocks a client on downstream infrastructure.
