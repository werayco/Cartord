import { Link } from "react-router-dom";
import { useShop } from "../../context/ShopContext";
import { ProductCard } from "../../components/ProductCard";
import { PageHeader } from "../../components/ui/StatCard";
import { EmptyState, GapNotice } from "../../components/ui/feedback";

export default function Wishlist() {
  const { wishlist } = useShop();
  return (
    <>
      <PageHeader title="Wishlist" subtitle="Products you've saved." />
      <div className="mb-6">
        <GapNotice title="wishlist storage">There is no wishlist endpoint, so saved items live in this browser only. Prices and stock shown may be out of date.</GapNotice>
      </div>
      {wishlist.length === 0 ? (
        <EmptyState icon="heart" title="Nothing saved yet" action={<Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">Browse products</Link>}>
          Tap the heart on any product to keep it here.
        </EmptyState>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          {wishlist.map((p) => <ProductCard key={p.sku} product={p} />)}
        </div>
      )}
    </>
  );
}
