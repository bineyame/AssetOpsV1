import type { ReactNode } from "react";
import { Link, Outlet } from "react-router-dom";

import type { FeatureFlags } from "../config/featureFlags";
import { RailIcon } from "../ui";
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
 * W1-UX-07 (`D-2026-10-17-w1-rail`): the entry point now sits where v6.9
 * places it, in the `WORKSPACE` footer under the operator rail, rather than in
 * a bar above the shell. This layout still owns it and still decides whether
 * it exists; it hands the rendered footer to the operator shell through the
 * outlet context, so `OperatorShellLayout` places chrome it is given and stays
 * flag-free. The footer is a workspace utility landmark of its own, never a
 * seventh operator group or root, and it renders once: there is no second copy
 * of the link above the shell.
 *
 * The Simulator Lab route is deliberately not nested under this layout: once a
 * developer is inside the developer workspace, that surface owns its own shell
 * and its own way back, and operator chrome must not follow them into it.
 */
/** What the workspace layout hands the operator shell to place. */
export interface WorkspaceChrome {
  /** The workspace footer, or null when the gate is closed. */
  footer: ReactNode;
}

export interface WorkspaceShellLayoutProps {
  flags: FeatureFlags;
}

export function WorkspaceShellLayout({ flags }: WorkspaceShellLayoutProps) {
  const workspaceEntryPoints = simulatorLabWorkspaceEntryPoints(flags);

  const footer =
    workspaceEntryPoints.length > 0 ? (
      <nav className="workspace-footer" aria-label="Workspace utilities">
        <p className="workspace-footer__label nav-rail__group-label" aria-hidden="true">
          WORKSPACE
        </p>
        <ul className="nav-rail__list">
          {workspaceEntryPoints.map((entryPoint) => (
            <li key={entryPoint.to}>
              <Link className="nav-rail__link" to={entryPoint.to} data-vocabulary-exempt="lab">
                <RailIcon name="lab" />
                <span className="nav-rail__label">{entryPoint.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    ) : null;

  const chrome: WorkspaceChrome = { footer };

  return (
    <div className="app-shell">
      <Outlet context={chrome} />
    </div>
  );
}
