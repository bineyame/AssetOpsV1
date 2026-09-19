/**
 * The Foundation subtab row.
 *
 * v6.9 line 2117 gives Foundation five subtabs:
 * `Definition | Topology | Controls | Changes | Readiness`. This renders four
 * of them, and the missing one is the point.
 *
 * ## Why Changes is not here, in any state
 *
 * `Changes` is not the mockup's `Version History` under a different name.
 * v6.9 lines 2149 and 2225-2228 make it a real intervention-and-change-effect
 * capability: what was altered, by whom, and what it did. No configuration-
 * change model exists in this product, so there is nothing to label, and the
 * T008 checkpoint explicitly removed this territory rather than leaving it as
 * chrome. A `Changes` tab labelled in place would name a capability whose
 * eventual meaning is not the one a reader would assume, which is worse than
 * naming nothing.
 *
 * ## Why three of these are links and one is not
 *
 * Definition, Topology and Controls each have content on this page, so each is
 * a link to the section that holds it. They are fragment links rather than
 * routes: the content is all on one screen, so a route would be a second
 * address for something already here, and a client-side tab that swapped
 * panels would hide content that has no reason to be hidden.
 *
 * Readiness is labelled in place. Evidence readiness is a canonical aspect of
 * a Foundation, so naming it is true, but this build has no readiness model
 * and therefore no section for it. It gets no link, no button, no route, no
 * disabled state, and deliberately no empty panel to point at - a section
 * heading with nothing under it is the layout form of a fabricated value.
 *
 * This is the same two-state treatment the operator Site tab row uses one
 * level up, and it renders with the same vocabulary classes, because it is the
 * same pattern: things you can open, and things this build can only name.
 */

/** The id of the section a subtab opens. */
export interface FoundationSubtabSection {
  label: string;
  kind: "section";
  /** The element id this subtab scrolls to. */
  targetId: string;
}

/** A canonical aspect with no content in this build. */
export interface FoundationSubtabLabel {
  label: string;
  kind: "labelled_in_place";
}

export type FoundationSubtab = FoundationSubtabSection | FoundationSubtabLabel;

/** Where each rendered section lives, so the row and the panels agree. */
export const FOUNDATION_DEFINITION_ID = "foundation-definition-heading";
export const FOUNDATION_TOPOLOGY_ID = "foundation-topology-heading";
export const FOUNDATION_CONTROLS_ID = "foundation-controls-heading";

/**
 * The row, in v6.9's order with `Changes` filtered out.
 *
 * One definition, consumed by the rendering and by the tests, so a subtab
 * cannot be added to the screen without appearing here first.
 */
export const FOUNDATION_SUBTABS: FoundationSubtab[] = [
  { label: "Definition", kind: "section", targetId: FOUNDATION_DEFINITION_ID },
  { label: "Topology", kind: "section", targetId: FOUNDATION_TOPOLOGY_ID },
  { label: "Controls", kind: "section", targetId: FOUNDATION_CONTROLS_ID },
  { label: "Readiness", kind: "labelled_in_place" },
];

/** The accessible name of the row. */
export const FOUNDATION_SUBTABS_LABEL = "Foundation sections";

export function FoundationSubtabs() {
  const groupStart = FOUNDATION_SUBTABS.findIndex(
    (subtab) => subtab.kind === "labelled_in_place",
  );

  return (
    <nav className="site-tabs" aria-label={FOUNDATION_SUBTABS_LABEL}>
      <ol className="site-tabs__list">
        {FOUNDATION_SUBTABS.map((subtab, index) => (
          <li
            className={
              index === groupStart
                ? "site-tabs__item site-tabs__item--group-start"
                : "site-tabs__item"
            }
            key={subtab.label}
          >
            {subtab.kind === "section" ? (
              <a className="site-tabs__link" href={`#${subtab.targetId}`}>
                {subtab.label}
              </a>
            ) : (
              <span className="site-tabs__label">{subtab.label}</span>
            )}
          </li>
        ))}
      </ol>

      <p className="site-tabs__aspects">
        Readiness has no content in this build yet.
      </p>
    </nav>
  );
}
