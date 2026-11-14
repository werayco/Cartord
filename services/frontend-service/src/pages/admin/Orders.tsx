import { useState } from "react";
import { ordersApi } from "../../api/orders";
import { useAsync } from "../../hooks/useAsync";
import { DataBlock } from "../../components/DataBlock";
import { PageHeader } from "../../components/ui/StatCard";
import { GapNotice } from "../../components/ui/feedback";
import { PeriodPicker } from "./PeriodPicker";

export default function AdminOrders() {
  const [period, setPeriod] = useState("all");
  const stats = useAsync(() => ordersApi.adminStatistics(period), [period]);
  const failed = useAsync(() => ordersApi.adminFailedStatistics(period), [period]);

  return (
    <>
      <PageHeader title="Order monitoring" subtitle="Order outcomes for the selected period." actions={<PeriodPicker value={period} onApply={setPeriod} />} />
      <div className="space-y-10">
        <DataBlock title="Order statistics" data={stats.data} loading={stats.loading} error={stats.error} onRetry={stats.reload} />
        <DataBlock title="Failed orders" data={failed.data} loading={failed.loading} error={failed.error} onRetry={failed.reload} />
        <GapNotice title="individual order lookup">Only aggregate statistics exist. Listing and inspecting single orders needs a new admin endpoint.</GapNotice>
      </div>
    </>
  );
}
