import { authApi } from "../../api/auth";
import { inventoryApi } from "../../api/inventory";
import { ordersApi } from "../../api/orders";
import { useAsync } from "../../hooks/useAsync";
import { DataBlock } from "../../components/DataBlock";
import { PageHeader } from "../../components/ui/StatCard";
import { GapNotice } from "../../components/ui/feedback";

export default function AdminOverview() {
  const users = useAsync(() => authApi.adminUserCount(), []);
  const orders = useAsync(() => ordersApi.adminStatistics("all"), []);
  const stock = useAsync(() => inventoryApi.adminSummary(), []);

  return (
    <>
      <PageHeader title="Platform overview" subtitle="Live figures from the Cartord services." />
      <div className="space-y-10">
        <DataBlock title="Users" data={users.data} loading={users.loading} error={users.error} onRetry={users.reload} />
        <DataBlock title="Orders" data={orders.data} loading={orders.loading} error={orders.error} onRetry={orders.reload} />
        <DataBlock title="Inventory" data={stock.data} loading={stock.loading} error={stock.error} onRetry={stock.reload} />
        <GapNotice title="activity feed and revenue charts">
          The backend returns counts and statistics only. A platform activity stream and time-series data for charts need new endpoints.
        </GapNotice>
      </div>
    </>
  );
}
