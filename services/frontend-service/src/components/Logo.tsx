import { Link } from "react-router-dom";

export function Logo({ to = "/", dark = false }: { to?: string; dark?: boolean }) {
  return (
    <Link
      to={to}
      className={`inline-flex items-center rounded-md ${dark ? "" : "bg-brand-800 p-1.5"}`}
      aria-label="Cartord home"
    >
      <img src="/cartord-logo-ii.png" alt="" className="h-8 w-auto" />
    </Link>
  );
}
