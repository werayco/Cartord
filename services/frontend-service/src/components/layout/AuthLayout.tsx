import { Outlet } from "react-router-dom";
import { Logo } from "../Logo";
import { Icon } from "../ui/Icon";

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="relative hidden overflow-hidden bg-brand-800 p-10 text-white lg:flex lg:flex-col">
        <Logo dark />
        <div className="mt-auto max-w-md pb-10">
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight">
            Shop smarter.
            <br />
            Sell better.
          </h2>
          <p className="mt-4 text-white/75">
            Discover independent sellers, ask the AI assistant what to buy, and manage your store from one place.
          </p>
          <ul className="mt-8 space-y-3 text-sm">
            {[
              ["shield", "Sign-in secured with signed access tokens"],
              ["chat", "An AI assistant that knows the catalogue"],
              ["store", "Seller tools for products and stock"],
            ].map(([icon, text]) => (
              <li key={text} className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-lime-400 text-ink">
                  <Icon name={icon as "shield"} size={16} />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <div aria-hidden="true" className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-brand-600/50" />
        <div aria-hidden="true" className="absolute -bottom-32 -right-10 h-72 w-72 rounded-full bg-brand-700/70" />
      </aside>
      <main className="flex items-center justify-center bg-cream px-4 py-10 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
