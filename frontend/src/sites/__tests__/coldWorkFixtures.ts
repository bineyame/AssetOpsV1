/**
 * W5-02 K2a: shared COLDCHAIN Site and union Action index / domain Action detail wire fixtures for the cold Work and
 * domain Action tests. Shapes follow `backend/assetops_backend/work/domain_action_index.py` exactly.
 */
import type { DomainActionDetail, DomainIndexBody, DomainIndexRow } from "../domainActionClient";
import type { SiteDetailReadModel } from "../siteReadModel";

export const SITE = "CR-TEST-01";
export const COLD_SITE = {
  site_id: SITE,
  display_name: "GreenHarvest Cold Room",
  site_type: "COLDCHAIN",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Africa/Addis_Ababa",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;

export const FROM = "2026-10-15T00:00:00Z";
export const TO = "2026-10-22T00:00:00Z";
export const KNOWN = "2026-10-22T09:30:00Z";
export const DOMAIN_ID = "6f1c2a7e-0d4b-4c3e-9a51-1b2c3d4e5f60";
export const W1_ID = "0b9d8c7a-6e5f-4a3b-8c2d-1e0f9a8b7c6d";
export const FINDING = "abcdef12-3456-4789-8abc-def012345678";
export const FINDING_REV = "11112222-3333-4444-8555-666677778888";
export const W1_FINDING = "99998888-7777-4666-8555-444433332222";
export const W1_REV = "12121212-3434-4565-8787-909090909090";

export function domainRow(over: Partial<DomainIndexRow> = {}): DomainIndexRow {
  return {
    action_id: DOMAIN_ID,
    action_code: "ACT-000051",
    domain: "COLDCHAIN",
    title: "Witness automatic-start test",
    owner_label: "Maintenance lead",
    due_at: null,
    raised_at: "2026-10-21T16:30:00Z",
    recorded_at: "2026-10-21T16:30:01Z",
    origin: {
      finding_id: FINDING,
      finding_revision_id: FINDING_REV,
      label: `Finding ${FINDING.slice(0, 8)}`,
      href: `/sites/${SITE}/findings/${FINDING}?revision_id=${FINDING_REV}`,
    },
    state: "OPEN",
    criterion_summary: "Start requested → generator runs → power → cooling",
    links: { action: `/sites/${SITE}/actions/${DOMAIN_ID}/verification`, history: null },
    ...over,
  } as DomainIndexRow;
}

export function w1Row(): DomainIndexRow {
  return {
    action_id: W1_ID,
    action_code: "ACT-000050",
    domain: "MINIGRID",
    title: null,
    owner_label: null,
    due_at: null,
    raised_at: "2026-10-20T10:00:00Z",
    recorded_at: "2026-10-20T10:00:00Z",
    origin: {
      finding_id: W1_FINDING,
      finding_revision_id: W1_REV,
      label: `Finding ${W1_FINDING.slice(0, 8)}`,
      href: `/sites/${SITE}/findings/${W1_FINDING}?revision_id=${W1_REV}`,
    },
    state: {
      application: "PENDING",
      accepted_at: "2026-10-20T10:00:00Z",
      applied_at: null,
      application_attempts: 0,
      failed_attempts: 0,
      last_failure: null,
      outcome: { state: "NOT_EVALUATED", statement: "" },
    },
    criterion_summary: null,
    links: { action: `/sites/${SITE}/actions/${W1_ID}`, history: `/sites/${SITE}/actions/${W1_ID}/history?event_id=e1` },
  } as DomainIndexRow;
}

export function indexBody(rows: DomainIndexRow[], over: Partial<DomainIndexBody> = {}): DomainIndexBody {
  return {
    schema_version: "site-domain-action-index-1",
    site_code: SITE,
    window: { from: FROM, to: TO, bounds: "[from, to)" },
    known_at: KNOWN,
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null },
    total_count: rows.length,
    all_due_dates_unset: rows.length > 0 && rows.every((r) => r.due_at === null),
    rows,
    next_cursor: null,
    selection_token: "sha256:abc",
    ...over,
  };
}

export function detailBody(over: Partial<DomainActionDetail> = {}): DomainActionDetail {
  return {
    schema_version: "domain-action-intent-read-1",
    site_code: SITE,
    action: {
      id: DOMAIN_ID,
      action_code: "ACT-000051",
      domain: "COLDCHAIN",
      title: "Witness automatic-start test",
      owner_label: "Maintenance lead",
      due_at: null,
      raised_at: "2026-10-21T16:30:00Z",
      recorded_at: "2026-10-21T16:30:01Z",
      state: "OPEN",
    },
    known_at: KNOWN,
    status: "CURRENT",
    intent: {
      id: "aaaa0000-0000-4000-8000-000000000001",
      recorded_at: "2026-10-21T16:31:00Z",
      criteria: [],
      basis: { finding_revision_id: FINDING_REV, work_case_id: "c1", work_record_id: null, accepted_evidence_ids: [] },
    },
    results: [],
    links: {
      finding: { label: `Finding ${FINDING.slice(0, 8)}`, href: null },
      work: { case_id: null, case_code: null, case_title: null, request_state: null, record_id: null, label: null, href: null },
    },
    source_provenance: null,
    selection_token: "sha256:def",
    ...over,
  };
}

/** A `fetch` stub for App-level tests: the two domain-work reads from the builders, every other read refused. */
export function coldFetch(index: DomainIndexBody = indexBody([domainRow()]), detail: DomainActionDetail = detailBody()) {
  const urls: string[] = [];
  const fetchStub = async (url: string) => {
    urls.push(url);
    const path = url.split("?")[0];
    if (path === `/api/sites/${SITE}/domain-work/action-index`) return new Response(JSON.stringify(index), { status: 200 });
    if (path === `/api/sites/${SITE}/domain-work/actions/${detail.action.id}`) return new Response(JSON.stringify(detail), { status: 200 });
    return new Response(JSON.stringify({ detail: { code: "WORK_STORE_UNAVAILABLE", message: "Unavailable in this test." } }), { status: 503 });
  };
  return { urls, fetchStub };
}
