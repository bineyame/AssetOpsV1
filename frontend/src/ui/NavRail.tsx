import { NavLink } from "react-router-dom";

import { RailIcon, type RailIconName } from "./RailIcon";

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
  /**
   * The rail group this item belongs to (T028: OPERATE, INTELLIGENCE). Items
   * render in the order given; a group header renders once, before the first
   * item of its group, so a one-item group is still headed. Ungrouped items
   * render with no header.
   */
  group?: string;
  /** V-01a round 2: the root's line icon, decorative beside the label. */
  icon?: RailIconName;
}

export interface NavRailProps {
  /** Names the landmark. Each shell's rail is a distinct landmark. */
  label: string;
  items: NavRailItem[];
}

export function NavRail({ label, items }: NavRailProps) {
  const sections: { group: string | undefined; items: NavRailItem[] }[] = [];
  for (const item of items) {
    const last = sections[sections.length - 1];
    if (last !== undefined && last.group === item.group) {
      last.items.push(item);
    } else {
      sections.push({ group: item.group, items: [item] });
    }
  }
  return (
    <nav className="nav-rail" aria-label={label}>
      {sections.map((section, index) => (
        <div className="nav-rail__group" key={`${section.group ?? ""}-${index}`}>
          {section.group === undefined ? null : (
            <p className="nav-rail__group-label" data-rail-group={section.group}>
              {section.group}
            </p>
          )}
          <ul className="nav-rail__list">
            {section.items.map((item) => (
              <li key={item.to}>
                <NavLink className="nav-rail__link" to={item.to} end={item.end}>
                  {item.icon === undefined ? null : <RailIcon name={item.icon} />}
                  <span className="nav-rail__label">{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
