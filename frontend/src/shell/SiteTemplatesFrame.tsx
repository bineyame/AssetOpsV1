import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import type {
  SiteTemplateCatalogClient,
  SiteTemplateListResult,
} from "./siteTemplateCatalogClient";

/**
 * Site Templates listing, a Simulator Lab developer-workspace surface.
 *
 * Served only when `simulator_lab.enabled` is true. It is not an operator
 * screen, it is not the Sites index, and nothing it lists is a Site: a
 * template has no `site_id`, no lifecycle status, no location, and no
 * place-bound timezone, and none of those fields exists to render.
 *
 * There is no Create, Instantiate, Use, Copy, upload, import, edit, Save,
 * Publish, delete, or rename control here, enabled or disabled. Nothing in
 * this slice can produce a Site, so a control that implied otherwise would be
 * a promise the product cannot keep. Creation arrives with the slice that
 * actually creates.
 *
 * Every value on this screen comes from a template document. The unavailable
 * state is stated rather than rendered as an empty catalog, because "no
 * templates ship" and "the catalog could not be read" are different facts.
 *
 * Paths arrive as props. This module must not spell a simulator URL: the
 * single chokepoint in `simulatorLabRoutes.tsx` is what keeps a Lab surface
 * from being addressable outside the gate.
 */
export interface SiteTemplatesFrameProps {
  catalog: SiteTemplateCatalogClient;
  templateHref: (templateId: string) => string;
  simulatorLabPath: string;
}

export function SiteTemplatesFrame({
  catalog,
  templateHref,
  simulatorLabPath,
}: SiteTemplatesFrameProps) {
  const [result, setResult] = useState<SiteTemplateListResult | null>(null);

  useEffect(() => {
    let active = true;

    void catalog.listTemplates().then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [catalog]);

  return (
    <main aria-labelledby="site-templates-heading">
      <h1 id="site-templates-heading">Site Templates</h1>
      <p>Developer workspace</p>

      <section aria-labelledby="site-templates-not-a-site-heading">
        <h2 id="site-templates-not-a-site-heading">A template is not a site</h2>
        <p>
          A site template is shipped, read-only configuration describing a kind
          of site. It is not a site: it has no site identity, no lifecycle
          status, no location, and no timezone bound to a real place. A
          template cannot be opened as a site, simulated, or given evidence,
          and no site exists in this build.
        </p>
        <p>
          Nothing on this screen creates, changes, or removes anything. A
          template is browsed here and nowhere else in the product.
        </p>
      </section>

      <section aria-labelledby="site-templates-catalog-heading">
        <h2 id="site-templates-catalog-heading">Shipped templates</h2>

        {result === null ? <p>Loading shipped site templates.</p> : null}

        {result?.status === "unavailable" ? (
          <p>
            The shipped template catalog could not be read, so no template can
            be listed. This is a statement about the catalog, not a statement
            that the build ships none.
          </p>
        ) : null}

        {result?.status === "loaded" && result.templates.length === 0 ? (
          <p>This build ships no site templates.</p>
        ) : null}

        {result?.status === "loaded" && result.templates.length > 0 ? (
          <ul>
            {result.templates.map((template) => (
              <li key={template.template_id}>
                <Link to={templateHref(template.template_id)}>
                  {template.display_name}
                </Link>
                <dl>
                  <dt>Template ID</dt>
                  <dd>{template.template_id}</dd>
                  <dt>Template version</dt>
                  <dd>{template.template_version}</dd>
                  <dt>Site type</dt>
                  <dd>{template.site_type}</dd>
                </dl>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <p>
        <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
      </p>
    </main>
  );
}
