/**
 * Finding detail (T028): the trust-defining page. It renders one backend
 * assessment by its `assessment_id` - the same object Performance > Dispatch
 * and the Overview card name - and recomputes nothing.
 *
 * Tabs: `Overview | Evidence | Alternatives`
 * (`D-2026-10-02-rendered-tabs-per-capability`; Recommendation and History
 * are not rendered until T034). The Overview follows the recommendation's
 * hierarchy (section 3 "Finding Detail"): the bounded claim, observed facts
 * apart from inference, confidence and its basis apart from coverage, the
 * claim ceiling, the consequence as a technical quantity only (no money:
 * T029), and the next step. Evidence lists the claims, each opening the claim
 * drawer; Alternatives lists the competing explanations and why each is
 * observed, left open or contradicted.
 *
 * Everything shown is reconstructible from accepted evidence with the
 * Simulator Lab off: this module reads the operator analytics and evidence
 * routes only.
 */
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Fact, FactList, Panel } from "../ui";
import {
  boundText,
  ClaimBadge,
  ClaimDrawer,
  confidenceWord,
  EvidenceLinks,
  Section,
  windowText,
  type OpenRecord,
} from "./findingPresentation";
import type { DomainPresentationProfile } from "./presentationProfile";
import { findingTypeLabel } from "./presentationProfile";
import type {
  Assessment,
  AssessmentDetail,
  SiteAnalyticsClient,
} from "./siteAnalyticsClient";
import type { EvidenceRead, SiteEvidenceClient } from "./siteEvidenceClient";

export type FindingDetailTab = "overview" | "evidence" | "alternatives";

export const FINDING_DETAIL_TABS: { id: FindingDetailTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "evidence", label: "Evidence" },
  { id: "alternatives", label: "Alternatives" },
];

export const FINDING_TABS_LABEL = "Finding sections";

export interface FindingDetailProps {
  siteId: string;
  assessmentId: string;
  tab: FindingDetailTab;
  client: SiteAnalyticsClient;
  evidence: SiteEvidenceClient;
  profile: DomainPresentationProfile | null;
  tabHref: (tab: FindingDetailTab) => string;
  dispatchHref: string;
  evidencePageHref: string;
  /** Lets the frame title the page once the assessment is read. */
  onLoaded?: (detail: AssessmentDetail) => void;
}

export function FindingDetail({
  siteId,
  assessmentId,
  tab,
  client,
  evidence,
  profile,
  tabHref,
  dispatchHref,
  evidencePageHref,
  onLoaded,
}: FindingDetailProps) {
  const [result, setResult] = useState<EvidenceRead<AssessmentDetail> | null>(null);
  const [params, setParams] = useSearchParams();

  useEffect(() => {
    let active = true;
    setResult(null);
    void client.getAssessment(siteId, assessmentId).then((loaded) => {
      if (active) {
        setResult(loaded);
        if (loaded.status === "loaded" && onLoaded !== undefined) {
          onLoaded(loaded.value);
        }
      }
    });
    return () => {
      active = false;
    };
    // onLoaded is a frame callback; re-reading on its identity would loop.
  }, [client, siteId, assessmentId]);

  if (result === null) {
    return <p>Loading the assessment.</p>;
  }
  if (result.status === "not_found") {
    return (
      <Panel heading="No such assessment" headingId="finding-not-found-heading">
        <p>
          No assessment with that ID exists for this site. This states that the
          assessment does not exist, not that the interval was assessed clean.
        </p>
      </Panel>
    );
  }
  if (result.status === "unavailable") {
    return (
      <Panel heading="Assessment unavailable" headingId="finding-unavailable-heading">
        <p>{result.message ?? "The assessment could not be read."}</p>
      </Panel>
    );
  }

  const detail = result.value;
  const a = detail.assessment;
  const record = params.get("record");
  const claim = params.get("claim");
  const open: OpenRecord = (link, claimText) => {
    const next = new URLSearchParams(params);
    next.set("record", link.message_id);
    next.set("claim", claimText);
    setParams(next);
  };
  const close = () => {
    const next = new URLSearchParams(params);
    next.delete("record");
    next.delete("claim");
    setParams(next);
  };
  const findingType = findingTypeLabel(profile, a.finding_type);

  return (
    <div className="finding-detail" data-finding={detail.assessment_id}>
      <FactList>
        <Fact term="Claim">
          <ClaimBadge level={detail.claim_level} label={detail.label} />{" "}
          <span data-finding-type={findingType.id} data-profile-known={findingType.known}>
            {findingType.label}
          </span>
        </Fact>
        <Fact term="Context">
          {`Site ${siteId}; generator interval ${a.interval.first_running_observed} to ${a.interval.last_running_observed}`}
        </Fact>
        <Fact term="Selected window">
          <span data-finding-window>{windowText(a.assessed_window)}</span>
        </Fact>
        <Fact term="Assessment">
          {`${detail.assessment_id}, revision ${detail.revision} of ${detail.revisions}, analytic ${a.analytic_id} ${a.model_version}`}
          {detail.finding_id === null ? " (an assessment without a Finding)" : ""}
          {detail.active ? "" : ` (retired ${detail.retired_at ?? ""})`}
        </Fact>
      </FactList>

      <nav className="site-tabs finding-tabs" aria-label={FINDING_TABS_LABEL}>
        <ol className="site-tabs__list">
          {FINDING_DETAIL_TABS.map((item) => (
            <li className="site-tabs__item" key={item.id}>
              <Link
                className="site-tabs__link"
                to={tabHref(item.id)}
                aria-current={item.id === tab ? "page" : undefined}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ol>
      </nav>

      <div className={record === null ? "finding-body" : "finding-body finding-body--drawer"}>
        <div className="finding-body__main">
          {tab === "overview" ? (
            <FindingOverview
              detail={detail}
              dispatchHref={dispatchHref}
              evidencePageHref={evidencePageHref}
              evidenceTabHref={tabHref("evidence")}
              alternativesTabHref={tabHref("alternatives")}
            />
          ) : tab === "evidence" ? (
            <FindingEvidence assessment={a} open={open} />
          ) : (
            <FindingAlternatives assessment={a} open={open} />
          )}
        </div>
        {record === null ? null : (
          <ClaimDrawer
            siteId={siteId}
            messageId={record}
            claim={claim}
            assessedWindow={a.assessed_window}
            modelVersion={a.model_version}
            evidence={evidence}
            onClose={close}
          />
        )}
      </div>
    </div>
  );
}

function FindingOverview({
  detail,
  dispatchHref,
  evidencePageHref,
  evidenceTabHref,
  alternativesTabHref,
}: {
  detail: AssessmentDetail;
  dispatchHref: string;
  evidencePageHref: string;
  evidenceTabHref: string;
  alternativesTabHref: string;
}) {
  const a = detail.assessment;
  const portions = a.portions_hours;
  const fuel = a.fuel;
  const openAlternatives = a.alternatives.filter((alt) => alt.status === "NOT_EXCLUDED");
  return (
    <div className="finding-overview">
      <Section heading="1. The claim" id="finding-claim-heading">
        <p className="finding-claim" data-finding-claim={a.claim_level}>
          {a.summary}
        </p>
      </Section>

      <Section heading="2. Observed facts" id="finding-facts-heading">
        <FactList>
          <Fact term="Generator interval">{a.interval.statement}</Fact>
          <Fact term="Duration">{boundText(a.interval.duration_hours, "h")}</Fact>
          <Fact term="Assessed segments">
            {`${a.segments.length} segments; ${a.segments.filter((s) => s.observed).length} with observed generator state`}
          </Fact>
          <Fact term="Accepted records used">
            {`${a.evidence_basis.message_ids.length} (basis digest ${a.evidence_basis.digest})`}
          </Fact>
        </FactList>
        <p className="overview-note">Inference from these facts:</p>
        <FactList>
          <Fact term="Candidate avoidable portion">
            {boundText(portions.CANDIDATE_AVOIDABLE, "h")}
          </Fact>
          <Fact term="Necessary portion">{boundText(portions.NECESSARY, "h")}</Fact>
          <Fact term="Indeterminate portion">{boundText(portions.INDETERMINATE, "h")}</Fact>
          <Fact term="Binding constraints">
            {a.binding_constraints.length === 0
              ? "None found in the assessed segments"
              : a.binding_constraints.map(constraintWord).join(", ")}
          </Fact>
        </FactList>
      </Section>

      <Section heading="3. Confidence and coverage" id="finding-confidence-heading">
        <FactList>
          <Fact term="Confidence">
            <span data-finding-confidence={a.confidence.level}>
              {confidenceWord(a.confidence.level)}
            </span>
            {a.confidence.basis.length === 0 ? null : (
              <ul className="cell-list" data-confidence-basis>
                {a.confidence.basis.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            )}
          </Fact>
          <Fact term="Coverage">
            <span data-finding-coverage>{a.coverage.statement}</span>
            <ul className="cell-list">
              {a.coverage.inputs.map((input) => (
                <li key={input.input} data-coverage-input={input.input}>
                  {`${input.label}: usable in ${input.usable_segments} of ${input.evaluated_segments} segments`}
                  {input.gaps.length === 0
                    ? ""
                    : `; gaps ${input.gaps.map((g) => `${g.start} to ${g.end} (${g.minutes} min)`).join(", ")}`}
                </li>
              ))}
            </ul>
          </Fact>
        </FactList>
      </Section>

      <Section heading="4. Claim ceiling" id="finding-ceiling-heading">
        {a.missing_evidence.length === 0 ? null : (
          <p data-finding-gaps>
            {`Missing or conflicting evidence: ${a.missing_evidence.join("; ")}.`}
          </p>
        )}
        <ul className="cell-list" data-claim-limits>
          {a.claim_limits.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </Section>

      <Section heading="5. Consequence (technical quantity)" id="finding-consequence-heading">
        <FactList>
          <Fact term="Indicative associated fuel">
            <span data-finding-fuel={fuel.status}>
              {fuel.status === "BOUNDED"
                ? `${fuel.low_litres} to ${fuel.high_litres} ${fuel.unit ?? "L"} (${fuel.basis})`
                : `Unavailable: ${fuel.reason ?? fuel.statement}`}
            </span>
          </Fact>
          {fuel.inputs === undefined ? null : (
            <>
              <Fact term="Duration input">
                {`${fuel.inputs.duration_hours.low} to ${fuel.inputs.duration_hours.high} h (${fuel.inputs.duration_hours.basis}). ${fuel.inputs.duration_hours.note}`}
              </Fact>
              <Fact term="Generator power input">
                {`${fuel.inputs.generator_kw.low} to ${fuel.inputs.generator_kw.high} kW (${fuel.inputs.generator_kw.basis}). ${fuel.inputs.generator_kw.note}`}
              </Fact>
              <Fact term="Consumption input">
                {`${fuel.inputs.specific_fuel_consumption.value} ${fuel.inputs.specific_fuel_consumption.unit} ±${fuel.inputs.specific_fuel_consumption.uncertainty_pct} % (${fuel.inputs.specific_fuel_consumption.basis}; ${fuel.inputs.specific_fuel_consumption.source})`}
              </Fact>
              {fuel.formula === undefined ? null : (
                <Fact term="Model basis">{fuel.formula}</Fact>
              )}
            </>
          )}
        </FactList>
        <p className="overview-note">{fuel.statement}</p>
      </Section>

      <Section heading="6. Next step" id="finding-next-heading">
        <ul className="cell-list">
          <li>
            <Link to={evidenceTabHref}>Challenge the claim record by record</Link>
            {" in the Evidence tab."}
          </li>
          <li>
            <Link to={alternativesTabHref}>
              {`Review ${openAlternatives.length} alternative explanation${openAlternatives.length === 1 ? "" : "s"} not excluded`}
            </Link>
            {" before acting."}
          </li>
          {a.missing_evidence.length === 0 ? null : (
            <li>
              <Link to={evidencePageHref}>Check the site&apos;s evidence coverage</Link>
              {" for the missing inputs named above."}
            </li>
          )}
          <li>
            <Link to={dispatchHref}>See this interval on Performance &gt; Dispatch</Link>.
          </li>
        </ul>
      </Section>
    </div>
  );
}

const CONSTRAINT_WORDS: Record<string, string> = {
  OPERATOR_OVERRIDE: "Operator override",
  MINIMUM_RUNTIME: "Minimum runtime",
  BATTERY_AT_RESERVE: "Battery at reserve",
  BATTERY_NEAR_RESERVE: "Battery near reserve",
  CAPABILITY_SHORTFALL: "Capability shortfall",
};

export function constraintWord(id: string): string {
  return CONSTRAINT_WORDS[id] ?? id;
}

function FindingEvidence({
  assessment,
  open,
}: {
  assessment: Assessment;
  open: OpenRecord;
}) {
  return (
    <Section heading="Claims and their records" id="finding-evidence-heading">
      <p className="overview-note">
        Each claim below is one assessed segment. Open a record to see its
        source, mapping, configuration basis and timestamps; opening it does
        not leave this Finding.
      </p>
      <ol className="claim-list">
        {assessment.segments.map((segment, index) => {
          const claimText = `${segment.label}, ${segment.start} to ${segment.end}`;
          const inputs = segment.inputs.at_start;
          return (
            <li
              key={`${segment.start}-${index}`}
              className="claim-list__item"
              data-claim-segment={segment.classification}
            >
              <p className="claim-list__head">
                <ClaimBadge level={segment.classification} label={segment.label} />{" "}
                {`${segment.start} to ${segment.end} (${segment.minutes} min)`}
                {segment.observed ? "" : ", generator state not observed"}
              </p>
              {segment.binding_constraint === null ? null : (
                <p>{`Binding constraint: ${constraintWord(segment.binding_constraint)}.`}</p>
              )}
              {segment.reasons.length === 0 ? null : (
                <ul className="cell-list">
                  {segment.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
              {segment.missing.length === 0 ? null : (
                <p data-claim-missing>{`Missing: ${segment.missing.join("; ")}.`}</p>
              )}
              {inputs === undefined ? null : (
                <p className="overview-note">
                  {`At start: load ${inputs.load_kw ?? "n/a"} kW, PV available ${inputs.pv_available_kw ?? "n/a"} kW, SOC ${inputs.soc_pct ?? "n/a"} %, reserve ${inputs.reserve_pct ?? "n/a"} %${inputs.reserve_source === null ? "" : ` (${inputs.reserve_source})`}, discharge capability ${inputs.discharge_capability_kw ?? "n/a"} kW, generator ${inputs.generator_kw ?? "n/a"} kW.`}
                </p>
              )}
              <EvidenceLinks links={segment.evidence} claim={claimText} open={open} />
            </li>
          );
        })}
      </ol>
    </Section>
  );
}

const ALTERNATIVE_STATUS: Record<string, string> = {
  OBSERVED: "Observed",
  NOT_EXCLUDED: "Not excluded",
  CONTRADICTED_BY_EVIDENCE: "Contradicted by evidence",
};

function FindingAlternatives({
  assessment,
  open,
}: {
  assessment: Assessment;
  open: OpenRecord;
}) {
  return (
    <Section heading="Competing explanations" id="finding-alternatives-heading">
      <ol className="claim-list">
        {assessment.alternatives.map((alt) => (
          <li key={alt.id} className="claim-list__item" data-alternative={alt.id}>
            <p className="claim-list__head">
              <strong>{alt.label}</strong>{" "}
              <span data-alternative-status={alt.status}>
                {ALTERNATIVE_STATUS[alt.status] ?? alt.status}
              </span>
            </p>
            <p>{alt.statement}</p>
            {alt.gaps === undefined || alt.gaps.length === 0 ? null : (
              <p data-alternative-gaps>
                {`Gaps: ${alt.gaps.map((g) => `${g.start} to ${g.end} (${g.minutes} min)`).join(", ")}.`}
              </p>
            )}
            <EvidenceLinks links={alt.evidence} claim={`Alternative: ${alt.label}`} open={open} />
          </li>
        ))}
      </ol>
    </Section>
  );
}
