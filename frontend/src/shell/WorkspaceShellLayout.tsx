import { Link, Outlet } from "react-router-dom";

import type { FeatureFlags } from "../config/featureFlags";
import { simulatorLabWorkspaceEntryPoints } from "./simulatorLabRoutes";

/**
 * Workspace-level shell chrome, above the operator shell.
 *
 * Its only job in this slice is the developer workspace entry point. The v6.9
 * product document is explicit that Simulator Lab adds "no new operator
 * navigation items" and is opened from the workspace utility menu, because it
 * is a separate developer workspace rather than an operator screen. So the
 * entry point lives in this workspace/utility landmark, and the operator
 * navigation list in `OperatorShellLayout` is flag-free and identical in both
 * gate states.
 *
 * This is a flat utility bar rather than a real menu control: a disclosure
 * menu, workspace switcher, global search, time window, and user menu are shell
 * furniture that no current slice can fill truthfully.
 *
 * The entry point is not the gate. The Simulator Lab route is absent from the
 * route table when `simulator_lab.enabled` is false, so removing this link is
 * never what makes the feature unreachable. When the gate is closed,
 * `simulatorLabWorkspaceEntryPoints` returns an empty list and this renders no
 * landmark at all, so a disabled build shows no workspace chrome, label, or
 * hint that a developer workspace exists.
 *
 * The Simulator Lab route is deliberately not nested under this layout: once a
 * developer is inside the developer workspace, that surface owns its own shell
 * and its own way back, and operator chrome must not follow them into it.
 */
export interface WorkspaceShellLayoutProps {
  flags: FeatureFlags;
}

export function WorkspaceShellLayout({ flags }: WorkspaceShellLayoutProps) {
  const workspaceEntryPoints = simulatorLabWorkspaceEntryPoints(flags);

  return (
    <div className="app-shell">
      {workspaceEntryPoints.length > 0 ? (
        <nav
          className="workspace-bar"
          aria-labelledby="workspace-utilities-label"
        >
          <p className="workspace-bar__label" id="workspace-utilities-label">
            Workspace utilities
          </p>
          <ul className="workspace-bar__list">
            {workspaceEntryPoints.map((entryPoint) => (
              <li key={entryPoint.to}>
                <Link className="workspace-bar__link" to={entryPoint.to}>
                  {entryPoint.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}

      <Outlet />
    </div>
  );
}
