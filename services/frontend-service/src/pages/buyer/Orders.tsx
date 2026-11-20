import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ordersApi, type CustomerOrder } from "../../api/orders";
import { searchApi } from "../../api/search";
import { useShop } from "../../context/ShopContext";
import { useAsync } from "../../hooks/useAsync";
import { PageHeader, StatCard } from "../../components/ui/StatCard";
import { EmptyState, ErrorState, Skeleton } from "../../components/ui/feedback";
import { formatDate, humanize, money } from "../../lib/format";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-900",
  confirmed: "bg-brand-50 text-brand-800",
  shipped: "bg-sky-100 text-sky-900",
  delivered: "bg-lime-100 text-lime-900",
  cancelled: "bg-ink/10 text-ink/60",
  failed: "bg-red-100 text-red-800",
};

const CLOSED = new Set(["cancelled", "failed"]);

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold capitalize ${STATUS_STYLE[status] ?? "bg-ink/10 text-ink/70"}`}>
      {humanize(status)}
    </span>
  );
}

function OrderCard({ order, name }: { order: CustomerOrder; name: string }) {
  const total = order.quantity * order.unit_price;
  return (
    <li className="card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Link to={`/product/${encodeURIComponent(order.sku)}`} className="font-bold hover:underline">
              {name}
            </Link>
            <StatusBadge status={order.status} />
          </div>
          <p className="mt-1 text-sm text-ink/55">
            {order.quantity} × {money(order.unit_price)}
            {order.sku !== name ? ` · ${order.sku}` : ""}
            {order.created_at ? ` · ${formatDate(order.created_at)}` : ""}
          </p>
          <p className="mt-1 font-mono text-xs text-ink/40" title={order.id}>
            {order.id.slice(0, 8)}
          </p>
        </div>
        <p className="text-lg font-extrabold">{money(total)}</p>
      </div>
    </li>
  );
}

export default function BuyerOrders() {
  const { orders: placedHere } = useShop();
  const summary = useAsync((signal) => ordersApi.summary(signal), []);
  const catalogue = useAsync((signal) => searchApi.all(signal), []);

  const names = useMemo(() => {
    const map = new Map<string, string>();
    for (const order of placedHere) map.set(order.sku, order.name);
    for (const product of catalogue.data ?? []) map.set(product.sku, product.name);
    return map;
  }, [placedHere, catalogue.data]);

  const records = summary.data?.orders ?? [];
  const delivered = records.filter((order) => order.status === "delivered").length;
  const closed = records.filter((order) => CLOSED.has(order.status)).length;
  const active = records.length - delivered - closed;
  const spend = summary.data?.total_spend ?? records.filter((order) => order.status === "delivered").reduce((sum, order) => sum + order.quantity * order.unit_price, 0);
  const summaryError = summary.data?.error ? summary.data.message : null;

  return (
    <>
      <PageHeader title="My orders" subtitle="Orders placed with your account." />

      {summary.error || summaryError ? (
        <ErrorState message={summary.error || summaryError || "Couldn't load orders."} onRetry={summary.reload} />
      ) : summary.loading ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
          </div>
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : records.length === 0 ? (
        <EmptyState icon="package" title="No orders yet" action={<Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">Start shopping</Link>}>
          When you check out, each order will show up here with its status.
        </EmptyState>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Orders" icon="package" value={records.length} />
            <StatCard label="Active" icon="truck" value={active} note="Pending, confirmed, or shipped" />
            <StatCard label="Delivered" icon="check" value={delivered} />
            <StatCard label="Spent" icon="wallet" value={money(spend)} note="Delivered orders" />
          </div>
          <ul className="mt-6 space-y-3">
            {records.map((order) => (
              <OrderCard key={order.id} order={order} name={names.get(order.sku) ?? order.sku} />
            ))}
          </ul>
        </>
      )}
    </>
  );
}
