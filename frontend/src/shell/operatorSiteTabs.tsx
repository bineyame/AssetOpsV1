import { RangeLink as Link } from "../ui/RangeLink";

import { useCurrentTabInView } from "../ui/useCurrentTabInView";
import "../ui/mock-deviation.css";

import {
  siteDetailHref,
  siteEvidenceHref,
  siteFinancialsHref,
  siteFoundationHref,
  sitePerformanceHref,
  siteWorkHref,
} from "./operatorSiteRoutes";

/**
 * The operator Site tab row: one definition, consumed by the rendering and by
 * the tests.
 *
 * The vocabulary is v6.9's operator Site tab set at lines 464 and 615, not the
 * mockup's. `ScreenMockups.png` screen 2 draws a tab row carrying
 * `Configuration`, `Devices`, `Gateway`, `Ingestion`, `Events` and `Logs`;
 * that is layout evidence that a Site page has a tab row, and it is the
 * Simulator Lab's run vocabulary rather than the operator product's. None of
 * those six is an operator Site tab here.
 *
 * This inventory lives in the operator shell and not in the shared Site
 * substrate. The substrate owns what a Site *is*; a tab row is a shell's
 * opinion about how its own workspace is divided, and the Lab's Site view will
 * carry a different one.
 *
 * ## One inventory, filtered by capability
 *
 * `D-2026-10-02-rendered-tabs-per-capability`: the canonical inventory below
 * defines ownership and future placement and lists all eight aspects in
 * canonical order; the RENDERED row holds only the entries whose capability
 * exists in this build. "Meaningful" is decided per capability, not per site:
 * once a capability exists its tab renders on every applicable site, and a
 * site without the evidence shows the gap inside the tab.
 *
 * Each tab is therefore a **destination** with a route behind it, or it is
 * not rendered. A later slice that gives an aspect a surface flips its
 * `capability` flag and registers the route; nothing else changes. The two
 * treatments this row does not use are disabled (a false claim that the
 * capability exists and is unavailable to you) and labelled in place, which is
 * not used in operator views at all.
 *
 * ## Why this is not an ARIA tablist
 *
 * Each destination is a route, and following one is navigation rather than a
 * panel swap. `role="tab"` promises a `tabpanel` in the same document under
 * arrow-key control, which is not what happens here, so the row is a `<nav>`
 * of links and the current one carries `aria-current="page"`. It also keeps
 * the row clear of the `[role='tab']` affordance ban the Site page asserts.
 */

/** An aspect of a Site, with the route that opens it once its capability exists. */
export interface OperatorSiteTab {
  label: string;
  /** Whether this build has a truthful surface for the aspect. */
  capability: boolean;
  /** The address this tab opens for the identified site. */
  href: (siteId: string) => string;
}

/**
 * IA-P P5 (spec §2.3, D-IAP.7, D-IAP.38 Q17): the Site's six tabs, in order. The paths keep today's segments (MD-IAP-8):
 * Operations opens `/work`, Setup opens `/foundation`. Health sits in Performance's section line, Uploads in
 * Evidence's, Changes and Assets in Setup's (`ui/SiteSections`). Findings leaves the row for the Findings home.
 */
export const CANONICAL_OPERATOR_SITE_TABS: OperatorSiteTab[] = [
  { label: "Overview", capability: true, href: siteDetailHref },
  // S6-03: Work, now Operations, with its Actions, Incidents and Maintenance lists.
  { label: "Operations", capability: true, href: (siteId) => siteWorkHref(siteId) },
  { label: "Performance", capability: true, href: (siteId) => sitePerformanceHref(siteId) },
  // S4-02a: Overview (Finding bridge, price in use) and Assumptions.
  { label: "Financials", capability: true, href: (siteId) => siteFinancialsHref(siteId) },
  { label: "Evidence", capability: true, href: siteEvidenceHref },
  { label: "Setup", capability: true, href: siteFoundationHref },
];

/** The six tab labels. */
export type OperatorSiteTabLabel = "Overview" | "Operations" | "Performance" | "Financials" | "Evidence" | "Setup";

/** The labels a frame may still name its page by: v6.9's eight, which map onto the six. */
export type LegacySiteTabLabel = "Foundation" | "Health" | "Findings" | "Work";

/**
 * IA-P P5 (spec §6 P5): the old-label map. Every frame's `current` goes through it, so a page named by its old tab
 * lights the new one. A Site Findings index (kept for a vertical whose alias has not shipped, MD-IAP-15) lights Evidence.
 */
export const SITE_TAB_OF: Record<OperatorSiteTabLabel | LegacySiteTabLabel, OperatorSiteTabLabel> = {
  Overview: "Overview",
  Foundation: "Setup",
  Health: "Performance",
  Performance: "Performance",
  Findings: "Evidence",
  Work: "Operations",
  Financials: "Financials",
  Evidence: "Evidence",
  Operations: "Operations",
  Setup: "Setup",
};

/** The tabs this build renders: the inventory filtered by capability. */
export const OPERATOR_SITE_TABS: OperatorSiteTab[] =
  CANONICAL_OPERATOR_SITE_TABS.filter((tab) => tab.capability);

/** The accessible name of the tab row landmark. */
export const OPERATOR_SITE_TABS_LABEL = "Site sections";

export interface OperatorSiteTabsProps {
  /**
   * The identity taken from the address. The row renders nothing when no site
   * is named: a tab row belongs to a subject, and without one every
   * destination would be an address with a hole in it.
   */
  siteId: string | undefined;
  /** The tab the reader is on, by its label or its old label (mapped through `SITE_TAB_OF`). */
  current: OperatorSiteTabLabel | LegacySiteTabLabel;
  /**
   * post-W6 W2-EV (R347 common mechanism): a domain Site's own destinations for
   * some tabs (EV Overview -> `/ev`, Evidence -> `/ev/evidence`, ...). Tabs not
   * named keep the canonical href. Never point a domain at the mini pages.
   */
  hrefs?: OperatorSiteTabHrefs;
  /**
   * post-W6 W2-EV: the selected read's window as a query (`?from=..&to=..&known_at=..`),
   * appended to every tab. Pass nothing (or "") without a loaded selected read.
   */
  search?: string;
}

/** post-W6 W2-EV: per-label href overrides for a domain Site. */
export type OperatorSiteTabHrefs = Partial<Record<OperatorSiteTabLabel, (siteId: string) => string>>;

/** post-W6 W2-EV: the address one tab opens, after overrides and the selected-window query. */
export function operatorSiteTabHref(tab: OperatorSiteTab, siteId: string, hrefs?: OperatorSiteTabHrefs, search?: string): string {
  const base = (hrefs?.[tab.label as OperatorSiteTabLabel] ?? tab.href)(siteId);
  if (!search) return base;
  const query = search.startsWith("?") ? search.slice(1) : search;
  if (query === "") return base;
  return `${base}${base.includes("?") ? "&" : "?"}${query}`;
}

export function OperatorSiteTabs({ siteId, current, hrefs, search }: OperatorSiteTabsProps) {
  const rowRef = useCurrentTabInView<HTMLElement>();
  const lit = SITE_TAB_OF[current];
  if (siteId === undefined) {
    return null;
  }

  return (
    <nav className="site-tabs site-tabs--site" aria-label={OPERATOR_SITE_TABS_LABEL} ref={rowRef}>
      <ol className="site-tabs__list">
        {OPERATOR_SITE_TABS.map((tab) => (
          <li className="site-tabs__item" key={tab.label}>
            <Link
              className="site-tabs__link"
              to={operatorSiteTabHref(tab, siteId, hrefs, search)}
              aria-current={tab.label === lit ? "page" : undefined}
            >
              {tab.label}
            </Link>
          </li>
        ))}
      </ol>
      {/* post-W6 W4 R333: up to 760 px the row wraps so every label stays visible (WCAG 2.2 reflow). The mock keeps
          one scrolling row, so the wrap is a proposed departure, labelled where it shows (the line is hidden wider). */}
      <p className="mock-deviation-line site-tabs__deviation" data-mock-deviation="R453">
        MOCK DEVIATION D2 (R453)
      </p>
    </nav>
  );
}
