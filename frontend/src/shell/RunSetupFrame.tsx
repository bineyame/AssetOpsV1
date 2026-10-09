import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable, Fact, FactList, PageHeader, Panel } from "../ui";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../sites/siteDirectoryClient";
import type {
  SiteDetailResult,
  SiteListResult,
  SiteSummary,
} from "../sites/siteReadModel";
import {
  useSiteTemplateLineage,
  type SiteTemplateLineageClient,
} from "../sites/siteTemplateLineage";
import {
  createSiteFoundationClient,
  type FoundationRead,
  type FoundationReadModel,
  type SiteFoundationClient,
} from "../sites/siteFoundationClient";
import { TemplateProvenanceText } from "../sites/TemplateProvenanceText";
import { deriveSiteView } from "../sites/siteViewModel";
import type {
  ScenarioCatalogClient,
  ScenarioDetail,
  ScenarioDetailResult,
  ScenarioParameter,
} from "./scenarioCatalogClient";
import {
  templateLineageText,
  type CreateRunResult,
  type RunProfilesResult,
  type RunPublicationProfile,
  type RunSetupClient,
  type RunSummary,
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
 * ## What the form chooses, and how it says so
 *
 * T019 left every field empty, because M4 found the browser auto-selecting
 * two components of the frozen deterministic identity while the screen said
 * nothing was prefilled. The defect was never that fields were filled: it was
 * that a person could not tell the form had chosen. The user settled the
 * constraint at that review, and T020 implements it - **a default is visible,
 * labelled as a default, and still changeable**.
 *
 * So each field that can be honestly defaulted arrives with a value AND with
 * a mark beside the control saying what the default was. The mark stays after
 * a person edits the field, because "the form chose 15 and you typed 30" is
 * more useful than a mark that disappears the moment it stops being true.
 *
 * Two of them are derived from records rather than chosen: the interval's
 * length comes from the scenario's own last entry, rounded up to a whole
 * number of timesteps, so the default covers the scenario it is for. The
 * start instant and the seed come from the clock, and the timestep is a
 * chosen number; all three are marked.
 *
 * **A value the scenario declares the run owns is never defaulted.** It is an
 * initial world value, and a form supplying one is the fabricated default run
 * setup refuses over. Those fields arrive empty however many of them there
 * are.
 *
 * Nothing is validated here either. The backend owns every rule and this
 * screen renders what it says, so a refusal is the product copy that names
 * what is wrong rather than a message written twice.
 *
 * ## The site is chosen here, and only here
 *
 * A scenario names no site (T025g, `D-2026-10-01-run-binds-scenario-to-site`),
 * so this screen does not derive one from it. It opens with no site selected,
 * never selects one for the person - not even when exactly one is configured -
 * and keeps Create disabled until a site is picked. Each row shows the site's
 * Foundation version and its template lineage with T025f's staleness note. No
 * row is filtered or disabled for being unable to honour the scenario: a
 * BLOCKED draft is a truthful record of what the chosen site lacks, and
 * computing compatibility here would be a second matcher beside run setup.
 *
 * ## Paths arrive as props
 *
 * This module must not spell a simulator URL: the single chokepoint in
 * `simulatorLabRoutes.tsx` is what keeps a Lab surface from being addressable
 * outside the gate.
 */
export interface RunSetupFrameProps {
  catalog: ScenarioCatalogClient;
  /** Every configured site, for the picker. */
  siteDirectory: SiteDirectoryClient;
  /** One site's Foundation version, read for each listed site. */
  siteDetail: SiteDetailClient;
  /**
   * T025f's template-lineage answers, for the staleness note on each picker
   * row. Optional: without it the rows show the recorded lineage alone.
   */
  templateLineage?: SiteTemplateLineageClient;
  runSetup: RunSetupClient;
  scenariosPath: string;
  simulatorLabPath: string;
  scenarioHref: (scenarioId: string) => string;
  /** Injected so a test can pin the day the defaults are derived from. */
  now?: () => Date;
  /**
   * S2-01a: the registered Site configuration effective at the run's start,
   * read for a registered Site only. Defaults to the product client.
   */
  siteFoundation?: Pick<SiteFoundationClient, "getFoundation">;
}

/** A whole-second UTC instant, the only start the setup request accepts. */
const UTC_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

const defaultSiteFoundation = createSiteFoundationClient();

/** Whether this Site is answered by the registered configuration store. */
export function isRegisteredSite(summary: SiteSummary | undefined | null): boolean {
  return summary?.configuration_store === "POSTGRES";
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

/** The timestep the form offers when nobody has chosen one. */
export const DEFAULT_TIMESTEP_MINUTES = 15;

/** Two digits of day, as `YYYY-MM-DD`, from an instant. */
function isoDay(at: Date): string {
  return at.toISOString().slice(0, 10);
}

/**
 * The interval the form offers, derived from the scenario it is for.
 *
 * The length is not chosen: it is the scenario's own last moment - the latest
 * offset any entry reaches, window lengths included - plus one timestep,
 * rounded up to a whole number of timesteps. A run's interval is half-open,
 * so an entry exactly at the end instant would fall outside it; the extra
 * step is what keeps the default an interval that covers the scenario rather
 * than one that refuses it.
 *
 * The start instant is midnight UTC today. That one is a clock reading and
 * has no record behind it, which is exactly why the field says it is a
 * default.
 */
export function defaultInterval(
  scenario: ScenarioDetail,
  now: Date,
  timestepMinutes: number = DEFAULT_TIMESTEP_MINUTES,
): { startTime: string; endTime: string } {
  const lastMoment = scenario.timeline.reduce((latest, entry) => {
    const ends = entry.offset_minutes + (entry.timing.duration_minutes ?? 0);
    return Math.max(latest, ends);
  }, 0);

  const steps = Math.floor(lastMoment / timestepMinutes) + 1;
  const start = new Date(`${isoDay(now)}T00:00:00Z`);
  const end = new Date(start.getTime() + steps * timestepMinutes * 60_000);

  return {
    startTime: `${start.toISOString().slice(0, 19)}Z`,
    endTime: `${end.toISOString().slice(0, 19)}Z`,
  };
}

/**
 * The seed the form offers: today's date with its separators removed.
 *
 * A seed has to be chosen by somebody and nothing in any record supplies one.
 * A date is at least explicable to the next person reading the run, which an
 * arbitrary constant is not.
 */
export function defaultSeed(now: Date): string {
  return isoDay(now).replace(/-/g, "");
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
  siteDirectory,
  siteDetail,
  templateLineage,
  runSetup,
  scenariosPath,
  simulatorLabPath,
  scenarioHref,
  now = () => new Date(),
  siteFoundation = defaultSiteFoundation,
}: RunSetupFrameProps) {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [scenario, setScenario] = useState<ScenarioDetailResult | null>(null);
  const [profiles, setProfiles] = useState<RunProfilesResult | null>(null);
  const [sites, setSites] = useState<SiteListResult | null>(null);
  const [siteDetails, setSiteDetails] = useState<
    Record<string, SiteDetailResult>
  >({});
  /** The site the person picked. Never set by the screen itself. */
  const [chosenSiteId, setChosenSiteId] = useState<string | null>(null);
  const [registeredRead, setRegisteredRead] = useState<{
    key: string;
    read: FoundationRead<FoundationReadModel>;
  } | null>(null);
  const lineage = useSiteTemplateLineage(templateLineage);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [result, setResult] = useState<CreateRunResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  /**
   * What the form chose, by field. Kept after an edit rather than cleared,
   * so the screen can still say what the default was.
   */
  const [defaults, setDefaults] = useState<Record<string, string>>({});

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
      if (!active) {
        return;
      }
      setProfiles(loaded);
      if (loaded.status !== "loaded") {
        return;
      }

      // A default only where there is exactly one option. With two, the form
      // would be choosing between them, and which model profile a run froze
      // decides whether it is READY - that is the choice M4 found being made
      // for people, and one option is not a choice.
      const model =
        loaded.modelProfiles.length === 1 ? loaded.modelProfiles[0] : null;
      const publication =
        loaded.publicationProfiles.length === 1
          ? loaded.publicationProfiles[0]
          : null;

      if (model !== null) {
        const key = profileKey(
          model.model_profile_id,
          model.model_profile_version,
        );
        setForm((current) => ({ ...current, modelProfile: key }));
        setDefaults((current) => ({
          ...current,
          modelProfile: model.display_name,
        }));
      }
      if (publication !== null) {
        const key = profileKey(
          publication.publication_profile_id,
          publication.publication_profile_version,
        );
        setForm((current) => ({ ...current, publicationProfile: key }));
        setDefaults((current) => ({
          ...current,
          publicationProfile: publication.display_name,
        }));
      }
    });

    return () => {
      active = false;
    };
  }, [catalog, runSetup, scenarioId]);

  // The interval is derived from the scenario, so it waits for the scenario
  // rather than being chosen at mount. The timestep and the seed do not need
  // it, and are set here too so that every default arrives at once - a form
  // that filled itself in stages would show a person two different forms.
  useEffect(() => {
    if (scenario?.status !== "loaded") {
      return;
    }
    const at = now();
    const interval = defaultInterval(scenario.scenario, at);
    const seed = defaultSeed(at);
    const timestep = String(DEFAULT_TIMESTEP_MINUTES);

    setForm((current) => ({
      ...current,
      startTime: interval.startTime,
      endTime: interval.endTime,
      timestep,
      seed,
    }));
    setDefaults((current) => ({
      ...current,
      startTime: interval.startTime,
      endTime: interval.endTime,
      timestep,
      seed,
    }));
    // `now` is a prop with a default value, so it changes identity on every
    // render; the scenario is what this depends on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  // S2-01a: for a registered Site, the configuration its registry selects at
  // the run's start, so the screen shows the basis the Draft will freeze.
  const startForRead = form.startTime;
  const registeredSiteId =
    sites?.status === "loaded" &&
    isRegisteredSite(sites.sites.find((s) => s.site_id === chosenSiteId))
      ? chosenSiteId
      : null;
  useEffect(() => {
    if (registeredSiteId === null || !UTC_INSTANT.test(startForRead)) {
      return;
    }
    let active = true;
    const key = `${registeredSiteId}@${startForRead}`;
    void siteFoundation
      .getFoundation(registeredSiteId, startForRead)
      .then((read) => {
        if (active) {
          setRegisteredRead({ key, read });
        }
      });
    return () => {
      active = false;
    };
  }, [siteFoundation, registeredSiteId, startForRead]);

  // Every configured site, then each one's Foundation version. Read for the
  // picker, never chosen from: the effect sets no selection.
  useEffect(() => {
    let active = true;

    void siteDirectory.listSites().then((listed) => {
      if (!active) {
        return;
      }
      setSites(listed);
      if (listed.status !== "loaded") {
        return;
      }
      for (const summary of listed.sites) {
        void siteDetail.getSite(summary.site_id).then((loaded) => {
          if (active) {
            // Every outcome, not only the one that works. An earlier version
            // kept the loading text forever when the read failed, left submit
            // enabled, and sent a foundation version of NaN.
            setSiteDetails((current) => ({
              ...current,
              [summary.site_id]: loaded,
            }));
          }
        });
      }
    });

    return () => {
      active = false;
    };
  }, [siteDirectory, siteDetail]);

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

  // The form waits for its derived defaults too, so it never renders once
  // without them. Before T025g the site read covered that gap; the picker reads
  // no site until one is listed, so the wait is stated here.
  if (
    scenario === null ||
    profiles === null ||
    (scenario.status === "loaded" && defaults.startTime === undefined)
  ) {
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
  const site = chosenSiteId === null ? null : siteDetails[chosenSiteId] ?? null;
  const registered = registeredSiteId !== null;
  const registeredKey = `${chosenSiteId ?? ""}@${form.startTime}`;
  const registeredBasis =
    registered && registeredRead?.key === registeredKey ? registeredRead.read : null;
  // A registered Site's version is the one its registered configuration
  // selects at the run's start, never the version effective today.
  const foundationVersion = registered
    ? registeredBasis?.status === "loaded" &&
      registeredBasis.value.acquisition_snapshot.available
      ? registeredBasis.value.revision.version
      : null
    : site?.status === "loaded"
      ? site.site.foundation.version
      : null;

  const siteReadFailure =
    chosenSiteId === null
      ? "Choose the site this run binds to first. No site is chosen for you."
      : site?.status === "not_found"
      ? "This site is no longer configured, so there is no foundation " +
        "version to freeze and no run can be set up."
      : site?.status === "unavailable"
        ? "The site store could not be read, so the foundation version this " +
          "run would freeze is unknown and no run can be set up."
        : registered
          ? registeredBasisProblem(form.startTime, registeredBasis)
          : null;

  const refusal = result?.status === "refused" ? result : null;
  const created = result?.status === "created" ? result.run : null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setResult(null);

    const outcome = await runSetup.createRun({
      site_id: chosenSiteId as string,
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

  /**
   * The mark that says this value is one the form chose.
   *
   * Rendered inside the field's own block and tied to the control with
   * `aria-describedby`, rather than left to a paragraph elsewhere on the
   * screen: a person looking at a filled field has to be able to see, there,
   * that nobody filled it. It keeps saying what the default WAS after an
   * edit, which is more useful than a mark that vanishes.
   */
  function defaultMark(field: string) {
    const chosen = defaults[field];
    if (chosen === undefined) {
      return null;
    }
    return (
      <span className="field-default" id={`run-setup-${field}-default`}>
        Default, chosen by this form: {chosen}
      </span>
    );
  }

  /** Every id a control is described by, defaults included. */
  function describedBy(field: string, ...ids: string[]) {
    const all = [...ids];
    if (defaults[field] !== undefined) {
      all.push(`run-setup-${field}-default`);
    }
    return all.length === 0 ? undefined : all.join(" ");
  }

  return frame(
    <>
      {explanation}

      <SitePicker
        sites={sites}
        siteDetails={siteDetails}
        lineage={lineage}
        chosenSiteId={chosenSiteId}
        onChoose={(siteId) => {
          setChosenSiteId(siteId);
          setResult(null);
        }}
      />

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
          <Fact term="Site">{chosenSiteId ?? "Not chosen yet"}</Fact>
          <Fact term="Foundation version">
            {foundationVersion === null
              ? siteReadFailure ?? "Loading the chosen site."
              : String(foundationVersion)}
          </Fact>
          {registered && registeredBasis?.status === "loaded" ? (
            <RegisteredBasisFacts model={registeredBasis.value} />
          ) : null}
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
              aria-describedby={describedBy(
                "startTime",
                "run-setup-interval-rule",
              )}
              onChange={(event) => update("startTime", event.target.value)}
            />
            {defaultMark("startTime")}
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
              aria-describedby={describedBy(
                "endTime",
                "run-setup-interval-rule",
              )}
              onChange={(event) => update("endTime", event.target.value)}
            />
            {defaultMark("endTime")}
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
              aria-describedby={describedBy(
                "timestep",
                "run-setup-timestep-rule",
              )}
              onChange={(event) => update("timestep", event.target.value)}
            />
            {defaultMark("timestep")}
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
              aria-describedby={describedBy("seed", "run-setup-seed-rule")}
              onChange={(event) => update("seed", event.target.value)}
            />
            {defaultMark("seed")}
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
              aria-describedby={describedBy(
                "modelProfile",
                "run-setup-model-profile-rule",
              )}
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
            {defaultMark("modelProfile")}
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
              aria-describedby={describedBy(
                "publicationProfile",
                "run-setup-publication-profile-rule",
              )}
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
            {defaultMark("publicationProfile")}
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
          <ProfileResolution
            profile={publicationProfiles.find(
              (profile) =>
                profileKey(
                  profile.publication_profile_id,
                  profile.publication_profile_version,
                ) === form.publicationProfile,
            )}
          />

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
            <p
              className="field-error"
              role="alert"
              data-setup-refusal-kind={refusal.refusalKind ?? undefined}
              data-setup-refusal-reason={refusal.reasonCode ?? undefined}
            >
              {refusalLabel(refusal.refusalKind)}
              {refusal.message} No draft run was created and nothing was
              written.
              {refusal.reasonCode ? (
                <span className="cell-secondary">
                  {" "}
                  Reason code: {refusal.reasonCode}.
                </span>
              ) : null}
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
                  "The chosen site has not been read yet, so the " +
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
 * The site this run binds to, chosen by the person and by nobody else.
 *
 * Opens with nothing selected and selects nothing on its own, even with one
 * site. Every configured site is a row with its Foundation version and its
 * template lineage, plus T025f's staleness note when the lineage answer says
 * the record is behind. No row is disabled: a site that cannot honour the
 * scenario gives a BLOCKED draft naming what it lacks, which is a truthful
 * record. A site whose Foundation version could not be read can be picked, and
 * Create then stays disabled with that reason.
 */
function SitePicker({
  sites,
  siteDetails,
  lineage,
  chosenSiteId,
  onChoose,
}: {
  sites: SiteListResult | null;
  siteDetails: Record<string, SiteDetailResult>;
  lineage: ReturnType<typeof useSiteTemplateLineage>;
  chosenSiteId: string | null;
  onChoose: (siteId: string) => void;
}) {
  return (
    <Panel
      heading="Choose the site this run binds to"
      headingId="run-setup-site-heading"
    >
      <p>
        A scenario names no site. The run is the only place a scenario version
        and a site version meet, so you choose the site here and nothing is
        chosen for you. Run setup then checks what the scenario needs against
        the site you pick: a site that cannot honour it still gives a draft,
        marked blocked, that names what the site lacks.
      </p>
      {sites === null ? (
        <p>Loading the configured sites.</p>
      ) : sites.status === "unavailable" ? (
        <p>
          The site store could not be read, so there is no site to choose and
          no run can be set up.
        </p>
      ) : sites.sites.length === 0 ? (
        <p>
          No site is configured, so there is no site to bind a run to. Create a
          site first.
        </p>
      ) : (
        <fieldset className="site-picker" data-site-picker="">
          <legend>Site</legend>
          {sites.sites.map((summary) => (
            <SitePickerRow
              key={summary.site_id}
              summary={summary}
              detail={siteDetails[summary.site_id]}
              lineage={lineage?.get(summary.site_id)}
              chosen={chosenSiteId === summary.site_id}
              onChoose={onChoose}
            />
          ))}
        </fieldset>
      )}
    </Panel>
  );
}

/**
 * Why a registered Site's basis is not available for this start, or null.
 */
function registeredBasisProblem(
  startTime: string,
  read: FoundationRead<FoundationReadModel> | null,
): string | null {
  if (!UTC_INSTANT.test(startTime)) {
    return (
      "This site uses its registered configuration, which is chosen by the " +
      "run's start time. Enter a start time to see which configuration applies."
    );
  }
  if (read === null) {
    return "Reading the registered configuration for this start time.";
  }
  if (read.status !== "loaded") {
    const message =
      "message" in read && read.message
        ? read.message
        : "The registered configuration could not be read for this start time.";
    return `${message} No run can be set up from it.`;
  }
  const snapshot = read.value.acquisition_snapshot;
  if (!snapshot.available) {
    return (
      `No complete registered configuration applies at this start time ` +
      `(${snapshot.code}): ${snapshot.reason} No run can be set up from it.`
    );
  }
  return null;
}

/**
 * The registered configuration the run's start selects, shown before setup.
 *
 * Setup selects it again and checks it covers the whole interval; this read is
 * what the Draft will freeze when it does.
 */
function RegisteredBasisFacts({ model }: { model: FoundationReadModel }) {
  const snapshot = model.acquisition_snapshot;
  const bindings = model.bindings.binding_set;
  return (
    <>
      <Fact term="Configuration">
        <span data-setup-registered-basis="">
          Registered configuration, chosen by the run's start time
        </span>
      </Fact>
      <Fact term="Foundation revision">
        {`Version ${model.revision.version}, valid from ${model.revision.valid_from}` +
          (model.revision.valid_to === null ? "" : ` to ${model.revision.valid_to}`)}
      </Fact>
      <Fact term="Signal bindings">
        {bindings === null
          ? "None registered"
          : `Version ${bindings.version}, valid from ${bindings.valid_from}` +
            (bindings.valid_to === null ? "" : ` to ${bindings.valid_to}`)}
      </Fact>
      {snapshot.available ? (
        <Fact term="Configuration snapshot">
          <code>{snapshot.sha256}</code> ({snapshot.schema})
        </Fact>
      ) : null}
    </>
  );
}

function SitePickerRow({
  summary,
  detail,
  lineage,
  chosen,
  onChoose,
}: {
  summary: SiteSummary;
  detail: SiteDetailResult | undefined;
  lineage: Parameters<typeof TemplateProvenanceText>[0]["lineage"];
  chosen: boolean;
  onChoose: (siteId: string) => void;
}) {
  const view = deriveSiteView(summary);
  const foundation =
    detail === undefined
      ? "Loading the site's Foundation version."
      : detail.status === "loaded"
        ? `Foundation version ${detail.site.foundation.version}`
        : detail.status === "not_found"
          ? "Foundation version: this site is no longer configured"
          : "Foundation version: the site store could not be read";
  const inputId = `run-setup-site-${summary.site_id}`;
  return (
    <p className="site-picker__row" data-site-picker-row={summary.site_id}>
      <input
        type="radio"
        id={inputId}
        name="run-setup-site"
        value={summary.site_id}
        checked={chosen}
        onChange={() => onChoose(summary.site_id)}
      />{" "}
      <label htmlFor={inputId}>
        {summary.display_name} ({summary.site_id})
      </label>
      <span className="cell-secondary" data-site-picker-foundation="">
        {foundation}
      </span>
      {summary.configuration_store === undefined ? null : (
        <span
          className="cell-secondary"
          data-site-picker-store={summary.configuration_store}
        >
          {isRegisteredSite(summary)
            ? "Registered configuration"
            : "Legacy Site file"}
        </span>
      )}
      <span className="cell-secondary" data-site-picker-lineage="">
        Created from template:{" "}
        <TemplateProvenanceText
          site={summary}
          provenance={view.templateProvenance}
          lineage={lineage}
        />
      </span>
    </p>
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
          <Fact term="Site template lineage">
            {templateLineageText(run.template_lineage)}
          </Fact>
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
            It is a draft and it has not been committed. Commit seals what an
            execution staged and releases it, and a draft nothing
            has executed has nothing staged to commit.
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

/**
 * S2-01b: a plain lead-in for the two publication-profile refusals a
 * registered Draft can meet; every other refusal's message stands alone.
 */
function refusalLabel(kind: string | null): string | null {
  if (kind === "PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE") {
    return "This publication profile needs a registered Site. ";
  }
  if (kind === "PUBLICATION_UNIT_MISMATCH") {
    return "A unit in this publication profile does not match the Site's registered binding. ";
  }
  return null;
}

/**
 * S2-01b: what the chosen profile's simulated devices round to before they
 * publish, so the person choosing it sees that the Lab reports are rounded
 * readings and not exact world values.
 */
function ProfileResolution({ profile }: { profile: RunPublicationProfile | undefined }) {
  const resolutions = profile?.device_resolutions ?? [];
  if (profile === undefined || (resolutions.length === 0 && !profile.requires_registered_site)) {
    return null;
  }
  const steps = Array.from(new Set(resolutions.map((item) => item.resolution)));
  return (
    <p
      className="note"
      data-setup-profile-resolution={steps.join(" ")}
      data-setup-profile-registered-only={profile.requires_registered_site ? "" : undefined}
    >
      {resolutions.length === 0
        ? null
        : `Simulated devices round each numeric reading half-to-even to ${steps.join(" or ")} in that signal's own unit before publishing it (${resolutions.length} signals). Status readings are not rounded. `}
      {profile.requires_registered_site
        ? "Only a draft on a registered Site can use this profile, because each unit is checked against the Site's registered binding."
        : null}
    </p>
  );
}
