import { Link } from "react-router-dom";

import {
  siteDetailHref,
  siteEvidenceHref,
  siteFinancialsHref,
  siteFindingsHref,
  siteFoundationHref,
  siteHealthHref,
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
 * The canonical Site tab inventory, in v6.9's order with Health placed where
 * the decision puts it.
 */
export const CANONICAL_OPERATOR_SITE_TABS: OperatorSiteTab[] = [
  { label: "Overview", capability: true, href: siteDetailHref },
  { label: "Foundation", capability: true, href: siteFoundationHref },
  // S7-01b: gateway contact, last-reported gateway facts and the battery entry.
  { label: "Health", capability: true, href: (siteId) => siteHealthHref(siteId) },
  // T028: Performance (Dispatch its only subtab) and the scoped Findings index.
  { label: "Performance", capability: true, href: (siteId) => sitePerformanceHref(siteId) },
  { label: "Findings", capability: true, href: siteFindingsHref },
  // S6-03: Work, with Actions its only list (Incidents and Maintenance are not built).
  { label: "Work", capability: true, href: (siteId) => siteWorkHref(siteId) },
  // S4-02a: Overview (Finding bridge, price in use) and Assumptions.
  { label: "Financials", capability: true, href: (siteId) => siteFinancialsHref(siteId) },
  { label: "Evidence", capability: true, href: siteEvidenceHref },
];

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
  /** The label of the tab the reader is currently on. */
  current: string;
}

export function OperatorSiteTabs({ siteId, current }: OperatorSiteTabsProps) {
  if (siteId === undefined) {
    return null;
  }

  return (
    <nav className="site-tabs" aria-label={OPERATOR_SITE_TABS_LABEL}>
      <ol className="site-tabs__list">
        {OPERATOR_SITE_TABS.map((tab) => (
          <li className="site-tabs__item" key={tab.label}>
            <Link
              className="site-tabs__link"
              to={tab.href(siteId)}
              aria-current={tab.label === current ? "page" : undefined}
            >
              {tab.label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}
