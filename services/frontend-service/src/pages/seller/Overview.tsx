import { Link } from "react-router-dom";
import { inventoryApi } from "../../api/inventory";
import { paymentsApi } from "../../api/payments";
import { useAuth } from "../../context/AuthContext";
import { useAsync } from "../../hooks/useAsync";
import { LinkButton } from "../../components/ui/Button";
import { PageHeader, StatCard } from "../../components/ui/StatCard";
import { ErrorState, GapNotice } from "../../components/ui/feedback";
import { StockBadge } from "../../components/ProductCard";
import { money } from "../../lib/format";

export default function SellerOverview() {
  const { user } = useAuth();
  const products = useAsync((s) => inventoryApi.list(s), []);
  const wallet = useAsync(() => paymentsApi.wallet("seller"), []);

  const list = products.data ?? [];
  const units = list.reduce((n, p) => n + p.available_quantity, 0);
  const low = list.filter((p) => p.available_quantity > 0 && p.available_quantity <= 5).length;
  const out = list.filter((p) => p.available_quantity <= 0).length;

  return (
    <>
      <PageHeader
        title={`Hello, ${user?.name?.split(" ")[0] || user?.username || "there"}`}
        subtitle="A snapshot of your store."
        actions={<LinkButton to="/seller/products/new" size="sm">Add product</LinkButton>}
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total products" icon="package" loading={products.loading} value={list.length} />
        <StatCard label="Units in stock" icon="store" loading={products.loading} value={units.toLocaleString()} />
        <StatCard label="Low or out of stock" icon="alert" loading={products.loading} value={low + out} note={`${low} low · ${out} out`} />
        <StatCard label="Wallet balance" icon="wallet" loading={wallet.loading} value={wallet.error ? "—" : money(wallet.data?.balance)} />
      </div>

      <section className="mt-10">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">Your products</h2>
          <Link to="/seller/products" className="text-sm font-semibold text-brand-700 hover:underline">Manage all</Link>
        </div>
        {products.error ? (
          <ErrorState message={products.error} onRetry={products.reload} />
        ) : (
          <div className="card divide-y divide-ink/5">
            {list.slice(0, 5).map((p) => (
              <div key={p.sku} className="flex items-center justify-between gap-4 p-4">
                <div className="min-w-0">
                  <p className="truncate font-semibold">{p.name}</p>
                  <p className="text-xs text-ink/50">SKU {p.sku}</p>
                </div>
                <StockBadge qty={p.available_quantity} />
                <p className="w-24 text-right font-bold">{money(p.unit_price)}</p>
              </div>
            ))}
            {!products.loading && list.length === 0 && <p className="p-6 text-sm text-ink/60">No products yet. Add your first one to start selling.</p>}
          </div>
        )}
      </section>

      <div className="mt-8">
        <GapNotice title="orders, revenue and sales analytics">
          There is no endpoint that lists a seller's orders or reports revenue by period, so those tiles aren't shown. The wallet balance above is the only sales figure the backend exposes.
        </GapNotice>
      </div>
    </>
  );
}
