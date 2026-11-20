import type { Role } from "./types";

interface Stored {
  access: string | null;
  refresh: string | null;
  role: Role | null;
}

const KEY = "cartord.session";
const empty: Stored = { access: null, refresh: null, role: null };
let cache: Stored | null = null;

function read(): Stored {
  if (cache) return cache;
  try {
    const raw = localStorage.getItem(KEY);
    cache = raw ? { ...empty, ...(JSON.parse(raw) as Partial<Stored>) } : { ...empty };
  } catch {
    cache = { ...empty };
  }
  return cache;
}

export const tokenStore = {
  get: (): Stored => read(),
  set(next: Stored) {
    cache = next;
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* storage unavailable: session lasts until reload */
    }
  },
  clear() {
    cache = { ...empty };
    try {
      localStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  },
};

/** The token response shape is not documented; accept the usual names. */
export function extractTokens(data: unknown): { access: string | null; refresh: string | null } {
  const response = data && typeof data === "object" ? (data as Record<string, unknown>) : {};
  const nested = response.tokens;
  const tokens =
    nested && typeof nested === "object" ? (nested as Record<string, unknown>) : response;
  const access = tokens.access_token ?? tokens.accessToken ?? tokens.token;
  const refresh = tokens.refresh_token ?? tokens.refreshToken;
  return {
    access: typeof access === "string" ? access : null,
    refresh: typeof refresh === "string" ? refresh : null,
  };
}
