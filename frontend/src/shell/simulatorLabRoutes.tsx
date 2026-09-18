import type { ReactElement } from "react";

import type { FeatureFlags } from "../config/featureFlags";
import { CreateSiteFrame } from "./CreateSiteFrame";
import { SimulatorLabFrame } from "./SimulatorLabFrame";
import { SimulatorLabShell } from "./SimulatorLabShell";
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
 * The label the Lab itself uses to reach the same create flow.
 *
 * Two entry points, one flow, one chokepoint. The operator index says where it
 * is sending you, because it is sending you out of the operator shell. Inside
 * the Lab there is nowhere to announce, so the label is the action. Both are
 * built here, from the same path, gated by the same flag.
 */
export const ADD_SITE_ENTRY_POINT_LABEL = "+ Add site";

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

/**
 * The Simulator Lab rail's items.
 *
 * Declared here because this module is the only place a simulator URL may be
 * spelled, and listed here because a rail item is a destination claim: each of
 * these two resolves to a surface that renders real content today. The mockup
 * rail's other items have no truthful route behind them in this build and are
 * therefore absent rather than dead.
 *
 * The create flow is not here. It is an action reached from a site index, not
 * a place, and it already has its entry points.
 */
const SIMULATOR_LAB_RAIL_ITEMS = [
  { to: SIMULATOR_LAB_PATH, label: "Simulator Lab", end: true },
  { to: SITE_TEMPLATES_PATH, label: "Site Templates", end: false },
];

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

  // Every Lab surface renders inside the Lab's own shell, so the workspace
  // carries one rail rather than each frame carrying its own chrome. The shell
  // is composed here rather than nested as a layout route because the Lab sits
  // outside both operator layouts on purpose: operator chrome must not follow
  // a developer into the developer workspace.
  const inLabShell = (surface: ReactElement): ReactElement => (
    <SimulatorLabShell railItems={SIMULATOR_LAB_RAIL_ITEMS}>
      {surface}
    </SimulatorLabShell>
  );

  return [
    {
      path: SIMULATOR_LAB_PATH,
      element: inLabShell(
        <SimulatorLabFrame
          siteTemplatesPath={SITE_TEMPLATES_PATH}
          addSiteEntryPoints={simulatorLabAddSiteEntryPoints(flags)}
        />,
      ),
    },
    {
      path: SITE_TEMPLATES_PATH,
      element: inLabShell(
        <SiteTemplatesFrame
          catalog={catalog}
          templateHref={siteTemplateHref}
          simulatorLabPath={SIMULATOR_LAB_PATH}
        />,
      ),
    },
    {
      path: SITE_TEMPLATE_DETAIL_PATH,
      element: inLabShell(
        <SiteTemplateFrame
          catalog={catalog}
          siteTemplatesPath={SITE_TEMPLATES_PATH}
          simulatorLabPath={SIMULATOR_LAB_PATH}
        />,
      ),
    },
    {
      path: CREATE_SITE_PATH,
      element: inLabShell(
        <CreateSiteFrame
          catalog={catalog}
          creation={creation}
          sitesPath={sitesPath}
          simulatorLabPath={SIMULATOR_LAB_PATH}
        />,
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

/**
 * The Lab's own way into the create flow.
 *
 * Deliberately the same path and the same gate as
 * `simulatorLabCreateSiteEntryPoints`, differing only in what it is called.
 * Adding a second path, or letting the Lab frame spell one, would be the
 * second chokepoint the gate check exists to prevent.
 */
export function simulatorLabAddSiteEntryPoints(
  flags: FeatureFlags,
): WorkspaceEntryPoint[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [{ to: CREATE_SITE_PATH, label: ADD_SITE_ENTRY_POINT_LABEL }];
}

/**
 * A Site action this build cannot perform yet, with what would make it
 * possible.
 *
 * Not a `WorkspaceEntryPoint`: an entry point has a `to`, and these have
 * nowhere to go. That is the point of them. They are the third affordance
 * state - rendered, disabled, and carrying the reason - as opposed to a tab
 * labelled in place, which names an aspect and is not a control at all.
 */
export interface GatedSiteAction {
  label: string;
  /** What would have to exist. Rendered beside the control, not hidden in a
   *  tooltip, because a reason nobody can see is not a reason. */
  unavailableBecause: string;
}

/**
 * The Site actions that belong to the Simulator Lab, and are therefore gated.
 *
 * Two rules apply to these controls and they are different rules, which is
 * why both are tested separately. The gate rule: with `simulator_lab.enabled`
 * false this returns an empty list, so a gate-off build renders no control, no
 * label and no hint that a developer workspace exists. The sequencing rule:
 * with the flag true the controls render, disabled, naming the causal step
 * that would make them work.
 *
 * They live here because this is the one gated module. A Site surface that
 * spelled `Open in Simulator Lab` itself would be a second place the gate has
 * to be remembered, which is exactly what the gate check exists to prevent.
 * The Site page receives these and renders them; it never decides them.
 */
export function simulatorLabSiteActions(
  flags: FeatureFlags,
): GatedSiteAction[] {
  if (!flags.simulatorLab.enabled) {
    return [];
  }

  return [
    {
      label: "Open in Simulator Lab",
      unavailableBecause:
        "The Simulator Lab has no Site view yet. It arrives with the Lab's " +
        "own Site and run surfaces, which are a later step than configuring " +
        "a site.",
    },
    {
      label: "Start Simulation",
      unavailableBecause:
        "Nothing can be simulated yet. A run needs a scenario and a runtime, " +
        "and neither exists in this build.",
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
