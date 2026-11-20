import { useEffect, useState, type FormEvent } from "react";
import { authApi } from "../../api/auth";
import { errorMessage } from "../../api/http";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { PageHeader } from "../../components/ui/StatCard";
import { GapNotice, InlineError, InlineSuccess } from "../../components/ui/feedback";
import { ChangePasswordCard } from "../shared/AccountSecurity";
import { email as isEmail, hasErrors, required, type Errors } from "../../lib/validate";
import { initials } from "../../lib/format";

export default function BuyerProfile() {
  const { user, reloadUser } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", shipping_address: "" });
  const [errors, setErrors] = useState<Errors>({});
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) setForm({ name: user.name, email: user.email, shipping_address: user.shipping_address ?? "" });
  }, [user]);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: Errors = { name: required(form.name, "Full name"), email: required(form.email, "Email") ?? isEmail(form.email), shipping_address: required(form.shipping_address, "Shipping address") };
    setErrors(next);
    if (hasErrors(next) || !user) return;
    const patch: Record<string, string> = {};
    if (form.name !== user.name) patch.name = form.name.trim();
    if (form.email !== user.email) patch.email = form.email.trim();
    if (form.shipping_address !== (user.shipping_address ?? "")) patch.shipping_address = form.shipping_address.trim();
    if (Object.keys(patch).length === 0) return setMsg({ ok: "Nothing to update." });
    setBusy(true);
    setMsg({});
    try {
      await authApi.updateBuyer(patch);
      await reloadUser();
      setMsg({ ok: "Profile updated." });
    } catch (err) {
      setMsg({ err: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader title="My profile" subtitle="Manage your account information." />
      <div className="grid gap-6 xl:grid-cols-2">
        <form onSubmit={submit} className="card space-y-4 p-6" noValidate>
          <div className="flex items-center gap-4">
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-600 text-xl font-bold text-white">{initials(user?.name || "?")}</span>
            <div>
              <p className="font-bold">{user?.name}</p>
              <p className="text-sm text-ink/60">@{user?.username}</p>
            </div>
          </div>
          <Input label="Full name" value={form.name} onChange={set("name")} error={errors.name} />
          <Input label="Email address" type="email" value={form.email} onChange={set("email")} error={errors.email} />
          <Input label="Username" value={user?.username ?? ""} disabled hint="Your username is your sign-in name and can't be changed here." readOnly />
          <Input label="Shipping address" value={form.shipping_address} onChange={set("shipping_address")} error={errors.shipping_address} />
          <InlineError message={msg.err} />
          <InlineSuccess message={msg.ok} />
          <Button type="submit" loading={busy}>Save changes</Button>
        </form>
        <div className="space-y-6">
          <ChangePasswordCard />
          <GapNotice title="profile picture and phone number">The auth service stores name, email, username and shipping address only. Profile pictures and phone numbers need new fields.</GapNotice>
        </div>
      </div>
    </>
  );
}
