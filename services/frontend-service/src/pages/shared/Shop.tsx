import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { searchApi } from "../../api/search";
import { useAsync } from "../../hooks/useAsync";
import { ProductCard } from "../../components/ProductCard";
import { Icon } from "../../components/ui/Icon";
import { Button } from "../../components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "../../components/ui/feedback";

type Sort = "relevance" | "price-asc" | "price-desc";

const PAGE_SIZE = 30;

export default function Shop() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const page = Math.max(1, Number(params.get("page")) || 1);
  const [draft, setDraft] = useState(query);
  const [sort, setSort] = useState<Sort>("relevance");
  const [inStockOnly, setInStockOnly] = useState(false);

  useEffect(() => setDraft(query), [query]);

  const setQueryParam = (next: string) => {
    setParams((current) => {
      const nextParams = new URLSearchParams(current);
      if (next) nextParams.set("q", next);
      else nextParams.delete("q");
      nextParams.delete("page");
      return nextParams;
    });
  };

  useEffect(() => {
    const next = draft.trim();
    if (next === query) return;
    const timer = window.setTimeout(() => setQueryParam(next), 300);
    return () => window.clearTimeout(timer);
  }, [draft, query]);

  const { data, loading, error, reload } = useAsync(
    (s) => (query ? searchApi.items(query, s) : searchApi.all(s)),
    [query],
  );

  const submit = (e: FormEvent) => {
    e.preventDefault();
    setQueryParam(draft.trim());
  };

  let items = data ?? [];
  if (inStockOnly) items = items.filter((p) => p.available_quantity > 0);
  if (sort === "price-asc") items = [...items].sort((a, b) => a.unit_price - b.unit_price);
  if (sort === "price-desc") items = [...items].sort((a, b) => b.unit_price - a.unit_price);

  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageItems = items.slice(start, start + PAGE_SIZE);

  const goToPage = (nextPage: number) => {
    setParams((current) => {
      const nextParams = new URLSearchParams(current);
      if (nextPage <= 1) nextParams.delete("page");
      else nextParams.set("page", String(nextPage));
      return nextParams;
    });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-extrabold tracking-tight">{query ? `Results for “${query}”` : "All products"}</h1>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <form onSubmit={submit} role="search" className="relative min-w-[16rem] flex-1">
          <Icon name="search" size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" />
          <input value={draft} onChange={(e) => setDraft(e.target.value)} aria-label="Search products" placeholder="Search products" className="field rounded-full pl-10" />
        </form>
        <label className="flex items-center gap-2 text-sm font-semibold">
          <input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)} className="h-4 w-4 accent-brand-600" />
          In stock only
        </label>
        <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label="Sort products" className="field w-auto rounded-full">
          <option value="relevance">Best match</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
        </select>
      </div>

      <div className="mt-8">
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 10 }, (_, i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon="search"
            title="Nothing matched"
            action={query ? <Button variant="outline" onClick={() => setQueryParam("")}>Clear search</Button> : undefined}
          >
            {query ? "Try a different word, or ask the AI assistant to help you find it." : "No products have been listed yet."}
          </EmptyState>
        ) : (
          <>
            <p className="mb-4 text-sm text-ink/60">
              Showing {start + 1}–{start + pageItems.length} of {items.length} product{items.length === 1 ? "" : "s"}
            </p>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {pageItems.map((p) => (
                <ProductCard key={p.sku} product={p} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <Button
                  variant="outline"
                  disabled={currentPage <= 1}
                  onClick={() => goToPage(currentPage - 1)}
                >
                  Previous
                </Button>
                <p className="text-sm font-semibold text-ink/70">
                  Page {currentPage} of {totalPages}
                </p>
                <Button
                  variant="outline"
                  disabled={currentPage >= totalPages}
                  onClick={() => goToPage(currentPage + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
