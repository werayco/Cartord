import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { searchApi } from "../api/search";
import { useAuth } from "../context/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { ProductCard } from "../components/ProductCard";
import { LinkButton } from "../components/ui/Button";
import { Icon, type IconName } from "../components/ui/Icon";
import { ErrorState, Skeleton } from "../components/ui/feedback";

/* Category chips are search shortcuts. The inventory schema has no category field yet. */
const categories: Array<{ label: string; query: string; icon: IconName }> = [
  { label: "Electronics", query: "electronics", icon: "layout" },
  { label: "Fashion", query: "fashion", icon: "tag" },
  { label: "Home & living", query: "home", icon: "home" },
  { label: "Beauty & care", query: "beauty", icon: "heart" },
  { label: "Computers", query: "laptop", icon: "card" },
  { label: "Sports", query: "sports", icon: "star" },
];

const benefits: Array<{ icon: IconName; title: string; text: string }> = [
  { icon: "shield", title: "Secure payments", text: "Orders are checked for stock and paid from your wallet." },
  { icon: "truck", title: "Reliable fulfilment", text: "Stock is reserved the moment you order." },
  { icon: "chat", title: "Ask, don't scroll", text: "The AI assistant finds and compares products for you." },
  { icon: "store", title: "Independent sellers", text: "Small businesses list and manage their own stock." },
];

function Featured() {
  const { status } = useAuth();
  const authed = status === "authed";
  const { data, loading, error, reload } = useAsync((s) => searchApi.all(s), [authed], authed);

  if (!authed) {
    return (
      <div className="card flex flex-col items-start gap-3 p-6">
        <p className="font-bold">Sign in to browse the live catalogue</p>
        <p className="text-sm text-ink/60">Product search is available to signed-in members.</p>
        <LinkButton to="/signin" size="sm">Sign in</LinkButton>
      </div>
    );
  }
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
        {[0, 1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
    );
  }
  const items = (data ?? []).slice(0, 5);
  if (items.length === 0) return <p className="text-sm text-ink/60">No products have been listed yet.</p>;
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
      {items.map((p) => (
        <ProductCard key={p.sku} product={p} />
      ))}
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const go = (e: FormEvent) => {
    e.preventDefault();
    navigate(q.trim() ? `/shop?q=${encodeURIComponent(q.trim())}` : "/shop");
  };

  return (
    <>
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-800 via-brand-700 to-brand-900 text-white">
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.15fr_1fr] lg:py-24">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-semibold text-lime-300">
              <Icon name="star" size={14} /> Your AI shopping assistant
            </p>
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
              Everything you need.
              <br />
              One smarter way to shop.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-white/80">
              Discover independent sellers and shop with an assistant that understands what you're looking for.
            </p>
            <form onSubmit={go} role="search" className="mt-8 flex max-w-xl gap-2">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                aria-label="Search products"
                placeholder="Try “wireless mouse”"
                className="min-w-0 flex-1 rounded-full bg-white px-5 py-3 text-ink placeholder:text-ink/45 focus:outline-none focus:ring-2 focus:ring-lime-400"
              />
              <button className="rounded-full bg-lime-400 px-6 font-bold text-ink hover:bg-lime-300">Search</button>
            </form>
            <div className="mt-6 flex flex-wrap gap-3">
              <LinkButton to="/shop" variant="lime" size="lg">Explore marketplace <Icon name="arrow" size={18} /></LinkButton>
              <LinkButton to="/signup?role=seller" variant="onDark" size="lg">Start selling</LinkButton>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-md" aria-hidden="true">
            <div className="rounded-3xl bg-white p-4 text-ink shadow-2xl">
              <div className="flex items-center gap-2 border-b border-ink/5 pb-3 text-sm font-bold">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white"><Icon name="star" size={14} /></span>
                Cartord assistant
              </div>
              <div className="mt-4 space-y-3 text-sm">
                <p className="ml-auto w-fit max-w-[80%] rounded-2xl rounded-br-sm bg-brand-600 px-4 py-2 text-white">
                  Show me a good mouse under ₦30,000
                </p>
                <p className="w-fit max-w-[85%] rounded-2xl rounded-bl-sm bg-brand-50 px-4 py-2">
                  Here are some options in stock right now.
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {["W", "E", "A"].map((c, i) => (
                    <div key={c} className={`flex h-20 items-center justify-center rounded-xl text-2xl font-extrabold ${i === 1 ? "bg-lime-300/60 text-brand-800" : "bg-brand-100 text-brand-700"}`}>{c}</div>
                  ))}
                </div>
              </div>
            </div>
            <p className="mt-3 text-center text-xs text-white/60">Illustration of the assistant experience</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          {categories.map((c) => (
            <Link key={c.label} to={`/shop?q=${encodeURIComponent(c.query)}`} className="card flex items-center gap-3 p-4 transition-colors hover:border-brand-300">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600"><Icon name={c.icon} /></span>
              <span className="text-sm font-bold">{c.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="mb-4 flex items-end justify-between">
          <h2 className="text-2xl font-extrabold tracking-tight">Trending on Cartord</h2>
          <Link to="/shop" className="text-sm font-semibold text-brand-700 hover:underline">View all products</Link>
        </div>
        <Featured />
      </section>

      <section className="mx-auto mt-12 grid max-w-7xl gap-5 px-4 sm:px-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-3xl bg-brand-800 p-8 text-white">
          <p className="flex items-center gap-2 text-sm font-semibold text-lime-300"><Icon name="chat" size={16} /> Cartord AI shopping assistant</p>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight">Ask. Discover. Shop.</h2>
          <p className="mt-3 max-w-lg text-white/80">Get instant recommendations, compare options and find answers about orders and returns, in plain language.</p>
          <LinkButton to="/chat" variant="lime" className="mt-6">Start chatting <Icon name="arrow" size={16} /></LinkButton>
        </div>
        <div className="rounded-3xl bg-ink p-8 text-white">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-lime-400 text-ink"><Icon name="store" size={24} /></span>
          <h2 className="mt-4 text-2xl font-extrabold">Are you a seller?</h2>
          <p className="mt-2 text-white/70">List products, manage stock and grow with independent-seller tools.</p>
          <LinkButton to="/signup?role=seller" variant="lime" className="mt-6">Start selling</LinkButton>
        </div>
      </section>

      <section className="mx-auto mt-12 grid max-w-7xl gap-4 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
        {benefits.map((b) => (
          <div key={b.title} className="card flex gap-3 p-5">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600"><Icon name={b.icon} /></span>
            <div>
              <h3 className="font-bold">{b.title}</h3>
              <p className="mt-1 text-sm text-ink/60">{b.text}</p>
            </div>
          </div>
        ))}
      </section>
    </>
  );
}
