import { Route, Routes } from "react-router-dom";

import { featureFlags, type FeatureFlags } from "./config/featureFlags";
import { OperatorShellFrame } from "./shell/OperatorShellFrame";
import { OperatorShellLayout } from "./shell/OperatorShellLayout";
import { RouteNotAvailableFrame } from "./shell/RouteNotAvailableFrame";
import { SiteConfigurationFrame } from "./shell/SiteConfigurationFrame";
import { SiteDetailsFrame } from "./shell/SiteDetailsFrame";
import { SitesFrame } from "./shell/SitesFrame";
import { WorkspaceShellLayout } from "./shell/WorkspaceShellLayout";
import { simulatorLabRoutes } from "./shell/simulatorLabRoutes";
import type { SiteTemplateCatalogClient } from "./shell/siteTemplateCatalogClient";

/**
 * Route table.
 *
 * Three levels, in shell order:
 *
 * 1. `WorkspaceShellLayout` is workspace-level chrome. It owns the gated
 *    developer workspace entry point and nothing else.
 * 2. `OperatorShellLayout` is the operator workspace: operator navigation and
 *    the operator route frames (shell home, Sites, Site Details, Site
 *    Configuration). It is flag-free and served in both gate states, because
 *    the Simulator Lab gate controls simulator surfaces and execution only.
 * 3. Simulator Lab is a separate developer workspace. Its routes come from
 *    `simulatorLabRoutes(flags)`, which returns an empty list when
 *    `simulator_lab.enabled` is false. The route is then never registered, so a
 *    direct Simulator Lab URL matches the catch-all and the UI serves a
 *    not-available frame rather than a hidden-but-reachable simulator surface.
 *
 * The Simulator Lab route sits outside both layouts, so the simulator surface
 * never renders operator navigation chrome and never appears to be an operator
 * page. The catch-all sits outside them too: an address this build does not
 * serve should not be dressed as a workspace.
 *
 * Site Details and Site Configuration are parameterless, because no Site schema
 * or Site identity exists yet.
 *
 * `siteTemplateCatalog` is an injection point for tests. The default client
 * reads the gated template API; a test can supply a fake so a UI assertion is
 * about what the screen renders from a template document rather than about
 * network timing.
 */
export interface AppProps {
  flags?: FeatureFlags;
  siteTemplateCatalog?: SiteTemplateCatalogClient;
}

export function App({ flags = featureFlags, siteTemplateCatalog }: AppProps) {
  return (
    <Routes>
      <Route element={<WorkspaceShellLayout flags={flags} />}>
        <Route element={<OperatorShellLayout />}>
          <Route path="/" element={<OperatorShellFrame />} />
          <Route path="/sites" element={<SitesFrame />} />
          <Route path="/site-details" element={<SiteDetailsFrame />} />
          <Route
            path="/site-configuration"
            element={<SiteConfigurationFrame />}
          />
        </Route>
      </Route>
      {simulatorLabRoutes(flags, siteTemplateCatalog).map((route) => (
        <Route key={route.path} path={route.path} element={route.element} />
      ))}
      <Route path="*" element={<RouteNotAvailableFrame />} />
    </Routes>
  );
}
