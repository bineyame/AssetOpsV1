/**
 * Frame for an address this build does not serve.
 *
 * The Simulator Lab route is absent from the route table when
 * `simulator_lab.enabled` is false, so a direct Simulator Lab URL falls through
 * to this frame. It deliberately does not name the Simulator Lab: a disabled
 * build should contain no simulator entry point, hint, or reference anywhere in
 * the UI.
 */
export function RouteNotAvailableFrame() {
  return (
    <main aria-labelledby="route-not-available-heading">
      <h1 id="route-not-available-heading">Page not available</h1>

      <section aria-labelledby="route-not-available-detail-heading">
        <h2 id="route-not-available-detail-heading">
          This address is not served
        </h2>
        <p>
          No page is served at this address. The address may come from a build
          with different features enabled, or it may not exist at all.
        </p>
      </section>
    </main>
  );
}
