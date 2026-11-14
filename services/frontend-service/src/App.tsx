import { Link, Navigate, Route, Routes } from "react-router-dom";
import { AuthLayout } from "./components/layout/AuthLayout";
import { DashboardLayout, type NavItem } from "./components/layout/DashboardLayout";
import { PublicLayout } from "./components/layout/PublicLayout";
import { useAuth } from "./context/AuthContext";
import { RequireAuth } from "./routes/RequireAuth";
import { homeFor } from "./lib/routes";

import Landing from "./pages/Landing";
import SignIn from "./pages/auth/SignIn";
import SignUp from "./pages/auth/SignUp";
import { ForgotPassword, MfaPage, VerifyAccount } from "./pages/auth/FeatureGap";
import Shop from "./pages/shared/Shop";
import ProductDetail from "./pages/shared/ProductDetail";
import WalletPage from "./pages/shared/WalletPage";
import { GapPage } from "./pages/shared/GapPage";
import ChatPage from "./pages/chat/ChatPage";

import BuyerOverview from "./pages/buyer/Overview";
import BuyerOrders from "./pages/buyer/Orders";
import Cart from "./pages/buyer/Cart";
import Wishlist from "./pages/buyer/Wishlist";
import BuyerProfile from "./pages/buyer/Profile";

import SellerOverview from "./pages/seller/Overview";
import SellerProducts from "./pages/seller/Products";
import ProductForm from "./pages/seller/ProductForm";
import Inventory from "./pages/seller/Inventory";
import SellerProfile from "./pages/seller/Profile";

import AdminOverview from "./pages/admin/Overview";
import AdminUsers from "./pages/admin/Users";
import AdminProducts from "./pages/admin/Products";
import AdminOrders from "./pages/admin/Orders";

const buyerNav: NavItem[] = [
  { to: "/buyer", label: "Dashboard", icon: "layout", end: true },
  { to: "/buyer/orders", label: "My Orders", icon: "clipboard" },
  { to: "/buyer/cart", label: "My Cart", icon: "cart" },
  { to: "/buyer/wishlist", label: "Wishlist", icon: "heart" },
  { to: "/buyer/notifications", label: "Notifications", icon: "bell" },
  { to: "/buyer/profile", label: "Settings", icon: "settings" },
];

const sellerNav: NavItem[] = [
  { to: "/seller", label: "Overview", icon: "layout", end: true },
  { to: "/seller/products", label: "Products", icon: "package" },
  { to: "/seller/inventory", label: "Inventory", icon: "store" },
  { to: "/seller/orders", label: "Orders", icon: "clipboard" },
  { to: "/seller/analytics", label: "Sales analytics", icon: "chart" },
  { to: "/seller/wallet", label: "Wallet", icon: "wallet" },
  { to: "/seller/notifications", label: "Notifications", icon: "bell" },
  { to: "/seller/profile", label: "Store & profile", icon: "user" },
];

const adminNav: NavItem[] = [
  { to: "/admin", label: "Overview", icon: "layout", end: true },
  { to: "/admin/users", label: "Users", icon: "users" },
  { to: "/admin/products", label: "Products", icon: "package" },
  { to: "/admin/orders", label: "Orders", icon: "clipboard" },
  { to: "/admin/payments", label: "Payments", icon: "card" },
  { to: "/admin/categories", label: "Categories", icon: "tag" },
  { to: "/admin/reports", label: "Reports", icon: "chart" },
];

const notificationsGap = (
  <GapPage title="Notifications" subtitle="Order and payment updates." gapTitle="in-app notifications">
    The notification service only sends email; it exposes no HTTP routes besides health. An endpoint to list and mark notifications as read is needed before an in-app inbox can be shown.
  </GapPage>
);

function NotFound() {
  const { role } = useAuth();
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-3 px-4 text-center">
      <h1 className="text-3xl font-extrabold">Page not found</h1>
      <p className="text-ink/60">That address doesn't lead anywhere on Cartord.</p>
      <Link to={role ? homeFor(role) : "/"} className="font-semibold text-brand-700 underline">Go back</Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Landing />} />
        <Route element={<RequireAuth />}>
          <Route path="shop" element={<Shop />} />
          <Route path="product/:sku" element={<ProductDetail />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Route>

      <Route element={<AuthLayout />}>
        <Route path="signin" element={<SignIn />} />
        <Route path="signup" element={<SignUp />} />
        <Route path="forgot-password" element={<ForgotPassword />} />
        <Route path="verify-account" element={<VerifyAccount />} />
        <Route path="mfa" element={<MfaPage />} />
      </Route>

      <Route element={<RequireAuth />}>
        <Route path="chat" element={<ChatPage />} />
        <Route path="dashboard" element={<DashboardRedirect />} />
      </Route>

      <Route element={<RequireAuth roles={["buyer"]} />}>
        <Route path="buyer" element={<DashboardLayout variant="buyer" nav={buyerNav} />}>
          <Route index element={<BuyerOverview />} />
          <Route path="orders" element={<BuyerOrders />} />
          <Route path="cart" element={<Cart />} />
          <Route path="wishlist" element={<Wishlist />} />
          <Route path="wallet" element={<Navigate to="/buyer" replace />} />
          <Route path="notifications" element={notificationsGap} />
          <Route path="profile" element={<BuyerProfile />} />
        </Route>
      </Route>

      <Route element={<RequireAuth roles={["seller"]} />}>
        <Route path="seller" element={<DashboardLayout variant="seller" nav={sellerNav} />}>
          <Route index element={<SellerOverview />} />
          <Route path="products" element={<SellerProducts />} />
          <Route path="products/new" element={<ProductForm />} />
          <Route path="products/:sku/edit" element={<ProductForm />} />
          <Route path="inventory" element={<Inventory />} />
          <Route
            path="orders"
            element={
              <GapPage title="Orders" subtitle="Incoming orders and fulfilment." gapTitle="seller orders">
                The order service has no endpoint that lists orders for a seller or updates fulfilment status. Add list-by-seller and status-update routes to build this screen.
              </GapPage>
            }
          />
          <Route
            path="analytics"
            element={
              <GapPage title="Sales analytics" subtitle="Revenue and product performance." gapTitle="seller analytics">
                No endpoint returns revenue, sales counts or per-product performance for a seller. The wallet balance is the only figure available today.
              </GapPage>
            }
          />
          <Route path="wallet" element={<WalletPage />} />
          <Route path="notifications" element={notificationsGap} />
          <Route path="profile" element={<SellerProfile />} />
        </Route>
      </Route>

      <Route element={<RequireAuth roles={["admin"]} />}>
        <Route path="admin" element={<DashboardLayout variant="admin" nav={adminNav} />}>
          <Route index element={<AdminOverview />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="products" element={<AdminProducts />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route
            path="payments"
            element={
              <GapPage title="Payments" subtitle="Platform payment activity." gapTitle="payment monitoring">
                The payment service exposes buyer and seller wallets only. Admin payment lists and statistics need new endpoints.
              </GapPage>
            }
          />
          <Route
            path="categories"
            element={
              <GapPage title="Categories" subtitle="Organise the catalogue." gapTitle="categories">
                Products have no category field and there is no category service. Add the model and CRUD endpoints first.
              </GapPage>
            }
          />
          <Route
            path="reports"
            element={
              <GapPage title="Reports & analytics" subtitle="Platform-wide reporting." gapTitle="reports">
                No reporting endpoints exist. The overview, users and orders pages already show every statistic the backend returns.
              </GapPage>
            }
          />
        </Route>
      </Route>
    </Routes>
  );
}

function DashboardRedirect() {
  const { role } = useAuth();
  return <Navigate to={homeFor(role)} replace />;
}
