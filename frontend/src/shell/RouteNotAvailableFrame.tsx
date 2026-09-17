import { PageHeader, Panel } from "../ui";

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
      <PageHeader
        title="Page not available"
        headingId="route-not-available-heading"
      />

      <Panel
        heading="This address is not served"
        headingId="route-not-available-detail-heading"
      >
        <p>
          No page is served at this address. The address may come from a build
          with different features enabled, or it may not exist at all.
        </p>
      </Panel>
    </main>
  );
}
