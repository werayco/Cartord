import { config, type ServiceName } from "../config/env";
import { extractTokens, tokenStore } from "./tokenStore";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  form?: FormData;
  query?: Record<string, string | number | undefined | null>;
  /** Send the bearer token. Defaults to true. */
  auth?: boolean;
  signal?: AbortSignal;
}

function messageFrom(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail)) {
    const parts = detail.map((d) =>
      d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : String(d),
    );
    if (parts.length) return parts.join(", ");
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return fallback;
}

function buildUrl(service: ServiceName, path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${config.services[service]}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

async function send(service: ServiceName, url: string, opts: RequestOptions, token: string | null) {
  const headers: Record<string, string> = { Accept: "application/json" };
  let body: BodyInit | undefined;
  if (opts.form) {
    body = opts.form;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    return await fetch(url, { method: opts.method ?? "GET", headers, body, signal: opts.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(
      `Can't reach the ${service} service. Check your connection and the service URL.`,
      0,
    );
  }
}

let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const { access, refresh, role } = tokenStore.get();
  if (!refresh) return false;
  const segment = role === "seller" ? "seller" : "buyer";
  try {
    const res = await fetch(`${config.services.auth}/api/v1/auth/${segment}/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(access ? { Authorization: `Bearer ${access}` } : {}),
      },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const next = extractTokens(await res.json());
    if (!next.access) return false;
    tokenStore.set({ access: next.access, refresh: next.refresh ?? refresh, role });
    return true;
  } catch {
    return false;
  }
}

export async function request<T = unknown>(
  service: ServiceName,
  path: string,
  opts: RequestOptions = {},
): Promise<T> {
  const auth = opts.auth ?? true;
  const url = buildUrl(service, path, opts.query);
  let res = await send(service, url, opts, auth ? tokenStore.get().access : null);

  if (res.status === 401 && auth && tokenStore.get().refresh) {
    refreshing ??= refreshTokens().finally(() => {
      refreshing = null;
    });
    if (await refreshing) res = await send(service, url, opts, tokenStore.get().access);
  }

  if (res.status === 401 && auth) {
    tokenStore.clear();
    window.dispatchEvent(new Event("cartord:unauthorized"));
  }

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data ? (data as { detail: unknown }).detail : data;
    const fallback =
      res.status === 403
        ? "You don't have permission to do that."
        : res.status === 404
          ? "We couldn't find what you asked for."
          : `Request failed (${res.status}).`;
    throw new ApiError(messageFrom(detail, fallback), res.status, detail);
  }
  return data as T;
}

export const errorMessage = (e: unknown): string =>
  e instanceof Error ? e.message : "Something went wrong. Try again.";
