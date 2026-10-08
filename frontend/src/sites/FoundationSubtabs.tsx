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
 * ## What is not here, in any state
 *
 * `Change & effect` (the mock's `Changes`) is an intervention-and-change-effect
 * capability with no supported model behind it; it is absent, never disabled
 * and never labelled in place (D-2026-10-02-rendered-tabs-per-capability).
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
 * The row, in v6.9's order with `Change & effect` filtered out.
 *
 * One definition, consumed by the rendering, the route table and the tests, so
 * a view cannot be added to the screen without appearing here first.
 */
export const FOUNDATION_SUBTABS: FoundationSubtab[] = [
  { label: "Site model", view: "model", segment: "" },
  { label: "Single line diagram", view: "sld", segment: "sld" },
  { label: "Readiness", view: "readiness", segment: "readiness" },
];

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
  current: FoundationView;
  /** The address of a view, carrying the selected period. Built by the shell. */
  hrefFor: (view: FoundationView) => string;
}

export function FoundationSubtabs({ current, hrefFor }: FoundationSubtabsProps) {
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
      </ol>
    </nav>
  );
}
