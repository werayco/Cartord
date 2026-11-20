import { useState, type FormEvent } from "react";
import { authApi } from "../../api/auth";
import { errorMessage } from "../../api/http";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { InlineError, InlineSuccess } from "../../components/ui/feedback";
import { hasErrors, minLength, required, type Errors } from "../../lib/validate";

export function ChangePasswordCard() {
  const { role } = useAuth();
  const [oldPw, setOld] = useState("");
  const [newPw, setNew] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const next: Errors = {
      old: required(oldPw, "Current password"),
      new: required(newPw, "New password") ?? minLength(newPw, 8, "New password"),
      confirm: confirm === newPw ? undefined : "Passwords don't match",
    };
    setErrors(next);
    if (hasErrors(next) || !role) return;
    setBusy(true);
    setMsg({});
    try {
      await authApi.changePassword(role, oldPw, newPw);
      setMsg({ ok: "Password updated." });
      setOld("");
      setNew("");
      setConfirm("");
    } catch (err) {
      setMsg({ err: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="card space-y-4 p-6" noValidate>
      <h2 className="text-lg font-bold">Password</h2>
      <Input label="Current password" type="password" autoComplete="current-password" value={oldPw} onChange={(e) => setOld(e.target.value)} error={errors.old} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="New password" type="password" autoComplete="new-password" value={newPw} onChange={(e) => setNew(e.target.value)} error={errors.new} />
        <Input label="Confirm new password" type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} error={errors.confirm} />
      </div>
      <InlineError message={msg.err} />
      <InlineSuccess message={msg.ok} />
      <Button type="submit" loading={busy}>Update password</Button>
    </form>
  );
}
