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
import type { SiteCreationClient } from "./shell/siteCreationClient";
import type { SiteTemplateCatalogClient } from "./shell/siteTemplateCatalogClient";
import {
  createSiteDirectoryClient,
  type SiteDirectoryClient,
} from "./sites/siteDirectoryClient";

/** The operator Sites path. Not a simulator path, and never gated. */
export const SITES_PATH = "/sites";

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
 * The Sites route composes the shared Site substrate in `frontend/src/sites/`
 * and is served in both gate states. Site Details and Site Configuration are
 * still the parameterless T002 frames: sites are addressed by `site_id` in the
 * next slice, and a destination must not appear before the route behind it
 * renders a truthful surface.
 *
 * `siteTemplateCatalog`, `siteDirectory`, and `siteCreation` are injection
 * points for tests. The default clients read the real APIs; a test supplies
 * fakes so a UI assertion is about what the screen renders from a record
 * rather than about network timing.
 */
export interface AppProps {
  flags?: FeatureFlags;
  siteTemplateCatalog?: SiteTemplateCatalogClient;
  siteDirectory?: SiteDirectoryClient;
  siteCreation?: SiteCreationClient;
}

export function App({
  flags = featureFlags,
  siteTemplateCatalog,
  siteDirectory = defaultSiteDirectory,
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
          <Route path="/site-details" element={<SiteDetailsFrame />} />
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
