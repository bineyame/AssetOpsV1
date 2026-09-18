import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Fact, FactList, PageHeader, Panel } from "../ui";
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
 * The flow has three steps because it has three stages of real input: choose a
 * template, supply identity, review what will be created. No step reviews
 * nothing, and no step exists to match a mockup's step count.
 *
 * Nothing here validates a field. The backend owns the identity rules, so the
 * flow lets the user proceed and renders what the backend says. A second set
 * of rules in the browser is a second set to keep in agreement, and the one in
 * the browser is the one that drifts.
 *
 * Refusal copy comes from the backend rather than being restated here, and a
 * refusal is placed against the field it concerns by the backend's own refusal
 * code, never by reading the message text. Reading the text would be exactly
 * the second copy of the rules this screen refuses to keep. Two codes name a
 * field, `TEMPLATE_NOT_FOUND` and `SITE_ID_IN_USE`, and each sends the flow
 * back to the step that owns it. Every other refusal renders where the user
 * is, because the screen does not know better than the backend which field is
 * at fault and will not guess.
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

type Step = 1 | 2 | 3;

const STEPS: { number: Step; label: string }[] = [
  { number: 1, label: "Choose a template" },
  { number: 2, label: "Site identity" },
  { number: 3, label: "Review and create" },
];

/** The refusal codes that name a field, and the step that owns that field. */
const REFUSAL_STEPS: Record<string, Step> = {
  TEMPLATE_NOT_FOUND: 1,
  SITE_ID_IN_USE: 2,
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
  const [step, setStep] = useState<Step>(1);

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
      return;
    }

    // Send the user back to the step that owns the refused field, so the
    // message sits beside the input it is about rather than under a review of
    // values that step no longer shows.
    if (created.status === "refused" && created.code !== null) {
      const owning = REFUSAL_STEPS[created.code];
      if (owning !== undefined) {
        setStep(owning);
      }
    }
  }

  const availableTemplates =
    templates?.status === "loaded" ? templates.templates : [];

  const refusal =
    result?.status === "refused"
      ? { message: result.message, code: result.code }
      : null;

  /** The refusal belonging to one step's field, or null. */
  function fieldRefusal(owner: Step): string | null {
    if (refusal === null || refusal.code === null) {
      return null;
    }
    return REFUSAL_STEPS[refusal.code] === owner ? refusal.message : null;
  }

  /** A refusal no code placed. It renders where the user is. */
  const unplacedRefusal =
    refusal !== null &&
    (refusal.code === null || REFUSAL_STEPS[refusal.code] === undefined)
      ? refusal.message
      : null;

  const templateRefusal = fieldRefusal(1);
  const siteIdRefusal = fieldRefusal(2);

  const chosenTemplate = availableTemplates.find(
    (template) => template.template_id === form.templateId,
  );

  function stepNav(back: boolean, next: ReactNode) {
    return (
      <p className="step-nav">
        {back ? (
          <button
            className="action"
            type="button"
            onClick={() => setStep((current) => (current - 1) as Step)}
          >
            Back
          </button>
        ) : null}
        {next}
      </p>
    );
  }

  return (
    <main aria-labelledby="create-site-heading">
      <PageHeader
        title="Create a site"
        headingId="create-site-heading"
        subtitle="Developer workspace"
      />

      <Panel
        heading="A site is created by copying a template"
        headingId="create-site-explanation-heading"
      >
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
      </Panel>

      <Panel heading="Site identity" headingId="create-site-form-heading">
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
          <>
            <ol className="steps" aria-label="Create a site">
              {STEPS.map((entry) => (
                <li
                  className="steps__step"
                  key={entry.number}
                  aria-current={entry.number === step ? "step" : undefined}
                >
                  {/*
                   * The step number is drawn by a CSS counter rather than
                   * rendered as text. These screens assert that every digit
                   * inside `main` traces to the template document or to what
                   * the user just typed, and a decorative "1" is neither. The
                   * guard is worth more than the glyph, exactly as it was for
                   * the brand mark in T009.
                   */}
                  {entry.label}
                </li>
              ))}
            </ol>

            <form onSubmit={submit} aria-labelledby="create-site-form-heading">
              {step === 1 ? (
                <>
                  <p className="toolbar__field">
                    <label
                      className="field-label"
                      htmlFor="create-site-template"
                    >
                      Template
                    </label>
                    <select
                      className="control"
                      id="create-site-template"
                      value={form.templateId}
                      aria-invalid={templateRefusal !== null || undefined}
                      aria-describedby={
                        templateRefusal === null
                          ? undefined
                          : "create-site-template-refusal"
                      }
                      onChange={(event) =>
                        update("templateId", event.target.value)
                      }
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
                    {templateRefusal === null ? null : (
                      <span
                        className="field-error"
                        id="create-site-template-refusal"
                        role="alert"
                      >
                        {templateRefusal}
                      </span>
                    )}
                  </p>

                  {stepNav(
                    false,
                    <button
                      className="action action--primary"
                      type="button"
                      onClick={() => setStep(2)}
                    >
                      Next
                    </button>,
                  )}
                </>
              ) : null}

              {step === 2 ? (
                <>
                  <p className="toolbar__field">
                    <label className="field-label" htmlFor="create-site-id">
                      Site ID
                    </label>
                    <input
                      className="control"
                      id="create-site-id"
                      name="site_id"
                      value={form.siteId}
                      aria-invalid={siteIdRefusal !== null || undefined}
                      aria-describedby={
                        siteIdRefusal === null
                          ? "create-site-id-rule"
                          : "create-site-id-rule create-site-id-refusal"
                      }
                      onChange={(event) => update("siteId", event.target.value)}
                    />
                    <span className="field-hint" id="create-site-id-rule">
                      Letters, digits, hyphens, and underscores. Site IDs are
                      unique and are compared without regard to case.
                    </span>
                    {siteIdRefusal === null ? null : (
                      <span
                        className="field-error"
                        id="create-site-id-refusal"
                        role="alert"
                      >
                        {siteIdRefusal}
                      </span>
                    )}
                  </p>

                  <p className="toolbar__field">
                    <label
                      className="field-label"
                      htmlFor="create-site-display-name"
                    >
                      Display name
                    </label>
                    <input
                      className="control"
                      id="create-site-display-name"
                      name="display_name"
                      value={form.displayName}
                      onChange={(event) =>
                        update("displayName", event.target.value)
                      }
                    />
                  </p>

                  <p className="toolbar__field">
                    <label
                      className="field-label"
                      htmlFor="create-site-country"
                    >
                      Country
                    </label>
                    <input
                      className="control"
                      id="create-site-country"
                      name="country"
                      value={form.country}
                      onChange={(event) => update("country", event.target.value)}
                    />
                  </p>

                  <p className="toolbar__field">
                    <label
                      className="field-label"
                      htmlFor="create-site-locality"
                    >
                      Locality
                    </label>
                    <input
                      className="control"
                      id="create-site-locality"
                      name="locality"
                      value={form.locality}
                      onChange={(event) =>
                        update("locality", event.target.value)
                      }
                    />
                  </p>

                  <p className="toolbar__field">
                    <label
                      className="field-label"
                      htmlFor="create-site-timezone"
                    >
                      Time zone
                    </label>
                    <input
                      className="control"
                      id="create-site-timezone"
                      name="timezone"
                      value={form.timezone}
                      aria-describedby="create-site-timezone-rule"
                      onChange={(event) =>
                        update("timezone", event.target.value)
                      }
                    />
                    <span className="field-hint" id="create-site-timezone-rule">
                      An IANA time zone name, such as Africa/Kampala.
                    </span>
                  </p>

                  {stepNav(
                    true,
                    <button
                      className="action action--primary"
                      type="button"
                      onClick={() => setStep(3)}
                    >
                      Next
                    </button>,
                  )}
                </>
              ) : null}

              {step === 3 ? (
                <>
                  {/*
                   * The review shows what the user supplied and which template
                   * it will be copied from, and nothing else. Source mode,
                   * configuration origin and lifecycle status are assigned by
                   * the backend when the site is created, so rendering them
                   * here would be predicting a record that does not exist yet.
                   */}
                  <FactList>
                    <Fact term="Template">
                      {chosenTemplate === undefined
                        ? form.templateId
                        : `${chosenTemplate.display_name} (${chosenTemplate.template_id} v${chosenTemplate.template_version})`}
                    </Fact>
                    <Fact term="Site ID">{form.siteId}</Fact>
                    <Fact term="Display name">{form.displayName}</Fact>
                    <Fact term="Country">{form.country}</Fact>
                    <Fact term="Locality">{form.locality}</Fact>
                    <Fact term="Time zone">{form.timezone}</Fact>
                  </FactList>

                  {unplacedRefusal === null ? null : (
                    <p className="field-error" role="alert">
                      {unplacedRefusal}
                    </p>
                  )}

                  {result?.status === "unavailable" ? (
                    <p className="field-error" role="alert">
                      The site could not be created because the site store could
                      not be reached. Nothing was written.
                    </p>
                  ) : null}

                  {result?.status === "created" ? (
                    <p role="status">
                      The site {result.site.site_id} was created and is listed
                      on the operator Sites index.
                    </p>
                  ) : null}

                  {stepNav(
                    true,
                    <button
                      className="action action--primary"
                      type="submit"
                      disabled={submitting}
                    >
                      Create site
                    </button>,
                  )}
                </>
              ) : null}
            </form>
          </>
        ) : null}
      </Panel>

      <p>
        <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>{" "}
        <Link to={sitesPath}>Go to Sites</Link>
      </p>
    </main>
  );
}
