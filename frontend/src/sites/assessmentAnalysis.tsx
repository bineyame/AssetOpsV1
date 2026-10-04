/**
 * The Analysis view of one assessed period (T028, D-2026-10-04-plain-language-
 * analysis-views): how the conclusion follows from the inputs. Shared by
 * Finding > Analysis and Performance > Dispatch > Analysis, so a Necessary
 * period (no Finding) has the same explanation as a Finding.
 *
 * It owns method and interpretation detail removed from the default views:
 * the values used for each assessed part, the reasons, confidence in detail,
 * record coverage, the operating-time and fuel calculation, and the
 * assessment reference. Evidence (records) and Alternatives (other possible
 * explanations) keep their own lists; this view links to them.
 *
 * Every sentence is the backend's plain reading (`reading`); the frontend only
 * formats values, times and layout. Nothing is recomputed.
 *
 * Graphics (checkpoint 2a): the assessed-period timeline with its parts
 * table selects one part (`?part=N`, 1-based); the reported values of that
 * part, record coverage by input and the fuel range follow. All draw the same
 * assessment this view was given.
 */
import { useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Fact, FactList } from "../ui";
import {
  AssessedPeriodTimeline,
  CoverageByInput,
  FuelRange,
  ReportedValues,
} from "./assessmentGraphics";
import {
  OUTCOME_WORDS,
  readablePeriod,
  readableTime,
  Section,
} from "./findingPresentation";
import type {
  Assessment,
  AssessmentSummary,
  EvidenceLink,
  Reading,
  RevisionSummary,
} from "./siteAnalyticsClient";

/** Plain input names, keyed by the assessment's stable input ids. */
export const INPUT_WORDS: Record<string, string> = {
  load: "Site demand",
  pv_available: "Available solar power",
  soc: "Battery charge",
  reserve: "Minimum battery reserve",
  discharge_capability: "Available battery output",
};

/**
 * The part shown by default: the first recorded part with the period's own
 * outcome, else the first recorded part, else the first part.
 */
export function defaultPart(a: Assessment): number {
  const own = a.segments.findIndex((s) => s.observed && s.classification === a.claim_level);
  if (own >= 0) {
    return own;
  }
  const recorded = a.segments.findIndex((s) => s.observed);
  return recorded >= 0 ? recorded : 0;
}

export interface AssessmentAnalysisProps {
  summary: AssessmentSummary;
  assessment: Assessment;
  /** Revision history, when the caller has it (Finding detail). */
  revisionHistory?: RevisionSummary[];
  /** Where each part's records are: a per-record link, or one tab link. */
  records:
    | { kind: "tab"; href: string }
    | { kind: "record"; href: (link: EvidenceLink) => string };
  /** The other-possible-explanations destination, when there is one. */
  alternativesHref: string | null;
  /** Extra links shown at the end (Finding, Dispatch, Site Evidence). */
  links?: ReactNode;
}

export function AssessmentAnalysis({
  summary,
  assessment: a,
  revisionHistory,
  records,
  alternativesHref,
  links,
}: AssessmentAnalysisProps) {
  const reading: Reading | undefined = summary.reading;
  const [params, setParams] = useSearchParams();
  const [side, setSide] = useState<"start" | "end">("start");
  if (reading === undefined) {
    return (
      <p data-analysis-unavailable>
        The plain explanation of this assessment is not available, so its analysis is not shown.
      </p>
    );
  }
  const fuel = a.fuel;
  const requested = params.get("part");
  const n = requested === null ? NaN : Number(requested);
  const requestedIndex =
    Number.isInteger(n) && n >= 1 && n <= a.segments.length ? n - 1 : null;
  const selected = requestedIndex ?? defaultPart(a);
  const segment = a.segments[selected];
  const partLabel = segment === undefined ? "" : `Part ${selected + 1} of ${a.segments.length}, ${readablePeriod(segment.start, segment.end)}`;
  const select = (index: number) => {
    const next = new URLSearchParams(params);
    next.set("part", String(index + 1));
    setParams(next, { replace: true });
  };
  return (
    <div className="assessment-analysis" data-analysis={summary.assessment_id}>
      <Section heading="How the conclusion was reached" id="analysis-parts-heading">
        <p>{reading.meaning}</p>
        {reading.reasons_needed.length === 0 ? null : (
          <p data-analysis-reasons-needed>
            {`Reasons the generator was needed: ${reading.reasons_needed.join(", ")}.`}
          </p>
        )}
        <AssessedPeriodTimeline
          source={a}
          outcomes={reading.segments.map((s) => s.outcome)}
          reasons={reading.segments.map((s) => s.reason)}
          selected={selected}
          onSelect={select}
          assessmentId={summary.assessment_id}
        />
      </Section>

      <Section heading="Values used for the selected part" id="analysis-values-heading">
        {requested !== null && requestedIndex === null ? (
          <p data-analysis-part-missing>
            {`Part ${requested} is not in this assessed period; the first part with the period's outcome is shown.`}
          </p>
        ) : null}
        {segment === undefined ? (
          <p>This assessed period has no parts.</p>
        ) : (
          <div data-analysis-selected-part={selected + 1}>
            <p>
              <strong>{`${partLabel}: ${reading.segments[selected]?.outcome ?? OUTCOME_WORDS[segment.classification] ?? "Assessed"}.`}</strong>{" "}
              {reading.segments[selected]?.reason ?? "Detail not available for this part of the assessment."}
            </p>
            <ReportedValues segment={segment} which={side} onWhich={setSide} partLabel={partLabel} />
            <p data-analysis-part-records>
              {"Records for this part: "}
              {records.kind === "tab" ? (
                <Link to={records.href}>{`${segment.evidence.length} records (Evidence)`}</Link>
              ) : segment.evidence.length === 0 ? (
                "none referenced"
              ) : (
                segment.evidence.map((link, index) => (
                  <span key={link.message_id}>
                    {index === 0 ? "" : ", "}
                    <Link to={records.href(link)} data-analysis-record={link.message_id}>
                      {`${link.device_id} / ${link.signal_id}, ${readableTime(link.source_time)}`}
                    </Link>
                  </span>
                ))
              )}
            </p>
          </div>
        )}
      </Section>

      <Section heading="Confidence in detail" id="analysis-confidence-heading">
        <p data-analysis-confidence={a.confidence.level}>
          <strong>{reading.confidence.word}</strong>
        </p>
        <ul className="cell-list" data-analysis-confidence-explanation>
          {reading.confidence.explanation.map((line, index) => (
            <li key={`${index}-${line}`}>{line}</li>
          ))}
        </ul>
      </Section>

      <Section heading="Record coverage" id="analysis-coverage-heading">
        <p>{reading.coverage_note}</p>
        <CoverageByInput
          inputs={a.coverage.inputs}
          unobserved={a.coverage.unobserved_generator_state}
          words={INPUT_WORDS}
        />
      </Section>

      <Section heading="Operating time and fuel calculation" id="analysis-fuel-heading">
        <FactList>
          <Fact term="Generator operating time">{reading.operating_time}</Fact>
          <Fact term="Recorded operating">
            {readablePeriod(a.interval.first_running_observed, a.interval.last_running_observed)}
          </Fact>
          <Fact term="Last record showing it off before">
            {a.interval.last_stopped_before === null
              ? "None: the start is open"
              : readableTime(a.interval.last_stopped_before)}
          </Fact>
          <Fact term="First record showing it off after">
            {a.interval.first_stopped_after === null
              ? "None: the end is open"
              : readableTime(a.interval.first_stopped_after)}
          </Fact>
        </FactList>
        <p className="overview-note">{reading.duration_note}</p>
        <div data-analysis-fuel={fuel.status}>
          <FuelRange fuel={fuel} reading={reading.fuel} />
        </div>
        {fuel.inputs === undefined ? null : (
          <>
            <FactList>
              <Fact term="Possibly avoidable operating time used">
                {`${fuel.inputs.duration_hours.low} to ${fuel.inputs.duration_hours.high} h`}
              </Fact>
              <Fact term="Generator output used">
                {`${fuel.inputs.generator_kw.low} to ${fuel.inputs.generator_kw.high} kW, from reported output`}
              </Fact>
              <Fact term="Fuel consumption setting">
                {`${fuel.inputs.specific_fuel_consumption.value} ${fuel.inputs.specific_fuel_consumption.unit}, ±${fuel.inputs.specific_fuel_consumption.uncertainty_pct} %, from the site's equipment details`}
              </Fact>
            </FactList>
            <p className="overview-note">
              {`The low figure multiplies the shorter time, the lower output and the fuel consumption less ${fuel.inputs.specific_fuel_consumption.uncertainty_pct} %; the high figure uses the longer time, the higher output and the fuel consumption plus ${fuel.inputs.specific_fuel_consumption.uncertainty_pct} %. ${reading.fuel.note}`}
            </p>
          </>
        )}
      </Section>

      <Section heading="Assessment reference" id="analysis-reference-heading">
        <FactList>
          <Fact term="Assessment method">{a.model_version}</Fact>
          <Fact term="Assessment reference">
            <span data-finding-assessment-id>{summary.assessment_id}</span>
            {summary.finding_id === null ? " (an assessed period without a Finding)" : ""}
            {summary.active ? "" : ` (withdrawn ${summary.retired_at === null ? "" : readableTime(summary.retired_at)})`}
          </Fact>
          <Fact term="Records used">
            {`${a.evidence_basis.message_ids.length} accepted records; verification reference ${a.evidence_basis.digest}`}
          </Fact>
          <Fact term="Revision">
            {`${summary.revision} of ${summary.revisions}. Every revision is kept.`}
            {revisionHistory === undefined ? null : (
              <ul className="cell-list" data-finding-revisions>
                {revisionHistory.map((r) => (
                  <li key={r.revision}>
                    {`Revision ${r.revision}, assessed ${readableTime(r.assessed_at)}, method ${r.model_version}: ${OUTCOME_WORDS[r.claim_level] ?? "Assessed"}; ${r.evidence_records} records`}
                  </li>
                ))}
              </ul>
            )}
          </Fact>
        </FactList>
        <ul className="cell-list" data-analysis-links>
          {records.kind === "tab" ? (
            <li>
              <Link to={records.href}>Supporting records for each part (Evidence)</Link>
            </li>
          ) : null}
          {alternativesHref === null ? null : (
            <li>
              <Link to={alternativesHref}>Other possible explanations (Alternatives)</Link>
            </li>
          )}
          {links}
        </ul>
      </Section>
    </div>
  );
}
