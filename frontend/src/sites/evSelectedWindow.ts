import { createContext, useContext, useEffect, type ReactNode } from "react";

import { coldWindowSearch, type AnalysedPeriodsRead } from "./coldAssessmentClient";

type SelectedRead = { window: { from: string | null; to: string | null; known_at: string | null } } & AnalysedPeriodsRead;

/**
 * PB-1c (PB-1b review L2): when a range holds analysed periods the read is about its `shown_period`, so the links
 * built from it (tabs, sessions, Findings) carry that period's exact window, not the requested range.
 */
export function shownWindow(read: SelectedRead): { from: string | null; to: string | null; known_at: string | null } {
  const w = read.window;
  const shown = read.shown_period;
  return shown ? { from: shown.from, to: shown.to, known_at: w.known_at } : w;
}

/**
 * post-W6 W2-EV (ruling Q14/Q23): the main-tab query an EV page carries is its loaded read's own selected
 * `from`, `to` and `known_at`, never the raw address. A refused, loading or no-window read carries none.
 */
export function selectedWindowSearch(read: SelectedRead | null | undefined): string {
  if (read === null || read === undefined) return "";
  const w = shownWindow(read);
  if (w.from === null || w.to === null) return "";
  return coldWindowSearch({ from: w.from, to: w.to, known_at: w.known_at });
}

/** An EV frame's main-tab row: fixed, or rendered from the selected read's query. */
export type EvTabs = ReactNode | ((search: string) => ReactNode);

export function renderEvTabs(tabs: EvTabs, search: string): ReactNode {
  return typeof tabs === "function" ? tabs(search) : tabs;
}

/**
 * post-W6 W2-EV (Q14): a screen reports its loaded read's selected query to the frame's main tabs through this context.
 * R347 (W5-EV) reuses it for the depth pages, so each carries its own loaded window and a refused read carries none.
 */
export const ReportSelected = createContext<((search: string) => void) | null>(null);

/** Report the loaded read's selected query (`""` for a refused, loading or no-window read) to the frame, if it listens. */
export function useReportSelectedWindow(read: SelectedRead | null | undefined): void {
  const report = useContext(ReportSelected);
  const search = selectedWindowSearch(read);
  useEffect(() => {
    report?.(search);
  }, [report, search]);
}
