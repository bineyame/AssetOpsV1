/**
 * Site > Evidence part B (T028 AC20): what can be assessed from this site's
 * records. One row per assessment the backend declares for this site (at
 * T028, dispatch), with Full, Limited or None and its plain meaning, the
 * conclusion available, and the missing records that limit it.
 *
 * Two views (D-2026-10-04-plain-language-analysis-views): the Overview table
 * here, and `CapabilityReadinessAnalysis` on Evidence > Analysis with the
 * scoring method, versions, required and optional records, and each gap with
 * its source reference.
 *
 * The backend scores every row (`readiness` on `/api/sites/{id}/analytics`,
 * `analytics/declaration.py` `score_readiness`, plain words from
 * `analytics/plain.py`), so every gap here is backend state (AC18 rule 3).
 * The profile only labels and orders the rows (rules 1 and 2 through
 * `servedCapabilities`). With no declared assessment the table renders
 * nothing: no row appears before a real conclusion exists. The readiness
 * scope is site-wide, never the selected window.
 */

import { Badge, DataTable, Fact, FactList } from "../ui";
import { Part } from "./panelPart";
import type { DomainPresentationProfile } from "./presentationProfile";
import { servedCapabilities } from "./presentationProfile";
import type { EvidenceRead } from "./siteEvidenceClient";
import type {
  AnalyticDeclaration,
  CapabilityReadiness,
  EvidenceRequirement,
  SiteAnalytics,
} from "./siteAnalyticsClient";
import { sourceReferences } from "./vocabularyReference";

export const CAPABILITY_HEADING_ID = "site-evidence-capability-heading";
export const CAPABILITY_METHOD_HEADING_ID = "site-evidence-capability-method-heading";

const QUESTION = "What can we assess from this site's records?";

type Rows = { id: string; label: string; known: boolean; analytic: AnalyticDeclaration }[];

function served(
  declaration: EvidenceRead<SiteAnalytics> | null,
  profile: DomainPresentationProfile | null,
): Rows | "unavailable" | null {
  if (declaration === null || declaration.status === "not_found") {
    return null;
  }
  if (declaration.status === "unavailable") {
    return "unavailable";
  }
  const analytics = declaration.value.analytics;
  if (analytics.length === 0) {
    return null;
  }
  const byId = new Map(analytics.map((item) => [item.analytic_id, item]));
  return servedCapabilities(
    profile,
    analytics.map((item) => ({ id: item.analytic_id, display_name: item.display_name })),
  ).map((row) => ({ ...row, analytic: byId.get(row.id) as AnalyticDeclaration }));
}

function Unavailable({ message }: { message: string | null }) {
  return (
    <Part heading={QUESTION} headingId={CAPABILITY_HEADING_ID}>
      <p data-capability-state="unavailable">
        {message ??
          "What can be assessed for this site could not be read, so nothing is said here about it."}
      </p>
    </Part>
  );
}

/** The assessed-period count, with the zero-period qualification. */
function assessedText(readiness: CapabilityReadiness): string {
  if (readiness.assessed_intervals === 0) {
    return readiness.level === "NONE"
      ? "No period can be assessed until records of generator operation are accepted."
      : "No period has been assessed yet: records exist, but whether they cover each period has not been checked.";
  }
  return `${readiness.assessed_intervals} assessed period${readiness.assessed_intervals === 1 ? "" : "s"}.`;
}

export function CapabilityReadinessTable({
  declaration,
  profile,
}: {
  declaration: EvidenceRead<SiteAnalytics> | null;
  profile: DomainPresentationProfile | null;
}) {
  const rows = served(declaration, profile);
  if (rows === null) {
    return null;
  }
  if (rows === "unavailable") {
    return (
      <Unavailable
        message={declaration?.status === "unavailable" ? declaration.message : null}
      />
    );
  }
  const scored = rows.find((row) => row.analytic.readiness)?.analytic.readiness;
  return (
    <Part heading={scored?.question ?? QUESTION} headingId={CAPABILITY_HEADING_ID} flush>
      <p className="note" data-capability-question>
        <strong>Scope: whole site.</strong>
        {scored?.scope === undefined ? "" : ` ${scored.scope}`}
      </p>
      <DataTable labelledBy={CAPABILITY_HEADING_ID}>
        <thead>
          <tr>
            <th scope="col">Assessment</th>
            <th scope="col">Records available</th>
            <th scope="col">Conclusion available</th>
            <th scope="col">Missing information</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <CapabilityRow key={row.id} label={row.label} known={row.known} analytic={row.analytic} />
          ))}
        </tbody>
      </DataTable>
    </Part>
  );
}

function CapabilityRow({
  label,
  known,
  analytic,
}: {
  label: string;
  known: boolean;
  analytic: AnalyticDeclaration;
}) {
  const readiness = analytic.readiness;
  const notReceived = [
    ...new Set((readiness?.optional_not_observed ?? []).map((item) => item.plain_role ?? item.role)),
  ];
  return (
    <tr
      data-capability={analytic.analytic_id}
      data-capability-known={known ? "yes" : "no"}
      data-capability-readiness={readiness?.level ?? "NOT_SCORED"}
    >
      <th scope="row">{label}</th>
      {readiness === undefined ? (
        <td colSpan={3} data-capability-not-scored>
          No readiness was given for this assessment, so none is shown.
        </td>
      ) : (
        <>
          <td>
            <Badge tone="neutral">{readiness.label}</Badge>
            {readiness.meaning === undefined ? null : (
              <p className="note" data-capability-meaning>
                {readiness.meaning}
              </p>
            )}
          </td>
          <td data-capability-ceiling={readiness.claim_ceiling.claim_level ?? "NONE"}>
            {readiness.conclusion ?? "Not available."}
          </td>
          <td>
            {readiness.missing_evidence.length === 0 ? (
              <span data-capability-missing="none">
                {readiness.assessed_intervals === 0
                  ? "Every required input has usable records."
                  : "Every required input has usable records; no gap limited an assessed period."}
              </span>
            ) : (
              <ul className="cell-list">
                {readiness.missing_evidence.map((item, index) => (
                  <li
                    key={`${item.kind}-${item.role}`}
                    data-capability-missing={item.kind}
                    data-capability-limits={item.limits_claim ? "yes" : "no"}
                  >
                    {readiness.gaps?.[index] ?? "Detail not available."}
                    {item.limits_claim ? "" : " (Not limiting.)"}
                  </li>
                ))}
              </ul>
            )}
            <p className="note" data-capability-assessed={readiness.assessed_intervals}>
              {assessedText(readiness)}
            </p>
            {notReceived.length === 0 ? null : (
              <p className="note" data-capability-not-observed>
                {`Not received: ${notReceived.join(", ")}. Absence is not proof that none existed.`}
              </p>
            )}
          </td>
        </>
      )}
    </tr>
  );
}

function requirementText(row: EvidenceRequirement): string {
  return row.available
    ? `${row.usable_records} usable record${row.usable_records === 1 ? "" : "s"}${row.last_source_time === null ? "" : `, latest ${row.last_source_time}`}`
    : "No usable record";
}

/** Evidence > Analysis: how readiness is scored and what each row was scored on. */
export function CapabilityReadinessAnalysis({
  declaration,
  profile,
}: {
  declaration: EvidenceRead<SiteAnalytics> | null;
  profile: DomainPresentationProfile | null;
}) {
  const rows = served(declaration, profile);
  if (rows === null) {
    return null;
  }
  if (rows === "unavailable") {
    return (
      <Unavailable
        message={declaration?.status === "unavailable" ? declaration.message : null}
      />
    );
  }
  return (
    <Part heading="How readiness is scored" headingId={CAPABILITY_METHOD_HEADING_ID}>
      {rows.map(({ id, label, analytic }) => {
        const readiness = analytic.readiness;
        return (
          <section key={id} data-capability-analysis={id} aria-label={`${label} readiness`}>
            <p className="note" data-capability-statement>
              {readiness?.method ?? "The scoring method is not available."}
            </p>
            <FactList>
              <Fact term="Scope">{readiness?.scope ?? "Whole site."}</Fact>
              <Fact term="Versions">
                <span data-capability-versions>
                  {`${label}: assessment method ${analytic.model_version}${readiness === undefined ? "" : `, readiness scoring ${readiness.basis_version}`}`}
                </span>
              </Fact>
              <Fact term="Required records">
                <ul className="cell-list" data-capability-required>
                  {analytic.required_evidence.map((row) => (
                    <li key={`${row.device_id}/${row.signal_id}`} data-requirement-available={row.available} {...sourceReferences(`${row.device_id} / ${row.signal_id}`)}>
                      {`${row.plain_role ?? row.role}: ${requirementText(row)} (reference ${row.device_id} / ${row.signal_id})`}
                    </li>
                  ))}
                </ul>
              </Fact>
              <Fact term="Optional records">
                <ul className="cell-list" data-capability-optional>
                  {analytic.optional_evidence.map((row) => (
                    <li key={`${row.device_id}/${row.signal_id}`} data-requirement-available={row.available} {...sourceReferences(`${row.device_id} / ${row.signal_id}`)}>
                      {`${row.plain_role ?? row.role}: ${row.available ? requirementText(row) : "none received; absence is not proof that none existed"} (reference ${row.device_id} / ${row.signal_id})`}
                    </li>
                  ))}
                </ul>
              </Fact>
              {readiness === undefined || readiness.missing_evidence.length === 0 ? null : (
                <Fact term="Gaps, with references">
                  <ul className="cell-list" data-capability-gap-detail>
                    {readiness.missing_evidence.map((item, index) => (
                      <li key={`${item.kind}-${item.role}`} {...sourceReferences(item.device_id === null ? null : `${item.device_id} / ${item.signal_id ?? ""}`, ...item.assessment_ids)}>
                        {readiness.gaps?.[index] ?? "Detail not available."}
                        {item.device_id === null ? "" : ` (reference ${item.device_id} / ${item.signal_id ?? ""})`}
                        {item.assessment_ids.length === 0
                          ? ""
                          : ` Assessed periods: ${item.assessment_ids.join(", ")}.`}
                      </li>
                    ))}
                  </ul>
                </Fact>
              )}
            </FactList>
          </section>
        );
      })}
    </Part>
  );
}
