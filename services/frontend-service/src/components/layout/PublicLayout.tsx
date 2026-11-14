import { useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { Logo } from "../Logo";
import { Icon, type IconName } from "../ui/Icon";
import { LinkButton } from "../ui/Button";
import { useAuth } from "../../context/AuthContext";
import { useShop } from "../../context/ShopContext";
import { homeFor } from "../../lib/routes";
import { AssistantShortcut } from "./AssistantShortcut";

const buyerMenu = [
  { to: "/buyer", label: "Dashboard", icon: "layout", end: true },
  { to: "/buyer/orders", label: "My Orders", icon: "clipboard" },
  { to: "/buyer/cart", label: "My Cart", icon: "cart" },
  { to: "/buyer/wishlist", label: "Wishlist", icon: "heart" },
  { to: "/buyer/wallet", label: "Wallet", icon: "wallet" },
  { to: "/buyer/notifications", label: "Notifications", icon: "bell" },
  { to: "/buyer/profile", label: "Settings", icon: "settings" },
] satisfies Array<{ to: string; label: string; icon: IconName; end?: boolean }>;

function Navbar() {
  const { status, role, logout } = useAuth();
  const { cartCount } = useShop();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const isBuyer = status === "authed" && role === "buyer";

  const submit = (e: FormEvent) => {
    e.preventDefault();
    navigate(q.trim() ? `/shop?q=${encodeURIComponent(q.trim())}` : "/shop");
    setOpen(false);
  };

  const link = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${isActive ? "bg-white/15" : "hover:bg-white/10"}`;

  return (
    <header className="sticky top-0 z-40 bg-brand-800 text-white">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        <Logo dark />
        <nav className="ml-4 hidden items-center gap-1 lg:flex" aria-label="Main">
          <NavLink to="/shop" className={link}>Shop</NavLink>
          <NavLink to="/signup?role=seller" className={link}>Sell</NavLink>
          {status !== "authed" && <NavLink to="/chat" className={link}>AI assistant</NavLink>}
        </nav>
        <form onSubmit={submit} role="search" className="relative ml-auto hidden max-w-xl flex-1 md:block">
          <Icon name="search" size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/45" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Search products"
            placeholder="Search for products…"
            className="w-full rounded-full bg-white py-2.5 pl-10 pr-4 text-sm text-ink placeholder:text-ink/45 focus:outline-none focus:ring-2 focus:ring-lime-400"
          />
        </form>
        <div className="ml-auto flex items-center gap-2 md:ml-0">
          {role === "buyer" && (
            <Link to="/buyer/cart" className="relative rounded-full p-2 hover:bg-white/10" aria-label={`Cart, ${cartCount} items`}>
              <Icon name="cart" size={20} />
              {cartCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-lime-400 px-1 text-[11px] font-bold text-ink">
                  {cartCount}
                </span>
              )}
            </Link>
          )}
          {isBuyer ? null : status === "authed" ? (
            <LinkButton to={homeFor(role)} variant="lime" size="sm">Dashboard</LinkButton>
          ) : (
            <>
              <Link to="/signin" className="hidden px-3 text-sm font-semibold hover:underline sm:inline">Sign in</Link>
              <LinkButton to="/signup" variant="lime" size="sm">Get started</LinkButton>
            </>
          )}
          <button
            className={`rounded-full p-2 hover:bg-white/10 ${isBuyer ? "" : "lg:hidden"}`}
            onClick={() => setOpen((o) => !o)}
            aria-label={isBuyer ? "Buyer menu" : "Menu"}
            aria-expanded={open}
          >
            <Icon name={open ? "x" : "menu"} size={20} />
          </button>
        </div>
      </div>
      {open && isBuyer && (
        <div className="absolute right-4 top-full z-50 w-72 max-w-[calc(100vw-2rem)] rounded-2xl border border-ink/10 bg-white p-3 text-ink shadow-xl sm:right-6">
          <form onSubmit={submit} role="search" className="mb-3 md:hidden">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Search products"
              placeholder="Search products…"
              className="w-full rounded-full border border-ink/10 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
            />
          </form>
          <nav className="space-y-1" aria-label="Buyer menu">
            {buyerMenu.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${
                    isActive ? "bg-brand-50 text-brand-800" : "hover:bg-ink/5"
                  }`
                }
              >
                <Icon name={item.icon} size={18} />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <button
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="mt-2 flex w-full items-center gap-3 border-t border-ink/10 px-3 pt-3 text-left text-sm font-semibold text-ink/70 hover:text-ink"
          >
            <Icon name="logout" size={18} />
            Log out
          </button>
        </div>
      )}
      {open && !isBuyer && (
        <div className="space-y-3 border-t border-white/10 px-4 py-4 lg:hidden">
          <form onSubmit={submit} role="search">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Search products"
              placeholder="Search for products…"
              className="w-full rounded-full bg-white px-4 py-2.5 text-sm text-ink focus:outline-none"
            />
          </form>
          <div className="flex flex-col gap-1">
            <NavLink to="/shop" className={link} onClick={() => setOpen(false)}>Shop</NavLink>
            <NavLink to="/signup?role=seller" className={link} onClick={() => setOpen(false)}>Sell</NavLink>
            {status !== "authed" && <NavLink to="/chat" className={link} onClick={() => setOpen(false)}>AI assistant</NavLink>}
          </div>
        </div>
      )}
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-16 bg-ink text-white/70">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4">
        <div className="md:col-span-2">
          <Logo dark />
          <p className="mt-3 max-w-sm text-sm">An AI-powered marketplace where independent sellers and curious shoppers meet.</p>
        </div>
        <div>
          <h3 className="mb-3 text-sm font-bold text-white">Marketplace</h3>
          <ul className="space-y-2 text-sm">
            <li><Link className="hover:text-white" to="/shop">Browse products</Link></li>
            <li><Link className="hover:text-white" to="/chat">Ask the AI assistant</Link></li>
            <li><Link className="hover:text-white" to="/signup?role=seller">Become a seller</Link></li>
          </ul>
        </div>
        <div>
          <h3 className="mb-3 text-sm font-bold text-white">Account</h3>
          <ul className="space-y-2 text-sm">
            <li><Link className="hover:text-white" to="/signin">Sign in</Link></li>
            <li><Link className="hover:text-white" to="/signup">Create account</Link></li>
            <li><Link className="hover:text-white" to="/forgot-password">Forgot password</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10 py-4 text-center text-xs">© {new Date().getFullYear()} Cartord</div>
    </footer>
  );
}

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <AssistantShortcut />
    </div>
  );
}
