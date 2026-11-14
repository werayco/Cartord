import { useState } from "react";
import { Link } from "react-router-dom";
import { inventoryApi } from "../../api/inventory";
import { errorMessage } from "../../api/http";
import type { Product } from "../../api/types";
import { useAsync } from "../../hooks/useAsync";
import { LinkButton } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { ConfirmModal } from "../../components/ui/Modal";
import { PageHeader } from "../../components/ui/StatCard";
import { EmptyState, ErrorState, InlineError, Skeleton } from "../../components/ui/feedback";
import { StockBadge } from "../../components/ProductCard";
import { money } from "../../lib/format";

export default function SellerProducts() {
  const { data, loading, error, reload } = useAsync((s) => inventoryApi.list(s), []);
  const [toDelete, setToDelete] = useState<Product | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const confirmDelete = async () => {
    if (!toDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await inventoryApi.remove(toDelete);
      setToDelete(null);
      reload();
    } catch (e) {
      setDeleteError(errorMessage(e));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <PageHeader title="Products" subtitle="Create, edit and remove your listings." actions={<LinkButton to="/seller/products/new" size="sm"><Icon name="plus" size={14} /> Add product</LinkButton>} />
      <InlineError message={deleteError && !toDelete ? deleteError : null} />
      {error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : loading ? (
        <div className="space-y-3">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-14" />)}</div>
      ) : (data ?? []).length === 0 ? (
        <EmptyState icon="package" title="No products yet" action={<LinkButton to="/seller/products/new" size="sm">Add your first product</LinkButton>}>
          Listings you create show up here and in the marketplace search.
        </EmptyState>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr><th className="table-th">Product</th><th className="table-th">SKU</th><th className="table-th">Price</th><th className="table-th">Stock</th><th className="table-th"><span className="sr-only">Actions</span></th></tr>
            </thead>
            <tbody className="divide-y divide-ink/5">
              {data!.map((p) => (
                <tr key={p.sku}>
                  <td className="table-td"><p className="font-semibold">{p.name}</p><p className="line-clamp-1 max-w-xs text-xs text-ink/50">{p.description}</p></td>
                  <td className="table-td text-ink/60">{p.sku}</td>
                  <td className="table-td font-semibold">{money(p.unit_price)}</td>
                  <td className="table-td"><div className="flex items-center gap-2">{p.available_quantity}<StockBadge qty={p.available_quantity} /></div></td>
                  <td className="table-td">
                    <div className="flex justify-end gap-1">
                      <Link to={`/seller/products/${encodeURIComponent(p.sku)}/edit`} className="rounded-full p-2 hover:bg-ink/5" aria-label={`Edit ${p.name}`}><Icon name="edit" size={16} /></Link>
                      <button onClick={() => { setDeleteError(null); setToDelete(p); }} className="rounded-full p-2 text-ink/60 hover:bg-red-50 hover:text-red-600" aria-label={`Delete ${p.name}`}><Icon name="trash" size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmModal open={!!toDelete} title="Delete this product?" confirmLabel="Delete product" danger loading={deleting} onConfirm={confirmDelete} onClose={() => setToDelete(null)}>
        <p><strong>{toDelete?.name}</strong> ({toDelete?.sku}) will be removed from the catalogue. This can't be undone.</p>
        <div className="mt-3"><InlineError message={deleteError} /></div>
      </ConfirmModal>
    </>
  );
}
