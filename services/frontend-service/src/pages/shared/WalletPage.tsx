import { paymentsApi } from "../../api/payments";
import { useAuth } from "../../context/AuthContext";
import { useAsync } from "../../hooks/useAsync";
import { PageHeader, StatCard } from "../../components/ui/StatCard";
import { ErrorState, GapNotice } from "../../components/ui/feedback";
import { humanize, money } from "../../lib/format";

export default function WalletPage() {
  const { role } = useAuth();
  const { data, loading, error, reload } = useAsync(() => paymentsApi.wallet(role ?? "buyer"), [role]);

  return (
    <>
      <PageHeader title="Wallet" subtitle={role === "seller" ? "Earnings from your sales." : "Your Cartord balance."} />
      {error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Balance" icon="wallet" loading={loading} value={money(data?.balance)} />
          {data &&
            Object.entries(data.raw)
              .filter(([k, v]) => typeof v === "number" && !/^(balance|available_balance|amount)$/.test(k) && !/id$/i.test(k))
              .slice(0, 3)
              .map(([k, v]) => <StatCard key={k} label={humanize(k)} value={String(v)} />)}
        </div>
      )}
      <div className="mt-6">
        <GapNotice title="wallet transactions and top-up">
          The payment service only exposes <code>GET /wallets/buyer</code> and <code>GET /wallets/seller</code>. Transaction history,
          funding and payouts need new endpoints.
        </GapNotice>
      </div>
    </>
  );
}
