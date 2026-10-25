import type { ReactNode } from "react";

import { coldWindowSearch } from "./coldAssessmentClient";

/**
 * post-W6 W2-EV (ruling Q14/Q23): the main-tab query an EV page carries is its loaded read's own selected
 * `from`, `to` and `known_at`, never the raw address. A refused, loading or no-window read carries none.
 */
export function selectedWindowSearch(read: { window: { from: string | null; to: string | null; known_at: string | null } } | null | undefined): string {
  if (read === null || read === undefined) return "";
  const w = read.window;
  if (w.from === null || w.to === null) return "";
  return coldWindowSearch({ from: w.from, to: w.to, known_at: w.known_at });
}

/** An EV frame's main-tab row: fixed, or rendered from the selected read's query. */
export type EvTabs = ReactNode | ((search: string) => ReactNode);

export function renderEvTabs(tabs: EvTabs, search: string): ReactNode {
  return typeof tabs === "function" ? tabs(search) : tabs;
}
