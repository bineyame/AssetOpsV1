/**
 * Site > Performance (T028): one subtab per served Performance capability,
 * and Dispatch as the only one at T028.
 *
 * The subtab row is the backend declaration (`/analytics`) presented through
 * the profile (`performanceSubtabs`, AC18 rules 1 and 2). Dispatch has two
 * contextual views (D-2026-10-04-plain-language-analysis-views), selected by
 * `?view=analysis` with the selected `interval` kept: Overview lists every
 * active assessed period in time order with its plain outcome, operating time
 * and main reason, and a selected period's concise explanation; Analysis
 * shows the shared assessment analysis of the selected period, which a Needed
 * period (no Finding, owner ruling 2026-10-03) needs most. Nothing is
 * recomputed: each row is the backend assessment by its `assessment_id`.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { DataTable, Fact, FactList, Panel } from "../ui";
import { AssessmentAnalysis } from "./assessmentAnalysis";
import { AssessedPeriodTimeline } from "./assessmentGraphics";
import {
  ClaimBadge,
  LocalViews,
  localView,
  localViewSearch,
  NextSteps,
  OUTCOME_WORDS,
  readablePeriod,
  type LocalView,
} from "./findingPresentation";
import {
  performanceSubtabs,
  type DomainPresentationProfile,
} from "./presentationProfile";
import type {
  Assessment,
  AssessmentSummary,
  DispatchAssessments,
  EvidenceLink,
  SiteAnalytics,
  SiteAnalyticsClient,
} from "./siteAnalyticsClient";
import type { EvidenceRead } from "./siteEvidenceClient";

export const PERFORMANCE_SUBTABS_LABEL = "Performance sections";

/** The served capability whose body this build can render. */
const RENDERABLE = new Set(["dispatch"]);

export interface SitePerformanceProps {
  siteId: string;
  client: SiteAnalyticsClient;
  profile: DomainPresentationProfile | null;
  /** The subtab in the address; the first served subtab when absent. */
  capabilityId: string | undefined;
  subtabHref: (capabilityId: string) => string;
  findingHref: (assessmentId: string) => string;
  /** The same Finding's Analysis tab. */
  findingAnalysisHref: (assessmentId: string) => string;
  /** One accepted record in the Site Evidence record inspector. */
  recordHref: (link: EvidenceLink) => string;
}

export function SitePerformance({
  siteId,
  client,
  profile,
  capabilityId,
  subtabHref,
  findingHref,
  findingAnalysisHref,
  recordHref,
}: SitePerformanceProps) {
  const [declaration, setDeclaration] = useState<EvidenceRead<SiteAnalytics> | null>(null);

  useEffect(() => {
    let active = true;
    setDeclaration(null);
    void client.getDeclaration(siteId).then((loaded) => {
      if (active) {
        setDeclaration(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId]);

  if (declaration === null) {
    return <p>Loading the site&apos;s assessments.</p>;
  }
  if (declaration.status !== "loaded") {
    return (
      <Panel heading="Performance unavailable" headingId="site-performance-unavailable-heading">
        <p>
          {declaration.status === "unavailable" && declaration.message !== null
            ? declaration.message
            : "The site's assessments could not be read."}
        </p>
      </Panel>
    );
  }

  const subtabs = performanceSubtabs(
    profile,
    declaration.value.analytics.map((item) => ({
      id: item.analytic_id,
      display_name: item.display_name,
    })),
  );
  if (subtabs.length === 0) {
    return (
      <Panel heading="No performance assessment" headingId="site-performance-none-heading">
        <p>{declaration.value.statement}</p>
      </Panel>
    );
  }
  const current = subtabs.find((item) => item.id === capabilityId) ?? subtabs[0];

  return (
    <div className="site-performance">
      <nav className="site-tabs site-subtabs" aria-label={PERFORMANCE_SUBTABS_LABEL}>
        <ol className="site-tabs__list">
          {subtabs.map((item) => (
            <li className="site-tabs__item" key={item.id}>
              <Link
                className="site-tabs__link"
                to={subtabHref(item.id)}
                data-performance-subtab={item.id}
                data-profile-known={item.known}
                data-emphasis={item.emphasis}
                aria-current={item.id === current.id ? "page" : undefined}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ol>
      </nav>
      {RENDERABLE.has(current.id) ? (
        <DispatchView
          siteId={siteId}
          client={client}
          findingHref={findingHref}
          findingAnalysisHref={findingAnalysisHref}
          recordHref={recordHref}
        />
      ) : (
        <Panel heading={current.label} headingId="site-performance-unbuilt-heading">
          <p>
            {`${current.label} results exist for this site, but this version has no screen for them yet.`}
          </p>
        </Panel>
      )}
    </div>
  );
}


type DispatchRow = AssessmentSummary & { assessment: Assessment };

export const DISPATCH_VIEWS_LABEL = "Dispatch views";

function DispatchView({
  siteId,
  client,
  findingHref,
  findingAnalysisHref,
  recordHref,
}: {
  siteId: string;
  client: SiteAnalyticsClient;
  findingHref: (assessmentId: string) => string;
  findingAnalysisHref: (assessmentId: string) => string;
  recordHref: (link: EvidenceLink) => string;
}) {
  const [result, setResult] = useState<EvidenceRead<DispatchAssessments> | null>(null);
  const [params, setParams] = useSearchParams();

  useEffect(() => {
    let active = true;
    setResult(null);
    void client.getDispatch(siteId).then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId]);

  if (result === null) {
    return <p>Loading the site&apos;s assessments.</p>;
  }
  if (result.status !== "loaded") {
    return (
      <Panel heading="Dispatch unavailable" headingId="site-dispatch-unavailable-heading">
        <p>
          {result.status === "unavailable" && result.message !== null
            ? result.message
            : "The assessed periods could not be read."}
        </p>
      </Panel>
    );
  }

  const rows = result.value.assessments;
  const view = localView(params);
  const selectedId = params.get("interval");
  const selected = rows.find((row) => row.assessment_id === selectedId) ?? null;
  const intervalSearch = (id: string, nextView: LocalView) => {
    const next = new URLSearchParams(params);
    next.set("interval", id);
    next.delete("part");
    return localViewSearch(next, nextView);
  };
  const select = (id: string) => {
    const next = new URLSearchParams(params);
    next.set("interval", id);
    next.delete("part");
    setParams(next);
  };
  const withoutSelection = new URLSearchParams(params);
  withoutSelection.delete("interval");
  const currentResults = localViewSearch(withoutSelection, "overview");

  return (
    <section aria-labelledby="site-dispatch-heading" className="dispatch-view">
      <h2 id="site-dispatch-heading" className="identity-heading">
        Was the generator needed?
      </h2>
      <LocalViews label={DISPATCH_VIEWS_LABEL} current={view} params={params} />
      {selectedId !== null && selected === null ? (
        <p data-dispatch-selected-missing>
          The selected assessed period is not among the current results: it may
          have been withdrawn or replaced. No other period has been put in its
          place. <Link to={{ search: currentResults }}>See the current results</Link>.
        </p>
      ) : null}
      {view === "analysis" ? (
        <DispatchAnalysis
          rows={rows}
          selected={selected}
          intervalSearch={intervalSearch}
          findingHref={findingHref}
          findingAnalysisHref={findingAnalysisHref}
          recordHref={recordHref}
        />
      ) : (
        <>
          <p className="overview-note" data-dispatch-question>
            For each period the generator operated, this asks whether the
            reported solar power and battery could have met the site demand
            instead. Each period, or part of one, is Needed (a recorded reason
            required the generator), Possibly avoidable (the reported solar power
            and battery output were more than the demand and no reason was
            recorded; not proof of wasted fuel) or Cannot determine (the records
            needed are missing or conflicting). A Needed period is explained here
            and has no Finding. Times are UTC.
          </p>
          {rows.length === 0 ? (
            <p data-dispatch-empty>
              No period of generator operation has been assessed from this
              site&apos;s accepted records.
            </p>
          ) : (
            <DataTable labelledBy="site-dispatch-heading">
              <thead>
                <tr>
                  <th scope="col">Period</th>
                  <th scope="col">Outcome</th>
                  <th scope="col">Timeline</th>
                  <th scope="col">Operating time</th>
                  <th scope="col">Main reason or missing information</th>
                  <th scope="col">Finding</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={row.assessment_id}
                    data-dispatch-interval={row.assessment_id}
                    data-claim-level={row.claim_level}
                    aria-selected={row.assessment_id === selectedId}
                  >
                    <th scope="row">
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => select(row.assessment_id)}
                      >
                        {readablePeriod(row.interval.first_running_observed, row.interval.last_running_observed)}
                      </button>
                    </th>
                    <td>
                      <ClaimBadge
                        level={row.claim_level}
                        label={row.reading?.outcome ?? OUTCOME_WORDS[row.claim_level] ?? "Assessed"}
                      />
                    </td>
                    <td>
                      <AssessedPeriodTimeline
                        compact
                        source={row.assessment}
                        outcomes={row.assessment.segments.map((_, i) => row.reading?.segments[i]?.outcome)}
                        assessmentId={row.assessment_id}
                      />
                    </td>
                    <td>{row.reading?.operating_time ?? "Not available"}</td>
                    <td data-dispatch-reason>{row.reading?.reason ?? "Not available"}</td>
                    <td>
                      {row.finding_id === null ? (
                        <span className="overview-note">No Finding (needed)</span>
                      ) : (
                        <Link
                          to={findingHref(row.finding_id)}
                          data-dispatch-finding-link={row.finding_id}
                        >
                          Open Finding
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
          {selected === null ? null : (
            <SelectedInterval
              row={selected}
              findingHref={findingHref}
              analysisSearch={intervalSearch(selected.assessment_id, "analysis")}
            />
          )}
        </>
      )}
    </section>
  );
}

function SelectedInterval({
  row,
  findingHref,
  analysisSearch,
}: {
  row: DispatchRow;
  findingHref: (assessmentId: string) => string;
  analysisSearch: string;
}) {
  const reading = row.reading;
  return (
    <Panel
      heading={`Period ${readablePeriod(row.interval.first_running_observed, row.interval.last_running_observed)}`}
      headingId="site-dispatch-selected-heading"
    >
      <div data-dispatch-selected={row.assessment_id}>
        {reading === undefined ? (
          <p>The plain reading of this period is not available.</p>
        ) : (
          <>
            <p>
              <strong>{reading.headline}</strong> {reading.reason}
            </p>
            <p data-dispatch-meaning className="overview-note">
              {reading.meaning}
            </p>
            <FactList>
              <Fact term="Generator operating time">{reading.operating_time}</Fact>
              <Fact term="Confidence">
                {reading.confidence.word}
                {reading.confidence.principal_limitation === null
                  ? ""
                  : `. ${reading.confidence.principal_limitation}`}
              </Fact>
              {reading.fuel.text === null ? null : (
                <Fact term={reading.fuel.label}>{`${reading.fuel.text}. ${reading.fuel.note}`}</Fact>
              )}
            </FactList>
            <ul className="cell-list" data-claim-limits>
              {reading.limits.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            <h3 className="finding-section__heading">What to check next</h3>
            <NextSteps reading={reading} href={() => null} />
          </>
        )}
        <ul className="cell-list">
          <li>
            <Link to={{ search: analysisSearch }} data-dispatch-analysis-link={row.assessment_id}>
              View the analysis of this period
            </Link>
          </li>
          <li>
            {row.finding_id === null ? (
              <span className="overview-note">
                A Needed period has no Finding: the reason above is its explanation.
              </span>
            ) : (
              <Link to={findingHref(row.finding_id)}>Open the Finding for this period</Link>
            )}
          </li>
        </ul>
      </div>
    </Panel>
  );
}

function DispatchAnalysis({
  rows,
  selected,
  intervalSearch,
  findingHref,
  findingAnalysisHref,
  recordHref,
}: {
  rows: DispatchRow[];
  selected: DispatchRow | null;
  intervalSearch: (id: string, view: LocalView) => string;
  findingHref: (assessmentId: string) => string;
  findingAnalysisHref: (assessmentId: string) => string;
  recordHref: (link: EvidenceLink) => string;
}) {
  if (rows.length === 0) {
    return (
      <p data-dispatch-analysis-empty>
        No period of generator operation has been assessed from this site&apos;s
        accepted records, so there is nothing to analyse yet.
      </p>
    );
  }
  return (
    <div data-dispatch-analysis={selected?.assessment_id ?? "none"}>
      <p className="overview-note">
        The analysis of one assessed period: how its outcome follows from the
        reported values. Choose a period:
      </p>
      <ul className="cell-list" data-dispatch-analysis-periods>
        {rows.map((row) => (
          <li key={row.assessment_id}>
            <Link
              to={{ search: intervalSearch(row.assessment_id, "analysis") }}
              aria-current={row.assessment_id === selected?.assessment_id ? "true" : undefined}
            >
              {`${readablePeriod(row.interval.first_running_observed, row.interval.last_running_observed)}: ${row.reading?.outcome ?? OUTCOME_WORDS[row.claim_level] ?? "Assessed"}`}
            </Link>
          </li>
        ))}
      </ul>
      {selected === null ? null : (
        <AssessmentAnalysis
          summary={selected}
          assessment={selected.assessment}
          records={{ kind: "record", href: recordHref }}
          alternativesHref={
            selected.finding_id === null ? null : `${findingHref(selected.finding_id)}/alternatives`
          }
          links={
            selected.finding_id === null ? null : (
              <li>
                <Link to={findingAnalysisHref(selected.finding_id)}>
                  Open this period&apos;s Finding
                </Link>
              </li>
            )
          }
        />
      )}
    </div>
  );
}
