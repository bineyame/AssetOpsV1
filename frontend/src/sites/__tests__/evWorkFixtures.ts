/**
 * W5-04 V2a (readiness rulings 39, 46, 47): pure component fixtures for the EV_CHARGING Site Work Actions tab. They are
 * shaped from the as-built V1b union index wire (`task/W5-04a-ev-work-backend`,
 * `backend/assetops_backend/work/domain_action_index.py` `_select`, `DomainActionReadService.index`) and make no
 * producer-backed claim: every ID, clock and name below is a test literal, never a mock SES/ACT/INC identifier or the
 * private manifest-only `Depot` label (ruling 52).
 *
 * Ruling 53 (V1 fix round): an intent-bearing EV row resolves its exact origin Finding at
 * `min(intent.recorded_at, index.known_at)`, as detail does; a later selected head leaves its `origin.href` non-null and
 * its status contribution CURRENT, and only an unavailable exact pinned selection yields `origin.href: null` with an
 * honest non-CURRENT status. The row shape is unchanged; `evRow()` is the pinned intent-bearing row, and
 * `evPinUnavailableRow()` the honest unavailable one.
 */
import type { DomainIndexBody, DomainIndexRow } from "../domainActionClient";
import type { SiteDetailReadModel } from "../siteReadModel";

export const EV_SITE_CODE = "EV-LAB-001";
/** A stored display name for the pure fixture (R111: the native Site name, never the mock's illustrative name). */
export const EV_SITE_NAME = "EV charging lab";
export const EV_SITE = {
  site_id: EV_SITE_CODE,
  display_name: EV_SITE_NAME,
  site_type: "EV_CHARGING",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Etc/UTC",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;

export const EV_FROM = "2026-10-06T00:00:00Z";
export const EV_TO = "2026-10-07T00:00:00Z";
export const EV_KNOWN = "2026-10-06T12:00:00Z";
export const EV_ACTION_ID = "3e0a9b1c-7d2f-4e6a-8b5c-0f1e2d3c4b5a";
export const EV_FINDING = "c0ffee12-3456-4789-8abc-def012345678";
export const EV_FINDING_REV = "5a5a5a5a-6b6b-4c7c-8d8d-9e9e9e9e9e9e";
export const EV_W1_ID = "7a6b5c4d-3e2f-4a1b-9c8d-7e6f5a4b3c2d";
export const EV_W1_FINDING = "44443333-2222-4111-8000-999988887777";
export const EV_W1_REV = "56565656-7878-4989-8a0a-1b1b1b1b1b1b";

/** The EV `criterion_summary` the server derives from the three validated EV keys (`work/domain_action.py`). */
export const EV_SUMMARY = "A complete witnessed session and no repeat fault";

/** One EV domain Action row exactly as the V1b index emits it (`domain:'EV_CHARGING'`, string title, `OPEN`). */
export function evRow(over: Partial<DomainIndexRow> = {}): DomainIndexRow {
  return {
    action_id: EV_ACTION_ID,
    action_code: "ACT-000061",
    domain: "EV_CHARGING",
    title: "Investigate connector 2",
    owner_label: "Charging operations",
    due_at: null,
    raised_at: "2026-10-06T09:10:00Z",
    recorded_at: "2026-10-06T09:10:01Z",
    origin: {
      finding_id: EV_FINDING,
      finding_revision_id: EV_FINDING_REV,
      label: `Finding ${EV_FINDING.slice(0, 8)}`,
      href: `/sites/${EV_SITE_CODE}/findings/${EV_FINDING}?revision_id=${EV_FINDING_REV}`,
    },
    state: "OPEN",
    criterion_summary: EV_SUMMARY,
    links: { action: `/sites/${EV_SITE_CODE}/actions/${EV_ACTION_ID}/verification`, history: null },
    ...over,
  } as DomainIndexRow;
}

/** A W1 battery row on the EV Site (pre-flight 28): W1 state object, no title, no criterion, the W1 address. */
export function evW1Row(): DomainIndexRow {
  return {
    action_id: EV_W1_ID,
    action_code: "ACT-000060",
    domain: "MINIGRID",
    title: null,
    owner_label: null,
    due_at: null,
    raised_at: "2026-10-06T08:00:00Z",
    recorded_at: "2026-10-06T08:00:00Z",
    origin: {
      finding_id: EV_W1_FINDING,
      finding_revision_id: EV_W1_REV,
      label: `Finding ${EV_W1_FINDING.slice(0, 8)}`,
      href: `/sites/${EV_SITE_CODE}/findings/${EV_W1_FINDING}?revision_id=${EV_W1_REV}`,
    },
    state: {
      application: "PENDING",
      accepted_at: "2026-10-06T08:00:00Z",
      applied_at: null,
      application_attempts: 0,
      failed_attempts: 0,
      last_failure: null,
      outcome: { state: "NOT_EVALUATED", statement: "" },
    },
    criterion_summary: null,
    links: { action: `/sites/${EV_SITE_CODE}/actions/${EV_W1_ID}`, history: `/sites/${EV_SITE_CODE}/actions/${EV_W1_ID}/history?event_id=e1` },
  } as DomainIndexRow;
}

/** The `site-domain-action-index-1` envelope for the EV Site. */
export function evIndexBody(rows: DomainIndexRow[], over: Partial<DomainIndexBody> = {}): DomainIndexBody {
  return {
    schema_version: "site-domain-action-index-1",
    site_code: EV_SITE_CODE,
    window: { from: EV_FROM, to: EV_TO, bounds: "[from, to)" },
    known_at: EV_KNOWN,
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null },
    total_count: rows.length,
    all_due_dates_unset: rows.length > 0 && rows.every((r) => r.due_at === null),
    rows,
    next_cursor: null,
    selection_token: "sha256:ev",
    ...over,
  };
}

/** `n` EV rows with distinct IDs and codes, newest first (a five-row page for the fold). */
export function evRows(n: number): DomainIndexRow[] {
  return Array.from({ length: n }, (_, i) =>
    evRow({
      action_id: `3e0a9b1c-7d2f-4e6a-8b5c-0f1e2d3c4b${String(i).padStart(2, "0")}`,
      action_code: `ACT-0000${70 + i}`,
      links: { action: `/sites/${EV_SITE_CODE}/actions/3e0a9b1c-7d2f-4e6a-8b5c-0f1e2d3c4b${String(i).padStart(2, "0")}/verification`, history: null },
    }),
  );
}

/** Ruling 53: the exact pinned selection is unavailable, so the server keeps the honest null source href. */
export function evPinUnavailableRow(): DomainIndexRow {
  const row = evRow();
  return { ...row, origin: { ...row.origin, href: null } } as DomainIndexRow;
}
