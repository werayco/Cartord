import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi, type RegisterBuyer, type RegisterSeller } from "../api/auth";
import { tokenStore } from "../api/tokenStore";
import type { Role, SessionUser } from "../api/types";
import { resolveRole } from "../lib/jwt";

type Status = "loading" | "authed" | "anon";

interface AuthValue {
  status: Status;
  role: Role | null;
  user: SessionUser | null;
  login: (role: Exclude<Role, "admin">, username: string, password: string) => Promise<Role>;
  registerBuyer: (body: RegisterBuyer) => Promise<void>;
  registerSeller: (body: RegisterSeller) => Promise<void>;
  logout: () => void;
  reloadUser: () => Promise<void>;
}

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>(() => (tokenStore.get().access ? "loading" : "anon"));
  const [role, setRole] = useState<Role | null>(tokenStore.get().role);
  const [user, setUser] = useState<SessionUser | null>(null);

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setRole(null);
    setStatus("anon");
  }, []);

  const loadUser = useCallback(async () => {
    const { access, role: stored } = tokenStore.get();
    if (!access || !stored) throw new Error("No session");
    const me = await authApi.me(stored, access);
    setUser(me);
    setRole(stored);
    setStatus("authed");
  }, []);

  useEffect(() => {
    if (tokenStore.get().access) {
      loadUser().catch(() => logout());
    }
  }, [loadUser, logout]);

  useEffect(() => {
    window.addEventListener("cartord:unauthorized", logout);
    return () => window.removeEventListener("cartord:unauthorized", logout);
  }, [logout]);

  const login = useCallback(
    async (chosen: Exclude<Role, "admin">, username: string, password: string) => {
      const tokens = await authApi.login(chosen, username, password);
      if (!tokens.access) throw new Error("The server did not return an access token.");
      const resolved = resolveRole(tokens.access, chosen);
      tokenStore.set({ access: tokens.access, refresh: tokens.refresh, role: resolved });
      await loadUser();
      return resolved;
    },
    [loadUser],
  );

  const value = useMemo<AuthValue>(
    () => ({
      status,
      role,
      user,
      login,
      registerBuyer: async (b) => void (await authApi.registerBuyer(b)),
      registerSeller: async (b) => void (await authApi.registerSeller(b)),
      logout,
      reloadUser: loadUser,
    }),
    [status, role, user, login, logout, loadUser],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside <AuthProvider>");
  return v;
}
