import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Icon } from "../ui/Icon";

export function AssistantShortcut() {
  const { status } = useAuth();
  const location = useLocation();

  if (status !== "authed" || location.pathname === "/chat") return null;

  return (
    <Link
      to="/chat"
      aria-label="Open AI assistant"
      title="AI assistant"
      className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-brand-700 text-white shadow-xl transition hover:scale-105 hover:bg-brand-800 focus:outline-none focus:ring-4 focus:ring-brand-300"
    >
      <Icon name="chat" size={24} />
    </Link>
  );
}
