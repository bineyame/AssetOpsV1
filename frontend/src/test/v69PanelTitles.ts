/**
 * The approved v69 panel title map (`D-2026-10-17-mockup-layout-spec`,
 * `.agent/architect-W1-fidelity.md`). It is exhaustive: every screen's expected
 * panel titles are exactly `frontend/docs/architecture/v69-rendered-panels.json`,
 * except the six substitutions below, which the Architect approved. Do not add
 * an entry to keep an extra app panel; move its content into its owning panel.
 *
 * A dynamic title is a function of the selected read, never of a mock fixture.
 */
import rendered from "../../docs/architecture/v69-rendered-panels.json";

export type DynamicTitle = (values: Record<string, string>) => string;

/** `screen:index` → the approved replacement for the JSON title. */
export const APPROVED_TITLE_CHANGES: Readonly<Record<string, string | DynamicTitle>> = {
  "foundation:2": "Identity and operating obligations",
  "dispatch:2": (v) => `Selected block · ${need(v, "interval")}`,
  "readiness:2": (v) => `Gateway status · ${need(v, "gateway")}`,
  "finding-evidence:1": (v) => `Evidence bundle · ${need(v, "finding")}`,
  "sld:1": (v) => (v.topology ? `${need(v, "site")} · ${v.topology}` : need(v, "site")),
  // W1-F2 coordinator ruling (2026-10-17, under D-2026-10-16-w1-ux): the plain variant of "How a claim limit is set".
  "evidence-analysis:2": "How each limit is set",
};

function need(values: Record<string, string>, key: string): string {
  const value = values[key];
  if (value === undefined || value === "") {
    throw new Error(`The dynamic panel title needs the selected read's "${key}" value.`);
  }
  return value;
}

const PANELS = (rendered as { panels: Record<string, { index: number; title: string }[]> }).panels;

/** The expected panel titles of one v69 screen, in order. */
export function expectedPanelTitles(screenId: string, values: Record<string, string> = {}): string[] {
  const entry = PANELS[screenId];
  if (entry === undefined) throw new Error(`No v69 rendered-panel entry for screen "${screenId}".`);
  return [...entry]
    .sort((a, b) => a.index - b.index)
    .map(({ index, title }) => {
      const change = APPROVED_TITLE_CHANGES[`${screenId}:${index}`];
      if (change === undefined) return title;
      return typeof change === "string" ? change : change(values);
    });
}
