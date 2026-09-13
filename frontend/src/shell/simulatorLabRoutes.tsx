import type { ReactElement } from "react";

import type { FeatureFlags } from "../config/featureFlags";
import { SimulatorLabFrame } from "./SimulatorLabFrame";

/**
 * The gated Simulator Lab route table and workspace entry-point table.
 *
 * This module is the ONLY place in the UI allowed to name a Simulator Lab URL;
 * `tools/check-architecture.ps1` fails the build if a simulator path literal
 * appears anywhere else in `frontend/src`. That keeps entry points from being
 * added outside the gate, which is how a "disabled" feature stays reachable by
 * direct URL.
 *
 * Both tables are derived from the same flag and both are empty when the flag
 * is false. When the route table is empty the path is never registered, so a
 * direct request falls through to the catch-all not-available frame instead of
 * rendering a hidden-but-reachable simulator surface. When the entry-point
 * table is empty the workspace chrome renders nothing at all, so a disabled
 * build contains no simulator link, label, or hint.
 *
 * Simulator Lab is a separate developer workspace, not an operator route, so
 * this is a workspace entry-point table and not an addition to the operator
 * navigation list in `OperatorShellLayout`. `WorkspaceEntryPoint` is a distinct
 * type from that list on purpose: the two are rendered by different landmarks
 * and must not be merged.
 */
export const SIMULATOR_LAB_PATH = "/simulator-lab";

/**
 * The workspace utility entry-point label from the v6.9 product document
 * ("Workspace utility menu: Open Simulator Lab"). It reads as an action that
 * leaves the operator shell, not as the name of an operator route.
 */
export const SIMULATOR_LAB_ENTRY_POINT_LABEL = "Open Simulator Lab";

export interface GatedRoute {
  path: string;
  element: ReactElement;
}

export interface WorkspaceEntryPoint {
  to: string;
  label: string;
}

export function simulatorLabRoutes(flags: FeatureFlags): GatedRoute[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ path: SIMULATOR_LAB_PATH, element: <SimulatorLabFrame /> }];
}

export function simulatorLabWorkspaceEntryPoints(
  flags: FeatureFlags,
): WorkspaceEntryPoint[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ to: SIMULATOR_LAB_PATH, label: SIMULATOR_LAB_ENTRY_POINT_LABEL }];
}
