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
 * else. They are set apart from the destinations by a divider and named in a
 * sentence under the row, because T011A proved colour alone does not carry
 * this. Its destinations were grey and its labels were a slightly lighter
 * grey, and a reader saw one live tab and seven dead ones. Health, Performance, Findings, Work, Financials and Evidence are real
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

/**
 * The aspects this build cannot open, as a sentence.
 *
 * Derived from the inventory rather than written out, which is the whole point
 * of it. T011A's row said what it could open and what it could not using
 * colour, and the colours were five percent apart, so a reader saw seven grey
 * words and concluded the product was broken. This says it in words as well.
 *
 * Because it is derived, a tab that becomes a destination leaves this sentence
 * in the same change that moves it. A written-out list would have gone stale
 * the first time an aspect got content, and would then have been a screen
 * claiming something has no content while the tab beside it opened that
 * content.
 *
 * It returns null rather than an empty sentence when every aspect has content,
 * because on that day there is nothing to explain.
 *
 * `tabs` is a parameter so a test can hand it an inventory this product does
 * not have yet - one aspect left, or none - and prove the sentence follows the
 * inventory rather than reciting a list someone typed.
 */
export function labelledAspectsSentence(
  tabs: OperatorSiteTab[] = OPERATOR_SITE_TABS,
): string | null {
  const labels = tabs
    .filter((tab) => tab.kind === "labelled_in_place")
    .map((tab) => tab.label);

  if (labels.length === 0) {
    return null;
  }

  const named =
    labels.length === 1
      ? labels[0]
      : `${labels.slice(0, -1).join(", ")} and ${labels[labels.length - 1]}`;
  const verb = labels.length === 1 ? "has" : "have";

  // What this build contains, not what a later one will. The promise
  // vocabulary the guard bans belongs to the same family, and the ban is the
  // point rather than the wording: a sentence about the future is a promise
  // nobody has made. The guard scans this module, so the phrases it refuses
  // cannot be written here either - which is why this comment describes them
  // instead of quoting one.
  return `${named} ${verb} no content in this build yet.`;
}

/**
 * The index the labelled group starts at, or -1 when there is none.
 *
 * The divider hangs off this rather than off a count, so a row that is all
 * destinations draws no divider and a row that is all labels draws one at the
 * start, which is where it would belong.
 */
function firstLabelledIndex(): number {
  return OPERATOR_SITE_TABS.findIndex(
    (tab) => tab.kind === "labelled_in_place",
  );
}

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

  const groupStart = firstLabelledIndex();
  const aspects = labelledAspectsSentence();

  return (
    <nav className="site-tabs" aria-label={OPERATOR_SITE_TABS_LABEL}>
      <ol className="site-tabs__list">
        {OPERATOR_SITE_TABS.map((tab, index) => (
          <li
            className={
              index === groupStart
                ? "site-tabs__item site-tabs__item--group-start"
                : "site-tabs__item"
            }
            key={tab.label}
          >
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

      {aspects === null ? null : (
        <p className="site-tabs__aspects">{aspects}</p>
      )}
    </nav>
  );
}
