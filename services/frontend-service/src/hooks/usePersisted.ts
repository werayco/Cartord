import { useCallback, useEffect, useState } from "react";

/** localStorage-backed state keyed per user. Pass null to disable persistence. */
export function usePersisted<T>(key: string | null, initial: T) {
  const [value, setValue] = useState<T>(initial);

  useEffect(() => {
    if (!key) {
      setValue(initial);
      return;
    }
    try {
      const raw = localStorage.getItem(key);
      setValue(raw ? (JSON.parse(raw) as T) : initial);
    } catch {
      setValue(initial);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const set = useCallback(
    (next: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const resolved = typeof next === "function" ? (next as (p: T) => T)(prev) : next;
        if (key) {
          try {
            localStorage.setItem(key, JSON.stringify(resolved));
          } catch {
            /* ignore quota errors */
          }
        }
        return resolved;
      });
    },
    [key],
  );

  return [value, set] as const;
}
