/**
 * Simulator Lab unavailable shell frame.
 *
 * T001 scope: this frame states that simulator execution is not served. It
 * exposes no run start, run inspection, rerun, truth overlay, or comparison
 * action. Configuration-driven serving behavior for `simulator_lab.enabled` is
 * owned by the Simulator Lab feature gate slice.
 */
export function SimulatorLabUnavailableFrame() {
  return (
    <main aria-labelledby="simulator-lab-heading">
      <h1 id="simulator-lab-heading">Simulator Lab</h1>

      <section aria-labelledby="simulator-lab-unavailable-heading">
        <h2 id="simulator-lab-unavailable-heading">Simulator Lab unavailable</h2>
        <p>
          Simulator execution is not available in this build. No simulated world,
          run, or simulator truth exists, and no run can be started, inspected,
          rerun, or compared.
        </p>
      </section>
    </main>
  );
}
