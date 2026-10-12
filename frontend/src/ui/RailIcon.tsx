/**
 * V-01a round 2 (owner follow-up 2: "the mockup has icons"): the line icons
 * the v6.9 rail draws beside each root, copied from the mock's icon set
 * (24 x 24, 1.6 stroke, round caps). Decorative by construction: the rail link
 * beside it carries its visible label, which is its accessible name, so the
 * icon is hidden from assistive technology and never stands in for a word.
 */
const RAIL_ICON_PATHS = {
  site: "M3 21V7l9-4 9 4v14 M8 21v-5h8v5 M7 8v3 M12 7v4 M17 8v3",
  finding: "M12 3L2 21h20L12 3z M12 9v5 M12 17v1",
  lab: "M9 2v7L3 19q-1 3 3 3h12q4 0 3-3L15 9V2 M7 2h10 M7 15h10",
  book: "M3 4h7l2 2 2-2h7v16h-7l-2 2-2-2H3z M12 6v16",
  log: "M6 3h12v18H6z M9 8h6 M9 12h6 M9 16h4",
  clock: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 7v6l4 2",
} as const;

export type RailIconName = keyof typeof RAIL_ICON_PATHS;

export function RailIcon({ name }: { name: RailIconName }) {
  return (
    <svg
      className="nav-rail__icon"
      data-rail-icon={name}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={RAIL_ICON_PATHS[name]} />
    </svg>
  );
}
