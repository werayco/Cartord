import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { Button } from "./Button";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="card flex flex-col items-start gap-3 border-red-200 bg-red-50/60 p-5">
      <div className="flex items-center gap-2 font-semibold text-red-700">
        <Icon name="alert" /> Couldn't load this
      </div>
      <p className="text-sm text-red-700/90">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <Icon name="refresh" size={14} /> Try again
        </Button>
      )}
    </div>
  );
}

export function InlineError({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
      {message}
    </p>
  );
}

export function InlineSuccess({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <p role="status" className="rounded-xl bg-brand-50 px-4 py-3 text-sm text-brand-800">
      {message}
    </p>
  );
}

export function EmptyState({
  icon = "package",
  title,
  children,
  action,
}: {
  icon?: IconName;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
        <Icon name={icon} size={22} />
      </span>
      <h3 className="text-base font-bold">{title}</h3>
      {children && <p className="max-w-sm text-sm text-ink/60">{children}</p>}
      {action}
    </div>
  );
}

/**
 * Marks a screen or action whose backend endpoint does not exist yet.
 * Keeps planned functionality visibly separate from what is wired to a real API.
 */
export function GapNotice({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex gap-3 rounded-2xl border border-amber-300/70 bg-amber-50 p-4 text-sm text-amber-900">
      <Icon name="info" className="mt-0.5 shrink-0" />
      <div>
        <p className="font-bold">Backend integration gap: {title}</p>
        <div className="mt-1 text-amber-900/85">{children}</div>
      </div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-ink/10 ${className}`} />;
}
