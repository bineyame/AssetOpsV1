/**
 * Minimal operator shell route frame.
 *
 * T001 scope: this frame proves the stack can render an operator surface. It
 * carries no Site data, no operational values, no source health, no analytics,
 * no Replay, and no Findings, and it must not imply that any of those exist.
 * Operator navigation and the Sites / Site Details / Site Configuration frames
 * are owned by a later slice.
 */
export function OperatorShellFrame() {
  return (
    <main aria-labelledby="operator-shell-heading">
      <h1 id="operator-shell-heading">AssetOps</h1>
      <p>Operator shell</p>

      <section aria-labelledby="operator-shell-empty-heading">
        <h2 id="operator-shell-empty-heading">No site data</h2>
        <p>
          No sites are configured and no operational evidence has been recorded.
          Site configuration, evidence, analytics, and findings are not
          implemented yet.
        </p>
      </section>
    </main>
  );
}
