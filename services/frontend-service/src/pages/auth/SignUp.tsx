import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { errorMessage } from "../../api/http";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { InlineError } from "../../components/ui/feedback";
import { RoleTabs } from "./SignIn";
import { email as isEmail, hasErrors, minLength, required, type Errors } from "../../lib/validate";

type Kind = "buyer" | "seller";

export default function SignUp() {
  const { registerBuyer, registerSeller } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [kind, setKind] = useState<Kind>(params.get("role") === "seller" ? "seller" : "buyer");
  const [form, setForm] = useState({ name: "", email: "", username: "", password: "", confirm: "", shipping_address: "" });
  const [errors, setErrors] = useState<Errors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: Errors = {
      name: required(form.name, "Full name"),
      email: required(form.email, "Email") ?? isEmail(form.email),
      username: required(form.username, "Username"),
      password: required(form.password, "Password") ?? minLength(form.password, 8, "Password"),
      confirm: form.confirm === form.password ? undefined : "Passwords don't match",
      shipping_address: kind === "buyer" ? required(form.shipping_address, "Shipping address") : undefined,
    };
    setErrors(next);
    if (hasErrors(next)) return;
    setBusy(true);
    setApiError(null);
    const base = { name: form.name.trim(), email: form.email.trim(), username: form.username.trim(), password: form.password };
    try {
      if (kind === "buyer") await registerBuyer({ ...base, shipping_address: form.shipping_address.trim() });
      else await registerSeller(base);
      navigate("/signin", { replace: true, state: { notice: "Account created. Sign in to continue." } });
    } catch (err) {
      setApiError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card p-6 sm:p-8">
      <h1 className="text-2xl font-extrabold tracking-tight">Create your account</h1>
      <p className="mt-1 text-sm text-ink/60">Join Cartord and start exploring.</p>
      <div className="mt-6 space-y-4">
        <RoleTabs
          value={kind}
          onChange={setKind}
          options={[
            { id: "buyer", label: "Buyer" },
            { id: "seller", label: "Seller" },
          ]}
        />
        <form onSubmit={submit} className="space-y-4" noValidate>
          <Input label="Full name" icon="user" autoComplete="name" value={form.name} onChange={set("name")} error={errors.name} />
          <Input label="Email address" icon="mail" type="email" autoComplete="email" value={form.email} onChange={set("email")} error={errors.email} placeholder="you@example.com" />
          <Input label="Username" autoComplete="username" value={form.username} onChange={set("username")} error={errors.username} hint="You'll use this to sign in." />
          {kind === "buyer" && (
            <Input label="Shipping address" autoComplete="street-address" value={form.shipping_address} onChange={set("shipping_address")} error={errors.shipping_address} />
          )}
          <Input label="Password" type="password" autoComplete="new-password" value={form.password} onChange={set("password")} error={errors.password} hint="At least 8 characters." />
          <Input label="Confirm password" type="password" autoComplete="new-password" value={form.confirm} onChange={set("confirm")} error={errors.confirm} />
          <InlineError message={apiError} />
          <Button type="submit" size="lg" className="w-full" loading={busy}>
            Create {kind} account
          </Button>
        </form>
      </div>
      <p className="mt-6 text-center text-sm text-ink/60">
        Already have an account? <Link to="/signin" className="font-semibold text-brand-700 hover:underline">Sign in</Link>
      </p>
    </div>
  );
}
