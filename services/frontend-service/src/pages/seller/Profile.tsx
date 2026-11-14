import { useAuth } from "../../context/AuthContext";
import { Input } from "../../components/ui/Input";
import { PageHeader } from "../../components/ui/StatCard";
import { GapNotice } from "../../components/ui/feedback";
import { ChangePasswordCard } from "../shared/AccountSecurity";
import { initials } from "../../lib/format";

export default function SellerProfile() {
  const { user } = useAuth();
  return (
    <>
      <PageHeader title="Store & profile" subtitle="Your seller account." />
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card space-y-4 p-6">
          <div className="flex items-center gap-4">
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-600 text-xl font-bold text-white">{initials(user?.name || "?")}</span>
            <div><p className="font-bold">{user?.name}</p><p className="text-sm text-ink/60">@{user?.username}</p></div>
          </div>
          <Input label="Full name" value={user?.name ?? ""} readOnly disabled />
          <Input label="Email address" value={user?.email ?? ""} readOnly disabled />
          <Input label="Username" value={user?.username ?? ""} readOnly disabled />
        </div>
        <div className="space-y-6">
          <ChangePasswordCard />
          <GapNotice title="editing seller details and store profile">
            The auth service has no seller update route (buyers have <code>PATCH /buyer/update</code>), so these fields are read-only. Store name, description, logo, business contact and address need a store-profile model and endpoints.
          </GapNotice>
        </div>
      </div>
    </>
  );
}
