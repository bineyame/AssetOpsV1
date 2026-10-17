/**
 * The v69 panel-structure guard (`D-2026-10-17-mockup-layout-spec`).
 *
 * A screen's main content must render exactly the v69 panel titles, in order,
 * with nothing panel-like before, between or after them. "Panel-like" is
 * deliberately broad so an extra card cannot slip past by changing its class:
 *
 *   - every level-2 heading in the main landmark (the page title is level 1);
 *   - every `section.panel`, `[data-headline-card]` or `.panel` element, whether
 *     or not it has a heading (an untitled card is reported as "(untitled)").
 *
 * Content inside a closed `<details>` disclosure or a hidden element is not on
 * the screen and is not counted; the selected tab's panels are.
 *
 * Use it after `settledScreen`, and in every variant (stocked, empty, refused):
 * a route with a valid screen identity keeps its panel slots with in-panel gaps.
 */
import { expect } from "vitest";

import { expectedPanelTitles } from "./v69PanelTitles";

function hiddenOrCollapsed(element: Element, root: Element): boolean {
  for (let node: Element | null = element; node !== null && node !== root; node = node.parentElement) {
    if (node instanceof HTMLElement && (node.hidden || node.getAttribute("aria-hidden") === "true")) return true;
    const parent = node.parentElement;
    if (parent instanceof HTMLDetailsElement && !parent.open && node.tagName !== "SUMMARY") return true;
  }
  return false;
}

function text(element: Element): string {
  return (element.textContent ?? "").replace(/\s+/g, " ").trim();
}

/** The panel titles a screen actually renders in its main content, in DOM order. */
export function renderedPanelTitles(scope?: HTMLElement): string[] {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const titles: string[] = [];
  const seenPanels = new Set<Element>();
  const candidates = root.querySelectorAll("h2, section.panel, .panel, [data-headline-card]");
  for (const element of Array.from(candidates)) {
    if (hiddenOrCollapsed(element, root)) continue;
    if (element.tagName === "H2") {
      const owner = element.closest("section.panel, .panel, [data-headline-card]");
      if (owner !== null && root.contains(owner)) seenPanels.add(owner);
      titles.push(text(element));
      continue;
    }
    // A panel element: counted through its own level-2 heading when it has one.
    const ownHeading = Array.from(element.querySelectorAll("h2")).find(
      (h) => h.closest("section.panel, .panel, [data-headline-card]") === element,
    );
    if (ownHeading === undefined && !seenPanels.has(element)) titles.push("(untitled)");
  }
  return titles;
}

/**
 * Assert the main content renders exactly the v69 panels of `screenId`
 * (`v69-rendered-panels.json` plus the approved title map), in order.
 * `values` supplies the selected read's values for dynamic titles.
 */
export function expectV69Panels(
  screenId: string,
  values: Record<string, string> = {},
  scope?: HTMLElement,
): void {
  const expected = expectedPanelTitles(screenId, values);
  const actual = renderedPanelTitles(scope);
  expect(actual, `panel structure of v69 screen "${screenId}"`).toEqual(expected);
}

/** The panel whose own heading is `title`, for in-panel gap assertions. */
export function panelTitled(title: string, scope?: HTMLElement): HTMLElement {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const heading = Array.from(root.querySelectorAll("h2")).find((h) => text(h) === title);
  const panel = heading?.closest<HTMLElement>("section.panel, .panel");
  if (panel === null || panel === undefined) throw new Error(`No panel titled "${title}".`);
  return panel;
}
