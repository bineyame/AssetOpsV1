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
 * Two further rules close the "answer card without a panel class" route
 * (W1-F1 review finding 1):
 *
 *   - Leading allowlist. Between the page chrome (breadcrumbs, page heading,
 *     tabs and subtabs) and panel 1, only the v69 leading patterns may render:
 *     the status strip, a page refusal, metric cards, chips and the selected-part
 *     notice. Any other element there fails, whatever its class or heading level.
 *   - No stray sections. Anywhere in the main content, an `h3`-`h6`, `section`,
 *     `article`, `[role=region]`, `.card` or `.callout` must sit inside a v69
 *     panel or an allowed leading pattern. Former panels are merged into their
 *     owning panel's table, key values or one-line note; they are never rebuilt
 *     as free-standing h3 subsections.
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

const PANEL_SELECTOR = "section.panel, .panel, [data-headline-card]";
/** Chrome: navigation, the page header and the Site date-bar slot (W2-04 Run-7 date-bar ruling). */
const CHROME_SELECTOR = "nav, header.page-header, .site-date-bar";
/**
 * The only v69 patterns permitted between the chrome and panel 1. W1-F2 added
 * `.v69-objective`, the mock's `.objective` line between status and cards. W4-03 u6b ruling 3 adds the canonical mini
 * Finding's `[data-analysis-helper]`: one noninteractive line directly after the section row, a ruled addition.
 */
const LEADING_SELECTOR =
  ".status-strip, [data-page-refusal], .v69-mheader, .v69-cards, .v69-chips, [data-selected-part-missing], [data-selected-part-chip], .v69-objective, [data-analysis-helper], " +

  // W3-03 run 2: the v69 `portfolio` screen's own three leading rows (context line, five value cards, pulse).
  ".portfolio-v2 > .portfolio-context, .portfolio-v2 > .value-grid, .portfolio-v2 > .portfolio-pulse";
/** Section-like elements that must not render outside a panel or leading pattern. */
const STRAY_SELECTOR = "h3, h4, h5, h6, section, article, [role=region], .card, .callout";

function describe(element: Element): string {
  const tag = element.tagName.toLowerCase();
  const cls = element.getAttribute("class");
  const label = text(element).slice(0, 60);
  return `<${tag}${cls ? ` class="${cls}"` : ""}> "${label}"`;
}

function firstPanel(root: Element): Element | null {
  for (const element of Array.from(root.querySelectorAll(`h2, ${PANEL_SELECTOR}`))) {
    if (hiddenOrCollapsed(element, root)) continue;
    if (element.tagName === "H2") return element.closest(PANEL_SELECTOR) ?? element;
    return element;
  }
  return null;
}

/**
 * Elements rendered before panel 1 that are neither page chrome nor an allowed
 * v69 leading pattern. Empty, hidden and collapsed elements are ignored.
 */
export function leadingIntruders(scope?: HTMLElement): string[] {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const panel = firstPanel(root);
  if (panel === null) return [];
  const intruders: string[] = [];
  for (let node: Element | null = panel; node !== null && node !== root; node = node.parentElement) {
    for (let sibling = node.previousElementSibling; sibling !== null; sibling = sibling.previousElementSibling) {
      if (hiddenOrCollapsed(sibling, root)) continue;
      if (sibling.matches(CHROME_SELECTOR) || sibling.matches(LEADING_SELECTOR)) continue;
      if (text(sibling) === "" && sibling.querySelector("img, svg, input, select, button") === null) continue;
      intruders.unshift(describe(sibling));
    }
  }
  return intruders;
}

/** Section-like elements outside every panel, leading pattern and chrome. */
export function strayOutsidePanels(scope?: HTMLElement): string[] {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const container = `${PANEL_SELECTOR}, ${LEADING_SELECTOR}, ${CHROME_SELECTOR}`;
  return Array.from(root.querySelectorAll(STRAY_SELECTOR))
    .filter((element) => !element.matches(PANEL_SELECTOR))
    .filter((element) => !hiddenOrCollapsed(element, root))
    .filter((element) => {
      const owner = element.closest(container);
      return owner === null || !root.contains(owner) || owner === root;
    })
    .map(describe);
}

/** Trailing or between-panel notes the v69 mock allows outside a panel. */
const ALLOWED_BETWEEN_SELECTOR = ".notice, .note, [data-readiness-scope], [data-page-refusal]";

/**
 * Content inside a status strip that is not a one-line `status-strip__*` part:
 * blocks, paragraphs and headings. The strip is a single line of chips and links.
 */
export function stripIntruders(scope?: HTMLElement): string[] {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const found: string[] = [];
  for (const strip of Array.from(root.querySelectorAll(".status-strip"))) {
    if (hiddenOrCollapsed(strip, root)) continue;
    for (const element of Array.from(strip.querySelectorAll("h1, h2, h3, h4, h5, h6, p, div, ul, ol, table, section"))) {
      if (hiddenOrCollapsed(element, root)) continue;
      if (text(element) === "") continue;
      const cls = element.getAttribute("class") ?? "";
      if (/(^|\s)status-strip__/.test(cls)) continue;
      found.push(describe(element));
    }
  }
  return found;
}

/**
 * Non-empty content blocks that are siblings of a panel (so sit between or
 * after panels) and are neither a panel, a wrapper of panels, chrome, a leading
 * pattern nor an allowed note.
 */
export function strayBetweenPanels(scope?: HTMLElement): string[] {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const found = new Set<Element>();
  const panels = Array.from(root.querySelectorAll(PANEL_SELECTOR)).filter(
    (panel) => panel.parentElement !== null && panel.parentElement.closest(PANEL_SELECTOR) === null,
  );
  for (const panel of panels) {
    const parent = panel.parentElement;
    if (parent === null) continue;
    for (const sibling of Array.from(parent.children)) {
      if (sibling === panel || found.has(sibling)) continue;
      if (hiddenOrCollapsed(sibling, root)) continue;
      if (sibling.matches(PANEL_SELECTOR) || sibling.querySelector(PANEL_SELECTOR) !== null) continue;
      if (sibling.matches(CHROME_SELECTOR) || sibling.matches(LEADING_SELECTOR) || sibling.matches(ALLOWED_BETWEEN_SELECTOR)) continue;
      if (sibling.closest(".status-strip") !== null) continue;
      if (text(sibling) === "" && sibling.querySelector("img, svg, input, select, button") === null) continue;
      found.add(sibling);
    }
  }
  return Array.from(found).map(describe);
}
/** The panel titles a screen actually renders in its main content, in DOM order. */
export function renderedPanelTitles(scope?: HTMLElement): string[] {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const titles: string[] = [];
  const seenPanels = new Set<Element>();
  const candidates = root.querySelectorAll(`h2, ${PANEL_SELECTOR}`);
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
  expect(leadingIntruders(scope), `elements before panel 1 of v69 screen "${screenId}"`).toEqual([]);
  expect(strayOutsidePanels(scope), `sections outside the panels of v69 screen "${screenId}"`).toEqual([]);
  expect(stripIntruders(scope), `blocks inside the status strip of v69 screen "${screenId}"`).toEqual([]);
  expect(strayBetweenPanels(scope), `content blocks between panels of v69 screen "${screenId}"`).toEqual([]);
}

/** The panel whose own heading is `title`, for in-panel gap assertions. */
export function panelTitled(title: string, scope?: HTMLElement): HTMLElement {
  const root = scope ?? document.querySelector("main") ?? document.body;
  const heading = Array.from(root.querySelectorAll("h2")).find((h) => text(h) === title);
  const panel = heading?.closest<HTMLElement>("section.panel, .panel");
  if (panel === null || panel === undefined) throw new Error(`No panel titled "${title}".`);
  return panel;
}

/**
 * Non-vacuity proof for a rendered route: plants an extra titled panel before
 * panel 1 of the current screen and asserts the guard rejects it, then removes
 * the plant so the screen is left as rendered.
 */
export function expectPlantedPanelRejected(screenId: string): void {
  const first = document.querySelector("main section.panel");
  expect(first, "the screen renders a panel 1 to plant before").not.toBeNull();
  const plant = document.createElement("section");
  plant.className = "panel";
  plant.innerHTML = "<h2>Planted extra panel</h2>";
  first!.parentElement!.insertBefore(plant, first);
  try {
    expect(() => expectV69Panels(screenId)).toThrow();
  } finally {
    plant.remove();
  }
  expectV69Panels(screenId);
}
