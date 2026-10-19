import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Fact, FactList, PageHeader, Panel } from "../ui";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../sites/siteDirectoryClient";
import type { SiteDetailResult, SiteListResult } from "../sites/siteReadModel";
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
import type {
  EvScenarioChoice,
  EvScenarioChoiceClient,
  EvScenarioChoicesResult,
} from "./evScenarioChoiceClient";
import type { CreateRunResult, RunSetupClient } from "./runSetupClient";
import { splitColdProfile } from "./ColdRunSetupFrame";
import {
  CreatedDraft,
  RegisteredBasisFacts,
  SitePicker,
  refusalLabel,
  registeredBasisProblem,
} from "./RunSetupFrame";

/**
 * W2-05b: set up a Draft run from one registered EV test run. A Simulator Lab
 * surface (`.agent/W2-05b-build-spec.md`, Run 1 rulings Q8-Q11).
 *
 * The Site is chosen first. Only a Site whose detail says `EV_CHARGING` reads
 * the EV choices, for that exact Site, and only the returned ones are offered;
 * the API separately checks registration. Choosing a row writes nothing;
 * **Create draft run** sends the chosen document's own values. It never enters
 * the legacy `RunSetupFrame` route and never uses that form's defaults.
 *
 * Paths arrive as props: this module must not spell a simulator URL.
 */
export interface EvRunSetupFrameProps {
  siteDirectory: SiteDirectoryClient;
  siteDetail: SiteDetailClient;
  templateLineage?: SiteTemplateLineageClient;
  evScenarios: EvScenarioChoiceClient;
  runSetup: RunSetupClient;
  simulatorLabPath: string;
  siteFoundation?: Pick<SiteFoundationClient, "getFoundation">;
}

export const EV_SITE_TYPE = "EV_CHARGING";
export const EV_CHOOSE_SITE_COPY = "Choose a site to see its EV test runs.";
export const EV_LOADING_COPY = "Loading the EV test runs.";
export const EV_NO_SELECTION_COPY =
  "Choose an EV test run first. Choosing one writes nothing.";
export const EV_EMPTY_COPY = "No EV test runs are available for this Site";
export const EV_FORBIDDEN_COPY = "EV test runs are not available for this Site";
export const EV_NOT_FOUND_COPY = "This Site could not be found";
export const EV_UNAVAILABLE_COPY = "EV test runs are temporarily unavailable";

const defaultSiteFoundation = createSiteFoundationClient();

export function EvRunSetupFrame({
  siteDirectory,
  siteDetail,
  templateLineage,
  evScenarios,
  runSetup,
  simulatorLabPath,
  siteFoundation = defaultSiteFoundation,
}: EvRunSetupFrameProps) {
  const [sites, setSites] = useState<SiteListResult | null>(null);
  const [siteDetails, setSiteDetails] = useState<
    Record<string, SiteDetailResult>
  >({});
  const lineage = useSiteTemplateLineage(templateLineage);
  /** The site the person picked. Never set by the screen itself. */
  const [chosenSiteId, setChosenSiteId] = useState<string | null>(null);
  const [choices, setChoices] = useState<EvScenarioChoicesResult | null>(null);
  const [retry, setRetry] = useState(0);
  const [chosenKey, setChosenKey] = useState<string | null>(null);
  const [basisRead, setBasisRead] = useState<{
    key: string;
    read: FoundationRead<FoundationReadModel>;
  } | null>(null);
  const [result, setResult] = useState<CreateRunResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  /** The Site the latest choice read was for; older answers are ignored. */
  const latestSite = useRef<string | null>(null);

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

  const chosenDetail =
    chosenSiteId === null ? undefined : siteDetails[chosenSiteId];
  const eligibility: "unknown" | "ev" | "other" | "not_found" | "unavailable" =
    chosenDetail === undefined
      ? "unknown"
      : chosenDetail.status === "loaded"
        ? chosenDetail.site.site_type === EV_SITE_TYPE
          ? "ev"
          : "other"
        : chosenDetail.status;

  // A retry after an unreadable Site detail reads that detail again.
  useEffect(() => {
    if (chosenSiteId === null || retry === 0 || eligibility !== "unavailable") {
      return;
    }
    let active = true;
    void siteDetail.getSite(chosenSiteId).then((loaded) => {
      if (active) {
        setSiteDetails((current) => ({ ...current, [chosenSiteId]: loaded }));
      }
    });
    return () => {
      active = false;
    };
    // Only an explicit retry re-reads; the directory effect reads the first time.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retry]);

  // The EV choices for exactly the chosen EV_CHARGING Site. A response for a
  // Site that is no longer chosen is dropped.
  useEffect(() => {
    latestSite.current = chosenSiteId;
    if (chosenSiteId === null || eligibility !== "ev") {
      return;
    }
    let active = true;
    void evScenarios.listEvScenarios(chosenSiteId).then((answer) => {
      if (!active || latestSite.current !== chosenSiteId) {
        return;
      }
      if (answer.status === "loaded" && answer.siteId !== chosenSiteId) {
        return;
      }
      setChoices(answer);
    });
    return () => {
      active = false;
    };
  }, [evScenarios, chosenSiteId, eligibility, retry]);

  const loadedChoices =
    choices?.status === "loaded" && choices.siteId === chosenSiteId
      ? choices.scenarios
      : null;
  const chosen =
    loadedChoices?.find(
      (choice) => `${choice.scenario_id}@${choice.scenario_version}` === chosenKey,
    ) ?? null;

  // The registered basis effective at the chosen document's start.
  const basisKey =
    chosenSiteId === null || chosen === null
      ? null
      : `${chosenSiteId}@${chosen.window.start}`;
  useEffect(() => {
    if (basisKey === null || chosenSiteId === null || chosen === null) {
      return;
    }
    let active = true;
    void siteFoundation
      .getFoundation(chosenSiteId, chosen.window.start)
      .then((read) => {
        if (active) {
          setBasisRead({ key: basisKey, read });
        }
      });
    return () => {
      active = false;
    };
    // `chosen` is derived each render; the key carries its identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siteFoundation, basisKey]);

  const basis =
    basisKey !== null && basisRead?.key === basisKey ? basisRead.read : null;
  const foundationVersion =
    basis?.status === "loaded" && basis.value.acquisition_snapshot.available
      ? basis.value.revision.version
      : null;
  const modelProfile = chosen === null ? null : splitColdProfile(chosen.model_profile);
  const publicationProfile =
    chosen === null ? null : splitColdProfile(chosen.publication_profile);

  /** The one choice-panel state, stated once there (Q9); null when rows are offered. */
  const panelState:
    | { kind: string; copy: string; retry: boolean; alert: boolean }
    | null =
    chosenSiteId === null
      ? { kind: "choose-site", copy: EV_CHOOSE_SITE_COPY, retry: false, alert: false }
      : eligibility === "not_found" || choices?.status === "not_found"
        ? { kind: "not-found", copy: EV_NOT_FOUND_COPY, retry: false, alert: true }
        : eligibility === "unavailable" || choices?.status === "unavailable"
          ? { kind: "unavailable", copy: EV_UNAVAILABLE_COPY, retry: true, alert: true }
          : choices?.status === "forbidden"
            ? { kind: "forbidden", copy: EV_FORBIDDEN_COPY, retry: false, alert: true }
            : eligibility === "other" ||
                (loadedChoices !== null && loadedChoices.length === 0)
              ? { kind: "empty", copy: EV_EMPTY_COPY, retry: false, alert: false }
              : loadedChoices === null
                ? { kind: "loading", copy: EV_LOADING_COPY, retry: false, alert: false }
                : null;
  const blockedReason =
    panelState !== null
      ? panelState.copy
      : chosen === null
        ? EV_NO_SELECTION_COPY
        : basis === null
          ? "Loading the registered configuration for the scenario start."
          : registeredBasisProblem(chosen.window.start, basis) ??
            (modelProfile === null || publicationProfile === null
              ? "The scenario's profile identities could not be read, so no run can be set up."
              : null);
  // Say it once: every choice-panel state is already stated in the EV test runs panel, so the
  // button stays disabled without repeating it beside it.
  const buttonReason = panelState !== null ? null : blockedReason;
  const canCreate =
    !submitting &&
    blockedReason === null &&
    chosen !== null &&
    foundationVersion !== null &&
    modelProfile !== null &&
    publicationProfile !== null;

  function chooseSite(siteId: string) {
    setChosenSiteId(siteId);
    setChoices(null);
    setChosenKey(null);
    setBasisRead(null);
    setResult(null);
  }

  async function create() {
    if (
      !canCreate ||
      chosenSiteId === null ||
      chosen === null ||
      foundationVersion === null ||
      modelProfile === null ||
      publicationProfile === null
    ) {
      return;
    }
    const siteAtSubmit = chosenSiteId;
    setSubmitting(true);
    setResult(null);
    const outcome = await runSetup.createRun({
      site_id: chosenSiteId,
      foundation_version: foundationVersion,
      scenario_id: chosen.scenario_id,
      scenario_version: chosen.scenario_version,
      interval: { start_time: chosen.window.start, end_time: chosen.window.end },
      timestep_minutes: 1,
      seed: chosen.seed,
      model_profile: modelProfile,
      publication_profile: publicationProfile,
      run_inputs: [],
    });
    setSubmitting(false);
    if (latestSite.current === siteAtSubmit) {
      setResult(outcome);
    }
  }

  const refusal = result?.status === "refused" ? result : null;
  const created = result?.status === "created" ? result.run : null;

  return (
    <main aria-labelledby="ev-run-setup-heading">
      <PageHeader
        title="Set up an EV charging draft run"
        headingId="ev-run-setup-heading"
        subtitle="Developer workspace"
      />

      <SitePicker
        sites={sites}
        siteDetails={siteDetails}
        lineage={lineage}
        chosenSiteId={chosenSiteId}
        onChoose={chooseSite}
      />

      <Panel heading="EV test runs" headingId="ev-run-setup-choices-heading">
        {panelState !== null ? (
          <>
            <p
              data-ev-choice-state={panelState.kind}
              role={panelState.alert ? "alert" : undefined}
            >
              {panelState.copy}
            </p>
            {panelState.retry ? (
              <p>
                <button
                  className="action"
                  type="button"
                  onClick={() => {
                    setChoices(null);
                    setRetry((count) => count + 1);
                  }}
                >
                  Retry
                </button>
              </p>
            ) : null}
          </>
        ) : (
          <fieldset className="site-picker" data-ev-choices="">
            <legend>EV test run</legend>
            {(loadedChoices ?? []).map((choice) => (
              <ChoiceRow
                key={`${choice.scenario_id}@${choice.scenario_version}`}
                choice={choice}
                chosen={chosen === choice}
                onChoose={() => {
                  setChosenKey(`${choice.scenario_id}@${choice.scenario_version}`);
                }}
              />
            ))}
          </fieldset>
        )}
      </Panel>

      {chosen === null ? null : (
        <Panel
          heading="What the EV test run fixes"
          headingId="ev-run-setup-facts-heading"
        >
          <FactList>
            <Fact term="Site">{chosenSiteId}</Fact>
            <Fact term="Scenario">{chosen.scenario_id}</Fact>
            <Fact term="Scenario version">{String(chosen.scenario_version)}</Fact>
            <Fact term="Interval start">{chosen.window.start}</Fact>
            <Fact term="Interval end">{chosen.window.end}</Fact>
            <Fact term="Seed">{String(chosen.seed)}</Fact>
            <Fact term="Timestep">1 minute</Fact>
            <Fact term="Model profile">{chosen.model_profile}</Fact>
            <Fact term="Publication profile">{chosen.publication_profile}</Fact>
            <Fact term="Observation profile">{chosen.observation_profile}</Fact>
            <Fact term="Foundation version">
              {foundationVersion === null ? "Not available" : String(foundationVersion)}
            </Fact>
            {basis?.status === "loaded" ? (
              <RegisteredBasisFacts model={basis.value} />
            ) : null}
          </FactList>
        </Panel>
      )}

      <Panel heading="Create the draft run" headingId="ev-run-setup-create-heading">
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
            type="button"
            disabled={!canCreate}
            aria-describedby={
              buttonReason === null ? undefined : "ev-run-setup-blocked-reason"
            }
            onClick={() => {
              void create();
            }}
          >
            Create draft run
          </button>
          {buttonReason === null ? null : (
            <span className="action-list__reason" id="ev-run-setup-blocked-reason">
              {buttonReason}
            </span>
          )}
        </p>
      </Panel>

      {created === null ? null : <CreatedDraft run={created} />}

      <p>
        <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
      </p>
    </main>
  );
}

function ChoiceRow({
  choice,
  chosen,
  onChoose,
}: {
  choice: EvScenarioChoice;
  chosen: boolean;
  onChoose: () => void;
}) {
  const inputId = `ev-run-setup-choice-${choice.scenario_id}-${choice.scenario_version}`;
  return (
    <p className="site-picker__row" data-ev-choice-row={choice.scenario_id}>
      <input
        type="radio"
        id={inputId}
        name="ev-run-setup-choice"
        value={`${choice.scenario_id}@${choice.scenario_version}`}
        checked={chosen}
        onChange={onChoose}
      />{" "}
      <label htmlFor={inputId}>
        {choice.display_name}
      </label>
    </p>
  );
}
