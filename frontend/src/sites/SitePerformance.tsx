/**
 * Site > Performance (T028): one subtab per served Performance capability,
 * and Dispatch as the only one at T028.
 *
 * The subtab row is the backend declaration (`/analytics`) presented through
 * the profile (`performanceSubtabs`, AC18 rules 1 and 2). The Dispatch body
 * lists every active assessed generator interval - Necessary, Candidate
 * avoidable and Indeterminate - in time order. Selecting one shows its binding
 * constraint or its missing evidence, and the policy, reserve and capability
 * at the interval's own time, then leads to its Finding. A Necessary interval
 * is an assessment without a Finding (owner ruling 2026-10-03), so it is
 * explained here and has no Finding link. Nothing is recomputed: each row is
 * the backend assessment by its `assessment_id`.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import { constraintWord } from "./FindingDetail";
import {
  boundText,
  ClaimBadge,
  confidenceWord,
  NextSteps,
  readablePeriod,
  windowText,
} from "./findingPresentation";
import {
  performanceSubtabs,
  type DomainPresentationProfile,
} from "./presentationProfile";
import type {
  Assessment,
  AssessmentSummary,
  DispatchAssessments,
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
}

export function SitePerformance({
  siteId,
  client,
  profile,
  capabilityId,
  subtabHref,
  findingHref,
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
    return <p>Loading the site&apos;s analytics.</p>;
  }
  if (declaration.status !== "loaded") {
    return (
      <Panel heading="Performance unavailable" headingId="site-performance-unavailable-heading">
        <p>
          {declaration.status === "unavailable" && declaration.message !== null
            ? declaration.message
            : "The site's analytic declaration could not be read."}
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
      <Panel heading="No performance analytic" headingId="site-performance-none-heading">
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
        <DispatchView siteId={siteId} client={client} findingHref={findingHref} />
      ) : (
        <Panel heading={current.label} headingId="site-performance-unbuilt-heading">
          <p>
            {`The backend serves the ${current.label} analytic, but this build has no screen for it yet.`}
          </p>
        </Panel>
      )}
    </div>
  );
}

type DispatchRow = AssessmentSummary & { assessment: Assessment };

function DispatchView({
  siteId,
  client,
  findingHref,
}: {
  siteId: string;
  client: SiteAnalyticsClient;
  findingHref: (assessmentId: string) => string;
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
            : "The dispatch assessments could not be read."}
        </p>
      </Panel>
    );
  }

  const rows = result.value.assessments;
  const selectedId = params.get("interval");
  const selected = rows.find((row) => row.assessment_id === selectedId) ?? null;
  const select = (id: string) => {
    const next = new URLSearchParams(params);
    next.set("interval", id);
    setParams(next);
  };

  return (
    <section aria-labelledby="site-dispatch-heading" className="dispatch-view">
      <h2 id="site-dispatch-heading" className="identity-heading">
        Was the generator needed?
      </h2>
      <p className="overview-note" data-dispatch-question>
        For each period the generator ran, this asks whether reported solar and
        battery capability could have carried the load. Each period is
        Necessary (an evidenced constraint required the generator), Candidate
        avoidable (capability exceeded load with no constraint evidenced; not
        proven waste) or Indeterminate (the evidence needed is missing or
        conflicting). A Necessary period is explained here and raises no Finding.
      </p>
      <Disclosure name="dispatch-method-details" summary="Method details">
        <p className="overview-note" data-dispatch-method>
          {`Analytic ${result.value.analytic_id}, model ${result.value.model_version}. Classified from accepted evidence only.`}
        </p>
      </Disclosure>
      {rows.length === 0 ? (
        <p data-dispatch-empty>
          No generator interval has been assessed from this site&apos;s accepted evidence.
        </p>
      ) : (
        <DataTable labelledBy="site-dispatch-heading">
          <thead>
            <tr>
              <th scope="col">Period</th>
              <th scope="col">Assessment</th>
              <th scope="col">Timeline</th>
              <th scope="col">Running time</th>
              <th scope="col">Reason</th>
              <th scope="col">Confidence</th>
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
                    {readablePeriod(
                      row.interval.first_running_observed,
                      row.interval.last_running_observed,
                    )}
                  </button>
                </th>
                <td>
                  <ClaimBadge level={row.claim_level} label={row.label} />
                </td>
                <td>
                  <SegmentStrip assessment={row.assessment} />
                </td>
                <td>{boundText(row.assessment.interval.duration_hours, "h")}</td>
                <td>{constraintOrGap(row.assessment)}</td>
                <td>{confidenceWord(row.confidence)}</td>
                <td>
                  {row.finding_id === null ? (
                    <span className="overview-note">No Finding (Necessary)</span>
                  ) : (
                    <Link to={findingHref(row.finding_id)} data-dispatch-finding-link={row.finding_id}>
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
        <SelectedInterval row={selected} findingHref={findingHref} />
      )}
    </section>
  );
}

function constraintOrGap(a: Assessment): string {
  if (a.claim_level === "INDETERMINATE" || a.binding_constraints.length === 0) {
    return a.missing_evidence.length === 0
      ? "No constraint evidenced"
      : `Missing: ${a.missing_evidence.join("; ")}`;
  }
  return a.binding_constraints.map(constraintWord).join(", ");
}

/** The interval's segments, sized by minutes and marked by their claim level. */
function SegmentStrip({ assessment }: { assessment: Assessment }) {
  return (
    <span
      className="segment-strip"
      role="img"
      aria-label={assessment.segments
        .map((s) => `${s.label} ${s.minutes} min`)
        .join(", ")}
    >
      {assessment.segments.map((segment, index) => (
        <span
          key={`${segment.start}-${index}`}
          className="segment-strip__part"
          data-claim-level={segment.classification}
          data-observed={segment.observed}
          style={{ flexGrow: Math.max(segment.minutes, 1) }}
        />
      ))}
    </span>
  );
}

function SelectedInterval({
  row,
  findingHref,
}: {
  row: DispatchRow;
  findingHref: (assessmentId: string) => string;
}) {
  const a = row.assessment;
  const first = a.segments.find((s) => s.inputs.at_start !== undefined)?.inputs.at_start;
  return (
    <Panel
      heading={`Period ${readablePeriod(a.interval.first_running_observed, a.interval.last_running_observed)}`}
      headingId="site-dispatch-selected-heading"
    >
      <div data-dispatch-selected={row.assessment_id}>
        <p>{a.summary}</p>
        {row.reading === undefined ? null : (
          <p data-dispatch-meaning>
            <ClaimBadge level={a.claim_level} label={a.label} /> {row.reading.meaning}
          </p>
        )}
        <FactList>
          <Fact term="Constraint requiring the generator">
            {a.binding_constraints.length === 0
              ? "None found"
              : a.binding_constraints.map(constraintWord).join(", ")}
          </Fact>
          <Fact term="Missing evidence">
            {a.missing_evidence.length === 0 ? "None named" : a.missing_evidence.join("; ")}
          </Fact>
          {first === undefined ? null : (
            <Fact term="At the interval's start">
              {`Load ${first.load_kw ?? "n/a"} kW; PV available ${first.pv_available_kw ?? "n/a"} kW; SOC ${first.soc_pct ?? "n/a"} %; reserve ${first.reserve_pct ?? "n/a"} %${first.reserve_source === null ? "" : ` (${first.reserve_source})`}; discharge capability ${first.discharge_capability_kw ?? "n/a"} kW; generator ${first.generator_kw ?? "n/a"} kW.`}
            </Fact>
          )}
          <Fact term="Period assessed">{windowText(a.assessed_window)}</Fact>
          <Fact term="Operator override">{a.alternatives[0]?.statement ?? "Not stated"}</Fact>
        </FactList>
        {row.reading === undefined ? null : (
          <>
            <h3 className="finding-section__heading">What to check next</h3>
            <NextSteps reading={row.reading} href={() => null} />
          </>
        )}
        {row.finding_id === null ? (
          <p className="overview-note">
            A Necessary interval is an assessment without a Finding: the
            binding constraint above is its explanation.
          </p>
        ) : (
          <p>
            <Link to={findingHref(row.finding_id)}>Open the Finding for this interval</Link>
          </p>
        )}
      </div>
    </Panel>
  );
}
