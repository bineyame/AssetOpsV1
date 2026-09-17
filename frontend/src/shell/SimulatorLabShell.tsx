import type { ReactNode } from "react";

import { AppHeader, NavRail, type NavRailItem } from "../ui";

/**
 * The Simulator Lab's own shell chrome.
 *
 * Until this slice the Lab had no rail at all: its one destination was a link
 * in the workspace body, on the stated principle that chrome follows content
 * rather than announcing destinations that do not exist yet. That principle is
 * unchanged and this rail obeys it. What changed is that the Lab now has two
 * surfaces that render truthful content, so a rail can list them honestly.
 *
 * The rail lists exactly those two. The mockups draw the Lab rail with `Home`,
 * `Scenarios`, `Devices`, `Ingestion`, `Events`, `Library`, `Documentation` and
 * `Settings` beside them; none of those has a route that renders a truthful
 * surface in this build, so none of them appears. A rail of ten items where
 * eight are dead teaches a product that does not exist, and the mockup is
 * authoritative about visual vocabulary, never about capability inventory.
 *
 * The create flow is deliberately not a rail item either. It is an action
 * reached from a site index, not a place, and it is already reached from the
 * two entry points T004 and T006 established.
 *
 * This is the Lab's rail and not the operator's. The two item sets are
 * declared by their own shells and share only the component that renders them,
 * so neither can reach the other's contents. The Lab's rail is never rendered
 * when the gate is closed, because the routes that compose this shell are not
 * registered at all in that state.
 *
 * The items are passed in rather than declared here, because a Simulator Lab
 * URL may be spelled only in the gated route module. That keeps the gate's one
 * chokepoint intact: this component names no simulator path.
 */
export interface SimulatorLabShellProps {
  railItems: NavRailItem[];
  children: ReactNode;
}

export function SimulatorLabShell({
  railItems,
  children,
}: SimulatorLabShellProps) {
  return (
    <div className="app-frame">
      <div className="app-frame__side">
        <AppHeader name="AssetOps" />
        <NavRail label="Simulator Lab routes" items={railItems} />
      </div>

      <div className="app-frame__body">
        <div className="app-frame__content">{children}</div>
      </div>
    </div>
  );
}
