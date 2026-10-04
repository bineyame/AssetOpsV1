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
 * Checkpoint 2 graphics anchor here: `data-graphic-anchor` marks where the
 * reported-values comparison and the coverage-count graphic land.
 */
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, Fact, FactList } from "../ui";
import {
  AssessedPeriodStrip,
  ClaimBadge,
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
  SegmentInputs,
} from "./siteAnalyticsClient";

/** Plain input names, keyed by the assessment's stable input ids. */
export const INPUT_WORDS: Record<string, string> = {
  load: "Site demand",
  pv_available: "Available solar power",
  soc: "Battery charge",
  reserve: "Minimum battery reserve",
  discharge_capability: "Available battery output",
};

const RESERVE_SOURCE: Record<string, string> = {
  policy: "site setting",
  "operator override": "operator instruction",
  "conflicting records": "conflicting records",
};

function value(v: string | null, unit: string): string {
  return v === null ? "Not reported" : `${v} ${unit}`;
}

/** The values one end of an assessed part was judged on. Missing is "Not reported", never zero. */
function InputValues({ inputs }: { inputs: SegmentInputs | undefined }) {
  if (inputs === undefined) {
    return <span className="overview-note">No values: generator operation not recorded.</span>;
  }
  return (
    <ul className="cell-list" data-segment-values>
      <li>{`Site demand: ${value(inputs.load_kw, "kW")}`}</li>
      <li>{`Available solar power: ${value(inputs.pv_available_kw, "kW")}`}</li>
      <li>{`Available battery output: ${value(inputs.discharge_capability_kw, "kW")}`}</li>
      <li>{`Generator output: ${value(inputs.generator_kw, "kW")}`}</li>
      <li>{`Battery charge: ${value(inputs.soc_pct, "%")}`}</li>
      <li>
        {`Minimum battery reserve: ${value(inputs.reserve_pct, "%")}`}
        {inputs.reserve_source === null
          ? ""
          : ` (${RESERVE_SOURCE[inputs.reserve_source] ?? "recorded setting"})`}
      </li>
    </ul>
  );
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
  if (reading === undefined) {
    return (
      <p data-analysis-unavailable>
        The plain explanation of this assessment is not available, so its analysis is not shown.
      </p>
    );
  }
  const fuel = a.fuel;
  return (
    <div className="assessment-analysis" data-analysis={summary.assessment_id}>
      <Section heading="How the conclusion was reached" id="analysis-parts-heading">
        <p>{reading.meaning}</p>
        {reading.reasons_needed.length === 0 ? null : (
          <p data-analysis-reasons-needed>
            {`Reasons the generator was needed: ${reading.reasons_needed.join(", ")}.`}
          </p>
        )}
        <AssessedPeriodStrip assessment={a} reading={reading} />
        <p className="overview-note">
          Each row is one assessed part of the period. The values are those used
          at the start and end of that part, as reported; they are not a
          continuous measurement. Times are UTC.
        </p>
        {/* Checkpoint 2: reported-values comparison graphic (data-graphic-anchor="reported-values"). */}
        <div data-graphic-anchor="reported-values">
          <DataTable labelledBy="analysis-parts-heading">
            <thead>
              <tr>
                <th scope="col">Assessed part</th>
                <th scope="col">Outcome and reason</th>
                <th scope="col">Values used at the start</th>
                <th scope="col">Values used at the end</th>
                <th scope="col">Records</th>
              </tr>
            </thead>
            <tbody>
              {a.segments.map((segment, index) => {
                const plain = reading.segments[index];
                return (
                  <tr key={`${segment.start}-${index}`} data-analysis-segment={segment.classification}>
                    <th scope="row">
                      {`${readablePeriod(segment.start, segment.end)} (${segment.minutes} min)`}
                    </th>
                    <td>
                      <ClaimBadge
                        level={segment.classification}
                        label={plain?.outcome ?? OUTCOME_WORDS[segment.classification] ?? "Assessed"}
                      />{" "}
                      {plain?.reason ?? "Detail not available for this part of the assessment."}
                    </td>
                    <td>
                      <InputValues inputs={segment.inputs.at_start} />
                    </td>
                    <td>
                      <InputValues inputs={segment.inputs.at_end} />
                    </td>
                    <td>
                      {records.kind === "tab" ? (
                        <Link to={records.href}>{`${segment.evidence.length} records (Evidence)`}</Link>
                      ) : segment.evidence.length === 0 ? (
                        "None referenced"
                      ) : (
                        <ul className="cell-list">
                          {segment.evidence.map((link) => (
                            <li key={link.message_id}>
                              <Link to={records.href(link)} data-analysis-record={link.message_id}>
                                {`${link.device_id} / ${link.signal_id}, ${readableTime(link.source_time)}`}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
        </div>
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
        {/* Checkpoint 2: coverage-count graphic (data-graphic-anchor="coverage-by-input"). */}
        <ul className="cell-list" data-graphic-anchor="coverage-by-input">
          {a.coverage.inputs.map((input) => (
            <li key={input.input} data-coverage-input={input.input}>
              {input.evaluated_segments === 0
                ? `${INPUT_WORDS[input.input] ?? input.label}: not assessed`
                : `${INPUT_WORDS[input.input] ?? input.label}: usable in ${input.usable_segments} of ${input.evaluated_segments} assessed parts of this period`}
              {input.gaps.length === 0
                ? ""
                : `; missing ${input.gaps.map((g) => `${readablePeriod(g.start, g.end)} (${g.minutes} min)`).join(", ")}`}
            </li>
          ))}
          {a.coverage.unobserved_generator_state.map((span) => (
            <li key={`gen-${span.start}`} data-coverage-unobserved>
              {`Generator operation not recorded: ${readablePeriod(span.start, span.end)} (${span.minutes} min)`}
            </li>
          ))}
        </ul>
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
        <p data-analysis-fuel={fuel.status}>
          <strong>{`${reading.fuel.label}: `}</strong>
          {reading.fuel.text ?? reading.fuel.note}
        </p>
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
