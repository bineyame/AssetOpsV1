/**
 * Sites route frame.
 *
 * T002 scope: this frame proves the Sites route renders inside the operator
 * shell. It lists nothing, because no Site schema, Site configuration, or Site
 * evidence exists yet. It must not show counts, operational values, source
 * health, analytics, Replay, or Findings.
 */
export function SitesFrame() {
  return (
    <main aria-labelledby="sites-heading">
      <h1 id="sites-heading">Sites</h1>

      <section aria-labelledby="sites-empty-heading">
        <h2 id="sites-empty-heading">No sites configured</h2>
        <p>
          No sites have been configured, so there is nothing to list. Site
          configuration, operating state, source health, analytics, Replay, and
          findings are not implemented yet.
        </p>
      </section>
    </main>
  );
}
