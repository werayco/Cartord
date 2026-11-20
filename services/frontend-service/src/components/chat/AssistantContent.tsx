import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatCard, ProductChoice } from "../../api/ai";
import { formatDate, humanize, money } from "../../lib/format";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-900",
  confirmed: "bg-brand-50 text-brand-800",
  shipped: "bg-sky-100 text-sky-900",
  delivered: "bg-lime-100 text-lime-900",
  cancelled: "bg-ink/10 text-ink/60",
  failed: "bg-red-100 text-red-800",
};

const markdownComponents: Components = {
  a: ({ href, children }) => {
    const safe = typeof href === "string" && /^(https?:\/\/|\/)/.test(href) ? href : undefined;
    if (!safe) return <span>{children}</span>;
    const external = safe.startsWith("http");
    return (
      <a
        href={safe}
        className="font-semibold text-brand-700 underline"
        {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
      >
        {children}
      </a>
    );
  },
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full border-collapse text-left">{children}</table>
    </div>
  ),
  th: ({ children }) => <th className="border-b border-ink/15 px-2 py-1.5 font-semibold">{children}</th>,
  td: ({ children }) => <td className="border-b border-ink/10 px-2 py-1.5 align-top">{children}</td>,
  code: ({ children }) => <code className="rounded bg-ink/5 px-1 py-0.5 text-[0.85em]">{children}</code>,
};

export function AssistantMarkdown({ text }: { text: string }) {
  return (
    <div className="rounded-2xl rounded-bl-sm bg-white px-4 py-2.5 text-sm shadow-card">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {text}
      </ReactMarkdown>
    </div>
  );
}

function ProductChoices({ items }: { items: ProductChoice[] }) {
  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-card">
      {items.map((item) => (
        <div key={item.number} className="flex gap-3 border-b border-ink/10 px-4 py-3 last:border-b-0">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-800">
            {item.number}
          </span>
          {item.imageUrl ? (
            <img
              src={item.imageUrl}
              alt=""
              className="h-14 w-14 shrink-0 rounded-lg object-cover bg-brand-50"
            />
          ) : (
            <div className="h-14 w-14 shrink-0 rounded-lg bg-brand-50" />
          )}
          <div className="min-w-0">
            <p className="font-semibold">{item.name}</p>
            <p className="text-sm text-ink/70">{money(item.price)}</p>
            {item.description && <p className="mt-1 line-clamp-2 text-sm text-ink/60">{item.description}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

function YesNo({
  card,
  onChoose,
}: {
  card: Extract<ChatCard, { kind: "yes_no" }>;
  onChoose?: (text: string) => void;
}) {
  return (
    <div className="flex gap-2">
      <button
        type="button"
        disabled={!onChoose}
        onClick={() => onChoose?.(card.yes)}
        className="rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-default disabled:opacity-60"
      >
        {card.yes}
      </button>
      <button
        type="button"
        disabled={!onChoose}
        onClick={() => onChoose?.(card.no)}
        className="rounded-full border border-ink/15 bg-white px-4 py-2 text-sm font-semibold text-ink hover:border-ink/30 disabled:cursor-default disabled:opacity-60"
      >
        {card.no}
      </button>
    </div>
  );
}

function ShippingAddress({ card }: { card: Extract<ChatCard, { kind: "shipping_address" }> }) {
  return (
    <div className="rounded-2xl bg-white px-4 py-3 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink/45">Shipping address</p>
      <p className="mt-1 font-semibold">{card.shippingAddress}</p>
    </div>
  );
}

function OrderSummary({ card }: { card: Extract<ChatCard, { kind: "order_summary" }> }) {
  return (
    <div className="rounded-2xl bg-white px-4 py-3 shadow-card">
      <div className="flex gap-3">
        {card.imageUrl ? (
          <img
            src={card.imageUrl}
            alt=""
            className="h-16 w-16 shrink-0 rounded-lg object-cover bg-brand-50"
          />
        ) : null}
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-ink/45">Order</p>
          <p className="mt-1 font-bold">{card.name}</p>
          <p className="text-sm text-ink/70">
            {card.quantity} × {money(card.unitPrice)}
          </p>
          <p className="mt-2 text-sm font-semibold">Total {money(card.total)}</p>
          {card.sku && <p className="mt-1 text-xs text-ink/45">{card.sku}</p>}
        </div>
      </div>
    </div>
  );
}

function OrderHistory({ card }: { card: Extract<ChatCard, { kind: "order_history" }> }) {
  return (
    <div className="overflow-hidden rounded-2xl bg-white text-sm shadow-card">
      <div className="grid grid-cols-3 gap-2 border-b border-ink/10 px-4 py-3">
        <div>
          <p className="text-xs text-ink/45">Orders</p>
          <p className="font-bold">{card.totalOrders}</p>
        </div>
        <div>
          <p className="text-xs text-ink/45">Delivered</p>
          <p className="font-bold">{card.deliveredOrders}</p>
        </div>
        <div>
          <p className="text-xs text-ink/45">Spent</p>
          <p className="font-bold">{money(card.totalSpend)}</p>
        </div>
      </div>
      {card.orders.length === 0 ? (
        <p className="px-4 py-3 text-ink/60">No orders yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr>
                <th className="border-b border-ink/15 px-3 py-2 font-semibold">Product</th>
                <th className="border-b border-ink/15 px-3 py-2 font-semibold">Qty</th>
                <th className="border-b border-ink/15 px-3 py-2 font-semibold">Total</th>
                <th className="border-b border-ink/15 px-3 py-2 font-semibold">Status</th>
                <th className="border-b border-ink/15 px-3 py-2 font-semibold">Date</th>
              </tr>
            </thead>
            <tbody>
              {card.orders.map((order, index) => (
                <tr key={`${order.sku}-${order.createdAt}-${index}`}>
                  <td className="border-b border-ink/10 px-3 py-2">{order.sku}</td>
                  <td className="border-b border-ink/10 px-3 py-2">{order.quantity}</td>
                  <td className="border-b border-ink/10 px-3 py-2">{money(order.quantity * order.unitPrice)}</td>
                  <td className="border-b border-ink/10 px-3 py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-bold capitalize ${STATUS_STYLE[order.status] ?? "bg-ink/10 text-ink/70"}`}>
                      {humanize(order.status || "unknown")}
                    </span>
                  </td>
                  <td className="border-b border-ink/10 px-3 py-2">{order.createdAt ? formatDate(order.createdAt) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function AssistantCards({ cards, onChoose }: { cards: ChatCard[]; onChoose?: (text: string) => void }) {
  return (
    <div className="space-y-3">
      {cards.map((card, index) => {
        if (card.kind === "product_choices") return <ProductChoices key={index} items={card.items} />;
        if (card.kind === "order_history") return <OrderHistory key={index} card={card} />;
        if (card.kind === "yes_no") return <YesNo key={index} card={card} onChoose={onChoose} />;
        if (card.kind === "shipping_address") return <ShippingAddress key={index} card={card} />;
        return <OrderSummary key={index} card={card} />;
      })}
    </div>
  );
}
