import { Fragment, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";

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
 *
 * W1-UX-07 (`D-2026-10-17-w1-rail`): an item is either a live destination or
 * an unavailable root. The model is a discriminated union, so an unavailable
 * item cannot carry `to`: it renders as text in a list item, muted, with the
 * visible status `Not available yet`, and it has no link, route, handler or
 * tab stop. Its accessible name is its label and that status. It is not a
 * disabled control (no `aria-disabled`, no disabled button): there is nothing
 * to switch on, only a place the product does not have yet.
 */
interface NavRailItemBase {
  /** The visible label. */
  label: string;
  /**
   * The rail group this item belongs to (OPERATIONS, INTELLIGENCE, ...).
   * Items render in the order given; a group header renders once, before the
   * first item of its group, so a group is headed even when every item in it
   * is unavailable. Ungrouped items render with no header.
   */
  group?: string;
  /** V-01a round 2: the root's line icon, decorative beside the label. */
  icon?: RailIconName;
}

/** A destination: a registered route renders a truthful surface behind it. */
export interface NavRailLiveItem extends NavRailItemBase {
  kind?: "live";
  /** The route this item opens. */
  to: string;
  /** Whether the active match is exact, for a root path. */
  end?: boolean;
}

/** A root the product has no truthful cross-site destination for yet. */
export interface NavRailUnavailableItem extends NavRailItemBase {
  kind: "unavailable";
  to?: never;
  end?: never;
}

export type NavRailItem = NavRailLiveItem | NavRailUnavailableItem;

/** The plain status every unavailable root shows; never colour alone. */
export const NAV_RAIL_UNAVAILABLE_STATUS = "Not available yet";

export interface NavRailProps {
  /** Names the landmark. Each shell's rail is a distinct landmark. */
  label: string;
  items: NavRailItem[];
  /**
   * W5-02c K4a (`.agent/W5-02c-K4-preflight-rulings.md` rulings 1-2): the label of the live root a shell selects for a
   * route whose path is not under that root's `to` (a Site Action detail selects `Actions`, v69 `rail()` root rule).
   * When set, every live item renders as a plain `Link` with the same href, icon and order, and only the named item
   * carries `active` and `aria-current="page"`. When absent or null, `NavLink` path matching applies unchanged.
   */
  activeLabel?: string | null;
}

function itemKey(item: NavRailItem): string {
  return item.kind === "unavailable" ? `unavailable:${item.label}` : item.to;
}

function railItem(item: NavRailItem, activeLabel: string | null): ReactNode {
  if (item.kind === "unavailable") {
    return (
      <li
        className="nav-rail__unavailable"
        aria-label={`${item.label}, ${NAV_RAIL_UNAVAILABLE_STATUS}`}
        data-rail-unavailable={item.label}
      >
        {item.icon === undefined ? null : <RailIcon name={item.icon} />}
        <span className="nav-rail__text">
          <span className="nav-rail__label">{item.label}</span>
          <span className="nav-rail__status" data-rail-status="unavailable">
            {NAV_RAIL_UNAVAILABLE_STATUS}
          </span>
        </span>
      </li>
    );
  }
  if (activeLabel !== null) {
    const active = item.label === activeLabel;
    return (
      <li>
        <Link
          className={active ? "nav-rail__link active" : "nav-rail__link"}
          to={item.to}
          aria-current={active ? "page" : undefined}
        >
          {item.icon === undefined ? null : <RailIcon name={item.icon} />}
          <span className="nav-rail__label">{item.label}</span>
        </Link>
      </li>
    );
  }
  return (
    <li>
      <NavLink className="nav-rail__link" to={item.to} end={item.end}>
        {item.icon === undefined ? null : <RailIcon name={item.icon} />}
        <span className="nav-rail__label">{item.label}</span>
      </NavLink>
    </li>
  );
}

export function NavRail({ label, items, activeLabel = null }: NavRailProps) {
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
              <Fragment key={itemKey(item)}>{railItem(item, activeLabel)}</Fragment>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
