import { Link } from "react-router-dom";

import { PageHeader, Panel } from "../ui";
import type { WorkspaceEntryPoint } from "./simulatorLabRoutes";

/**
 * Simulator Lab shell frame, served only when `simulator_lab.enabled` is true.
 *
 * This is the developer workspace surface, not an operator product page. It is
 * reached from the workspace utility entry point in `WorkspaceShellLayout`,
 * never from operator navigation, and it renders outside the operator route
 * layout so it carries no operator chrome.
 *
 * Scope: the Lab's surfaces are the shipped Site Templates catalog and the
 * create-from-template flow. It exposes no run start, run inspection, rerun,
 * truth overlay, comparison, staging, ingestion, analytics, Replay, or
 * Findings surface, because none of those exists yet.
 *
 * Creation is the one thing it can do, and the copy on this screen says so.
 * Until T010 it said the opposite - that no site could be created from a
 * template in this build - which was true when T005 wrote it and became false
 * the moment this frame grew an `+ Add site` entry point. That is the failure
 * this product's copy rules exist to catch, so the statement went rather than
 * being left to age.
 *
 * The Site Templates link and the create entry point both resolve to surfaces
 * with real content. They sit in the workspace body; the Lab's rail, added in
 * T009, lists destinations rather than actions, and creating a site is an
 * action reached from here rather than a place.
 *
 * The documented simulator-to-product bridge is `Open in AssetOps` on an
 * eligible committed run. That bridge needs a run and a Site identity, so it is
 * owned by a later slice; until then the way back is a plain link to the
 * operator shell and claims nothing about runs or evidence.
 */
export interface SimulatorLabFrameProps {
  siteTemplatesPath: string;
  /**
   * The Lab's way into the create flow, supplied by the gated route module.
   * Empty when the gate is closed, though a closed gate never serves this
   * frame at all, so the empty case is belt and braces rather than a state a
   * user reaches.
   */
  addSiteEntryPoints: WorkspaceEntryPoint[];
}

export function SimulatorLabFrame({
  siteTemplatesPath,
  addSiteEntryPoints,
}: SimulatorLabFrameProps) {
  return (
    <main aria-labelledby="simulator-lab-heading">
      <PageHeader
        title="Simulator Lab"
        headingId="simulator-lab-heading"
        subtitle="Developer workspace"
      />

      <Panel
        heading="Site Templates"
        headingId="simulator-lab-templates-heading"
      >
        <p>
          Browse the shipped, read-only site configuration templates. A
          template is not a site: it has no site identity, no lifecycle status,
          no location, and no timezone bound to a real place. A site is created
          by copying one, and the copy is a separate object from that moment
          on: the template is never changed by it and never changes it back.
        </p>
        <p>
          <Link to={siteTemplatesPath}>Site Templates</Link>
        </p>

        {/*
         * The Lab's entry into the create flow. The same path and the same
         * gate as the operator index's, differing only in its label: two entry
         * points, one flow, one chokepoint.
         */}
        {addSiteEntryPoints.map((entryPoint) => (
          <p key={entryPoint.to}>
            <Link className="action action--primary" to={entryPoint.to}>
              {entryPoint.label}
            </Link>
          </p>
        ))}
      </Panel>

      <Panel
        heading="No simulator run exists"
        headingId="simulator-lab-empty-heading"
      >
        <p>
          No simulated world, site, device, or simulator run exists, and run
          execution is not implemented yet. Nothing can be started, inspected,
          rerun, or compared against simulator truth here.
        </p>
        <p>
          This is a developer and simulator workspace, separate from the
          operator product shell. It never shows operator findings, analytics,
          confidence, reconciliation results, health scores, or any other
          product conclusion, and it is not part of operator navigation.
        </p>
        <p>
          Simulator truth is never product evidence. Nothing on this screen is a
          claim about a real site.
        </p>
      </Panel>

      <p>
        <Link to="/">Back to the operator shell</Link>
      </p>
    </main>
  );
}
