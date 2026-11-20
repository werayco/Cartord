import { request } from "./http";
import { extractTokens } from "./tokenStore";
import { normalizeUser, type Role, type SessionUser } from "./types";
import { decodeJwt } from "../lib/jwt";

const base = "/api/v1/auth";
const seg = (role: Role) => (role === "seller" ? "seller" : "buyer");

export interface RegisterBuyer {
  email: string;
  name: string;
  username: string;
  password: string;
  shipping_address: string;
}
export type RegisterSeller = Omit<RegisterBuyer, "shipping_address">;

export const authApi = {
  async login(role: Role, username: string, password: string) {
    const data = await request("auth", `${base}/${seg(role)}/login`, {
      method: "POST",
      auth: false,
      body: { username, password },
    });
    return extractTokens(data);
  },

  registerBuyer: (body: RegisterBuyer) =>
    request("auth", `${base}/buyer/register`, { method: "POST", auth: false, body }),

  registerSeller: (body: RegisterSeller) =>
    request("auth", `${base}/seller/register`, { method: "POST", auth: false, body }),

  async me(role: Role, accessToken: string): Promise<SessionUser> {
    // No admin /me endpoint is documented; derive the admin identity from the token claims.
    if (role === "admin") return normalizeUser(decodeJwt(accessToken));
    return normalizeUser(await request("auth", `${base}/${seg(role)}/me`));
  },

  updateBuyer: (patch: Partial<Pick<SessionUser, "name" | "email" | "username" | "shipping_address">>) =>
    request("auth", `${base}/buyer/update`, { method: "PATCH", body: patch }),

  changePassword: (role: Role, old_password: string, new_password: string) =>
    request("auth", `${base}/${seg(role)}/change-password`, {
      method: "POST",
      body: { old_password, new_password },
    }),

  deleteBuyer: (username: string, password: string) =>
    request("auth", `${base}/buyer/delete`, { method: "DELETE", body: { username, password } }),

  adminUserCount: () => request("auth", `${base}/admin/users/count`),
  adminCustomerStats: (period: string) =>
    request("auth", `${base}/admin/customers/statistics`, { query: { period } }),
};
