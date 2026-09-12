/**
 * Site Configuration route frame.
 *
 * T002 scope: this frame proves the Site Configuration route renders inside the
 * operator shell. No Site or Foundation configuration is loaded, and no site
 * identifier is assumed or hard-coded. It exposes no editing, Save, or Publish
 * action, because configuration semantics are owned by later slices.
 */
export function SiteConfigurationFrame() {
  return (
    <main aria-labelledby="site-configuration-heading">
      <h1 id="site-configuration-heading">Site configuration</h1>

      <section aria-labelledby="site-configuration-empty-heading">
        <h2 id="site-configuration-empty-heading">
          Site configuration unavailable
        </h2>
        <p>
          No site configuration exists in this build. Configuration content
          cannot be viewed, edited, saved, or published here, and no site schema
          or foundation content is available yet.
        </p>
      </section>
    </main>
  );
}
