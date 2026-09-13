import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import type {
  SiteTemplateCatalogClient,
  SiteTemplateListResult,
} from "./siteTemplateCatalogClient";
import type {
  CreateSiteResult,
  SiteCreationClient,
} from "./siteCreationClient";

/**
 * Create a site from a shipped template. A Simulator Lab surface.
 *
 * Served only when `simulator_lab.enabled` is true. Authoring a simulated site
 * is a Lab capability, so the flow and its API live behind the gate. What it
 * produces is not a Lab object: it is a normal product site in the product
 * store, carrying simulated source mode as provenance, visible on the operator
 * Sites index, and still visible when the Lab is switched off. There is no
 * publish step and no promote step, because it was a product object from the
 * instant it existed.
 *
 * The relationship between the template and the site it makes is a copy, and
 * the copy is stated on the screen rather than left to be inferred. A later
 * change to the template never reaches back into a site already created from
 * it.
 *
 * What this flow cannot do, and does not pretend to: it cannot edit a site,
 * rename one, duplicate one, or remove one. In M1 a site's configuration is
 * fixed at creation and its site ID is immutable, so this screen offers
 * creation and nothing else.
 *
 * Refusal copy comes from the backend rather than being restated here. The
 * backend owns the identity rules, and a second copy of them in the UI is a
 * second copy that can drift.
 *
 * Paths arrive as props. This module must not spell a simulator URL: the
 * single chokepoint in `simulatorLabRoutes.tsx` is what keeps a Lab surface
 * from being addressable outside the gate.
 */
export interface CreateSiteFrameProps {
  catalog: SiteTemplateCatalogClient;
  creation: SiteCreationClient;
  sitesPath: string;
  simulatorLabPath: string;
}

interface FormState {
  templateId: string;
  siteId: string;
  displayName: string;
  country: string;
  locality: string;
  timezone: string;
}

const EMPTY_FORM: FormState = {
  templateId: "",
  siteId: "",
  displayName: "",
  country: "",
  locality: "",
  timezone: "",
};

export function CreateSiteFrame({
  catalog,
  creation,
  sitesPath,
  simulatorLabPath,
}: CreateSiteFrameProps) {
  const [templates, setTemplates] = useState<SiteTemplateListResult | null>(
    null,
  );
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [result, setResult] = useState<CreateSiteResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    void catalog.listTemplates().then((loaded) => {
      if (!active) {
        return;
      }
      setTemplates(loaded);
      if (loaded.status === "loaded" && loaded.templates.length > 0) {
        setForm((current) =>
          current.templateId === ""
            ? { ...current, templateId: loaded.templates[0].template_id }
            : current,
        );
      }
    });

    return () => {
      active = false;
    };
  }, [catalog]);

  function update(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);

    const created = await creation.createSite({
      template_id: form.templateId,
      site_id: form.siteId,
      display_name: form.displayName,
      location: { country: form.country, locality: form.locality },
      timezone: form.timezone,
    });

    setResult(created);
    setSubmitting(false);

    if (created.status === "created") {
      setForm({ ...EMPTY_FORM, templateId: form.templateId });
    }
  }

  const backLinks = (
    <p>
      <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>{" "}
      <Link to={sitesPath}>Go to Sites</Link>
    </p>
  );

  const availableTemplates =
    templates?.status === "loaded" ? templates.templates : [];

  return (
    <main aria-labelledby="create-site-heading">
      <h1 id="create-site-heading">Create a site</h1>
      <p>Developer workspace</p>

      <section aria-labelledby="create-site-explanation-heading">
        <h2 id="create-site-explanation-heading">
          A site is created by copying a template
        </h2>
        <p>
          Choose a shipped template and supply the identity of the site you are
          configuring. The template&apos;s foundation content is copied into the
          new site, and the site records which template and which template
          version it came from. The copy is not a link: changing the template
          later never changes a site already created from it.
        </p>
        <p>
          The site is a normal site in the product from the moment it is
          created. It carries simulated source mode as provenance, appears on
          the operator Sites index, and stays there when the Simulator Lab is
          switched off. Nothing is published or promoted.
        </p>
        <p>
          A site ID is permanent. Configuration is fixed at creation in this
          milestone: a site cannot be edited, renamed, duplicated, or removed
          afterwards.
        </p>
      </section>

      <section aria-labelledby="create-site-form-heading">
        <h2 id="create-site-form-heading">Site identity</h2>

        {templates === null ? <p>Loading shipped site templates.</p> : null}

        {templates?.status === "unavailable" ? (
          <p>
            The shipped template catalog could not be read, so no site can be
            created here. This is a statement about the catalog, not a
            statement that the build ships none.
          </p>
        ) : null}

        {templates?.status === "loaded" && availableTemplates.length === 0 ? (
          <p>
            This build ships no site templates, so there is nothing to create a
            site from.
          </p>
        ) : null}

        {availableTemplates.length > 0 ? (
          <form onSubmit={submit} aria-labelledby="create-site-form-heading">
            <p>
              <label htmlFor="create-site-template">Template</label>
              <select
                id="create-site-template"
                value={form.templateId}
                onChange={(event) => update("templateId", event.target.value)}
              >
                {availableTemplates.map((template) => (
                  <option
                    key={template.template_id}
                    value={template.template_id}
                  >
                    {template.display_name}
                  </option>
                ))}
              </select>
            </p>

            <p>
              <label htmlFor="create-site-id">Site ID</label>
              <input
                id="create-site-id"
                name="site_id"
                value={form.siteId}
                aria-describedby="create-site-id-rule"
                onChange={(event) => update("siteId", event.target.value)}
              />
              <span id="create-site-id-rule">
                Letters, digits, hyphens, and underscores. Site IDs are unique
                and are compared without regard to case.
              </span>
            </p>

            <p>
              <label htmlFor="create-site-display-name">Display name</label>
              <input
                id="create-site-display-name"
                name="display_name"
                value={form.displayName}
                onChange={(event) => update("displayName", event.target.value)}
              />
            </p>

            <p>
              <label htmlFor="create-site-country">Country</label>
              <input
                id="create-site-country"
                name="country"
                value={form.country}
                onChange={(event) => update("country", event.target.value)}
              />
            </p>

            <p>
              <label htmlFor="create-site-locality">Locality</label>
              <input
                id="create-site-locality"
                name="locality"
                value={form.locality}
                onChange={(event) => update("locality", event.target.value)}
              />
            </p>

            <p>
              <label htmlFor="create-site-timezone">Time zone</label>
              <input
                id="create-site-timezone"
                name="timezone"
                value={form.timezone}
                aria-describedby="create-site-timezone-rule"
                onChange={(event) => update("timezone", event.target.value)}
              />
              <span id="create-site-timezone-rule">
                An IANA time zone name, such as Africa/Kampala.
              </span>
            </p>

            <p>
              <button type="submit" disabled={submitting}>
                Create site
              </button>
            </p>
          </form>
        ) : null}

        {result?.status === "created" ? (
          <p role="status">
            The site {result.site.site_id} was created and is listed on the
            operator Sites index.
          </p>
        ) : null}

        {result?.status === "refused" ? (
          <p role="alert">{result.message}</p>
        ) : null}

        {result?.status === "unavailable" ? (
          <p role="alert">
            The site could not be created because the site store could not be
            reached. Nothing was written.
          </p>
        ) : null}
      </section>

      {backLinks}
    </main>
  );
}
