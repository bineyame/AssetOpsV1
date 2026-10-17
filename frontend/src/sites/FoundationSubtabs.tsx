import { Link } from "react-router-dom";

/**
 * The Foundation view row (S1-03).
 *
 * v6.9 gives Foundation a view row: `Site model | Single line diagram |
 * Readiness | Change & effect`. Architect decision
 * `D-2026-10-08-s1-foundation-organization` (section 2) revises the earlier D2
 * ruling: an imported Site renders the first three as real, direct-linkable
 * views in the mock's order, all reading the same selected `at` period.
 *
 * ## Change & effect (W1-F5b)
 *
 * `D-2026-10-17-f5-subtabs-and-contact` puts the mock's fourth entry back: a
 * live link to the existing Foundation Changes route (S6-01b), shown on the
 * Changes screens and their sibling views. It is not a Foundation view of the
 * selected period, so it is not in `FOUNDATION_SUBTABS` and never reaches the
 * view frame; `Changes` as a label stays absent.
 *
 * `Readiness` here is configuration readiness (S1-02): bindings, roles and
 * Foundation gaps. Claim and capability readiness stays on Site > Evidence.
 *
 * ## Who gets the row
 *
 * Only a Site imported into the persisted store. A Site still read from its
 * original document has no stored Foundation, binding set or snapshot, so a
 * Readiness or SLD view of it would imply records it does not have; it keeps
 * its single legacy page and renders no row.
 *
 * The superseded `Definition | Topology | Controls` contents row is gone: those
 * are in-page headings now, never a second tab-like row competing with this.
 */

export type FoundationView = "model" | "sld" | "readiness";

export interface FoundationSubtab {
  label: string;
  view: FoundationView;
  /** The path segment under `/sites/{code}/foundation`; empty for the default view. */
  segment: string;
}

/**
 * The period views, in v6.9's order; `FOUNDATION_CHANGE_SUBTAB` follows them in the row.
 *
 * One definition, consumed by the rendering, the route table and the tests, so
 * a view cannot be added to the screen without appearing here first.
 */
export const FOUNDATION_SUBTABS: FoundationSubtab[] = [
  { label: "Site model", view: "model", segment: "" },
  { label: "Single line diagram", view: "sld", segment: "sld" },
  { label: "Readiness", view: "readiness", segment: "readiness" },
];

/** The row's fourth entry: the existing Foundation Changes route, not a period view. */
export const FOUNDATION_CHANGE_SUBTAB = { label: "Change & effect", segment: "changes" } as const;

/** The current entry of the row: a view, or the Change & effect entry on a Changes screen. */
export type FoundationRowEntry = FoundationView | "changes";

/** The accessible name of the row. */
export const FOUNDATION_SUBTABS_LABEL = "Foundation views";

/** The view a path segment names, or null for a segment that is not a view. */
export function foundationViewFor(segment: string | undefined): FoundationView | null {
  const match = FOUNDATION_SUBTABS.find((subtab) => subtab.segment === (segment ?? ""));
  return match === undefined ? null : match.view;
}

export function foundationViewLabel(view: FoundationView): string {
  return FOUNDATION_SUBTABS.find((subtab) => subtab.view === view)?.label ?? "";
}

export interface FoundationSubtabsProps {
  current: FoundationRowEntry;
  /** The address of a view, carrying the selected period. Built by the shell. */
  hrefFor: (view: FoundationView) => string;
  /** The mock gives Change & effect to the mini-grid row only; a cold-room Site's row has the three views. */
  withChanges?: boolean;
}

/** The Changes route, beside the Site model address (`/sites/{code}/foundation/changes`); it takes no period. */
function changesHref(hrefFor: (view: FoundationView) => string): string {
  return `${hrefFor("model").split("?")[0].replace(/\/$/, "")}/${FOUNDATION_CHANGE_SUBTAB.segment}`;
}

export function FoundationSubtabs({ current, hrefFor, withChanges = true }: FoundationSubtabsProps) {
  return (
    <nav className="site-tabs site-subtabs foundation-views" aria-label={FOUNDATION_SUBTABS_LABEL}>
      <ol className="site-tabs__list">
        {FOUNDATION_SUBTABS.map((subtab) => (
          <li className="site-tabs__item" key={subtab.view}>
            <Link
              className="site-tabs__link"
              to={hrefFor(subtab.view)}
              data-foundation-view={subtab.view}
              aria-current={subtab.view === current ? "page" : undefined}
            >
              {subtab.label}
            </Link>
          </li>
        ))}
        {withChanges ? (
        <li className="site-tabs__item">
          <Link
            className="site-tabs__link"
            to={changesHref(hrefFor)}
            data-foundation-view="changes"
            aria-current={current === "changes" ? "page" : undefined}
          >
            {FOUNDATION_CHANGE_SUBTAB.label}
          </Link>
        </li>
        ) : null}
      </ol>
    </nav>
  );
}

/** The path segment of a view under `/sites/{code}/foundation` (empty for Site model). */
export function foundationViewSegment(view: FoundationView): string {
  return FOUNDATION_SUBTABS.find((subtab) => subtab.view === view)?.segment ?? "";
}
