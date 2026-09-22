import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable, Fact, FactList, PageHeader, Panel } from "../ui";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { SiteDetailResult } from "../sites/siteReadModel";
import type {
  ScenarioCatalogClient,
  ScenarioDetailResult,
  ScenarioParameter,
} from "./scenarioCatalogClient";
import type {
  CreateRunResult,
  RunProfilesResult,
  RunSetupClient,
  RunSummary,
} from "./runSetupClient";

/**
 * Set up a Draft SimulationRun from one saved scenario. A Simulator Lab
 * surface.
 *
 * ## What this screen does, and what it refuses to claim
 *
 * It freezes the inputs a later causal kernel will consume and shows the
 * complete frozen summary of what was frozen, with the answerer for every
 * value. It does not execute anything: no run has ever run in this build,
 * there is no state trajectory, no staged envelope, no commit eligibility, no
 * accepted evidence and no finding, and there is no control on this screen
 * that would produce one.
 *
 * ## The two outcomes, kept apart
 *
 * A refusal means the request could not be frozen: no run identity was
 * allocated and nothing was written, so the screen says exactly that and
 * there is nothing to go and look at. A created Draft is persisted whether it
 * is `READY` or `BLOCKED`, and a blocked Draft renders its frozen inputs in
 * full beside the reasons it may not execute - because those inputs are what
 * a reader needs in order to decide what to change.
 *
 * The distinction comes from the backend's response shape rather than from
 * reading its message text. A second copy of the rules in the browser is a
 * second copy to keep in agreement, and the one in the browser is the one
 * that drifts.
 *
 * ## Nothing is prefilled
 *
 * The interval, the timestep and the seed are empty until a person types
 * them. A prefilled number would be a digit on this screen that no record
 * supplies, which is the rule every screen in this tree is held to, and it
 * would also be run setup quietly choosing part of a run's deterministic
 * identity.
 *
 * Nothing is validated here either. The backend owns every rule and this
 * screen renders what it says, so a refusal is the product copy that names
 * what is wrong rather than a message written twice.
 *
 * ## Paths arrive as props
 *
 * This module must not spell a simulator URL: the single chokepoint in
 * `simulatorLabRoutes.tsx` is what keeps a Lab surface from being addressable
 * outside the gate.
 */
export interface RunSetupFrameProps {
  catalog: ScenarioCatalogClient;
  siteDetail: SiteDetailClient;
  runSetup: RunSetupClient;
  scenariosPath: string;
  simulatorLabPath: string;
  scenarioHref: (scenarioId: string) => string;
}

interface FormState {
  startTime: string;
  endTime: string;
  timestep: string;
  seed: string;
  modelProfile: string;
  publicationProfile: string;
  runInputs: Record<string, string>;
}

const EMPTY_FORM: FormState = {
  startTime: "",
  endTime: "",
  timestep: "",
  seed: "",
  modelProfile: "",
  publicationProfile: "",
  runInputs: {},
};

/** A profile selection, as one value a `<select>` can carry. */
function profileKey(id: string, version: number): string {
  return `${id}@${version}`;
}

function splitProfileKey(
  key: string,
): { profile_id: string; profile_version: number } {
  const at = key.lastIndexOf("@");
  return {
    profile_id: at === -1 ? key : key.slice(0, at),
    profile_version: at === -1 ? Number.NaN : Number.parseInt(key.slice(at + 1), 10),
  };
}

/**
 * A whole number a person typed, for the two fields that take one.
 *
 * Text that is not a whole number becomes `NaN`, which is serialized as
 * `null` and refused by the backend with the rule it broke. That is
 * deliberate: the rule lives in one place, and this screen does not restate
 * it in order to refuse a little earlier.
 *
 * Used for the timestep and the seed ONLY. Both really are whole numbers in
 * the contract, so a decimal in either is a value the backend refuses and
 * should.
 */
function typedWholeNumber(text: string): number {
  return /^-?\d+$/.test(text.trim()) ? Number.parseInt(text.trim(), 10) : Number.NaN;
}

/**
 * A quantity a person typed, for a value the scenario says the run owns.
 *
 * Decimals reach the backend. An earlier version parsed every field as a
 * whole number, so a typed volume of eight hundred and twelve point five
 * became `NaN`, arrived as `null`, and came back refused as MISSING - a
 * refusal about a field the person had filled in, produced by this screen
 * quietly having an opinion while its own docstring says the backend owns
 * every rule. A run input is a quantity; how many decimals a unit may carry
 * is the contract's business and not this screen's.
 */
function typedQuantity(text: string): number {
  const trimmed = text.trim();
  return /^-?\d+(\.\d+)?$/.test(trimmed) ? Number.parseFloat(trimmed) : Number.NaN;
}

/** The parameters this scenario declares the run owns, in authored order. */
function runOwnedParameters(
  parameters: ScenarioParameter[],
): ScenarioParameter[] {
  return parameters.filter(
    (parameter) => parameter.ownership?.owner === "RUN_OVERRIDE",
  );
}

export function RunSetupFrame({
  catalog,
  siteDetail,
  runSetup,
  scenariosPath,
  simulatorLabPath,
  scenarioHref,
}: RunSetupFrameProps) {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [scenario, setScenario] = useState<ScenarioDetailResult | null>(null);
  const [profiles, setProfiles] = useState<RunProfilesResult | null>(null);
  const [site, setSite] = useState<SiteDetailResult | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [result, setResult] = useState<CreateRunResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    if (scenarioId === undefined) {
      setScenario({ status: "not_found" });
      return undefined;
    }

    void catalog.getScenario(scenarioId).then((loaded) => {
      if (active) {
        setScenario(loaded);
      }
    });
    // Loaded, and deliberately not chosen from. An earlier version selected
    // the first of each, which made two components of the frozen
    // deterministic identity values nobody picked - and the model profile is
    // what decides READY against BLOCKED, so the screen would have been
    // choosing the outcome. Both selects lead with an empty option and the
    // backend refuses an unchosen profile, which is the same division of
    // labour as every other field here.
    void runSetup.listProfiles().then((loaded) => {
      if (active) {
        setProfiles(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [catalog, runSetup, scenarioId]);

  const targetSiteId =
    scenario?.status === "loaded" &&
    scenario.targetResolution.state === "RESOLVED"
      ? scenario.targetResolution.site_id
      : null;

  useEffect(() => {
    let active = true;

    if (targetSiteId === null) {
      return undefined;
    }

    void siteDetail.getSite(targetSiteId).then((loaded) => {
      if (active) {
        // Every outcome, not only the one that works. An earlier version
        // kept the loading text forever when the read failed, left submit
        // enabled, and sent a foundation version of NaN.
        setSite(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [siteDetail, targetSiteId]);

  const backLinks = (
    <p>
      {scenarioId === undefined ? null : (
        <>
          <Link to={scenarioHref(scenarioId)}>Back to the scenario</Link>{" "}
        </>
      )}
      <Link to={scenariosPath}>Back to Scenarios</Link>{" "}
      <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
    </p>
  );

  function frame(children: ReactNode) {
    return (
      <main aria-labelledby="run-setup-heading">
        <PageHeader
          title="Set up a draft run"
          headingId="run-setup-heading"
          subtitle="Developer workspace"
        />
        {children}
        {backLinks}
      </main>
    );
  }

  if (scenario === null || profiles === null) {
    return frame(<p>Loading the run setup inputs.</p>);
  }

  if (scenario.status === "not_found") {
    return frame(
      <Panel
        heading="No such saved scenario"
        headingId="run-setup-missing-heading"
      >
        <p>
          No scenario with that scenario identity is saved, so there is nothing
          to set a run up for. Scenario identities are not site identities and
          not run identities.
        </p>
      </Panel>,
    );
  }

  if (scenario.status === "unavailable") {
    return frame(
      <Panel
        heading="Scenario unavailable"
        headingId="run-setup-unavailable-heading"
      >
        <p>
          The scenario store could not be read, so this scenario cannot be set
          up. Nothing is known about its content, and no run was created.
        </p>
      </Panel>,
    );
  }

  const detail = scenario.scenario;
  const resolution = scenario.targetResolution;

  const explanation = (
    <Panel
      heading="What setting a run up does"
      headingId="run-setup-explanation-heading"
    >
      <p>
        Setting a run up freezes the inputs a simulation would consume: the
        site and its foundation version, the scenario version and its resolved
        parameters, the interval, the timestep, the seed, the versioned model
        and publication profiles, and every initial world value with the owner
        that answers for it. The draft records those and nothing else.
      </p>
      <p>
        It does not run anything. No simulation has been executed in this
        build, so a draft has no state, no trajectory, no output, no staged
        gateway envelope, no accepted evidence and no finding, and none of
        those can be produced from this screen.
      </p>
      <p>
        A draft is either ready, meaning the selected model profile can
        execute every input the scenario requires, or blocked, meaning it
        cannot and the draft says which. A blocked draft is still created and
        still persisted: what it froze is what you need in order to decide
        what to change.
      </p>
    </Panel>
  );

  if (resolution.state !== "RESOLVED" || resolution.site_id === null) {
    return frame(
      <>
        {explanation}
        <Panel
          heading="No configured site to bind this run to"
          headingId="run-setup-no-site-heading"
        >
          <p>{resolution.reason}</p>
          <p>
            A run is bound to a concrete site and to the exact version of its
            foundation. Until this scenario&apos;s target site is configured
            here, there is nothing to freeze and no run can be set up.
          </p>
        </Panel>
      </>,
    );
  }

  const allParameters = [
    ...detail.public_parameters,
    ...detail.timeline.flatMap((entry) => entry.parameters),
  ];
  const runOwned = runOwnedParameters(allParameters);

  const modelProfiles =
    profiles.status === "loaded" ? profiles.modelProfiles : [];
  const publicationProfiles =
    profiles.status === "loaded" ? profiles.publicationProfiles : [];

  /**
   * The foundation version this run would freeze, or nothing.
   *
   * A run names the exact version it was set up against, so a version this
   * screen does not have is a run it cannot set up. There is no fallback,
   * and the control below is disabled while it is missing - which is not the
   * screen validating a value, it is the screen declining to send a request
   * it cannot fill in.
   */
  const foundationVersion =
    site?.status === "loaded" ? site.site.foundation.version : null;

  const siteReadFailure =
    site?.status === "not_found"
      ? "This site is no longer configured, so there is no foundation " +
        "version to freeze and no run can be set up."
      : site?.status === "unavailable"
        ? "The site store could not be read, so the foundation version this " +
          "run would freeze is unknown and no run can be set up."
        : null;

  const refusal = result?.status === "refused" ? result : null;
  const created = result?.status === "created" ? result.run : null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);

    const outcome = await runSetup.createRun({
      site_id: resolution.site_id as string,
      foundation_version: foundationVersion as number,
      scenario_id: detail.scenario_id,
      scenario_version: detail.version.scenario_version,
      interval: { start_time: form.startTime, end_time: form.endTime },
      timestep_minutes: typedWholeNumber(form.timestep),
      seed: typedWholeNumber(form.seed),
      model_profile: splitProfileKey(form.modelProfile),
      publication_profile: splitProfileKey(form.publicationProfile),
      run_inputs: runOwned.map((parameter) => ({
        parameter_id: parameter.parameter_id,
        value: typedQuantity(form.runInputs[parameter.parameter_id] ?? ""),
        unit: parameter.unit ?? "",
      })),
    });

    setResult(outcome);
    setSubmitting(false);
  }

  function update(field: keyof Omit<FormState, "runInputs">, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return frame(
    <>
      {explanation}

      <Panel
        heading="What the scenario and the site already fix"
        headingId="run-setup-fixed-heading"
      >
        {/*
         * Read from records, never typed. A run names the exact scenario
         * version and the exact foundation version it was set up against,
         * and choosing either of those is not run setup's to offer.
         */}
        <FactList>
          <Fact term="Scenario">{detail.scenario_id}</Fact>
          <Fact term="Scenario version">
            {String(detail.version.scenario_version)}
          </Fact>
          <Fact term="Site">{resolution.site_id}</Fact>
          <Fact term="Foundation version">
            {foundationVersion === null
              ? siteReadFailure ?? "Loading the configured site."
              : String(foundationVersion)}
          </Fact>
        </FactList>
      </Panel>

      <Panel heading="Run inputs" headingId="run-setup-form-heading">
        <form onSubmit={submit} aria-labelledby="run-setup-form-heading">
          <p className="toolbar__field">
            <label className="field-label" htmlFor="run-setup-start">
              Interval start
            </label>
            <input
              className="control"
              id="run-setup-start"
              name="start_time"
              value={form.startTime}
              aria-describedby="run-setup-interval-rule"
              onChange={(event) => update("startTime", event.target.value)}
            />
          </p>

          <p className="toolbar__field">
            <label className="field-label" htmlFor="run-setup-end">
              Interval end
            </label>
            <input
              className="control"
              id="run-setup-end"
              name="end_time"
              value={form.endTime}
              aria-describedby="run-setup-interval-rule"
              onChange={(event) => update("endTime", event.target.value)}
            />
            <span className="field-hint" id="run-setup-interval-rule">
              Two UTC instants, spelled as a date and a time with a trailing Z.
              The interval is half-open: it covers its start instant up to but
              not including its end instant.
            </span>
          </p>

          <p className="toolbar__field">
            <label className="field-label" htmlFor="run-setup-timestep">
              Timestep in minutes
            </label>
            <input
              className="control"
              id="run-setup-timestep"
              name="timestep_minutes"
              value={form.timestep}
              aria-describedby="run-setup-timestep-rule"
              onChange={(event) => update("timestep", event.target.value)}
            />
            <span className="field-hint" id="run-setup-timestep-rule">
              A whole number of minutes. The interval must be a whole multiple
              of it, so that no step runs past the end of the interval.
            </span>
          </p>

          <p className="toolbar__field">
            <label className="field-label" htmlFor="run-setup-seed">
              Seed
            </label>
            <input
              className="control"
              id="run-setup-seed"
              name="seed"
              value={form.seed}
              aria-describedby="run-setup-seed-rule"
              onChange={(event) => update("seed", event.target.value)}
            />
            <span className="field-hint" id="run-setup-seed-rule">
              A whole number. It is part of what makes a run reproducible, so
              it is chosen rather than defaulted.
            </span>
          </p>

          <p className="toolbar__field">
            <label className="field-label" htmlFor="run-setup-model-profile">
              Model profile
            </label>
            <select
              className="control"
              id="run-setup-model-profile"
              value={form.modelProfile}
              aria-describedby="run-setup-model-profile-rule"
              onChange={(event) => update("modelProfile", event.target.value)}
            >
              <option value="">Choose a model profile</option>
              {modelProfiles.map((profile) => (
                <option
                  key={profileKey(
                    profile.model_profile_id,
                    profile.model_profile_version,
                  )}
                  value={profileKey(
                    profile.model_profile_id,
                    profile.model_profile_version,
                  )}
                >
                  {profile.display_name}
                </option>
              ))}
            </select>
            <span className="field-hint" id="run-setup-model-profile-rule">
              The versioned model decides which world states can be executed.
              An input it does not model blocks the draft rather than being
              left out of it.
            </span>
          </p>

          <p className="toolbar__field">
            <label
              className="field-label"
              htmlFor="run-setup-publication-profile"
            >
              Publication profile
            </label>
            <select
              className="control"
              id="run-setup-publication-profile"
              value={form.publicationProfile}
              aria-describedby="run-setup-publication-profile-rule"
              onChange={(event) =>
                update("publicationProfile", event.target.value)
              }
            >
              <option value="">Choose a publication profile</option>
              {publicationProfiles.map((profile) => (
                <option
                  key={profileKey(
                    profile.publication_profile_id,
                    profile.publication_profile_version,
                  )}
                  value={profileKey(
                    profile.publication_profile_id,
                    profile.publication_profile_version,
                  )}
                >
                  {profile.display_name}
                </option>
              ))}
            </select>
            <span
              className="field-hint"
              id="run-setup-publication-profile-rule"
            >
              The versioned publication profile is the only thing that may
              resolve a reporting cadence, a simulator source identity, or a
              gateway identity. Nothing derives them from the site, from a
              device, or from how the site was created, so a profile that
              declares none blocks the draft.
            </span>
          </p>

          {profiles.status === "unavailable" ? (
            <p className="field-error" role="alert">
              The versioned profiles could not be read, so there is nothing to
              choose between and no run can be set up. This is a statement
              about the request that failed, not a statement that the build
              ships none.
            </p>
          ) : null}

          {runOwned.length === 0 ? (
            <p className="note">
              This scenario declares no value the run owns, so there is nothing
              further to supply. A value the scenario owns cannot be overridden
              here: that would be a second answer to a settled question.
            </p>
          ) : (
            runOwned.map((parameter) => (
              <p className="toolbar__field" key={parameter.parameter_id}>
                <label
                  className="field-label"
                  htmlFor={`run-input-${parameter.parameter_id}`}
                >
                  {parameter.display_name}
                  {parameter.unit === null ? "" : ` in ${parameter.unit}`}
                </label>
                <input
                  className="control"
                  id={`run-input-${parameter.parameter_id}`}
                  name={parameter.parameter_id}
                  value={form.runInputs[parameter.parameter_id] ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      runInputs: {
                        ...current.runInputs,
                        [parameter.parameter_id]: event.target.value,
                      },
                    }))
                  }
                />
                <span className="field-hint">
                  The scenario declares that the run owns this value, so it
                  must be supplied. Nothing defaults it.
                </span>
              </p>
            ))
          )}

          {refusal === null ? null : (
            <p className="field-error" role="alert">
              {refusal.message} No draft run was created and nothing was
              written.
            </p>
          )}

          {result?.status === "unavailable" ? (
            /*
             * The backend's sentence, or this screen's, and never both. Every
             * 503 branch already ends by saying nothing was written, so
             * appending it here printed it twice - "Nothing was written.
             * Nothing was written." on a real run-store failure. The fallback
             * says it because there is no message to say it.
             */
            <p className="field-error" role="alert">
              {result.message ??
                "The draft could not be created because the request could " +
                  "not be completed. Nothing was written."}
            </p>
          ) : null}

          {result?.status === "created_but_unreadable" ? (
            <p className="field-error" role="alert">
              A draft run was created and persisted, and this screen could not
              read the summary that came back, so none of it is shown below.
              Something was written: do not set the same run up again assuming
              nothing was.
            </p>
          ) : null}

          <p className="step-nav">
            <button
              className="action action--primary"
              type="submit"
              disabled={submitting || foundationVersion === null}
              aria-describedby={
                foundationVersion === null ? "run-setup-blocked-reason" : undefined
              }
            >
              Create draft run
            </button>
            {foundationVersion === null ? (
              <span
                className="action-list__reason"
                id="run-setup-blocked-reason"
              >
                {siteReadFailure ??
                  "The configured site has not been read yet, so the " +
                    "foundation version this run would freeze is not known."}
              </span>
            ) : null}
          </p>
        </form>
      </Panel>

      {created === null ? null : <CreatedDraft run={created} />}
    </>,
  );
}

/**
 * The setup summary: what was frozen, and whether it can be executed.
 *
 * Every digit here comes from the run record. The frozen input table is the
 * dense one on this screen - four columns, an unbreakable identity in one of
 * them and a sentence in another - so it keeps every column and scrolls
 * inside its own region, which the shared table primitive supplies.
 *
 * `T020` owns the run inventory and the run detail surface. This is the setup
 * summary for the draft that was just created and it is addressed by nothing:
 * there is no link to it, because a surface to link to does not exist yet.
 */
function CreatedDraft({ run }: { run: RunSummary }) {
  const blocked = run.execution_status === "BLOCKED";

  return (
    <>
      <Panel
        heading="The draft run this created"
        headingId="run-setup-created-heading"
      >
        <p role="status">
          A draft run was created and persisted. It has not been executed.
        </p>
        <FactList>
          <Fact term="Run ID">{run.run_id}</Fact>
          <Fact term="Lifecycle status">{run.lifecycle_status}</Fact>
          <Fact term="Execution status">{run.execution_status}</Fact>
          <Fact term="Created">{run.created_at}</Fact>
        </FactList>
        <p>
          The run identity is its own. It is not the site identity, not the
          scenario identity, and not a scenario label: it was allocated when
          the draft was created.
        </p>
      </Panel>

      <Panel
        heading="The frozen inputs"
        headingId="run-setup-frozen-heading"
        flush
      >
        <DataTable labelledBy="run-setup-frozen-heading">
          <thead>
            <tr>
              <th scope="col">Input</th>
              <th scope="col">Frozen value</th>
              <th scope="col">Answered by</th>
              <th scope="col">Which record answered</th>
            </tr>
          </thead>
          <tbody>
            {run.frozen_inputs.map((row) => (
              <tr key={`${row.identity_field}-${row.field}`}>
                <th scope="row">{row.field}</th>
                <td>{row.value}</td>
                <td>{row.answered_by}</td>
                <td className="cell-secondary">{row.answered_by_detail}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>

      {blocked ? (
        <Panel
          heading="Why this draft cannot be executed"
          headingId="run-setup-blocked-heading"
          flush
        >
          <DataTable labelledBy="run-setup-blocked-heading">
            <thead>
              <tr>
                <th scope="col">Reason</th>
                <th scope="col">What it is about</th>
                <th scope="col">Why</th>
              </tr>
            </thead>
            <tbody>
              {run.blocking_reasons.map((reason) => (
                <tr key={`${reason.kind}-${reason.subject}`}>
                  <th scope="row">{reason.kind}</th>
                  <td>{reason.subject}</td>
                  <td className="cell-secondary">{reason.statement}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      ) : (
        <Panel
          heading="This draft is ready"
          headingId="run-setup-ready-heading"
        >
          <p>
            The selected model profile can execute every input this scenario
            requires, and the publication profile resolved the cadence and both
            publication identities. Ready means the frozen inputs could be
            executed; it does not mean anything has been.
          </p>
        </Panel>
      )}

      {run.unsupported_optional_inputs.length === 0 ? null : (
        <Panel
          heading="Optional inputs this profile does not support"
          headingId="run-setup-optional-heading"
        >
          <ul className="cell-list">
            {run.unsupported_optional_inputs.map((item) => (
              <li key={`${item.state_key}-${item.execution_role}`}>
                {item.statement}
              </li>
            ))}
          </ul>
          <p>
            These are recorded rather than dropped. A run that quietly ignored
            part of a scenario would claim to have executed something it partly
            skipped.
          </p>
        </Panel>
      )}

      <Panel
        heading="What this draft is not"
        headingId="run-setup-not-heading"
      >
        <ul className="cell-list">
          <li>
            It has not been executed, so there is no state trajectory and no
            output of any kind.
          </li>
          <li>
            Nothing has been staged for a gateway, and no source envelope
            exists.
          </li>
          <li>
            It is a draft and it cannot be committed. Committing is what makes
            simulated history permanent and releases evidence from it, and no
            slice in this build can do either.
          </li>
          <li>
            No evidence has been accepted from it, and no operator surface
            shows anything because of it.
          </li>
          <li>
            No conclusion has been drawn from it. A draft run is an intention
            to simulate, not a result.
          </li>
        </ul>
      </Panel>
    </>
  );
}
