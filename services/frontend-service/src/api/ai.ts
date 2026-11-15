import { config } from "../config/env";
import { normalizeProduct, type Product } from "./types";

export type ChatStatus = "connecting" | "open" | "closed";

export interface ProductChoice {
  number: number;
  name: string;
  price: number;
  description: string;
}

export interface HistoryOrder {
  sku: string;
  quantity: number;
  unitPrice: number;
  status: string;
  createdAt: string;
}

export type ChatCard =
  | { kind: "product_choices"; items: ProductChoice[] }
  | { kind: "order_summary"; name: string; sku: string; quantity: number; unitPrice: number; total: number }
  | { kind: "order_history"; totalOrders: number; deliveredOrders: number; totalSpend: number; orders: HistoryOrder[] }
  | { kind: "yes_no"; yes: string; no: string }
  | { kind: "shipping_address"; shippingAddress: string };

export interface IncomingChat {
  type: string;
  text: string;
  products: Product[];
  card?: ChatCard;
  cards?: ChatCard[];
  conversationId?: string;
  messageId?: string;
  title?: string;
}

const TEXT_KEYS = ["response", "message", "content", "text", "answer", "reply", "output"];

function firstString(o: Record<string, unknown>): string | undefined {
  for (const k of TEXT_KEYS) if (typeof o[k] === "string" && o[k]) return o[k] as string;
  return undefined;
}

function readNumber(value: unknown): number | undefined {
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export function readCard(value: unknown): ChatCard | undefined {
  if (!value || typeof value !== "object") return undefined;
  const card = value as Record<string, unknown>;
  if (card.kind === "product_choices" && Array.isArray(card.items)) {
    const items: ProductChoice[] = [];
    for (const raw of card.items) {
      if (!raw || typeof raw !== "object") continue;
      const item = raw as Record<string, unknown>;
      const number = readNumber(item.number);
      const price = readNumber(item.price);
      if (number === undefined || price === undefined || typeof item.name !== "string") continue;
      items.push({
        number,
        name: item.name,
        price,
        description: typeof item.description === "string" ? item.description : "",
      });
    }
    return items.length ? { kind: "product_choices", items } : undefined;
  }
  if (card.kind === "order_history") {
    const totalOrders = readNumber(card.total_orders);
    const deliveredOrders = readNumber(card.delivered_orders);
    const totalSpend = readNumber(card.total_spend);
    if (totalOrders === undefined || deliveredOrders === undefined || totalSpend === undefined) return undefined;
    const orders: HistoryOrder[] = [];
    if (Array.isArray(card.orders)) {
      for (const raw of card.orders) {
        if (!raw || typeof raw !== "object") continue;
        const item = raw as Record<string, unknown>;
        const quantity = readNumber(item.quantity);
        const unitPrice = readNumber(item.unit_price);
        if (quantity === undefined || unitPrice === undefined || typeof item.sku !== "string") continue;
        orders.push({
          sku: item.sku,
          quantity,
          unitPrice,
          status: typeof item.status === "string" ? item.status : "",
          createdAt: typeof item.created_at === "string" ? item.created_at : "",
        });
      }
    }
    return { kind: "order_history", totalOrders, deliveredOrders, totalSpend, orders };
  }
  if (card.kind === "shipping_address" && typeof card.shipping_address === "string" && card.shipping_address) {
    return { kind: "shipping_address", shippingAddress: card.shipping_address };
  }
  if (card.kind === "yes_no") {
    const yes = typeof card.yes === "string" && card.yes ? card.yes : "Yes";
    const no = typeof card.no === "string" && card.no ? card.no : "No";
    return { kind: "yes_no", yes, no };
  }
  if (card.kind === "order_summary" && typeof card.name === "string") {
    const quantity = readNumber(card.quantity);
    const unitPrice = readNumber(card.unit_price);
    const total = readNumber(card.total);
    if (quantity === undefined || unitPrice === undefined || total === undefined) return undefined;
    return {
      kind: "order_summary",
      name: card.name,
      sku: typeof card.sku === "string" ? card.sku : "",
      quantity,
      unitPrice,
      total,
    };
  }
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
  const listed = Array.isArray(o.cards) ? o.cards.flatMap((item) => {
    const parsedCard = readCard(item);
    return parsedCard ? [parsedCard] : [];
  }) : [];
  const card = readCard(o.card);
  const cards = listed.length ? listed : card ? [card] : [];
  const eventText =
    type === "token" && typeof o.delta === "string"
      ? o.delta
      : type === "error" && typeof o.error === "string"
        ? o.error
        : type === "question" && typeof o.question === "string"
          ? o.question
          : type === "thought" && typeof o.message === "string"
            ? o.message
            : type === "ack" || type === "done" || type === "title" || type === "card"
              ? ""
              : firstString(o) ?? (products.length || cards.length ? "" : JSON.stringify(parsed));
  return {
    type,
    text: eventText,
    products,
    card: cards[0],
    cards,
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
