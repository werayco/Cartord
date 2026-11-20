export type Role = "buyer" | "seller" | "admin";

export interface ProductImage {
  id: string;
  url: string;
  alt_text?: string | null;
  sort_order: number;
}

export interface Product {
  id?: string | number;
  sku: string;
  name: string;
  description: string;
  unit_price: number;
  available_quantity: number;
  reserved_quantity: number;
  images: ProductImage[];
}

const num = (v: unknown, fallback = 0): number => {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
};

export function normalizeProduct(raw: unknown): Product {
  const r = (raw ?? {}) as Record<string, unknown>;
  // Elasticsearch-style hits keep the document in _source
  const s = (r._source && typeof r._source === "object" ? r._source : r) as Record<string, unknown>;
  return {
    id: (s.id ?? r._id) as string | number | undefined,
    sku: String(s.sku ?? ""),
    name: String(s.name ?? s.title ?? "Untitled product"),
    description: String(s.description ?? ""),
    unit_price: num(s.unit_price ?? s.price),
    available_quantity: num(s.available_quantity ?? s.quantity ?? s.stock),
    reserved_quantity: num(s.reserved_quantity),
    images: Array.isArray(s.images)
      ? s.images.flatMap((image): ProductImage[] => {
          if (!image || typeof image !== "object") return [];
          const item = image as Record<string, unknown>;
          if (typeof item.url !== "string" || typeof item.id !== "string") return [];
          return [{
            id: item.id,
            url: item.url,
            alt_text: typeof item.alt_text === "string" ? item.alt_text : null,
            sort_order: num(item.sort_order),
          }];
        })
      : [],
  };
}

/** Accepts a bare array or common wrappers ({items}, {data}, {results}, ES {hits:{hits}}). */
export function unwrapList(raw: unknown): unknown[] {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object") {
    const o = raw as Record<string, unknown>;
    for (const key of ["items", "data", "results", "products", "response", "hits"]) {
      const v = o[key];
      if (Array.isArray(v)) return v;
      if (v && typeof v === "object" && Array.isArray((v as Record<string, unknown>).hits)) {
        return (v as Record<string, unknown>).hits as unknown[];
      }
    }
  }
  return [];
}

export const toProducts = (raw: unknown): Product[] => unwrapList(raw).map(normalizeProduct);

export interface Wallet {
  balance: number;
  raw: Record<string, unknown>;
}

export function normalizeWallet(raw: unknown): Wallet {
  const r = (raw ?? {}) as Record<string, unknown>;
  return { balance: num(r.balance ?? r.current_balance ?? r.available_balance ?? r.amount), raw: r };
}

export interface SessionUser {
  name: string;
  username: string;
  email: string;
  shipping_address?: string;
}

export function normalizeUser(raw: unknown): SessionUser {
  const r = (raw ?? {}) as Record<string, unknown>;
  const username = String(r.username ?? r.sub ?? "");
  return {
    name: String(r.name ?? r.full_name ?? username),
    username,
    email: String(r.email ?? ""),
    shipping_address: r.shipping_address ? String(r.shipping_address) : undefined,
  };
}
