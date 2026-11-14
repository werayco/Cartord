import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { PageSpinner } from "../components/ui/Spinner";
import type { Role } from "../api/types";
import { homeFor } from "../lib/routes";

/** Blocks anonymous visitors and, when `roles` is given, sends other roles to their own area. */
export function RequireAuth({ roles }: { roles?: Role[] }) {
  const { status, role } = useAuth();
  const location = useLocation();
  if (status === "loading") return <PageSpinner />;
  if (status === "anon") return <Navigate to="/signin" replace state={{ from: location.pathname + location.search }} />;
  if (roles && role && !roles.includes(role)) return <Navigate to={homeFor(role)} replace />;
  return <Outlet />;
}
