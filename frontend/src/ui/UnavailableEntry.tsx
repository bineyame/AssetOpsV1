/**
 * W1-F5b (`D-2026-10-17-f5-subtabs-and-contact`): an unbuilt entry in a named v69 in-page tab row or lens-chip
 * row. It reuses the rail's unavailable-entry semantics (W1-UX-07): readable, muted text in a list item, with
 * the visible and accessible status "Not available yet". It is not a control: no `href`, `to`, handler,
 * pointer affordance, tab stop, `disabled` or `aria-disabled`, so Enter and Space have nothing to activate.
 *
 * The status text lives only in this file (reviewed exemption in `tools/checks/missing-claim-scan.mjs`): it
 * describes a destination this build has not made, not a missing claim about a site.
 */
const IN_PAGE_UNAVAILABLE_STATUS = "Not available yet";

/** One unbuilt tab in a `.site-tabs` row, in the mock's position. */
export function UnavailableTab({ label }: { label: string }) {
  return (
    <li
      className="site-tabs__item site-tabs__item--unavailable"
      aria-label={`${label}, ${IN_PAGE_UNAVAILABLE_STATUS}`}
      data-tab-unavailable={label}
    >
      {/* One text node, so the product-vocabulary scan reads the mock label with its status (Scenarios is glossed
          only in this exact form, D-2026-10-17-f5-subtabs-and-contact). */}
      <span className="site-tabs__status" data-tab-status="unavailable">
        {`${label} · ${IN_PAGE_UNAVAILABLE_STATUS}`}
      </span>
    </li>
  );
}

/** One unbuilt lens chip in a `.v69-chips` row. */
export function UnavailableChip({ label }: { label: string }) {
  return (
    <li
      className="v69-chip v69-chip--unavailable"
      aria-label={`${label}, ${IN_PAGE_UNAVAILABLE_STATUS}`}
      data-chip-unavailable={label}
    >
      {label} <span className="v69-chip__status" data-chip-status="unavailable">{IN_PAGE_UNAVAILABLE_STATUS}</span>
    </li>
  );
}

/**
 * W2-05a: one unbuilt in-page link entry of a v69 attention row (for example an Action the mock links to that this
 * build cannot open), in the mock link's position. Same semantics as a tab or chip: a muted list item, not a control.
 */
export function UnavailableLinkEntry({ label }: { label: string }) {
  return (
    <ul className="v69-unavailable-links">
      <li className="v69-unavailable-link" aria-label={`${label}, ${IN_PAGE_UNAVAILABLE_STATUS}`} data-link-unavailable={label}>
        {`${label} · ${IN_PAGE_UNAVAILABLE_STATUS}`}
      </li>
    </ul>
  );
}
