import { inventoryApi } from "../../api/inventory";
import type { Product } from "../../api/types";
import { useAsync } from "../../hooks/useAsync";
import { DataBlock } from "../../components/DataBlock";
import { PageHeader } from "../../components/ui/StatCard";
import { ErrorState, GapNotice, Skeleton } from "../../components/ui/feedback";
import { money } from "../../lib/format";

function StockTable({ title, rows, loading, error, retry }: { title: string; rows: Product[] | null; loading: boolean; error: string | null; retry: () => void }) {
  return (
    <section>
      <h2 className="mb-3 text-lg font-bold">{title}</h2>
      {error ? (
        <ErrorState message={error} onRetry={retry} />
      ) : loading ? (
        <Skeleton className="h-32" />
      ) : (rows ?? []).length === 0 ? (
        <p className="card p-5 text-sm text-ink/60">Nothing to flag here.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full">
            <thead><tr><th className="table-th">Product</th><th className="table-th">SKU</th><th className="table-th">Price</th><th className="table-th">Available</th><th className="table-th">Reserved</th></tr></thead>
            <tbody className="divide-y divide-ink/5">
              {rows!.map((p) => (
                <tr key={p.sku}><td className="table-td font-semibold">{p.name}</td><td className="table-td text-ink/60">{p.sku}</td><td className="table-td">{money(p.unit_price)}</td><td className="table-td">{p.available_quantity}</td><td className="table-td">{p.reserved_quantity}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function AdminProducts() {
  const summary = useAsync(() => inventoryApi.adminSummary(), []);
  const low = useAsync(() => inventoryApi.adminLowStock(), []);
  const out = useAsync(() => inventoryApi.adminOutOfStock(), []);

  return (
    <>
      <PageHeader title="Products & inventory" subtitle="Stock health across the marketplace." />
      <div className="space-y-10">
        <DataBlock title="Inventory summary" data={summary.data} loading={summary.loading} error={summary.error} onRetry={summary.reload} />
        <StockTable title="Low stock" rows={low.data} loading={low.loading} error={low.error} retry={low.reload} />
        <StockTable title="Out of stock" rows={out.data} loading={out.loading} error={out.error} retry={out.reload} />
        <GapNotice title="listing moderation and reports">
          There's no endpoint to hide, flag or remove another seller's product, or to read user-submitted reports.
        </GapNotice>
      </div>
    </>
  );
}
