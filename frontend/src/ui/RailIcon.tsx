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
  // W1-UX-07: the remaining v6.9 root icons, for the unavailable rail roots.
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  asset: "M7 4h10v16H7z M10 1h4 M10 8h4 M10 12h4 M10 16h4",
  action: "M8 4h11v17H5V4h3 M9 2h6v4H9z M8 12l3 3 5-6",
  incident: "M12 3v10 M12 17v1 M4 3h16v18H4z",
  work: "M14 4a5 5 0 0 0-6 6L2 16l6 6 6-6a5 5 0 0 0 6-6l-4 4-5-5 3-5z",
  evidence: "M5 3h10l4 4v14H5z M14 3v5h5 M8 12h8 M8 16h6",
  money: "M12 2v20 M17 6H9a3 3 0 0 0 0 6h6a3 3 0 0 1 0 6H6",
  info: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 10v7 M12 7v1",
  gear: "M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M19 5l-2 2 M7 17l-2 2",
} as const;

export type RailIconName = keyof typeof RAIL_ICON_PATHS;

export function RailIcon({ name }: { name: RailIconName }) {
  return (
    <svg
      className="nav-rail__icon"
      width={18}
      height={18}
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
