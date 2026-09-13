import { Route, Routes } from "react-router-dom";

import { featureFlags, type FeatureFlags } from "./config/featureFlags";
import { OperatorShellFrame } from "./shell/OperatorShellFrame";
import { OperatorShellLayout } from "./shell/OperatorShellLayout";
import { RouteNotAvailableFrame } from "./shell/RouteNotAvailableFrame";
import { SiteConfigurationFrame } from "./shell/SiteConfigurationFrame";
import { SiteDetailFrame } from "./shell/SiteDetailFrame";
import { SitesFrame } from "./shell/SitesFrame";
import { WorkspaceShellLayout } from "./shell/WorkspaceShellLayout";
import {
  SITES_PATH,
  SITE_DETAIL_ROUTE_PATH,
} from "./shell/operatorSiteRoutes";
import { simulatorLabRoutes } from "./shell/simulatorLabRoutes";
import type { SiteCreationClient } from "./shell/siteCreationClient";
import type { SiteTemplateCatalogClient } from "./shell/siteTemplateCatalogClient";
import {
  createSiteDirectoryClient,
  type SiteDetailClient,
  type SiteDirectoryClient,
} from "./sites/siteDirectoryClient";

export { SITES_PATH };

/**
 * One client for the whole app, built once at module scope.
 *
 * The routes are rebuilt on every render, and a fresh client each time would
 * change the identity of the prop the Sites index keys its load effect on, so
 * the store would be re-read in a loop.
 */
const defaultSiteDirectory = createSiteDirectoryClient();

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
 * The Sites routes compose the shared Site substrate in `frontend/src/sites/`
 * and are served in both gate states. A site is addressed by `site_id`, so
 * Site Details hangs off the Sites path with the identity in it and is reached
 * from a Sites row. The parameterless `/site-details` frame from T002 is gone:
 * a Site Details link that names no site is not a destination, and no slice
 * leaves a placeholder standing once its identified route exists. Site
 * Configuration is still the parameterless T002 frame and is removed the same
 * way by the slice that gives it an identified replacement.
 *
 * `siteTemplateCatalog`, `siteDirectory`, `siteDetail`, and `siteCreation` are injection
 * points for tests. The default clients read the real APIs; a test supplies
 * fakes so a UI assertion is about what the screen renders from a record
 * rather than about network timing.
 */
export interface AppProps {
  flags?: FeatureFlags;
  siteTemplateCatalog?: SiteTemplateCatalogClient;
  siteDirectory?: SiteDirectoryClient;
  siteDetail?: SiteDetailClient;
  siteCreation?: SiteCreationClient;
}

export function App({
  flags = featureFlags,
  siteTemplateCatalog,
  siteDirectory = defaultSiteDirectory,
  siteDetail = defaultSiteDirectory,
  siteCreation,
}: AppProps) {
  return (
    <Routes>
      <Route element={<WorkspaceShellLayout flags={flags} />}>
        <Route element={<OperatorShellLayout />}>
          <Route path="/" element={<OperatorShellFrame />} />
          <Route
            path={SITES_PATH}
            element={<SitesFrame flags={flags} directory={siteDirectory} />}
          />
          <Route
            path={SITE_DETAIL_ROUTE_PATH}
            element={
              <SiteDetailFrame detail={siteDetail} sitesPath={SITES_PATH} />
            }
          />
          <Route
            path="/site-configuration"
            element={<SiteConfigurationFrame />}
          />
        </Route>
      </Route>
      {simulatorLabRoutes(
        flags,
        siteTemplateCatalog,
        siteCreation,
        SITES_PATH,
      ).map((route) => (
        <Route key={route.path} path={route.path} element={route.element} />
      ))}
      <Route path="*" element={<RouteNotAvailableFrame />} />
    </Routes>
  );
}
