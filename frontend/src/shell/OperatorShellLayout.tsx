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
 * This list does not grow for a Site Foundation slice, and it loses the items
 * that stopped being true. A navigation destination is a stronger claim than a
 * button: a button says an action exists, navigation says the product has a
 * place. So an item appears only when the route behind it renders a truthful
 * surface, and a parameterless site destination is not one.
 *
 * `Site details` was a T002 route placeholder from before site identity
 * existed. A site is now addressed by `site_id` and its page is reached from a
 * Sites row, so the item and its parameterless route are gone rather than left
 * standing beside their identified replacement. Nothing was added in its
 * place: the identified route is not a navigation destination, because a
 * navigation item cannot name which site it would open.
 *
 * `Site configuration` is still parameterless and still here. It is removed by
 * the slice that makes its identified replacement real, the same way and for
 * the same reason.
 */
const operatorRoutes = [
  { to: "/", label: "Operator home", end: true },
  { to: "/sites", label: "Sites", end: false },
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
