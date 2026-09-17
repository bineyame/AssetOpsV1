import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable, Fact, FactList, PageHeader, Panel } from "../ui";
import type {
  SiteTemplateCatalogClient,
  SiteTemplateDetailResult,
} from "./siteTemplateCatalogClient";

/**
 * Read-only inspection of one shipped site template.
 *
 * This shows the Foundation content the template would produce, rendered from
 * the template document rather than from any fixed value in this file. It is
 * component truth about an archetype, not evidence: that a template declares a
 * generator does not mean a generator exists, is commissioned, or has ever
 * reported a measurement. So there is no telemetry, chart, source health,
 * evidence, analytics, Replay, or Findings here, and no source-mode badge,
 * because a template has no source.
 *
 * There is also no single line diagram, no empty frame reserved for one, and
 * no signal selector: configured topology is a later causal step, and a
 * diagram frame with nothing behind it would claim the step had landed.
 *
 * No Create, Instantiate, Use, Copy, upload, import, edit, Save, Publish,
 * delete, or rename control exists on this surface, enabled or disabled.
 */
export interface SiteTemplateFrameProps {
  catalog: SiteTemplateCatalogClient;
  siteTemplatesPath: string;
  simulatorLabPath: string;
}

export function SiteTemplateFrame({
  catalog,
  siteTemplatesPath,
  simulatorLabPath,
}: SiteTemplateFrameProps) {
  const { templateId } = useParams<{ templateId: string }>();
  const [result, setResult] = useState<SiteTemplateDetailResult | null>(null);

  useEffect(() => {
    let active = true;

    if (templateId === undefined) {
      setResult({ status: "not_found" });
      return undefined;
    }

    void catalog.getTemplate(templateId).then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [catalog, templateId]);

  const backLinks = (
    <p>
      <Link to={siteTemplatesPath}>Back to Site Templates</Link>{" "}
      <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
    </p>
  );

  if (result === null) {
    return (
      <main aria-labelledby="site-template-heading">
        <PageHeader title="Site template" headingId="site-template-heading" />
        <p>Loading the shipped site template.</p>
        {backLinks}
      </main>
    );
  }

  if (result.status === "not_found") {
    return (
      <main aria-labelledby="site-template-heading">
        <PageHeader title="Site template" headingId="site-template-heading" />
        <Panel
          heading="No such shipped site template"
          headingId="site-template-missing-heading"
        >
          <p>
            This build ships no site template with that template identity.
            Template identities are not site identities, and no site can be
            addressed here.
          </p>
        </Panel>
        {backLinks}
      </main>
    );
  }

  if (result.status === "unavailable") {
    return (
      <main aria-labelledby="site-template-heading">
        <PageHeader title="Site template" headingId="site-template-heading" />
        <Panel
          heading="Site template unavailable"
          headingId="site-template-unavailable-heading"
        >
          <p>
            The shipped template catalog could not be read, so this template
            cannot be shown. Nothing is known about its content.
          </p>
        </Panel>
        {backLinks}
      </main>
    );
  }

  const template = result.template;

  return (
    <main aria-labelledby="site-template-heading">
      <PageHeader
        title={template.display_name}
        headingId="site-template-heading"
        subtitle="Developer workspace"
      />

      <Panel
        heading="A template is not a site"
        headingId="site-template-not-a-site-heading"
      >
        <p>
          This is shipped, read-only configuration for a kind of site. It is
          not a site: it has no site identity, no lifecycle status, no
          location, and no timezone bound to a real place. It cannot be opened
          as a site, simulated, or given evidence, and this build contains no
          site.
        </p>
        <p>
          Template identity is its own identity space. A template identity
          never becomes a site identity.
        </p>
      </Panel>

      <Panel
        heading="Template identity"
        headingId="site-template-identity-heading"
      >
        <FactList>
          <Fact term="Template ID">{template.template_id}</Fact>
          <Fact term="Template version">{template.template_version}</Fact>
        </FactList>
      </Panel>

      <Panel
        heading="Foundation content"
        headingId="site-template-foundation-heading"
      >
        <FactList>
          <Fact term="Site type">{template.site_type}</Fact>
          <Fact term="Summary">{template.summary}</Fact>
        </FactList>

        <h3 id="site-template-components-heading">Declared components</h3>
        <DataTable labelledBy="site-template-components-heading">
          <thead>
            <tr>
              <th scope="col">Component ID</th>
              <th scope="col">Component type</th>
              <th scope="col">Name</th>
              <th scope="col">Declared rating</th>
            </tr>
          </thead>
          <tbody>
            {template.components.map((component) => (
              <tr key={component.component_id}>
                <td>{component.component_id}</td>
                <td>{component.component_type}</td>
                <td>{component.display_name}</td>
                <td>
                  {component.rating === null
                    ? "Not declared"
                    : `${component.rating.value} ${component.rating.unit}`}
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>

        <p>
          These are the components the template declares, with their declared
          design ratings. They are component truth about the archetype, not
          evidence: no device exists, nothing has reported, and no operating
          state, source health, analytics, Replay, or findings exist for a
          template.
        </p>
      </Panel>

      {backLinks}
    </main>
  );
}
