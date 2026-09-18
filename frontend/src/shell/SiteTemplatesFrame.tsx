import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { DataTable, PageHeader, Panel } from "../ui";
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
/** The type filter's "no filter" value. Not a site type, so it cannot collide
 *  with one the catalog contains. */
const ALL_TYPES = "__all__";

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
  const [search, setSearch] = useState("");
  const [siteType, setSiteType] = useState(ALL_TYPES);

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

  const shipped = result?.status === "loaded" ? result.templates : [];

  /** The site types the shipped catalog actually contains, in order. */
  const siteTypes = useMemo(
    () => Array.from(new Set(shipped.map((t) => t.site_type))).sort(),
    [shipped],
  );

  const matching = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return shipped.filter((template) => {
      if (siteType !== ALL_TYPES && template.site_type !== siteType) {
        return false;
      }
      if (needle === "") {
        return true;
      }
      return (
        template.display_name.toLowerCase().includes(needle) ||
        template.template_id.toLowerCase().includes(needle)
      );
    });
  }, [shipped, search, siteType]);

  return (
    <main aria-labelledby="site-templates-heading">
      <PageHeader
        title="Site Templates"
        headingId="site-templates-heading"
        subtitle="Developer workspace"
      />

      <Panel
        heading="A template is not a site"
        headingId="site-templates-not-a-site-heading"
      >
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
      </Panel>

      <Panel
        heading="Shipped templates"
        headingId="site-templates-catalog-heading"
        flush={shipped.length > 0}
      >
        {shipped.length > 0 ? (
          <div className="toolbar">
            <p className="toolbar__field toolbar__field--grow">
              <label className="field-label" htmlFor="site-templates-search">
                Search templates
              </label>
              <input
                className="control"
                id="site-templates-search"
                type="search"
                value={search}
                placeholder="Name or template ID"
                onChange={(event) => setSearch(event.target.value)}
              />
            </p>

            <p className="toolbar__field">
              <label className="field-label" htmlFor="site-templates-type">
                Site type
              </label>
              <select
                className="control"
                id="site-templates-type"
                value={siteType}
                onChange={(event) => setSiteType(event.target.value)}
              >
                {/*
                 * Every option is a type some shipped template actually has.
                 * The filter is built from the records present rather than
                 * from the site-type enum, because offering a value nothing
                 * matches teaches a catalog this build does not ship.
                 */}
                <option value={ALL_TYPES}>All types</option>
                {siteTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </p>
          </div>
        ) : null}

        {result === null ? <p>Loading shipped site templates.</p> : null}

        {result?.status === "unavailable" ? (
          <p>
            The shipped template catalog could not be read, so no template can
            be listed. This is a statement about the catalog, not a statement
            that the build ships none.
          </p>
        ) : null}

        {result?.status === "loaded" && shipped.length === 0 ? (
          <p>This build ships no site templates.</p>
        ) : null}

        {shipped.length > 0 && matching.length === 0 ? (
          <p className="panel__body">
            No shipped template matches this search and filter. This is a
            statement about the filter, not about what the build ships:{" "}
            {shipped.length === 1
              ? "one template ships"
              : `${shipped.length} templates ship`}
            .
          </p>
        ) : null}

        {matching.length > 0 ? (
          <DataTable labelledBy="site-templates-catalog-heading">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Template ID</th>
                <th scope="col">Version</th>
                <th scope="col">Site type</th>
                <th scope="col">Summary</th>
              </tr>
            </thead>
            <tbody>
              {matching.map((template) => (
                <tr key={template.template_id}>
                  <td>
                    <Link to={templateHref(template.template_id)}>
                      {template.display_name}
                    </Link>
                  </td>
                  <td>{template.template_id}</td>
                  <td>{template.template_version}</td>
                  <td>{template.site_type}</td>
                  <td>{template.summary}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : null}
      </Panel>

      <p>
        <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
      </p>
    </main>
  );
}
