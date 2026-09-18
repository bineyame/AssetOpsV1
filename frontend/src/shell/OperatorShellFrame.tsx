import { PageHeader, Panel } from "../ui";

/**
 * Minimal operator shell route frame.
 *
 * T001 scope: this frame proves the stack can render an operator surface. It
 * carries no Site data, no operational values, no source health, no analytics,
 * no Replay, and no Findings, and it must not imply that any of those exist.
 * Operator navigation and the Sites, Site Details and Foundation surfaces were
 * owned by later slices and now exist; the Sites index is where a site is
 * found, and this frame still says only what it can say without reading one.
 *
 * Its copy names what the product cannot do yet, so it loses an item when a
 * slice makes that item true. T011A takes the Foundation surface out of the
 * list: T008 built it, and a build that renders a site's Foundation must not
 * also announce that there is no such screen. The sentence before it is left
 * exactly as T001 wrote it, including its unconditional "No sites are
 * configured", which is a separate staleness this slice is not the place to
 * settle.
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
          Evidence, analytics, and findings are not implemented yet.
        </p>
      </Panel>
    </main>
  );
}
