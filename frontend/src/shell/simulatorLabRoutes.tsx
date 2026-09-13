import type { ReactElement } from "react";

import type { FeatureFlags } from "../config/featureFlags";
import { CreateSiteFrame } from "./CreateSiteFrame";
import { SimulatorLabFrame } from "./SimulatorLabFrame";
import { SiteTemplateFrame } from "./SiteTemplateFrame";
import { SiteTemplatesFrame } from "./SiteTemplatesFrame";
import {
  createSiteCreationClient,
  type SiteCreationClient,
} from "./siteCreationClient";
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

/** Creating a site is a Lab capability, so the create flow hangs off the Lab
 *  prefix too. What it produces is a normal product site in the product store,
 *  listed by the ungated operator Sites index; the gate covers this surface,
 *  never the object it creates. */
export const CREATE_SITE_PATH = `${SIMULATOR_LAB_PATH}/create-site`;

/** The gated template and create APIs, spelled here for the same chokepoint
 *  reason. The operator Sites API is not a simulator path and is not spelled
 *  here: it is never gated. */
export const SITE_TEMPLATES_API_PATH = "/api/simulator-lab/site-templates";
export const CREATE_SITE_API_PATH = "/api/simulator-lab/sites";

/**
 * The workspace utility entry-point label from the v6.9 product document
 * ("Workspace utility menu: Open Simulator Lab"). It reads as an action that
 * leaves the operator shell, not as the name of an operator route.
 */
export const SIMULATOR_LAB_ENTRY_POINT_LABEL = "Open Simulator Lab";

/**
 * The label the operator Sites index uses to reach the create flow.
 *
 * It reads as an action that leaves the operator shell, like the workspace
 * entry point above, and it is deliberately not the name of an operator route.
 * It is rendered only when the gate is open, so a gate-off build never names
 * the Simulator Lab.
 */
export const CREATE_SITE_ENTRY_POINT_LABEL = "Create a site in the Simulator Lab";

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

const defaultSiteCreation = createSiteCreationClient(CREATE_SITE_API_PATH);

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
  creation: SiteCreationClient = defaultSiteCreation,
  sitesPath: string = "/sites",
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
    {
      path: CREATE_SITE_PATH,
      element: (
        <CreateSiteFrame
          catalog={catalog}
          creation={creation}
          sitesPath={sitesPath}
          simulatorLabPath={SIMULATOR_LAB_PATH}
        />
      ),
    },
  ];
}

/**
 * The gated way from the operator Sites index into the create flow.
 *
 * Separate from the workspace entry point above because the two are rendered
 * by different landmarks and mean different things: one opens the developer
 * workspace, the other starts a specific piece of work. Both are derived from
 * the same flag and both are empty when it is false, and neither is the gate:
 * the route is absent from the route table when the flag is false, so removing
 * a link is never what makes a surface unreachable.
 */
export function simulatorLabCreateSiteEntryPoints(
  flags: FeatureFlags,
): WorkspaceEntryPoint[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ to: CREATE_SITE_PATH, label: CREATE_SITE_ENTRY_POINT_LABEL }];
}

export function simulatorLabWorkspaceEntryPoints(
  flags: FeatureFlags,
): WorkspaceEntryPoint[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ to: SIMULATOR_LAB_PATH, label: SIMULATOR_LAB_ENTRY_POINT_LABEL }];
}
