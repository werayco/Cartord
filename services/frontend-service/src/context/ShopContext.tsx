import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import type { Product } from "../api/types";
import { usePersisted } from "../hooks/usePersisted";
import { uid } from "../lib/uid";
import { useAuth } from "./AuthContext";

/*
 * The backend has no cart, wishlist, recently-viewed or order-history endpoints (see README gaps).
 * Until it does, these live in the browser, scoped per signed-in username. They are UI conveniences,
 * not a source of truth: prices and stock are always re-validated by the order service.
 */

export interface CartLine {
  sku: string;
  name: string;
  unit_price: number;
  max: number;
  quantity: number;
  /** Idempotency key for this line. Regenerated when the quantity changes. */
  key: string;
}

export interface LocalOrder {
  id: string;
  sku: string;
  name: string;
  quantity: number;
  total: number;
  placedAt: string;
}

interface ShopValue {
  cart: CartLine[];
  cartCount: number;
  cartTotal: number;
  addToCart: (p: Product, qty?: number) => void;
  setQty: (sku: string, qty: number) => void;
  removeLine: (sku: string) => void;
  completeLine: (sku: string, order: LocalOrder) => void;
  wishlist: Product[];
  toggleWish: (p: Product) => void;
  isWished: (sku: string) => boolean;
  recent: Product[];
  pushRecent: (p: Product) => void;
  orders: LocalOrder[];
}

const Ctx = createContext<ShopValue | null>(null);

export function ShopProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const scope = user?.username ? `cartord.${user.username}` : null;
  const [cart, setCart] = usePersisted<CartLine[]>(scope && `${scope}.cart`, []);
  const [wishlist, setWishlist] = usePersisted<Product[]>(scope && `${scope}.wishlist`, []);
  const [recent, setRecent] = usePersisted<Product[]>(scope && `${scope}.recent`, []);
  const [orders, setOrders] = usePersisted<LocalOrder[]>(scope && `${scope}.orders`, []);

  const addToCart = useCallback(
    (p: Product, qty = 1) =>
      setCart((lines) => {
        const max = Math.max(0, p.available_quantity);
        const existing = lines.find((l) => l.sku === p.sku);
        if (existing) {
          return lines.map((l) =>
            l.sku === p.sku
              ? { ...l, max, quantity: Math.min(max || l.quantity + qty, l.quantity + qty), key: uid() }
              : l,
          );
        }
        return [
          ...lines,
          { sku: p.sku, name: p.name, unit_price: p.unit_price, max, quantity: Math.min(qty, max || qty), key: uid() },
        ];
      }),
    [setCart],
  );

  const setQty = useCallback(
    (sku: string, qty: number) =>
      setCart((lines) =>
        lines.map((l) => (l.sku === sku ? { ...l, quantity: Math.max(1, Math.min(qty, l.max || qty)), key: uid() } : l)),
      ),
    [setCart],
  );

  const removeLine = useCallback((sku: string) => setCart((l) => l.filter((x) => x.sku !== sku)), [setCart]);

  const completeLine = useCallback(
    (sku: string, order: LocalOrder) => {
      setCart((l) => l.filter((x) => x.sku !== sku));
      setOrders((o) => [order, ...o].slice(0, 100));
    },
    [setCart, setOrders],
  );

  const toggleWish = useCallback(
    (p: Product) =>
      setWishlist((w) => (w.some((x) => x.sku === p.sku) ? w.filter((x) => x.sku !== p.sku) : [p, ...w])),
    [setWishlist],
  );

  const pushRecent = useCallback(
    (p: Product) => setRecent((r) => [p, ...r.filter((x) => x.sku !== p.sku)].slice(0, 12)),
    [setRecent],
  );

  const value = useMemo<ShopValue>(
    () => ({
      cart,
      cartCount: cart.reduce((n, l) => n + l.quantity, 0),
      cartTotal: cart.reduce((n, l) => n + l.quantity * l.unit_price, 0),
      addToCart,
      setQty,
      removeLine,
      completeLine,
      wishlist,
      toggleWish,
      isWished: (sku) => wishlist.some((x) => x.sku === sku),
      recent,
      pushRecent,
      orders,
    }),
    [cart, wishlist, recent, orders, addToCart, setQty, removeLine, completeLine, toggleWish, pushRecent],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useShop(): ShopValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useShop must be used inside <ShopProvider>");
  return v;
}
