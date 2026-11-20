import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { Logo } from "../Logo";
import { Icon, type IconName } from "../ui/Icon";
import { LinkButton } from "../ui/Button";
import { useAuth } from "../../context/AuthContext";
import { initials } from "../../lib/format";
import { AssistantShortcut } from "./AssistantShortcut";

export interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  end?: boolean;
}

type Variant = "buyer" | "seller" | "admin";

const tone: Record<Variant, { active: string; badge: string; label: string }> = {
  buyer: { active: "bg-brand-600 text-white", badge: "bg-brand-50 text-brand-700", label: "Buyer" },
  seller: { active: "bg-lime-400 text-ink", badge: "bg-lime-300/60 text-brand-900", label: "Seller" },
  admin: { active: "bg-amber-400 text-ink", badge: "bg-amber-100 text-amber-900", label: "Administrator" },
};

export function DashboardLayout({ variant, nav }: { variant: Variant; nav: NavItem[] }) {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const t = tone[variant];

  const sidebar = (
    <div className="flex h-full flex-col bg-ink-800 p-4 text-white/80">
      <div className="px-2 py-2">
        <Logo to={`/${variant}`} dark />
        {variant === "admin" && (
          <span className="mt-3 inline-block rounded-full bg-amber-400 px-2.5 py-0.5 text-xs font-bold text-ink">
            Admin console
          </span>
        )}
      </div>
      <nav className="mt-6 flex-1 space-y-1" aria-label={`${t.label} navigation`}>
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors ${
                isActive ? t.active : "hover:bg-white/10"
              }`
            }
          >
            <Icon name={item.icon} size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      {variant === "buyer" && (
        <div className="mb-3 rounded-2xl bg-brand-700 p-4 text-sm text-white">
          <p className="font-bold">Become a seller</p>
          <p className="mt-1 text-white/75">Reach customers across the marketplace.</p>
          <LinkButton to="/signup?role=seller" variant="lime" size="sm" className="mt-3 w-full">
            Start selling
          </LinkButton>
        </div>
      )}
      <button
        onClick={logout}
        className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold hover:bg-white/10"
      >
        <Icon name="logout" size={18} /> Log out
      </button>
    </div>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[16rem_minmax(0,1fr)]">
      <aside className="sticky top-0 hidden h-screen lg:block">{sidebar}</aside>

      {open && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-ink/50" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-64">{sidebar}</div>
        </div>
      )}

      <div className="min-w-0">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-ink/5 bg-cream/90 px-4 py-3 backdrop-blur sm:px-8">
          <button className="rounded-full p-2 hover:bg-ink/5 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <Icon name="menu" size={20} />
          </button>
          <div className="ml-auto flex items-center gap-3">
            {variant !== "admin" && (
              <>
                <Link to="/shop" className="hidden rounded-full p-2 hover:bg-ink/5 sm:block" aria-label="Browse products">
                  <Icon name="search" size={20} />
                </Link>
                <Link to={`/${variant}/notifications`} className="rounded-full p-2 hover:bg-ink/5" aria-label="Notifications">
                  <Icon name="bell" size={20} />
                </Link>
              </>
            )}
            <span className={`hidden rounded-full px-2.5 py-1 text-xs font-bold sm:inline ${t.badge}`}>{t.label}</span>
            <span className="flex items-center gap-2 text-sm font-semibold">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
                {initials(user?.name || user?.username || "?")}
              </span>
              <span className="hidden max-w-[10rem] truncate sm:inline">{user?.name || user?.username}</span>
            </span>
          </div>
        </header>
        <main className="px-4 py-8 sm:px-8">
          <Outlet />
        </main>
      </div>
      <AssistantShortcut />
    </div>
  );
}
