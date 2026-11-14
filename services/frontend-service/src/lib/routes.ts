import type { Role } from "../api/types";

export const homeFor = (role: Role | null): string =>
  role === "admin" ? "/admin" : role === "seller" ? "/seller" : role === "buyer" ? "/shop" : "/signin";
