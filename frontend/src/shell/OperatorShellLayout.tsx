import { useEffect, useState } from "react";
import { useLocation, useOutletContext, useSearchParams } from "react-router-dom";

import { AppHeader, NavRail, type NavRailItem } from "../ui";
import { RangeFocusProvider } from "../ui/rangeFocus";
import { railHomeOf } from "./iaRoutes";
import { SharedRangeBar, SharedRangeOutlet } from "./SharedRangeBar";
import { rangeSearch } from "./sharedRange";
import type { WorkspaceChrome } from "./WorkspaceShellLayout";
import "./demonstrationBanner.css";

/**
 * POLISH §6 D-1 (R651): the one quiet, app-wide note that this build shows example Sites and records. OWN-G3b (R2-G3b
 * 16): "prepared for this walkthrough" dropped (client-facing wording).
 */
export const DEMONSTRATION_BANNER = "Demonstration · example sites and records";

/**
 * Operator navigation layout.
 *
 * This list is deliberately flag-free. The Simulator Lab gate controls
 * simulator surfaces only, so operator routes and their navigation are
 * identical in both gate states, and Simulator Lab is not an operator route:
 * it is a separate developer workspace reached from the workspace chrome in
 * `WorkspaceShellLayout`. Nothing in this module may depend on
 * `simulator_lab.enabled`, and no simulator entry belongs in this list.
 *
 * This list does not grow for a Site Foundation slice, and it loses the items
 * that stopped being true. A navigation destination is a stronger claim than a
 * button: a button says an action exists, navigation says the product has a
 * place. So an item appears only when the route behind it renders a truthful
 * surface, and a parameterless site destination is not one.
 *
 * `Site details` and `Site configuration` were T002 route placeholders from
 * before site identity existed. A site is now addressed by `site_id`, its page
 * is reached from a Sites row, and its configuration is reached from the site,
 * so both items and both parameterless routes are gone rather than left
 * standing beside their identified replacements. Nothing was added in their
 * place: neither identified route is a navigation destination, because a
 * navigation item cannot name which site it would open.
 *
 * What is left is what a navigation item can truthfully say: the Sites index.
 * T027 removed the T002 `Operator home` item and its placeholder frame; `/`
 * now redirects to the Portfolio (IA-P P1, D-IA.15).
 *
 * T028 adds the Findings rail root, which owns the global Findings index, and
 * the group headers (`D-2026-10-02-grammar-ownership-test`).
 *
 * W1-UX-07 (owner decision 2026-10-17, `D-2026-10-17-w1-rail`): the rail shows
 * the full v6.9 root inventory, in the groups, labels and order of the mock's
 * `ROOTS` and `rail()`. Only Portfolio, Sites, Findings, Actions, Evidence and Financials own a truthful cross-site
 * destination today, so only they are live; every other root is an
 * `unavailable` item, which the item model forbids from carrying a route. A
 * site-scoped screen does not make its root live: the rail cannot choose a
 * site. Promote a root only in the slice that supplies and reviews its
 * cross-site route, with this list, the route table and
 * `tools/checks/navigation-truthfulness.ps1` changed together.
 *
 * One item per line: the navigation-truthfulness guard parses this list.
 */
const operatorRailItems: NavRailItem[] = [
  { kind: "live", to: "/portfolio", label: "Portfolio", end: false, group: "OPERATIONS", icon: "grid" },
  { kind: "live", to: "/sites", label: "Sites", end: false, group: "OPERATIONS", icon: "site" },
  { kind: "unavailable", label: "Assets & cover", group: "OPERATIONS", icon: "asset" },
  { kind: "live", to: "/findings", label: "Findings", end: false, group: "INTELLIGENCE", icon: "finding" },
  { kind: "unavailable", label: "Decisions", group: "WORK", icon: "decide" },
  { kind: "unavailable", label: "Plan", group: "WORK", icon: "clock" },
  { kind: "live", to: "/actions", label: "Actions", end: false, group: "WORK", icon: "action" },
  { kind: "live", to: "/incidents", label: "Incidents", end: false, group: "WORK", icon: "incident" },
  { kind: "live", to: "/maintenance", label: "Maintenance", end: false, group: "WORK", icon: "work" },
  { kind: "unavailable", label: "Results", group: "ASSURANCE", icon: "book" },
  { kind: "live", to: "/evidence", label: "Evidence & records", end: false, group: "ASSURANCE", icon: "evidence" },
  { kind: "live", to: "/financials", label: "Financials", end: false, group: "BUSINESS", icon: "money" },
  { kind: "unavailable", label: "Settings", group: "ADMIN", icon: "gear" },
];

/**
 * IA-P P1 (spec §2.1, §5.1, D-IAP.5): the menu is IA-1's `IA_RAIL` (groups, order, labels). Decisions goes live in
 * P2 and Results in P3b; Plan is unavailable while the product has no plan record (D-IAP.1, MD-IAP-1). Operational
 * records is the Records tab of Evidence & records. The item an address lights is `railHomeOf` (`iaRoutes.ts`), which
 * replaced `railActiveLabel`: a Site Action detail lights Actions, a Site Finding detail Findings, every other address
 * its §2.4 family. The guard in `tools/checks/navigation-truthfulness.ps1` pins the call form below.
 */

/**
 * The rail is a real component now, but it owns no items: this list is still
 * declared here and passed in. `NavRail` renders what a shell gives it and has
 * no default, so the operator rail and the Lab rail cannot converge through
 * the component they share.
 *
 * The landmark keeps its accessible name, `Operator routes`, because that name
 * is what the T003 and T004 boundary tests identify it by.
 *
 * The workspace footer under the rail is not decided here: the workspace
 * layout renders it (or nothing, with the Simulator Lab gate closed) and this
 * shell only places it, so nothing in this module depends on the gate.
 */
export function OperatorShellLayout() {
  const chrome = useOutletContext<WorkspaceChrome | undefined>();
  // W1-F5a carry 5: at phone width the rail collapses behind a Menu button, as the v69 mock hides its rail
  // (`mockups.css` max-width:760px `.rail{display:none}`), instead of stacking above the content. Above the
  // narrow breakpoint the button is hidden and the rail is always shown; every destination stays in the DOM.
  // The button exists only at that width: elsewhere the rail is always shown, so the shell adds no control.
  const narrow = useNarrowViewport();
  const [railOpen, setRailOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setRailOpen(false), [pathname]);
  // SR-1 (SR.3): the rail keeps the address range. `SharedRangeOutlet` completes an estate address that has none
  // before the page mounts (same path, replace, no history entry).
  const [params] = useSearchParams();
  const railSearch = rangeSearch(params);

  return (
    <div
      className={
        railOpen
          ? "app-frame app-frame--operator app-frame--rail-open"
          : "app-frame app-frame--operator"
      }
    >
      <div className="app-frame__side">
        <div className="app-frame__brand-row">
          <AppHeader name="AssetOps" />
          {narrow ? (
            <button
              type="button"
              className="app-frame__menu-toggle"
              aria-expanded={railOpen}
              aria-controls="operator-rail-body"
              onClick={() => setRailOpen((open) => !open)}
            >
              Menu
            </button>
          ) : null}
        </div>
        <div className="app-frame__rail-body" id="operator-rail-body">
          <NavRail label="Operator routes" items={operatorRailItems} activeLabel={railHomeOf(pathname)} search={railSearch} />
          {chrome?.footer ?? null}
        </div>
      </div>

      <RangeFocusProvider>
      <div className="app-frame__body">
        {/* SR-1 (v71 Change 0b): the top-bar row holds the one shared date range; the demonstration banner stays. */}
        <header className="app-topbar" data-shared-range-topbar>
          <SharedRangeBar />
        </header>
        <p className="demonstration-banner" role="note" data-demonstration-banner>
          {DEMONSTRATION_BANNER}
        </p>
        <div className="app-frame__content">
          <SharedRangeOutlet />
        </div>
      </div>
      </RangeFocusProvider>
    </div>
  );
}

/** Phone width, where the operator rail collapses (the 640px shell breakpoint in `primitives.css`). */
const NARROW_QUERY = "(max-width: 640px)";

function useNarrowViewport(): boolean {
  const query =
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia(NARROW_QUERY)
      : null;
  const [narrow, setNarrow] = useState(query?.matches ?? false);
  useEffect(() => {
    if (query === null) return undefined;
    const update = () => setNarrow(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
    // `query` is re-created each render; the media query text is fixed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return narrow;
}
