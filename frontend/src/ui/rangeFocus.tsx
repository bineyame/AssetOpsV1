/**
 * SR-2 (proposal 2026-11-10 "Item 12.5", SR.3 "Finer views inside the range"): a page that shows one day inside the
 * shared range tells the shell which day it shows, so the top bar never claims the range over a one-day board. The
 * `FocusPicker` declares it; the `SharedRangeBar` reads it. Nothing here is kept outside React state: the day itself
 * lives in the page's address (`day=`).
 */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export interface RangeFocus {
  /** The calendar day the page shows (`YYYY-MM-DD`). */
  day: string;
}

interface RangeFocusSlot {
  focus: RangeFocus | null;
  setFocus: (focus: RangeFocus | null) => void;
}

const RangeFocusContext = createContext<RangeFocusSlot | null>(null);

export function RangeFocusProvider({ children }: { children: ReactNode }) {
  const [focus, setFocus] = useState<RangeFocus | null>(null);
  const slot = useMemo(() => ({ focus, setFocus }), [focus]);
  return <RangeFocusContext.Provider value={slot}>{children}</RangeFocusContext.Provider>;
}

/** The day the current page shows, when it shows one day; `null` otherwise (or outside the operator shell). */
export function useRangeFocus(): RangeFocus | null {
  return useContext(RangeFocusContext)?.focus ?? null;
}

/** Declares the day this page shows while it is mounted; `null` declares nothing. */
export function useDeclareRangeFocus(day: string | null): void {
  const setFocus = useContext(RangeFocusContext)?.setFocus;
  useEffect(() => {
    if (setFocus === undefined || day === null) return undefined;
    setFocus({ day });
    return () => setFocus(null);
  }, [setFocus, day]);
}
