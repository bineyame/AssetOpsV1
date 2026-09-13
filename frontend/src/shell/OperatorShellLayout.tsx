import { NavLink, Outlet } from "react-router-dom";

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

export function OperatorShellLayout() {
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
        </ul>
      </nav>

      <Outlet />
    </>
  );
}
