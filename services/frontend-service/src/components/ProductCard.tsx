import { Link } from "react-router-dom";
import type { Product } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { useShop } from "../context/ShopContext";
import { money } from "../lib/format";
import { Button } from "./ui/Button";
import { Icon } from "./ui/Icon";

const hues = ["bg-brand-100 text-brand-700", "bg-lime-300/50 text-brand-800", "bg-emerald-100 text-emerald-800", "bg-teal-100 text-teal-800"];

export function ProductVisual({ product, className = "h-36" }: { product: Product; className?: string }) {
  const image = product.images?.[0];
  if (image) {
    return (
      <img
        src={image.url}
        alt={image.alt_text || product.name}
        className={`w-full rounded-xl object-cover ${className}`}
      />
    );
  }

  const hue = hues[(product.sku.charCodeAt(0) || 0) % hues.length];
  return (
    <div className={`flex items-center justify-center rounded-xl text-4xl font-extrabold ${hue} ${className}`} aria-hidden="true">
      {product.name.trim().charAt(0).toUpperCase() || "?"}
    </div>
  );
}

export function StockBadge({ qty }: { qty: number }) {
  if (qty <= 0) return <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700">Out of stock</span>;
  if (qty < 10) return <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800">Only {qty} left</span>;
  return <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">In stock</span>;
}

export function ProductCard({ product, compact = false }: { product: Product; compact?: boolean }) {
  const { role } = useAuth();
  const { addToCart, toggleWish, isWished } = useShop();
  const wished = isWished(product.sku);
  const soldOut = product.available_quantity <= 0;

  return (
    <article className="card flex flex-col p-3">
      <div className="relative">
        <Link to={`/product/${encodeURIComponent(product.sku)}`} aria-label={`View ${product.name}`}>
          <ProductVisual product={product} className={compact ? "h-24" : "h-36"} />
        </Link>
        {role === "buyer" && (
          <button
            onClick={() => toggleWish(product)}
            aria-pressed={wished}
            aria-label={wished ? "Remove from wishlist" : "Add to wishlist"}
            className="absolute right-2 top-2 rounded-full bg-white/90 p-1.5 shadow-sm hover:bg-white"
          >
            <Icon name="heart" size={16} className={wished ? "fill-red-500 text-red-500" : "text-ink/60"} />
          </button>
        )}
      </div>
      <div className="mt-3 flex flex-1 flex-col gap-1">
        <Link to={`/product/${encodeURIComponent(product.sku)}`} className="line-clamp-2 text-sm font-bold hover:underline">
          {product.name}
        </Link>
        <p className="text-xs text-ink/50">SKU {product.sku}</p>
        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="text-base font-extrabold">{money(product.unit_price)}</span>
          <StockBadge qty={product.available_quantity} />
        </div>
      </div>
      {role === "buyer" && !compact && (
        <Button variant="outline" size="sm" className="mt-3 w-full" disabled={soldOut} onClick={() => addToCart(product)}>
          <Icon name="cart" size={14} /> {soldOut ? "Unavailable" : "Add to cart"}
        </Button>
      )}
    </article>
  );
}
