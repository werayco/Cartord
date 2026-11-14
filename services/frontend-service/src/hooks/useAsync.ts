import { useCallback, useEffect, useState } from "react";
import { errorMessage } from "../api/http";

interface State<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export function useAsync<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  deps: unknown[] = [],
  enabled = true,
) {
  const [state, setState] = useState<State<T>>({ data: null, error: null, loading: enabled });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    const ctrl = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    fn(ctrl.signal)
      .then((data) => {
        if (!ctrl.signal.aborted) setState({ data, error: null, loading: false });
      })
      .catch((e) => {
        if (ctrl.signal.aborted) return;
        setState({ data: null, error: errorMessage(e), loading: false });
      });
    return () => ctrl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick, enabled]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}
