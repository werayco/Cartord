import { config } from "../config/env";

export function money(value: number | null | undefined): string {
  try {
    return new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: config.currency,
      maximumFractionDigits: 0,
    }).format(Number(value ?? 0));
  } catch {
    return `${config.currency} ${Number(value ?? 0).toLocaleString()}`;
  }
}

export function compact(value: number): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function humanize(key: string): string {
  return key
    .replace(/[_-]+/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/^./, (c) => c.toUpperCase());
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return (parts[0][0] + (parts[1]?.[0] ?? "")).toUpperCase();
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-NG", { day: "numeric", month: "short", year: "numeric" });
}
