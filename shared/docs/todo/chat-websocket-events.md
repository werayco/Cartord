# Cartord AI Service - Chat WebSocket Events

Frontend integration guide for building the chat UI against the AI service: the websocket event protocol (§1–§4) and the REST endpoint for renaming a conversation (§5).

> Derived from `services/ai_service`: `routers/websocket_router.py`, `controllers/chat_controller.py`, `kafka/consumer.py`, `services/socket_registry.py`, `nodes/order_flow.py`, `services/agent_tools.py`, `services/title_generator.py`, `routers/conversation.py`.

---

## 1. Connecting

```
ws(s)://<host>/api/v1/ws/chat?token=<ACCESS_JWT>
```

- The JWT goes in the **`token` query param**. It must be an **access** token , signed HS256 by the auth service.
- On a missing, invalid or expired token the server rejects the connection **before accepting the handshake** (it closes with `1008`). Browsers usually surface this as a failed connection (`onclose` with code `1006`), not `1008`, so treat "failed to open" as "refresh the token and retry".
- After the connection is open, an unexpected server failure closes the socket with code **`1011`**.
- The AI service listens on port `9000` by default (see the root README). Use whatever your gateway or ingress exposes.

---

## 2. Client → server

One JSON shape, sent as text:

```json
{
  "content": "What's my wallet balance?",
  "conversation_id": "0199...",   // optional
  "message_id": "7b0c..."         // optional
}
```

| Field | Required | Notes |
|---|---|---|
| `content` | **yes** | The user's text. |
| `conversation_id` | no | Omit on the first message of a chat, the server creates a conversation and returns its id in `ack`. **Send it on every later message**, otherwise each message starts a brand-new conversation. Must belong to the signed-in user. |
| `message_id` | no | A UUID. If omitted, the server generates one. Generating it client-side is recommended: you can render the user bubble optimistically and match it to the `ack`. **Never reuse a `message_id`** (it's the primary key of the stored message). |

The same message shape is used to **answer a `question`** (see §3.5): it's just another message in the same `conversation_id`.

---

## 3. Server → client events

Every event is a JSON object with a **`type`** discriminator. Parse each frame and switch on `type`.

### Quick reference

| `type` | Sent when | Key fields |
|---|---|---|
| `ack` | The user message was saved | `message_id`, `conversation_id` |
| `thought` | The agent is working (status text) | `message`, `node?`, `conversation_id`, `message_id` |
| `token` | A chunk of the assistant's reply | `delta`, `conversation_id`, `message_id` |
| `question` | The agent needs more input; the turn is paused | `question`, `conversation_id`, `message_id` |
| `done` | The reply is complete and saved | `conversation_id`, `user_message_id`, `assistant_message_id` |
| `error` | Something failed | `error`, plus ids **only for stream errors** |
| `title` | An auto-generated title is ready for a **new** conversation | `title`, `conversation_id` (no `message_id`) |

### ID cheat sheet

| ID | What it identifies | Where you see it |
|---|---|---|
| `conversation_id` | The chat thread (UUID, server-generated) | every event except protocol-level `error` |
| `message_id` | **The user's message** that triggered the turn | `ack`, `thought`, `token`, `question`, stream `error` |
| `user_message_id` | Same value as the `message_id` above | `done` only (the field is renamed here) |
| `assistant_message_id` | The saved **assistant** reply | `done` only |

> **Important:** `message_id` on `token` / `thought` / `question` is the **user's** message id, not the assistant's. The assistant message only gets its own id in `done`. Key your in-progress assistant bubble by the user's `message_id`, then attach `assistant_message_id` when `done` arrives.

---

### 3.1 `ack`

Sent immediately after the user's message is committed. It confirms receipt and tells you the `conversation_id` (essential for the first message of a new chat).

```json
{"type":"ack","message_id":"xxxxx","conversation_id":"xxxxx"}
```

UI use: mark the user bubble as "sent", store `conversation_id`, show a typing indicator until the next event. For a new chat, this is also the moment to add it to the sidebar with a placeholder name ("New chat") until its `title` arrives (§3.7).

### 3.2 `thought`

A short, human-readable status line about what the agent is doing ("Checking your wallet balance..."). Transient: **not saved** and not part of the reply.

```json
{"type":"thought","node":"wallet_balance_node","message":"Hold on a sec...","conversation_id":"xxxxx","message_id":"xxxxx"}
```

- `message` is safe to show as-is.
- `node` is **optional**. Thoughts from the order-flow nodes include it; thoughts emitted from agent tools (wallet, order summary, shipping address, FAQ lookup) **do not**. Treat it as an opaque label, don't build logic on it.
- A turn can have zero, one or many thoughts, sent before and between tokens.

UI use: a single "status" line under the pending bubble that is **replaced** by each new thought and **cleared** on the first `token`, `question`, `error` or `done`.

<details>
<summary>All current thought messages (for reference / QA)</summary>

| `node` | `message` |
|---|---|
| `collect_order_details` | Checking the product and quantity for your order... · I need a few more details to continue. |
| `validate_item` | Checking your product selection... · Searching the catalog for matching products... · Several products match. Please choose one from the options. |
| `check_wallet` | Checking whether your wallet can cover this order... |
| `confirm_order` | Your order summary is ready for confirmation. |
| `place_order_node` | Submitting your order... |
| `wallet_balance_node` | Retrieving your wallet balance... · Hold on a sec... · Oops! Something is going on... |
| *(none - tools)* | Updating your shipping address... · Your shipping address has been updated. / I couldn't update your shipping address. · Analyzing your order history... · Almost Done... · Your order analytics are ready. / I couldn't retrieve your order analytics. · Checking your wallet balance... · Hold on a sec... · Working on it... · Looking that up in the store knowledge base... · I found the relevant information. |

</details>

### 3.3 `token`

A piece of the assistant's answer. **Append `delta` to the assistant bubble** in arrival order. Don't trim or add whitespace; deltas carry their own spacing.

```json
{"type":"token","conversation_id":"xxxxxx","message_id":"xxxxx","delta":"!"}
```

- Chunk sizes vary; some replies produced by the order flow (e.g. "Done! I've placed your order…") are fixed sentences and may arrive as one large `token` instead of many small ones.
- Render incrementally; if you render Markdown, re-parse the accumulated string rather than each delta.

### 3.4 `done`

The reply is complete **and has been saved**. Finalize the bubble and stop the typing indicator.

```json
{"type":"done","conversation_id":"xxxxxx","user_message_id":"xxxxx","assistant_message_id":"xxxxx"}
```

Use `assistant_message_id` as the stable id for the finished assistant message (keys, copy/regenerate/feedback actions, de-duplication against history).

### 3.5 `question`

The agent needs more input from the user (for example, which product, how many, or "Should I place the order?"). **The turn pauses here, and no `done` follows.**

```json
{"type":"question","conversation_id":"xxxxxx","message_id":"xxxxx","question":"Sure, could you tell me which product you'd like (name or description) and how many you'd like?"}
```

To answer, send a **normal message** (§2) with the **same `conversation_id`**. The server detects the paused flow and treats your message as the answer, then streams the rest of the turn (new `ack`, thoughts, tokens, `done`) under the **new** message's `message_id`.

Answers the flow understands:

| Question | Accepted replies |
|---|---|
| Confirm order ("Should I place the order?") | Confirm: `yes`, `y`, `confirm`, `yeah`, `yep`, `sure`, `go ahead`, `do it`. Anything else is treated as a **no**. |
| Any step | Cancel: `cancel`, `never mind`, `nevermind`, `stop`, `no thanks`, `no` |
| Choose among several products | The option's **number** (`"1"`, `"2"`, …) |
| Missing details | Free text (e.g. "2 black hoodies") |

UI idea: render the question as an assistant bubble and, when it's a confirmation, add **Yes** / **Cancel** quick-reply buttons that simply send `"yes"` / `"cancel"`.

### 3.6 `error`

Two different shapes use the same `type`:

**a) Protocol errors**, returned directly when your message was rejected (no ids):

```json
{"type":"error","error":"Conversation not found"}
```

| `error` | Cause |
|---|---|
| `Conversation not found` | Unknown `conversation_id`, or one that belongs to another user |
| `Missing required field: 'content'` | `content` absent |
| `Invalid ID format` | `conversation_id` / `message_id` isn't a valid UUID |
| `Internal server error` | Unexpected failure (the socket may also close with `1011`) |

**b) Stream errors**, sent while generating a reply (with ids):

```json
{"type":"error","conversation_id":"xxxxx","message_id":"xxxxx","error":"Something went wrong generating a reply, try again."}
```

A stream error ends the turn: **no `done` follows**. Show the error on the matching bubble (by `message_id`) and offer a retry. When retrying, send the text as a **new** message with a new `message_id`.

### 3.7 `title`

The auto-generated title for a **new** conversation, used for the sidebar entry.

```json
{"type":"title","conversation_id":"xxxxx","title":"Wallet balance check"}
```

- **Only once per conversation**, and only for the **first message of a new conversation** (the one you sent without a `conversation_id`). Follow-up messages never produce a `title` event.
- It is generated in the background, in parallel with the reply. It usually arrives somewhere between `ack` and `done`, but it **can arrive after `done`** (or after a `question`), so don't tie it to the end of the turn.
- **No `message_id`.** A title belongs to the conversation, not to a turn. Route it by `conversation_id`.
- Short by design: aimed at 6 words or fewer, hard-capped at 60 characters, in the user's language, without quotes or trailing punctuation.
- It is **not** part of the assistant's reply: it never appears as a `token` and is not stored as a message.
- **Best-effort.** If generation fails, no event is sent and the stored title stays `null`. Fall back to "New chat" (or a truncated first message) and never wait on it or show a spinner indefinitely.
- If the user renames the conversation (§8) before the generated title is ready, the rename wins and **no `title` event is sent** at all.
- Conversations created before this feature existed have a `null` title and will never receive one.

UI use: add the sidebar entry on `ack` with a placeholder, then swap in the text when `title` arrives.

---

## 4. Typical sequences

**New chat (first message, with auto-title)**
```
→ {content:"how much do i have in my wallet?"}                   ← no conversation_id
← ack      {conversation_id: "C1", message_id: "M1"}              ← learn C1 here
← thought  "Retrieving your wallet balance..."
← title    {conversation_id: "C1", title: "Wallet balance check"} ← can land anywhere from here on
← token    "Your wallet balance is 1500.00."
← done
```
The `title` position varies: it may also arrive after `done`.

**Simple lookup (wallet balance)**
```
→ {content:"what's my balance?"}
← ack
← thought  "Retrieving your wallet balance..."
← thought  "Hold on a sec..."
← token    "Your wallet balance is 1500.00."
← done
```

**General question with tool use**
```
← ack
← thought  "Looking that up in the store knowledge base..."   (no `node`)
← thought  "I found the relevant information."
← token … token … token                                      (streamed answer)
← done
```

**Multi-turn: placing an order**
```
→ {content:"I want to buy a hoodie"}
← ack
← thought  (collect_order_details) "Checking the product and quantity…"
← thought  (collect_order_details) "I need a few more details to continue."
← question "Sure, could you tell me how many you'd like?"      ← paused, no done

→ {content:"2", conversation_id}                                 ← the answer
← ack                                                            (new message_id)
← thought … (validate_item / check_wallet / confirm_order)
← question "That's 2 x Hoodie for a total of 80.00. Should I place the order?"

→ {content:"yes", conversation_id}
← ack
← thought  (place_order_node) "Submitting your order..."
← token    "Done! I've placed your order for 2 x Hoodie."
← done
```

---



## 5. REST: rename a conversation

Renaming is a plain REST call that returns JSON. **It does not emit anything over the websocket.**

```
PATCH /api/v1/conversations/{conversation_id}
Authorization: Bearer <ACCESS_JWT>
Content-Type: application/json
```

Note the auth difference: REST takes the token in the `Authorization` header; only the websocket uses the `?token=` query param.

**Request body**

```json
{"title": "My wallet questions"}
```

- 1 to 100 characters after trimming.
- Runs of spaces and newlines are collapsed to a single space, so `"  a   b\n c "` is stored as `"a b c"`.

**Response `200`**

```json
{"id": "xxxxx", "title": "My wallet questions"}
```

**Errors**

| Status | Cause |
|---|---|
| `404` | Conversation doesn't exist **or belongs to another user** (the two are deliberately indistinguishable) |
| `422` | Title blank or longer than 100 characters, or `conversation_id` isn't a valid UUID |
| `401` / `403` | Missing, invalid or expired token |