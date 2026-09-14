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
 * `Site details` and `Site configuration` were T002 route placeholders from
 * before site identity existed. A site is now addressed by `site_id`, its page
 * is reached from a Sites row, and its configuration is reached from the site,
 * so both items and both parameterless routes are gone rather than left
 * standing beside their identified replacements. Nothing was added in their
 * place: neither identified route is a navigation destination, because a
 * navigation item cannot name which site it would open.
 *
 * What is left is what a navigation item can truthfully say: the operator home
 * and the Sites index. This list has not gained an item since T004 and does
 * not gain one here.
 */
const operatorRoutes = [
  { to: "/", label: "Operator home", end: true },
  { to: "/sites", label: "Sites", end: false },
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
