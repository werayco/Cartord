import type { Role } from "../api/types";

export function decodeJwt(token: string): Record<string, unknown> {
  try {
    const payload = token.split(".")[1];
    if (!payload) return {};
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as Record<string, unknown>;
  } catch {
    return {};
  }
}

/**
 * Works out the account role from the token claims. The claim name is not documented in the
 * repo, so several common names are checked; `hint` is used when none match.
 */
export function resolveRole(token: string, hint: Role): Role {
  const claims = decodeJwt(token);
  const raw = [claims.role, claims.roles, claims.user_type, claims.type, claims.account_type]
    .flat()
    .filter((v): v is string => typeof v === "string")
    .join(" ")
    .toLowerCase();
  if (/admin|employee|staff/.test(raw)) return "admin";
  if (/seller|vendor|merchant/.test(raw)) return "seller";
  if (/buyer|customer/.test(raw)) return "buyer";
  return hint;
}
