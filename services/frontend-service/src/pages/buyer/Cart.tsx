import { useState } from "react";
import { Link } from "react-router-dom";
import { ordersApi } from "../../api/orders";
import { errorMessage } from "../../api/http";
import { useShop } from "../../context/ShopContext";
import { Button } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/StatCard";
import { EmptyState, InlineSuccess } from "../../components/ui/feedback";
import { money } from "../../lib/format";

export default function Cart() {
  const { cart, cartTotal, setQty, removeLine, completeLine } = useShop();
  const [placing, setPlacing] = useState(false);
  const [lineErrors, setLineErrors] = useState<Record<string, string>>({});
  const [done, setDone] = useState<number>(0);

  // The order API accepts a list; each cart line is submitted as a one-item order.
  // The line's idempotency key is reused on retry, so a double click or network retry can't duplicate it.
  const checkout = async () => {
    setPlacing(true);
    setDone(0);
    const errors: Record<string, string> = {};
    let placed = 0;
    for (const line of [...cart]) {
      try {
        const [result] = await ordersApi.place(line.key, line.sku, line.quantity);
        if (!result) throw new Error("The order service returned no order result.");
        completeLine(line.sku, {
          id: result.order_id,
          sku: line.sku,
          name: line.name,
          quantity: result.quantity,
          total: result.quantity * result.unit_price,
          placedAt: new Date().toISOString(),
        });
        placed += 1;
      } catch (e) {
        errors[line.sku] = errorMessage(e);
      }
    }
    setLineErrors(errors);
    setDone(placed);
    setPlacing(false);
  };

  if (cart.length === 0) {
    return (
      <>
        <PageHeader title="Shopping cart" />
        {done > 0 && <div className="mb-4"><InlineSuccess message={`${done} order${done === 1 ? "" : "s"} placed. Track them under My orders.`} /></div>}
        <EmptyState icon="cart" title="Your cart is empty" action={<Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">Browse products</Link>}>
          Add something you like and it will show up here.
        </EmptyState>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Shopping cart" subtitle={`${cart.length} item${cart.length === 1 ? "" : "s"}`} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <ul className="space-y-3">
          {cart.map((l) => (
            <li key={l.sku} className="card p-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="min-w-0 flex-1">
                  <Link to={`/product/${encodeURIComponent(l.sku)}`} className="font-bold hover:underline">{l.name}</Link>
                  <p className="text-sm text-ink/50">{money(l.unit_price)} each</p>
                </div>
                <div className="flex items-center rounded-full border border-ink/15">
                  <button className="p-2 disabled:opacity-40" disabled={placing || l.quantity <= 1} onClick={() => setQty(l.sku, l.quantity - 1)} aria-label={`Decrease ${l.name}`}><Icon name="minus" size={14} /></button>
                  <span className="w-8 text-center text-sm font-bold">{l.quantity}</span>
                  <button className="p-2 disabled:opacity-40" disabled={placing || (l.max > 0 && l.quantity >= l.max)} onClick={() => setQty(l.sku, l.quantity + 1)} aria-label={`Increase ${l.name}`}><Icon name="plus" size={14} /></button>
                </div>
                <p className="w-24 text-right font-extrabold">{money(l.quantity * l.unit_price)}</p>
                <button className="rounded-full p-2 text-ink/50 hover:bg-red-50 hover:text-red-600" disabled={placing} onClick={() => removeLine(l.sku)} aria-label={`Remove ${l.name}`}><Icon name="trash" size={16} /></button>
              </div>
              {lineErrors[l.sku] && <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{lineErrors[l.sku]}</p>}
            </li>
          ))}
        </ul>

        <aside className="card h-fit space-y-4 p-5">
          <h2 className="text-lg font-bold">Order summary</h2>
          <div className="flex items-center justify-between text-sm"><span className="text-ink/60">Subtotal</span><span className="font-semibold">{money(cartTotal)}</span></div>
          <div className="flex items-center justify-between border-t border-ink/5 pt-4"><span className="font-bold">Total</span><span className="text-xl font-extrabold">{money(cartTotal)}</span></div>
          <Button size="lg" className="w-full" loading={placing} onClick={checkout}>Place order</Button>
          <p className="text-xs text-ink/55">Each item is placed as its own order and paid from your wallet. Stock and price are confirmed by the order service.</p>
          {done > 0 && <InlineSuccess message={`${done} order${done === 1 ? "" : "s"} placed.`} />}
        </aside>
      </div>
    </>
  );
}
