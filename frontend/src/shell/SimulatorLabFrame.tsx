import { Link } from "react-router-dom";

/**
 * Simulator Lab shell frame, served only when `simulator_lab.enabled` is true.
 *
 * T003 scope: this is an empty shell. It exposes no run start, run inspection,
 * rerun, truth overlay, comparison, staging, ingestion, analytics, or Findings
 * surface, because none of those exist yet. The only control is a link back to
 * the operator shell.
 */
export function SimulatorLabFrame() {
  return (
    <main aria-labelledby="simulator-lab-heading">
      <h1 id="simulator-lab-heading">Simulator Lab</h1>

      <section aria-labelledby="simulator-lab-empty-heading">
        <h2 id="simulator-lab-empty-heading">Simulator Lab is empty</h2>
        <p>
          The Simulator Lab surface is enabled, but it is an empty shell. No
          simulated world, site, device, or simulator run exists, and run
          execution is not implemented yet. Nothing can be started, inspected,
          rerun, or compared against simulator truth here.
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
