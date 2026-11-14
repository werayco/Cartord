import type { ReactNode } from "react";
import { compact, humanize } from "../lib/format";
import { StatCard } from "./ui/StatCard";
import { ErrorState, Skeleton } from "./ui/feedback";

/*
 * Admin statistics endpoints return schemas that aren't documented. Rather than guessing field
 * names, this renders whatever comes back: numbers become stat cards, arrays of objects become
 * tables, and nested objects are flattened to "Parent child" labels.
 */

type Scalar = string | number | boolean | null;

function flatten(value: unknown, prefix = "", out: Array<[string, Scalar]> = []): Array<[string, Scalar]> {
  if (value === null || typeof value !== "object") {
    out.push([prefix || "Value", value as Scalar]);
    return out;
  }
  if (Array.isArray(value)) return out;
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    const label = prefix ? `${prefix} ${humanize(k).toLowerCase()}` : humanize(k);
    if (v && typeof v === "object" && !Array.isArray(v)) flatten(v, label, out);
    else if (!Array.isArray(v)) out.push([label, v as Scalar]);
  }
  return out;
}

function collectTables(value: unknown, prefix = ""): Array<{ title: string; rows: Record<string, unknown>[] }> {
  if (Array.isArray(value)) {
    const rows = value.filter((r): r is Record<string, unknown> => !!r && typeof r === "object" && !Array.isArray(r));
    return rows.length ? [{ title: prefix || "Details", rows }] : [];
  }
  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([k, v]) =>
      collectTables(v, prefix ? `${prefix} ${humanize(k).toLowerCase()}` : humanize(k)),
    );
  }
  return [];
}

const show = (v: unknown): string => {
  if (typeof v === "number") return Number.isInteger(v) && Math.abs(v) >= 100000 ? compact(v) : v.toLocaleString();
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
};

export function DataBlock({
  title,
  data,
  loading,
  error,
  onRetry,
  extra,
}: {
  title: string;
  data: unknown;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  extra?: ReactNode;
}) {
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (loading) {
    return (
      <section>
        <h2 className="mb-3 text-lg font-bold">{title}</h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </section>
    );
  }
  const scalars = flatten(data).slice(0, 16);
  const tables = collectTables(data);
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-bold">{title}</h2>
        {extra}
      </div>
      {scalars.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {scalars.map(([label, v]) => (
            <StatCard key={label} label={label} value={show(v)} />
          ))}
        </div>
      )}
      {tables.map((t) => (
        <div key={t.title} className="card mt-4 overflow-x-auto">
          <p className="px-4 pt-4 text-sm font-bold">{t.title}</p>
          <table className="mt-2 min-w-full">
            <thead>
              <tr>
                {Object.keys(t.rows[0]).map((c) => (
                  <th key={c} className="table-th">{humanize(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-ink/5">
              {t.rows.map((r, i) => (
                <tr key={i}>
                  {Object.keys(t.rows[0]).map((c) => (
                    <td key={c} className="table-td">{show(r[c])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      {scalars.length === 0 && tables.length === 0 && <p className="text-sm text-ink/60">The service returned no data for this period.</p>}
    </section>
  );
}
