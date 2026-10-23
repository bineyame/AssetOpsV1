/**
 * W5-02a core review M1: the W6 request-detail runtime validator accepts a domain Action link (null event ID).
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { readGlobalWorkDetail, type GlobalWorkDetailBody, type WorkCaseDetailEvent } from "../globalWorkClient";

const CASE = "6f1c2d3e-4a5b-4c6d-8e7f-001122334455";
const OVERVIEW = `/maintenance/requests/${CASE}?site_id=KOBO-001`;
const RECORD = `/maintenance/requests/${CASE}/record?site_id=KOBO-001`;
const HISTORY = `/maintenance/requests/${CASE}/history?site_id=KOBO-001`;
const ACTION = "00000000-0000-4000-8000-000000000501";
const EVENT = "00000000-0000-4000-8000-000000000502";
const FINDING_REVISION = "00000000-0000-4000-8000-000000000503";

function event(n: number, kind: string, payload: Record<string, unknown> = {}): WorkCaseDetailEvent {
  return {
    id: `00000000-0000-4000-8000-${String(300 + n).padStart(12, "0")}`,
    kind,
    payload,
    occurred_at: `2026-10-20T11:59:0${n}Z`,
    recorded_at: `2026-10-20T11:59:0${n}Z`,
    actor_kind: "SERVICE",
    actor_id: "service:w401-fixture",
  };
}

function detail(over: Partial<GlobalWorkDetailBody> = {}, state = "IN_PROGRESS"): GlobalWorkDetailBody {
  return {
    schema_version: "global-work-detail-1",
    selected: {
      site_code: "KOBO-001",
      site_id: "00000000-0000-4000-8000-000000000002",
      case_id: CASE,
      case_code: "WR-000001",
      case_kind: "MAINTENANCE_REQUEST",
      known_at: "2026-10-22T12:00:00.000000Z",
    },
    work_detail: {
      schema_version: "work-case-detail-1",
      site_code: "KOBO-001",
      case: {
        id: CASE,
        code: "WR-000001",
        kind: "MAINTENANCE_REQUEST",
        asset_id: null,
        occurred_at: "2026-10-18T10:00:00Z",
        created_at: "2026-10-20T11:59:00Z",
        state,
        incident_id: null,
      },
      selected_revision: {
        id: "00000000-0000-4000-8000-000000000201",
        revision_no: 2,
        supersedes_revision_id: "00000000-0000-4000-8000-000000000200",
        title: "Inspect starter and control circuit again",
        narrative: "Starter inspection requested.",
        reason: "Scope widened",
        recorded_at: "2026-10-20T11:59:06Z",
        actor_kind: "SERVICE",
        actor_id: "service:w401-fixture",
        occurred_at: "2026-10-20T11:59:06Z",
      },
      finding_links: [],
      action_links: [],
      cited_accepted_evidence_ids: [],
      events: [
        event(0, "CREATED"),
        event(1, "ASSIGN", { assignee: "Field team A" }),
        event(2, "COMMENT", { text: "Parts ordered" }),
        event(4, "COMPLETE", { maintenance_record_id: "00000000-0000-4000-8000-000000000401" }),
        event(5, "REOPEN", { reason: "Fault returned" }),
      ],
      records: [
        {
          id: "00000000-0000-4000-8000-000000000401",
          activity: "Replaced starter relay and tested the start.",
          outcome_note: null,
          occurred_at: "2026-10-20T11:59:03Z",
          recorded_at: "2026-10-20T11:59:03Z",
          supersedes_record_id: null,
        },
      ],
      source_provenance: {
        classification: "AUTHORED_DEMONSTRATION",
        state: "KNOWN",
        source_ids: [],
        evidence_ids: [],
        basis_sha256: `sha256:${"0".repeat(64)}`,
        reasons: [],
      },
      coverage: { state: "COMPLETE", reason: null },
    },
    work_asset: null,
    history: { revisions: [], operational_records: [] },
    links: {
      site: { label: "Kobo", href: "/sites/KOBO-001" },
      overview: { label: "Overview", href: OVERVIEW },
      record: { label: "Maintenance record", href: RECORD },
      history: { label: "History", href: HISTORY },
      source_incident: null,
      findings: [],
      actions: [],
    },
    ...over,
  };
}


function respond(body: GlobalWorkDetailBody) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })));
}

describe("readGlobalWorkDetail action links", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("test_read_global_work_detail_accepts_domain_action_link_with_null_event", async () => {
    const domain = { kind: "DOMAIN_ACTION", action_id: ACTION, action_event_id: null, finding_revision_id: FINDING_REVISION };
    const base = detail();
    respond(detail({ work_detail: { ...base.work_detail, action_links: [domain] } }));
    const result = await readGlobalWorkDetail("/api/work/requests/x");
    expect(result.status).toBe("loaded");
    if (result.status === "loaded") expect(result.value.work_detail.action_links).toEqual([domain]);

    const w1 = { action_id: ACTION, action_event_id: EVENT };
    respond(detail({ work_detail: { ...base.work_detail, action_links: [w1] } }));
    const second = await readGlobalWorkDetail("/api/work/requests/x");
    expect(second.status).toBe("loaded");
    if (second.status === "loaded") expect(second.value.work_detail.action_links).toEqual([w1]);
  });
});
