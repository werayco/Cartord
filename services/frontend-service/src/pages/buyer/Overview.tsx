import { Link } from "react-router-dom";
import { paymentsApi } from "../../api/payments";
import { searchApi } from "../../api/search";
import { useAuth } from "../../context/AuthContext";
import { useShop } from "../../context/ShopContext";
import { useAsync } from "../../hooks/useAsync";
import { ProductCard } from "../../components/ProductCard";
import { LinkButton } from "../../components/ui/Button";
import { PageHeader, StatCard } from "../../components/ui/StatCard";
import { ErrorState, Skeleton } from "../../components/ui/feedback";
import { formatDate, money } from "../../lib/format";

export default function BuyerOverview() {
  const { user } = useAuth();
  const { cartCount, wishlist, orders, recent } = useShop();
  const wallet = useAsync(() => paymentsApi.wallet("buyer"), []);
  const catalogue = useAsync((s) => searchApi.all(s), []);

  return (
    <>
      <PageHeader
        title={`Hello, ${user?.name?.split(" ")[0] || user?.username || "there"}`}
        subtitle="Here's what's happening with your account."
        actions={<LinkButton to="/chat" variant="outline" size="sm">Ask the AI assistant</LinkButton>}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Wallet balance" icon="wallet" loading={wallet.loading} value={wallet.error ? "—" : money(wallet.data?.balance)} />
        <StatCard label="Items in cart" icon="cart" value={cartCount} />
        <StatCard label="Wishlist" icon="heart" value={wishlist.length} />
        <StatCard label="Orders placed here" icon="package" value={orders.length} note="This device only" />
      </div>

      <section className="mt-10">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">Recent orders</h2>
          <Link to="/buyer/orders" className="text-sm font-semibold text-brand-700 hover:underline">View all</Link>
        </div>
        {orders.length === 0 ? (
          <div className="card p-6 text-sm text-ink/60">
            You haven't placed an order from this device yet. <Link className="font-semibold text-brand-700 underline" to="/shop">Browse products</Link>
          </div>
        ) : (
          <div className="card divide-y divide-ink/5">
            {orders.slice(0, 3).map((o) => (
              <div key={o.id} className="flex items-center justify-between gap-4 p-4">
                <div>
                  <p className="font-semibold">{o.name}</p>
                  <p className="text-xs text-ink/50">{o.quantity} × · {formatDate(o.placedAt)}</p>
                </div>
                <p className="font-bold">{money(o.total)}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <h2 className="mb-3 text-lg font-bold">From the catalogue</h2>
        {catalogue.error ? (
          <ErrorState message={catalogue.error} onRetry={catalogue.reload} />
        ) : catalogue.loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-64" />)}</div>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {(catalogue.data ?? []).slice(0, 4).map((p) => <ProductCard key={p.sku} product={p} />)}
          </div>
        )}
      </section>

      {recent.length > 0 && (
        <section className="mt-10">
          <h2 className="mb-3 text-lg font-bold">Recently viewed</h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {recent.slice(0, 4).map((p) => <ProductCard key={p.sku} product={p} compact />)}
          </div>
        </section>
      )}
    </>
  );
}
