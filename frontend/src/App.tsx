import { Route, Routes } from "react-router-dom";

import { featureFlags, type FeatureFlags } from "./config/featureFlags";
import { OperatorShellFrame } from "./shell/OperatorShellFrame";
import { OperatorShellLayout } from "./shell/OperatorShellLayout";
import { RouteNotAvailableFrame } from "./shell/RouteNotAvailableFrame";
import { SiteConfigurationFrame } from "./shell/SiteConfigurationFrame";
import { SiteDetailsFrame } from "./shell/SiteDetailsFrame";
import { SitesFrame } from "./shell/SitesFrame";
import { simulatorLabRoutes } from "./shell/simulatorLabRoutes";

/**
 * Route table.
 *
 * Operator route frames (shell home, Sites, Site Details, Site Configuration)
 * render inside `OperatorShellLayout` and are served in both gate states: the
 * Simulator Lab gate controls simulator surfaces and execution only.
 *
 * Simulator Lab routes come from `simulatorLabRoutes(flags)`, which returns an
 * empty list when `simulator_lab.enabled` is false. The route is then never
 * registered, so a direct Simulator Lab URL matches the catch-all and the UI
 * serves a not-available frame rather than a hidden-but-reachable simulator
 * surface. The Simulator Lab route stays outside the operator layout, so the
 * simulator surface never renders operator navigation chrome.
 *
 * Site Details and Site Configuration are parameterless, because no Site schema
 * or Site identity exists yet.
 */
export interface AppProps {
  flags?: FeatureFlags;
}

export function App({ flags = featureFlags }: AppProps) {
  return (
    <Routes>
      <Route element={<OperatorShellLayout flags={flags} />}>
        <Route path="/" element={<OperatorShellFrame />} />
        <Route path="/sites" element={<SitesFrame />} />
        <Route path="/site-details" element={<SiteDetailsFrame />} />
        <Route
          path="/site-configuration"
          element={<SiteConfigurationFrame />}
        />
      </Route>
      {simulatorLabRoutes(flags).map((route) => (
        <Route key={route.path} path={route.path} element={route.element} />
      ))}
      <Route path="*" element={<RouteNotAvailableFrame />} />
    </Routes>
  );
}
