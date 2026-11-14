import { config } from "../config/env";
import { normalizeProduct, type Product } from "./types";

export type ChatStatus = "connecting" | "open" | "closed";

export interface IncomingChat {
  type: string;
  text: string;
  products: Product[];
  conversationId?: string;
  messageId?: string;
  title?: string;
}

const TEXT_KEYS = ["response", "message", "content", "text", "answer", "reply", "output"];

function firstString(o: Record<string, unknown>): string | undefined {
  for (const k of TEXT_KEYS) if (typeof o[k] === "string" && o[k]) return o[k] as string;
  return undefined;
}

export function decodeIncoming(data: string): IncomingChat {
  let parsed: unknown = data;
  try {
    parsed = JSON.parse(data);
  } catch {
    /* plain text frame */
  }
  if (typeof parsed === "string") return { type: "message", text: parsed, products: [] };
  if (!parsed || typeof parsed !== "object") return { type: "message", text: String(parsed), products: [] };

  let o = parsed as Record<string, unknown>;
  if (o.data && typeof o.data === "object" && !Array.isArray(o.data)) {
    o = { ...o, ...(o.data as Record<string, unknown>) };
  }
  const type = typeof o.type === "string" ? o.type : "message";
  const list = o.products ?? o.recommendations ?? o.items;
  const products = Array.isArray(list) ? list.map(normalizeProduct) : [];
  const eventText =
    type === "token" && typeof o.delta === "string"
      ? o.delta
      : type === "error" && typeof o.error === "string"
        ? o.error
        : type === "question" && typeof o.question === "string"
          ? o.question
          : type === "thought" && typeof o.message === "string"
            ? o.message
            : type === "ack" || type === "done" || type === "title"
              ? ""
              : firstString(o) ?? (products.length ? "" : JSON.stringify(parsed));
  return {
    type,
    text: eventText,
    products,
    conversationId: typeof o.conversation_id === "string" ? o.conversation_id : undefined,
    messageId: typeof o.message_id === "string" ? o.message_id : undefined,
    title: typeof o.title === "string" ? o.title : undefined,
  };
}

export function encodeOutgoing(text: string, messageId: string, conversationId?: string): string {
  return JSON.stringify({
    [config.aiWsMessageField]: text,
    message_id: messageId,
    ...(conversationId ? { conversation_id: conversationId } : {}),
  });
}

interface Handlers {
  onStatus: (s: ChatStatus) => void;
  onMessage: (m: IncomingChat) => void;
}

export class ChatSocket {
  private ws: WebSocket | null = null;
  private attempts = 0;
  private stopped = false;
  private timer: number | undefined;
  private token: string;
  private handlers: Handlers;

  constructor(token: string, handlers: Handlers) {
    this.token = token;
    this.handlers = handlers;
  }

  connect() {
    this.stopped = false;
    this.handlers.onStatus("connecting");
    const url = `${config.aiWsUrl}?token=${encodeURIComponent(this.token)}`;
    const ws = new WebSocket(url);
    this.ws = ws;
    ws.onopen = () => {
      this.attempts = 0;
      this.handlers.onStatus("open");
    };
    ws.onmessage = (ev) => this.handlers.onMessage(decodeIncoming(String(ev.data)));
    ws.onclose = () => {
      this.handlers.onStatus("closed");
      if (this.stopped) return;
      const delay = Math.min(15000, 1000 * 2 ** this.attempts++);
      this.timer = window.setTimeout(() => this.connect(), delay);
    };
    ws.onerror = () => ws.close();
  }

  send(text: string, messageId: string, conversationId?: string): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) return false;
    this.ws.send(encodeOutgoing(text, messageId, conversationId));
    return true;
  }

  close() {
    this.stopped = true;
    window.clearTimeout(this.timer);
    this.ws?.close();
  }
}
