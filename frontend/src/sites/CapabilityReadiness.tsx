/**
 * Site > Evidence part B (T028 AC20): the capability table, above source
 * health. One row per analytic the backend declares for this Site (at T028,
 * dispatch), with readiness Full, Limited or None, the claim ceiling and the
 * missing evidence.
 *
 * The backend scores every row (`readiness` on `/api/sites/{id}/analytics`,
 * `analytics/declaration.py` `score_readiness`), so every gap here is backend
 * state (AC18 rule 3). The presentation profile only labels and orders the
 * rows (rules 1 and 2 through `servedCapabilities`). With no declared analytic
 * the table renders nothing: no row appears before a real claim exists.
 */

import { Badge, DataTable, Panel } from "../ui";
import type { DomainPresentationProfile } from "./presentationProfile";
import { servedCapabilities } from "./presentationProfile";
import type { EvidenceRead } from "./siteEvidenceClient";
import type { AnalyticDeclaration, SiteAnalytics } from "./siteAnalyticsClient";

export const CAPABILITY_HEADING_ID = "site-evidence-capability-heading";

export function CapabilityReadinessTable({
  declaration,
  profile,
}: {
  declaration: EvidenceRead<SiteAnalytics> | null;
  profile: DomainPresentationProfile | null;
}) {
  if (declaration === null || declaration.status === "not_found") {
    return null;
  }
  if (declaration.status === "unavailable") {
    return (
      <Panel heading="Capability readiness" headingId={CAPABILITY_HEADING_ID}>
        <p data-capability-state="unavailable">
          {declaration.message ??
            "The analytic declaration could not be read, so nothing is said here about what AssetOps can claim for this site."}
        </p>
      </Panel>
    );
  }
  const analytics = declaration.value.analytics;
  if (analytics.length === 0) {
    return null;
  }
  const byId = new Map(analytics.map((item) => [item.analytic_id, item]));
  const rows = servedCapabilities(
    profile,
    analytics.map((item) => ({ id: item.analytic_id, display_name: item.display_name })),
  );
  const statement = analytics.find((item) => item.readiness)?.readiness?.statement;

  return (
    <Panel heading="Capability readiness" headingId={CAPABILITY_HEADING_ID} flush>
      <p className="note" data-capability-statement>
        What AssetOps can claim from this site&apos;s accepted records, per
        analytic. {statement ?? ""}
      </p>
      <DataTable labelledBy={CAPABILITY_HEADING_ID}>
        <thead>
          <tr>
            <th scope="col">Capability</th>
            <th scope="col">Readiness</th>
            <th scope="col">Claim ceiling</th>
            <th scope="col">Missing evidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <CapabilityRow
              key={row.id}
              label={row.label}
              known={row.known}
              analytic={byId.get(row.id) as AnalyticDeclaration}
            />
          ))}
        </tbody>
      </DataTable>
    </Panel>
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
  const notObserved = [
    ...new Set((readiness?.optional_not_observed ?? []).map((item) => item.role)),
  ];
  return (
    <tr
      data-capability={analytic.analytic_id}
      data-capability-known={known ? "yes" : "no"}
      data-capability-readiness={readiness?.level ?? "NOT_SCORED"}
    >
      <th scope="row">
        {label}
        <span className="note">{` ${analytic.model_version}`}</span>
      </th>
      {readiness === undefined ? (
        <td colSpan={3} data-capability-not-scored>
          The backend served no readiness for this analytic, so none is shown.
        </td>
      ) : (
        <>
          <td>
            <Badge tone="neutral">{readiness.label}</Badge>
          </td>
          <td data-capability-ceiling={readiness.claim_ceiling.claim_level ?? "NONE"}>
            <strong>{readiness.claim_ceiling.label}</strong>
            {`: ${readiness.claim_ceiling.statement}`}
          </td>
          <td>
            {readiness.missing_evidence.length === 0 ? (
              <span data-capability-missing="none">
                No required evidence is missing.
              </span>
            ) : (
              <ul className="cell-list">
                {readiness.missing_evidence.map((item) => (
                  <li
                    key={`${item.kind}-${item.role}`}
                    data-capability-missing={item.kind}
                    data-capability-limits={item.limits_claim ? "yes" : "no"}
                  >
                    {item.statement}
                  </li>
                ))}
              </ul>
            )}
            {notObserved.length === 0 ? null : (
              <p className="note" data-capability-not-observed>
                {`Not observed: ${notObserved.join(", ")}. Absence is not proof that none existed.`}
              </p>
            )}
          </td>
        </>
      )}
    </tr>
  );
}
