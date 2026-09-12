import { NavLink, Outlet } from "react-router-dom";

import type { FeatureFlags } from "../config/featureFlags";
import {
  SIMULATOR_LAB_NAV_LABEL,
  SIMULATOR_LAB_PATH,
} from "./simulatorLabRoutes";

/**
 * Operator navigation layout.
 *
 * Operator entries are always present: the Simulator Lab gate controls
 * simulator surfaces only, so operator routes and their navigation work
 * identically in both gate states.
 *
 * The Simulator Lab entry point appears only when `simulator_lab.enabled` is
 * true. It is an entry point, not the gate: the route itself is absent from the
 * route table when the flag is false, so removing this link is never what makes
 * the feature unreachable.
 *
 * The Site Details and Site Configuration paths carry no site identifier,
 * because no Site schema or Site identity exists yet. Identified site routes
 * are owned by the Site Foundation slices.
 */
const operatorRoutes = [
  { to: "/", label: "Operator home", end: true },
  { to: "/sites", label: "Sites", end: false },
  { to: "/site-details", label: "Site details", end: false },
  { to: "/site-configuration", label: "Site configuration", end: false },
];

export interface OperatorShellLayoutProps {
  flags: FeatureFlags;
}

export function OperatorShellLayout({ flags }: OperatorShellLayoutProps) {
  return (
    <>
      <nav aria-label="Operator routes">
        <ul>
          {operatorRoutes.map((route) => (
            <li key={route.to}>
              <NavLink to={route.to} end={route.end}>
                {route.label}
              </NavLink>
            </li>
          ))}
          {flags.simulatorLab.enabled ? (
            <li>
              <NavLink to={SIMULATOR_LAB_PATH}>
                {SIMULATOR_LAB_NAV_LABEL}
              </NavLink>
            </li>
          ) : null}
        </ul>
      </nav>

      <Outlet />
    </>
  );
}
