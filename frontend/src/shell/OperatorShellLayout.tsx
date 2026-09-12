import { NavLink, Outlet } from "react-router-dom";

/**
 * Operator navigation layout.
 *
 * T002 scope: this layout owns the first operator navigation structure. It
 * links only operator route frames and deliberately exposes no Simulator Lab
 * entry point; serving behavior for `simulator_lab.enabled` is owned by the
 * Simulator Lab feature gate slice, so the Simulator Lab route stays outside
 * this layout.
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
