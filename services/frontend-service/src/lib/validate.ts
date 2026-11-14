export type Errors<T extends string = string> = Partial<Record<T, string>>;

export const required = (v: string, label: string) => (v.trim() ? undefined : `${label} is required`);

export const email = (v: string) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? undefined : "Enter a valid email address";

export const minLength = (v: string, n: number, label: string) =>
  v.length >= n ? undefined : `${label} must be at least ${n} characters`;

export const positiveNumber = (v: string, label: string) => {
  const n = Number(v);
  return v.trim() !== "" && Number.isFinite(n) && n >= 0 ? undefined : `${label} must be 0 or more`;
};

export const hasErrors = (e: Errors) => Object.values(e).some(Boolean);
