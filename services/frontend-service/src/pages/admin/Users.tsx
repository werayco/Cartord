import { useState } from "react";
import { authApi } from "../../api/auth";
import { useAsync } from "../../hooks/useAsync";
import { DataBlock } from "../../components/DataBlock";
import { PageHeader } from "../../components/ui/StatCard";
import { GapNotice } from "../../components/ui/feedback";
import { PeriodPicker } from "./PeriodPicker";

export default function AdminUsers() {
  const [period, setPeriod] = useState("all");
  const count = useAsync(() => authApi.adminUserCount(), []);
  const stats = useAsync(() => authApi.adminCustomerStats(period), [period]);

  return (
    <>
      <PageHeader title="Users" subtitle="Buyer and seller account statistics." />
      <div className="space-y-10">
        <DataBlock title="User count" data={count.data} loading={count.loading} error={count.error} onRetry={count.reload} />
        <DataBlock title="Customer statistics" data={stats.data} loading={stats.loading} error={stats.error} onRetry={stats.reload} extra={<PeriodPicker value={period} onApply={setPeriod} />} />
        <GapNotice title="user lists and account actions">
          The auth service has no admin endpoint to list, search, suspend or delete buyers and sellers. <code>GET /auth/seller/sellers</code> requires a seller token, so the admin console can't use it. Those routes are needed for full buyer and seller management.
        </GapNotice>
      </div>
    </>
  );
}
