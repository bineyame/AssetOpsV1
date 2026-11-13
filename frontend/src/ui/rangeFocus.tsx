/**
 * SR-2 (proposal 2026-11-10 "Item 12.5", SR.3 "Finer views inside the range"): a page that shows one day inside the
 * shared range tells the shell which day it shows, so the top bar never claims the range over a one-day board. The
 * `FocusPicker` declares it; the `SharedRangeBar` reads it. Nothing here is kept outside React state: the day itself
 * lives in the page's address (`day=`).
 *
 * SR-4c (D-SR.6, architect rev 8 §8.2): a page declares either the span it shows (one day or part of the range) or
 * that it shows "now" (point in time), so the bar says "All pages" only where the content follows the range. Every
 * declaration is made in a layout effect, so the bar never paints "All pages" first.
 */
import { createContext, useContext, useLayoutEffect, useMemo, useState, type ReactNode } from "react";

/** D-SR.64: "own period" is one record read at its own period (a Finding), never re-cut by the range. */
export type RangeNotUsedNote = "shows now" | "current settings" | "prices valid now" | "own period";

export type RangeFocus =
  /** The calendar days the page shows (`YYYY-MM-DD`, `to` included; one day when equal). */
  | { kind: "span"; from: string; to: string }
  /** A point-in-time page: the range is not used. */
  | { kind: "now"; note: RangeNotUsedNote };

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

/** What the current page declared about the range; `null` when it declared nothing (or outside the operator shell). */
export function useRangeFocus(): RangeFocus | null {
  return useContext(RangeFocusContext)?.focus ?? null;
}

/** Declares the days this page shows while it is mounted; a `null` bound declares nothing. */
export function useDeclareRangeSpan(from: string | null, to: string | null): void {
  const setFocus = useContext(RangeFocusContext)?.setFocus;
  useLayoutEffect(() => {
    if (setFocus === undefined || from === null || to === null) return undefined;
    setFocus({ kind: "span", from, to });
    return () => setFocus(null);
  }, [setFocus, from, to]);
}

/** Declares the day this page shows while it is mounted; `null` declares nothing. */
export function useDeclareRangeFocus(day: string | null): void {
  useDeclareRangeSpan(day, day);
}

/** Declares that this page shows a point in time (the range is not used) while it is mounted; `null` declares nothing. */
export function useDeclareRangeNotUsed(note: RangeNotUsedNote | null): void {
  const setFocus = useContext(RangeFocusContext)?.setFocus;
  useLayoutEffect(() => {
    if (setFocus === undefined || note === null) return undefined;
    setFocus({ kind: "now", note });
    return () => setFocus(null);
  }, [setFocus, note]);
}

/** A component form of `useDeclareRangeNotUsed`, for frames that branch by Site type. */
export function RangeNotUsed({ note }: { note: RangeNotUsedNote }) {
  useDeclareRangeNotUsed(note);
  return null;
}

/** A component form of `useDeclareRangeSpan`. */
export function RangeSpan({ from, to }: { from: string | null; to: string | null }) {
  useDeclareRangeSpan(from, to);
  return null;
}
