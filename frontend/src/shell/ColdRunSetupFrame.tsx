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
  ColdScenarioChoice,
  ColdScenarioChoiceClient,
  ColdScenarioChoicesResult,
} from "./coldScenarioChoiceClient";
import type { CreateRunResult, RunSetupClient } from "./runSetupClient";
import {
  CreatedDraft,
  RegisteredBasisFacts,
  SitePicker,
  refusalLabel,
  registeredBasisProblem,
} from "./RunSetupFrame";

/**
 * W2-02: set up a Draft run from one registered cold-chain scenario. A
 * Simulator Lab surface (`.agent/W2-02-build-spec.md`, "Cold Lab setup UI
 * closure").
 *
 * The Site is chosen first, then the cold choices are read for that exact
 * Site and only the returned ones are offered. Choosing a row writes nothing;
 * **Create draft run** sends the chosen document's own values. It never enters
 * the legacy `RunSetupFrame` route, which loads the legacy-only scenario
 * detail, and never uses that form's defaults.
 *
 * Paths arrive as props: this module must not spell a simulator URL.
 */
export interface ColdRunSetupFrameProps {
  siteDirectory: SiteDirectoryClient;
  siteDetail: SiteDetailClient;
  templateLineage?: SiteTemplateLineageClient;
  coldScenarios: ColdScenarioChoiceClient;
  runSetup: RunSetupClient;
  simulatorLabPath: string;
  siteFoundation?: Pick<SiteFoundationClient, "getFoundation">;
}

export const COLD_CHOOSE_SITE_COPY = "Choose a site to see its cold scenarios.";
export const COLD_EMPTY_COPY = "No cold scenarios are available for this site.";
export const COLD_UNAVAILABLE_COPY =
  "Cold scenarios are unavailable. The scenario or registration store could " +
  "not be read. No run was created. Try again.";

const defaultSiteFoundation = createSiteFoundationClient();

/** `cold-thermal/1` -> `{profile_id: "cold-thermal", profile_version: 1}`. */
export function splitColdProfile(
  identity: string,
): { profile_id: string; profile_version: number } | null {
  const slash = identity.lastIndexOf("/");
  if (slash <= 0) {
    return null;
  }
  const version = identity.slice(slash + 1);
  if (!/^[1-9][0-9]*$/.test(version)) {
    return null;
  }
  return {
    profile_id: identity.slice(0, slash),
    profile_version: Number(version),
  };
}

export function ColdRunSetupFrame({
  siteDirectory,
  siteDetail,
  templateLineage,
  coldScenarios,
  runSetup,
  simulatorLabPath,
  siteFoundation = defaultSiteFoundation,
}: ColdRunSetupFrameProps) {
  const [sites, setSites] = useState<SiteListResult | null>(null);
  const [siteDetails, setSiteDetails] = useState<
    Record<string, SiteDetailResult>
  >({});
  const lineage = useSiteTemplateLineage(templateLineage);
  /** The site the person picked. Never set by the screen itself. */
  const [chosenSiteId, setChosenSiteId] = useState<string | null>(null);
  const [choices, setChoices] = useState<ColdScenarioChoicesResult | null>(null);
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

  // The cold choices for exactly the chosen Site. A response for a Site that
  // is no longer chosen is dropped.
  useEffect(() => {
    latestSite.current = chosenSiteId;
    if (chosenSiteId === null) {
      return;
    }
    let active = true;
    void coldScenarios.listColdScenarios(chosenSiteId).then((answer) => {
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
  }, [coldScenarios, chosenSiteId, retry]);

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
      : `${chosenSiteId}@${chosen.start}`;
  useEffect(() => {
    if (basisKey === null || chosenSiteId === null || chosen === null) {
      return;
    }
    let active = true;
    void siteFoundation
      .getFoundation(chosenSiteId, chosen.start)
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

  const blockedReason =
    chosenSiteId === null
      ? COLD_CHOOSE_SITE_COPY
      : choices?.status === "unavailable"
        ? COLD_UNAVAILABLE_COPY
        : loadedChoices !== null && loadedChoices.length === 0
          ? COLD_EMPTY_COPY
          : chosen === null
            ? "Choose a cold scenario first. Choosing one writes nothing."
            : basis === null
              ? "Loading the registered configuration for the scenario start."
              : registeredBasisProblem(chosen.start, basis) ??
                (modelProfile === null || publicationProfile === null
                  ? "The scenario's profile identities could not be read, so no run can be set up."
                  : null);
  // Say it once (W2-02 review M2): the choose-site, unavailable and empty states are already stated in
  // the Cold scenarios panel, so the button stays disabled without repeating them beside it.
  const panelStatesReason =
    chosenSiteId === null ||
    choices?.status === "unavailable" ||
    (loadedChoices !== null && loadedChoices.length === 0);
  const buttonReason = panelStatesReason ? null : blockedReason;
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
      interval: { start_time: chosen.start, end_time: chosen.end },
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
    <main aria-labelledby="cold-run-setup-heading">
      <PageHeader
        title="Set up a cold-chain draft run"
        headingId="cold-run-setup-heading"
        subtitle="Developer workspace"
      />

      <SitePicker
        sites={sites}
        siteDetails={siteDetails}
        lineage={lineage}
        chosenSiteId={chosenSiteId}
        onChoose={chooseSite}
      />

      <Panel heading="Cold scenarios" headingId="cold-run-setup-choices-heading">
        {chosenSiteId === null ? (
          <p data-cold-choice-state="choose-site">{COLD_CHOOSE_SITE_COPY}</p>
        ) : choices?.status === "unavailable" ? (
          <>
            <p data-cold-choice-state="unavailable" role="alert">
              {COLD_UNAVAILABLE_COPY}
            </p>
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
          </>
        ) : loadedChoices === null ? (
          <p>Loading the cold scenarios.</p>
        ) : loadedChoices.length === 0 ? (
          <p data-cold-choice-state="empty">{COLD_EMPTY_COPY}</p>
        ) : (
          <fieldset className="site-picker" data-cold-choices="">
            <legend>Cold scenario</legend>
            {loadedChoices.map((choice) => (
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
          heading="What the cold scenario fixes"
          headingId="cold-run-setup-facts-heading"
        >
          <FactList>
            <Fact term="Site">{chosenSiteId}</Fact>
            <Fact term="Scenario">{chosen.scenario_id}</Fact>
            <Fact term="Scenario version">{String(chosen.scenario_version)}</Fact>
            <Fact term="Interval start">{chosen.start}</Fact>
            <Fact term="Interval end">{chosen.end}</Fact>
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

      <Panel heading="Create the draft run" headingId="cold-run-setup-create-heading">
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
              buttonReason === null ? undefined : "cold-run-setup-blocked-reason"
            }
            onClick={() => {
              void create();
            }}
          >
            Create draft run
          </button>
          {buttonReason === null ? null : (
            <span className="action-list__reason" id="cold-run-setup-blocked-reason">
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
  choice: ColdScenarioChoice;
  chosen: boolean;
  onChoose: () => void;
}) {
  const inputId = `cold-run-setup-choice-${choice.scenario_id}-${choice.scenario_version}`;
  return (
    <p className="site-picker__row" data-cold-choice-row={choice.scenario_id}>
      <input
        type="radio"
        id={inputId}
        name="cold-run-setup-choice"
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
