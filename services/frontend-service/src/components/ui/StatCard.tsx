import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { Skeleton } from "./feedback";

export function StatCard({
  label,
  value,
  icon,
  loading,
  note,
}: {
  label: string;
  value: ReactNode;
  icon?: IconName;
  loading?: boolean;
  note?: string;
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between text-sm text-ink/60">
        <span>{label}</span>
        {icon && (
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <Icon name={icon} size={16} />
          </span>
        )}
      </div>
      <div className="mt-2 text-2xl font-extrabold tracking-tight">
        {loading ? <Skeleton className="h-8 w-24" /> : value}
      </div>
      {note && <p className="mt-1 text-xs text-ink/50">{note}</p>}
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink/60">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
