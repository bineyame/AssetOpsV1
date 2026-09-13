import { Link } from "react-router-dom";

/**
 * Simulator Lab shell frame, served only when `simulator_lab.enabled` is true.
 *
 * This is the developer workspace surface, not an operator product page. It is
 * reached from the workspace utility entry point in `WorkspaceShellLayout`,
 * never from operator navigation, and it renders outside the operator route
 * layout so it carries no operator chrome.
 *
 * Scope: this is an empty shell. It exposes no run start, run inspection,
 * rerun, truth overlay, comparison, staging, ingestion, analytics, Replay, or
 * Findings surface, because none of those exist yet. The only control is a link
 * back to the operator shell.
 *
 * The documented simulator-to-product bridge is `Open in AssetOps` on an
 * eligible committed run. That bridge needs a run and a Site identity, so it is
 * owned by a later slice; until then the way back is a plain link to the
 * operator shell and claims nothing about runs or evidence.
 */
export function SimulatorLabFrame() {
  return (
    <main aria-labelledby="simulator-lab-heading">
      <h1 id="simulator-lab-heading">Simulator Lab</h1>
      <p>Developer workspace</p>

      <section aria-labelledby="simulator-lab-empty-heading">
        <h2 id="simulator-lab-empty-heading">Simulator Lab is empty</h2>
        <p>
          The Simulator Lab surface is enabled, but it is an empty shell. No
          simulated world, site, device, or simulator run exists, and run
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
      </section>

      <p>
        <Link to="/">Back to the operator shell</Link>
      </p>
    </main>
  );
}
