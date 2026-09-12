import type { ReactElement } from "react";

import type { FeatureFlags } from "../config/featureFlags";
import { SimulatorLabFrame } from "./SimulatorLabFrame";

/**
 * The gated Simulator Lab route table.
 *
 * This module is the ONLY place in the UI allowed to name a Simulator Lab URL;
 * `tools/check-architecture.ps1` fails the build if a simulator path literal
 * appears anywhere else in `frontend/src`. That keeps entry points from being
 * added outside the gate, which is how a "disabled" feature stays reachable by
 * direct URL.
 *
 * When the flag is false this returns no routes at all, so the path is never
 * registered: a direct request falls through to the catch-all not-available
 * frame instead of rendering a hidden-but-reachable simulator surface.
 */
export const SIMULATOR_LAB_PATH = "/simulator-lab";

export const SIMULATOR_LAB_NAV_LABEL = "Simulator Lab";

export interface GatedRoute {
  path: string;
  element: ReactElement;
}

export function simulatorLabRoutes(flags: FeatureFlags): GatedRoute[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ path: SIMULATOR_LAB_PATH, element: <SimulatorLabFrame /> }];
}
