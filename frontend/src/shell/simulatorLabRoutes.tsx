import type { ReactElement } from "react";

import type { FeatureFlags } from "../config/featureFlags";
import { SimulatorLabFrame } from "./SimulatorLabFrame";
import { SiteTemplateFrame } from "./SiteTemplateFrame";
import { SiteTemplatesFrame } from "./SiteTemplatesFrame";
import {
  createSiteTemplateCatalogClient,
  type SiteTemplateCatalogClient,
} from "./siteTemplateCatalogClient";

/**
 * The gated Simulator Lab route table and workspace entry-point table.
 *
 * This module is the ONLY place in the UI allowed to name a Simulator Lab URL,
 * route or API; `tools/check-architecture.ps1` fails the build if a simulator
 * path literal appears anywhere else in `frontend/src`. That keeps entry
 * points from being added outside the gate, which is how a "disabled" feature
 * stays reachable by direct URL. Every Lab surface therefore hangs off
 * `SIMULATOR_LAB_PATH`, and the frames receive their paths as props rather
 * than importing them, so the chokepoint stays a single module rather than
 * becoming a convention.
 *
 * Both tables are derived from the same flag and both are empty when the flag
 * is false. When the route table is empty the paths are never registered, so a
 * direct request falls through to the catch-all not-available frame instead of
 * rendering a hidden-but-reachable simulator surface. When the entry-point
 * table is empty the workspace chrome renders nothing at all, so a disabled
 * build contains no simulator link, label, or hint.
 *
 * Simulator Lab is a separate developer workspace, not an operator route, so
 * this is a workspace entry-point table and not an addition to the operator
 * navigation list in `OperatorShellLayout`. `WorkspaceEntryPoint` is a distinct
 * type from that list on purpose: the two are rendered by different landmarks
 * and must not be merged.
 */
export const SIMULATOR_LAB_PATH = "/simulator-lab";

/** Lab-only surfaces, addressed under the Lab prefix so the one chokepoint
 *  covers them. Site Templates is a Lab capability: authoring a simulated site
 *  belongs to the developer workspace, while the Sites index, Site Details and
 *  Site Configuration are operator surfaces and are never gated. */
export const SITE_TEMPLATES_PATH = `${SIMULATOR_LAB_PATH}/site-templates`;
export const SITE_TEMPLATE_DETAIL_PATH = `${SITE_TEMPLATES_PATH}/:templateId`;

/** The gated template API, spelled here for the same chokepoint reason. */
export const SITE_TEMPLATES_API_PATH = "/api/simulator-lab/site-templates";

/**
 * The workspace utility entry-point label from the v6.9 product document
 * ("Workspace utility menu: Open Simulator Lab"). It reads as an action that
 * leaves the operator shell, not as the name of an operator route.
 */
export const SIMULATOR_LAB_ENTRY_POINT_LABEL = "Open Simulator Lab";

/**
 * One client for the whole app.
 *
 * Built once at module scope rather than per call: the routes factory runs on
 * every render, and a fresh client each time would change the identity of the
 * prop the template frames key their load effect on, so the catalog would be
 * re-read in a loop.
 */
const defaultSiteTemplateCatalog = createSiteTemplateCatalogClient(
  SITE_TEMPLATES_API_PATH,
);

export function siteTemplateHref(templateId: string): string {
  return `${SITE_TEMPLATES_PATH}/${encodeURIComponent(templateId)}`;
}

export interface GatedRoute {
  path: string;
  element: ReactElement;
}

export interface WorkspaceEntryPoint {
  to: string;
  label: string;
}

export function simulatorLabRoutes(
  flags: FeatureFlags,
  catalog: SiteTemplateCatalogClient = defaultSiteTemplateCatalog,
): GatedRoute[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [
    {
      path: SIMULATOR_LAB_PATH,
      element: <SimulatorLabFrame siteTemplatesPath={SITE_TEMPLATES_PATH} />,
    },
    {
      path: SITE_TEMPLATES_PATH,
      element: (
        <SiteTemplatesFrame
          catalog={catalog}
          templateHref={siteTemplateHref}
          simulatorLabPath={SIMULATOR_LAB_PATH}
        />
      ),
    },
    {
      path: SITE_TEMPLATE_DETAIL_PATH,
      element: (
        <SiteTemplateFrame
          catalog={catalog}
          siteTemplatesPath={SITE_TEMPLATES_PATH}
          simulatorLabPath={SIMULATOR_LAB_PATH}
        />
      ),
    },
  ];
}

export function simulatorLabWorkspaceEntryPoints(
  flags: FeatureFlags,
): WorkspaceEntryPoint[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ to: SIMULATOR_LAB_PATH, label: SIMULATOR_LAB_ENTRY_POINT_LABEL }];
}
