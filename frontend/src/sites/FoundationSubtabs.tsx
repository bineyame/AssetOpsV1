/**
 * The Foundation subtab row.
 *
 * v6.9 line 2117 gives Foundation five subtabs:
 * `Definition | Topology | Controls | Changes | Readiness`. This renders three
 * of them, per `D-2026-10-02-rendered-tabs-per-capability`: the rendered set
 * holds only subtabs this build has a truthful section for, and "labelled in
 * place" is not used in operator views.
 *
 * ## Why Changes and Readiness are not here, in any state
 *
 * `Changes` is a real intervention-and-change-effect capability (v6.9 lines
 * 2149 and 2225-2228) with no configuration-change model behind it yet; it
 * joins this row at T034 and not before. `Readiness` is not rendered at all:
 * claim readiness lives on Site > Evidence only.
 *
 * ## Why these are links
 *
 * Definition, Topology and Controls each have content on this page, so each is
 * a link to the section that holds it. They are fragment links rather than
 * routes: the content is all on one screen, so a route would be a second
 * address for something already here, and a client-side tab that swapped
 * panels would hide content that has no reason to be hidden.
 *
 * ## Why this does not look like the tab row above it
 *
 * A tab row says "this swaps what you are looking at". This says "this is
 * further down the same page". T013 first rendered it with the tab classes,
 * and the Architect's UI/UX ruling was that two stacked rows in one treatment
 * ask a reader to infer two different behaviours from one appearance. So it is
 * `.section-nav`: smaller, lighter, a contents line rather than a switcher,
 * with no active state, because nothing is "current" when every section is on
 * the page at once.
 */

/** The id of the section a subtab opens. */
export interface FoundationSubtabSection {
  label: string;
  kind: "section";
  /** The element id this subtab scrolls to. */
  targetId: string;
}

export type FoundationSubtab = FoundationSubtabSection;

/** Where each rendered section lives, so the row and the panels agree. */
export const FOUNDATION_DEFINITION_ID = "foundation-definition-heading";
export const FOUNDATION_TOPOLOGY_ID = "foundation-topology-heading";
export const FOUNDATION_CONTROLS_ID = "foundation-controls-heading";

/**
 * The row, in v6.9's order with `Changes` and `Readiness` filtered out.
 *
 * One definition, consumed by the rendering and by the tests, so a subtab
 * cannot be added to the screen without appearing here first.
 */
export const FOUNDATION_SUBTABS: FoundationSubtab[] = [
  { label: "Definition", kind: "section", targetId: FOUNDATION_DEFINITION_ID },
  { label: "Topology", kind: "section", targetId: FOUNDATION_TOPOLOGY_ID },
  { label: "Controls", kind: "section", targetId: FOUNDATION_CONTROLS_ID },
];

/** The accessible name of the row. */
export const FOUNDATION_SUBTABS_LABEL = "Foundation sections";

export function FoundationSubtabs() {
  return (
    <nav className="section-nav" aria-label={FOUNDATION_SUBTABS_LABEL}>
      <p className="section-nav__label">On this page</p>
      <ol className="section-nav__list">
        {FOUNDATION_SUBTABS.map((subtab) => (
          <li className="section-nav__item" key={subtab.label}>
            <a className="section-nav__link" href={`#${subtab.targetId}`}>
              {subtab.label}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
