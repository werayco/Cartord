import { useState } from "react";
import { inventoryApi } from "../../api/inventory";
import { errorMessage } from "../../api/http";
import type { Product } from "../../api/types";
import { useAsync } from "../../hooks/useAsync";
import { Button } from "../../components/ui/Button";
import { PageHeader } from "../../components/ui/StatCard";
import { EmptyState, ErrorState, InlineError, Skeleton } from "../../components/ui/feedback";
import { StockBadge } from "../../components/ProductCard";

export default function Inventory() {
  const { data, loading, error, reload } = useAsync((s) => inventoryApi.list(s), []);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const save = async (p: Product) => {
    const raw = edits[p.sku];
    const qty = Math.floor(Number(raw));
    if (raw === undefined || !Number.isFinite(qty) || qty < 0) return;
    setSaving(p.sku);
    setSaveError(null);
    try {
      await inventoryApi.update({ ...p, available_quantity: qty });
      setEdits((e) => {
        const { [p.sku]: _drop, ...rest } = e;
        return rest;
      });
      reload();
    } catch (e) {
      setSaveError(`${p.name}: ${errorMessage(e)}`);
    } finally {
      setSaving(null);
    }
  };

  return (
    <>
      <PageHeader title="Inventory" subtitle="Adjust stock levels without opening each product." />
      <div className="mb-4"><InlineError message={saveError} /></div>
      {error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : loading ? (
        <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-14" />)}</div>
      ) : (data ?? []).length === 0 ? (
        <EmptyState icon="store" title="No stock to manage">Add a product first, then return here to adjust its quantity.</EmptyState>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full">
            <thead><tr><th className="table-th">Product</th><th className="table-th">Status</th><th className="table-th">Reserved</th><th className="table-th">Available</th><th className="table-th"><span className="sr-only">Save</span></th></tr></thead>
            <tbody className="divide-y divide-ink/5">
              {data!.map((p) => {
                const draft = edits[p.sku];
                const dirty = draft !== undefined && Number(draft) !== p.available_quantity;
                return (
                  <tr key={p.sku}>
                    <td className="table-td"><p className="font-semibold">{p.name}</p><p className="text-xs text-ink/50">SKU {p.sku}</p></td>
                    <td className="table-td"><StockBadge qty={p.available_quantity} /></td>
                    <td className="table-td text-ink/60">{p.reserved_quantity}</td>
                    <td className="table-td">
                      <input type="number" min={0} aria-label={`Available quantity for ${p.name}`} className="field w-28 py-1.5" value={draft ?? String(p.available_quantity)} onChange={(e) => setEdits((s) => ({ ...s, [p.sku]: e.target.value }))} />
                    </td>
                    <td className="table-td text-right"><Button size="sm" disabled={!dirty} loading={saving === p.sku} onClick={() => save(p)}>Save</Button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
