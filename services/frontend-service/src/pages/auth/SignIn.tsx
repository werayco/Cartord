import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { errorMessage } from "../../api/http";
import type { Role } from "../../api/types";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { InlineError, InlineSuccess } from "../../components/ui/feedback";
import { homeFor } from "../../lib/routes";
import { required, hasErrors, type Errors } from "../../lib/validate";

type LoginRole = Exclude<Role, "admin">;

const roles: Array<{ id: LoginRole; label: string }> = [
  { id: "buyer", label: "Buyer" },
  { id: "seller", label: "Seller" },
];

function getRedirectTarget(value: unknown): string | null {
  let target: string | null = null;
  if (typeof value === "string") {
    target = value;
  } else if (value && typeof value === "object") {
    const location = value as Record<string, unknown>;
    if (typeof location.pathname === "string") {
      target = `${location.pathname}${typeof location.search === "string" ? location.search : ""}${typeof location.hash === "string" ? location.hash : ""}`;
    }
  }

  if (!target || !target.startsWith("/") || target.startsWith("//")) return null;
  if (target.split(/[?#]/, 1)[0] === "/signin") return null;
  return target;
}

export function RoleTabs<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: Array<{ id: T; label: string }>;
}) {
  return (
    <div role="tablist" className="grid rounded-full bg-ink/5 p-1" style={{ gridTemplateColumns: `repeat(${options.length}, 1fr)` }}>
      {options.map((o) => (
        <button
          key={o.id}
          role="tab"
          type="button"
          aria-selected={value === o.id}
          onClick={() => onChange(o.id)}
          className={`rounded-full py-2 text-sm font-semibold transition-colors ${value === o.id ? "bg-brand-600 text-white shadow-sm" : "text-ink/70 hover:text-ink"}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export default function SignIn() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state ?? {}) as { from?: unknown; notice?: string };

  const [role, setRole] = useState<LoginRole>("buyer");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: Errors = { username: required(username, "Username"), password: required(password, "Password") };
    setErrors(next);
    if (hasErrors(next)) return;
    setBusy(true);
    setApiError(null);
    try {
      const resolved = await login(role, username.trim(), password);
      const redirect =
        getRedirectTarget(state.from) ??
        getRedirectTarget(new URLSearchParams(location.search).get("redirect"));
      navigate(redirect ?? (resolved === "buyer" ? "/shop" : homeFor(resolved)), { replace: true });
    } catch (err) {
      setApiError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card p-6 sm:p-8">
      <h1 className="text-2xl font-extrabold tracking-tight">Welcome back</h1>
      <p className="mt-1 text-sm text-ink/60">Sign in to continue your shopping journey.</p>

      <div className="mt-6 space-y-4">
        <RoleTabs value={role} onChange={setRole} options={roles} />
        <InlineSuccess message={state.notice} />
        <form onSubmit={submit} className="space-y-4" noValidate>
          <Input label="Username" icon="user" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} error={errors.username} placeholder="janedoe" />
          <Input label="Password" icon="lock" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} placeholder="Enter your password" />
          <div className="text-right text-sm">
            <Link to="/forgot-password" className="font-semibold text-brand-700 hover:underline">Forgot password?</Link>
          </div>
          <InlineError message={apiError} />
          <Button type="submit" size="lg" className="w-full" loading={busy}>Sign in</Button>
        </form>
      </div>
      <p className="mt-6 text-center text-sm text-ink/60">
        New to Cartord? <Link to="/signup" className="font-semibold text-brand-700 hover:underline">Create an account</Link>
      </p>
    </div>
  );
}
