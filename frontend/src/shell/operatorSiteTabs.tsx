import { Link } from "react-router-dom";

import { siteDetailHref, siteFoundationHref } from "./operatorSiteRoutes";

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
 * substrate. The substrate owns what a Site *is* - its read model, its derived
 * facts, and the components that present them - and both shells compose that.
 * A tab row is a shell's opinion about how its own workspace is divided, and
 * the Lab's Site view will carry a different one, so a substrate that owned
 * this would have to branch on which shell was rendering it.
 *
 * ## Two states, and the third one this row refuses
 *
 * A tab is a **destination** only when there is a route behind it that renders
 * a truthful surface for the identified site. Overview and Foundation are the
 * two the product has.
 *
 * The other six are **labelled in place**: the label renders, and nothing
 * else. Health, Performance, Findings, Work, Financials and Evidence are real
 * aspects of a Site in this product's own model, so naming them is true. What
 * is not true yet is that the product can show any of them, because M1 has no
 * accepted evidence, no performance read model, no findings, no work records
 * and no financial content.
 *
 * The state deliberately not used is disabled. A greyed-out tab says the
 * capability exists and is unavailable to you right now, which is a different
 * and false claim: these are not switched off, they are not built. So a
 * labelled-in-place tab is a plain `<span>` with no link, no button, no
 * `aria-disabled`, no title attribute, and no route registered behind it. A
 * click does nothing because there is nothing to click.
 *
 * ## Why this is not an ARIA tablist
 *
 * Each destination is a route, and following one is navigation rather than a
 * panel swap. `role="tab"` promises a `tabpanel` in the same document under
 * arrow-key control, which is not what happens here, so the row is a `<nav>`
 * of links and the current one carries `aria-current="page"`. It also keeps
 * the row clear of the `[role='tab']` affordance ban the Site page asserts.
 */

/** A tab with a route behind it. */
export interface OperatorSiteDestinationTab {
  label: string;
  kind: "destination";
  /** The address this tab opens for the identified site. */
  href: (siteId: string) => string;
}

/** A tab that names a real aspect of a Site the product cannot yet show. */
export interface OperatorSiteLabelledTab {
  label: string;
  kind: "labelled_in_place";
}

export type OperatorSiteTab =
  | OperatorSiteDestinationTab
  | OperatorSiteLabelledTab;

/**
 * The operator Site tab row, in v6.9's order.
 *
 * A tab moves from `labelled_in_place` to `destination` in the slice that
 * gives it content, and never before: the move is what makes the label a
 * promise the product can keep.
 */
export const OPERATOR_SITE_TABS: OperatorSiteTab[] = [
  { label: "Overview", kind: "destination", href: siteDetailHref },
  { label: "Foundation", kind: "destination", href: siteFoundationHref },
  { label: "Health", kind: "labelled_in_place" },
  { label: "Performance", kind: "labelled_in_place" },
  { label: "Findings", kind: "labelled_in_place" },
  { label: "Work", kind: "labelled_in_place" },
  { label: "Financials", kind: "labelled_in_place" },
  { label: "Evidence", kind: "labelled_in_place" },
];

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
            {tab.kind === "destination" ? (
              <Link
                className="site-tabs__link"
                to={tab.href(siteId)}
                aria-current={tab.label === current ? "page" : undefined}
              >
                {tab.label}
              </Link>
            ) : (
              <span className="site-tabs__label">{tab.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
