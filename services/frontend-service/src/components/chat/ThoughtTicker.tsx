import { useEffect, useRef, useState } from "react";

interface ThoughtTickerProps {
  active: boolean;
  thoughts: string[];
  onExited: () => void;
}

interface ThoughtLine {
  current: string;
  previous: string | null;
  revision: number;
}

const DISPLAY_MS = 600;
const TRANSITION_MS = 250;

export function ThoughtTicker({ active, thoughts, onExited }: ThoughtTickerProps) {
  const [line, setLine] = useState<ThoughtLine>({
    current: "Thinking...",
    previous: null,
    revision: 0,
  });
  const [visible, setVisible] = useState(active);
  const queue = useRef<string[]>([]);
  const receivedCount = useRef(0);
  const currentStartedAt = useRef(Date.now());
  const activeRef = useRef(active);
  const timer = useRef<number | undefined>(undefined);
  const transitionTimer = useRef<number | undefined>(undefined);
  const exitTimer = useRef<number | undefined>(undefined);
  const onExitedRef = useRef(onExited);

  activeRef.current = active;
  onExitedRef.current = onExited;

  const advance = useRef<() => void>(() => {});
  advance.current = () => {
    timer.current = undefined;
    if (!activeRef.current) return;

    const next = queue.current.shift();
    if (next === undefined) return;

    setLine((current) => ({
      current: next,
      previous: current.current,
      revision: current.revision + 1,
    }));
    currentStartedAt.current = Date.now();

    window.clearTimeout(transitionTimer.current);
    transitionTimer.current = window.setTimeout(() => {
      setLine((current) => ({ ...current, previous: null }));
      transitionTimer.current = undefined;
    }, TRANSITION_MS);

    if (queue.current.length > 0) {
      timer.current = window.setTimeout(() => advance.current(), DISPLAY_MS);
    }
  };

  useEffect(() => {
    if (active) {
      window.clearTimeout(exitTimer.current);
      setVisible(true);
      return;
    }

    queue.current = [];
    window.clearTimeout(timer.current);
    timer.current = undefined;
    window.clearTimeout(transitionTimer.current);
    transitionTimer.current = undefined;
    setLine((current) => ({ ...current, previous: null }));
    setVisible(false);
    exitTimer.current = window.setTimeout(() => {
      onExitedRef.current();
      exitTimer.current = undefined;
    }, TRANSITION_MS);

    return () => window.clearTimeout(exitTimer.current);
  }, [active]);

  useEffect(() => {
    const incoming = thoughts.slice(receivedCount.current);
    if (incoming.length > 0) {
      receivedCount.current = thoughts.length;
      queue.current.push(...incoming);
    }
    if (!activeRef.current || timer.current !== undefined || queue.current.length === 0) return;

    const remaining = Math.max(0, DISPLAY_MS - (Date.now() - currentStartedAt.current));
    timer.current = window.setTimeout(() => advance.current(), remaining);
  }, [active, thoughts]);

  useEffect(
    () => () => {
      window.clearTimeout(timer.current);
      window.clearTimeout(transitionTimer.current);
      window.clearTimeout(exitTimer.current);
    },
    [],
  );

  return (
    <div
      aria-live="polite"
      className={`relative h-6 overflow-hidden transition-opacity duration-[250ms] ${visible ? "opacity-100" : "opacity-0"}`}
    >
      {line.previous !== null && (
        <div
          key={`thought-out-${line.revision}`}
          className="thought-slide-up-out absolute inset-0 flex items-center gap-2 whitespace-nowrap"
        >
          <span className="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-gray-400" />
          <span className="truncate text-sm text-gray-500">{line.previous}</span>
        </div>
      )}
      <div
        key={`thought-in-${line.revision}`}
        className={`absolute inset-0 flex items-center gap-2 whitespace-nowrap ${line.revision > 0 ? "thought-slide-up-in" : ""}`}
      >
        <span className="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-gray-400" />
        <span className="truncate text-sm text-gray-500">{line.current}</span>
      </div>
    </div>
  );
}
