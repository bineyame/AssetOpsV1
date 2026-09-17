import { NavLink } from "react-router-dom";

/**
 * The left navigation rail, as a real component.
 *
 * It renders the items it is given and owns none of them. That is the whole
 * point: the operator rail and the Simulator Lab rail are separate item sets
 * supplied by their own shells, and neither shell can reach the other's list
 * through this component. A rail that owned a default list would be a third
 * place where a destination could appear, and the one rule this navigation has
 * is that a destination appears only when a truthful route stands behind it.
 *
 * Nothing here is gated, because nothing here knows what a gate is. A shell
 * that must not show an item does not pass it.
 */
export interface NavRailItem {
  /** The route this item opens. */
  to: string;
  /** The visible label. */
  label: string;
  /** Whether the active match is exact, for a root path. */
  end?: boolean;
}

export interface NavRailProps {
  /** Names the landmark. Each shell's rail is a distinct landmark. */
  label: string;
  items: NavRailItem[];
}

export function NavRail({ label, items }: NavRailProps) {
  return (
    <nav className="nav-rail" aria-label={label}>
      <ul className="nav-rail__list">
        {items.map((item) => (
          <li key={item.to}>
            <NavLink className="nav-rail__link" to={item.to} end={item.end}>
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
