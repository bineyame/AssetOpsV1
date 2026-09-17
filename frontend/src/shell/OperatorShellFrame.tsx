import { PageHeader, Panel } from "../ui";

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
      <PageHeader
        title="AssetOps"
        headingId="operator-shell-heading"
        subtitle="Operator shell"
      />

      <Panel heading="No site data" headingId="operator-shell-empty-heading">
        <p>
          No sites are configured and no operational evidence has been recorded.
          Site configuration, evidence, analytics, and findings are not
          implemented yet.
        </p>
      </Panel>
    </main>
  );
}
