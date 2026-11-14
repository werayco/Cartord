import { Link } from "react-router-dom";
import { useShop } from "../../context/ShopContext";
import { ordersApi } from "../../api/orders";
import { useAsync } from "../../hooks/useAsync";
import { PageHeader } from "../../components/ui/StatCard";
import { EmptyState, ErrorState, GapNotice, Skeleton } from "../../components/ui/feedback";
import { formatDate, money } from "../../lib/format";

export default function BuyerOrders() {
  const { orders } = useShop();
  const summary = useAsync((signal) => ordersApi.summary(signal), []);
  return (
    <>
      <PageHeader title="My orders" subtitle="Orders you've placed from this device." />
      {summary.error ? (
        <div className="mb-6">
          <ErrorState message={summary.error} onRetry={summary.reload} />
        </div>
      ) : summary.loading ? (
        <div className="mb-6"><Skeleton className="h-36" /></div>
      ) : summary.data ? (
        <section className="card mb-6 p-5">
          <h2 className="font-bold">Order summary</h2>
          <pre className="mt-3 whitespace-pre-wrap font-sans text-sm leading-6 text-ink/70">{summary.data.message}</pre>
        </section>
      ) : null}
      <div className="mb-6">
        <GapNotice title="order history and status tracking">
          The service provides a summary, but no endpoint for individual order records or live status. The table below is a local record of orders placed on this device.
        </GapNotice>
      </div>
      {orders.length === 0 ? (
        <EmptyState icon="package" title="No orders yet" action={<Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">Start shopping</Link>}>
          Orders you place will appear here.
        </EmptyState>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full">
            <thead><tr><th className="table-th">Item</th><th className="table-th">SKU</th><th className="table-th">Qty</th><th className="table-th">Total</th><th className="table-th">Placed</th></tr></thead>
            <tbody className="divide-y divide-ink/5">
              {orders.map((o) => (
                <tr key={o.id}>
                  <td className="table-td font-semibold">{o.name}</td>
                  <td className="table-td text-ink/60">{o.sku}</td>
                  <td className="table-td">{o.quantity}</td>
                  <td className="table-td font-semibold">{money(o.total)}</td>
                  <td className="table-td text-ink/60">{formatDate(o.placedAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
