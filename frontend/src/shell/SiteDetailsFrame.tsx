/**
 * Site Details route frame.
 *
 * T002 scope: this frame proves the Site Details route renders inside the
 * operator shell. It describes no site. No site identifier is assumed, chosen,
 * or hard-coded, and no operating state, single-line diagram, devices, source
 * health, analytics, Replay, or Findings exist to show.
 */
export function SiteDetailsFrame() {
  return (
    <main aria-labelledby="site-details-heading">
      <h1 id="site-details-heading">Site details</h1>

      <section aria-labelledby="site-details-empty-heading">
        <h2 id="site-details-empty-heading">No site to show</h2>
        <p>
          No site has been configured, so this frame describes no site. Site
          identity, operating state, single-line diagram, devices, source
          health, analytics, Replay, and findings are not implemented yet.
        </p>
      </section>
    </main>
  );
}
