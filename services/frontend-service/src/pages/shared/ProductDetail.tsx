import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { searchApi } from "../../api/search";
import { useAuth } from "../../context/AuthContext";
import { useShop } from "../../context/ShopContext";
import { useAsync } from "../../hooks/useAsync";
import { ProductCard, ProductVisual, StockBadge } from "../../components/ProductCard";
import { Button } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { EmptyState, ErrorState, GapNotice, Skeleton } from "../../components/ui/feedback";
import { money } from "../../lib/format";

export default function ProductDetail() {
  const { sku = "" } = useParams();
  const { role } = useAuth();
  const { addToCart, toggleWish, isWished, pushRecent } = useShop();
  const [qty, setQty] = useState(1);
  const [added, setAdded] = useState(false);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);

  // No GET-by-id route exists, so the product is found in the full catalogue (see README gaps).
  const { data, loading, error, reload } = useAsync((s) => searchApi.all(s), []);
  const product = data?.find((p) => p.sku === sku);

  useEffect(() => {
    if (product) pushRecent(product);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [product?.sku]);

  useEffect(() => {
    setSelectedImageId(null);
  }, [product?.sku]);

  if (error) return <div className="mx-auto max-w-5xl px-4 py-10"><ErrorState message={error} onRetry={reload} /></div>;
  if (loading) return <div className="mx-auto grid max-w-5xl gap-8 px-4 py-10 md:grid-cols-2"><Skeleton className="h-80" /><Skeleton className="h-80" /></div>;
  if (!product) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-10">
        <EmptyState title="Product not found" action={<Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">Back to shop</Link>}>
          It may have been removed or sold out of the catalogue.
        </EmptyState>
      </div>
    );
  }

  const max = Math.max(1, product.available_quantity);
  const soldOut = product.available_quantity <= 0;
  const related = (data ?? []).filter((p) => p.sku !== product.sku).slice(0, 4);
  const selectedImage = product.images.find((image) => image.id === selectedImageId) ?? product.images[0];

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">← All products</Link>
      <div className="mt-4 grid gap-8 md:grid-cols-2">
        <div>
          {selectedImage ? (
            <img src={selectedImage.url} alt={selectedImage.alt_text || product.name} className="h-72 w-full rounded-xl object-cover md:h-96" />
          ) : (
            <ProductVisual product={product} className="h-72 text-8xl md:h-96" />
          )}
          {product.images.length > 1 && (
            <div className="mt-3 flex gap-2 overflow-x-auto">
              {product.images.map((image) => (
                <button
                  key={image.id}
                  type="button"
                  onClick={() => setSelectedImageId(image.id)}
                  aria-label={`View ${image.alt_text || product.name}`}
                  aria-pressed={selectedImage?.id === image.id}
                  className={`shrink-0 rounded-lg ring-offset-2 ${selectedImage?.id === image.id ? "ring-2 ring-brand-600" : "hover:ring-1 hover:ring-ink/30"}`}
                >
                  <img src={image.url} alt="" className="h-16 w-16 rounded-lg object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">{product.name}</h1>
          <p className="mt-1 text-sm text-ink/50">SKU {product.sku}</p>
          <p className="mt-4 text-3xl font-extrabold">{money(product.unit_price)}</p>
          <div className="mt-2"><StockBadge qty={product.available_quantity} /></div>
          <p className="mt-5 whitespace-pre-line text-ink/75">{product.description || "No description provided."}</p>

          {role === "buyer" ? (
            <div className="mt-6 space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center rounded-full border border-ink/15 bg-white">
                  <button className="p-2.5 disabled:opacity-40" onClick={() => setQty((q) => Math.max(1, q - 1))} disabled={qty <= 1} aria-label="Decrease quantity"><Icon name="minus" size={16} /></button>
                  <span className="w-8 text-center text-sm font-bold" aria-live="polite">{qty}</span>
                  <button className="p-2.5 disabled:opacity-40" onClick={() => setQty((q) => Math.min(max, q + 1))} disabled={qty >= max} aria-label="Increase quantity"><Icon name="plus" size={16} /></button>
                </div>
                <Button disabled={soldOut} onClick={() => { addToCart(product, qty); setAdded(true); }}>
                  <Icon name="cart" size={16} /> {soldOut ? "Unavailable" : "Add to cart"}
                </Button>
                <Button variant="outline" onClick={() => toggleWish(product)} aria-pressed={isWished(product.sku)}>
                  <Icon name="heart" size={16} className={isWished(product.sku) ? "fill-red-500 text-red-500" : ""} />
                  {isWished(product.sku) ? "Saved" : "Save"}
                </Button>
              </div>
              {added && (
                <p role="status" className="text-sm text-brand-700">
                  Added to your cart. <Link to="/buyer/cart" className="font-semibold underline">Go to cart</Link>
                </p>
              )}
            </div>
          ) : (
            <p className="mt-6 text-sm text-ink/60">Sign in with a buyer account to purchase.</p>
          )}
          <div className="mt-6">
            <GapNotice title="Categories and reviews">
              Product categories and customer reviews are not currently supported.
            </GapNotice>
          </div>
        </div>
      </div>

      {related.length > 0 && (
        <section className="mt-14">
          <h2 className="mb-4 text-xl font-extrabold">More from the catalogue</h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {related.map((p) => <ProductCard key={p.sku} product={p} compact />)}
          </div>
        </section>
      )}
    </div>
  );
}
