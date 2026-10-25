/**
 * Test-only estate bodies shaped as the reviewed wire (`estate-finding-index-2`, `estate-action-index-1`). IDs are
 * synthetic UUIDs from the spec's injected-test range; no mock F/ACT ID, count or price is used.
 */
import type {
  EstateActionRow,
  EstateActionsBody,
  EstateClient,
  EstateCoverageSite,
  EstateFindingRow,
  EstateFindingsBody,
  EstateLens,
  EstateResult,
  EstateScopeBody,
} from "../estateClient";

export const SITE_A = "10000000-0000-4000-8000-000000000011";
export const SITE_B = "10000000-0000-4000-8000-000000000012";
export const FROM = "2026-10-13T00:00:00Z";
export const TO = "2026-10-20T00:00:00Z";
export const KNOWN = "2026-10-20T09:30:00Z";

const BLOCK = {
  classification: "REGISTERED_SIMULATION",
  state: "REGISTERED_SIMULATION",
  source_ids: [],
  evidence_ids: [],
  basis_sha256: `sha256:${"a".repeat(64)}`,
  reasons: [],
};

export function site(siteId: string, state: EstateCoverageSite["state"]): EstateCoverageSite {
  return {
    site_id: siteId,
    state,
    committed_watermark: null,
    selection_id: null,
    match_state: "COMPLETE",
    job_state: "SETTLED",
    source_freshness: "RECENT",
  };
}

export function findingRow(n: number, over: Partial<EstateFindingRow> = {}): EstateFindingRow {
  const fid = `10000000-0000-4000-8000-0000000001${String(n).padStart(2, "0")}`;
  const frid = `10000000-0000-4000-8000-0000000002${String(n).padStart(2, "0")}`;
  return {
    finding_id: fid,
    finding_revision_id: frid,
    site_id: SITE_A,
    site_code: "KOBO-001",
    site_name: "Kobo Mini-grid",
    finding_label: `Finding ${fid.slice(0, 8)}`,
    title: `Stored finding title ${n}`,
    priority: null,
    confidence: null,
    confidence_reasons: [],
    lifecycle: "SUPPORTED",
    lens_flags: [],
    consequence: {
      state: "UNPRICED",
      amount: null,
      amount_low: null,
      amount_high: null,
      currency: null,
      source_revision_id: null,
    },
    source_provenance: BLOCK,
    episode_start: "2026-10-14T08:00:00Z",
    status: "CURRENT",
    links: { finding: `/sites/KOBO-001/findings/${fid}?revision_id=${frid}`, site: "/sites/KOBO-001" },
    ...over,
  };
}

export function findingsBody(lens: EstateLens, over: Partial<EstateFindingsBody> = {}): EstateFindingsBody {
  const rows = over.rows ?? [findingRow(1)];
  return {
    schema_version: "estate-finding-index-2",
    scope: { tenant_id: "t", authorized_site_count: 2, covered_site_count: 2, access_basis: `sha256:${"b".repeat(64)}` },
    window: { from: FROM, to: TO, bounds: "[from, to)", known_at: KNOWN },
    status: "CURRENT",
    coverage: { state: "COMPLETE", sites: [site(SITE_A, "CURRENT"), site(SITE_B, "CURRENT")] },
    lens,
    state_filter: "all",
    summary: {
      high_priority: null,
      low_confidence: null,
      awaiting_verification: 0,
      basis_count: rows.length,
      supported_findings: rows.filter((r) => r.lifecycle === "SUPPORTED").length,
    },
    order: "episode_start desc, finding_id asc",
    total_count: rows.length,
    rows,
    next_cursor: null,
    selection_token: `sha256:${"c".repeat(64)}`,
    ...over,
  };
}

export function actionRow(over: Partial<EstateActionRow> = {}): EstateActionRow {
  return {
    action_id: "10000000-0000-4000-8000-000000000201",
    action_code: "ACT-000001",
    site_id: SITE_A,
    site_code: "KOBO-001",
    site_name: "Kobo Mini-grid",
    created_at: "2026-10-14T14:00:00Z",
    selected_event_id: "10000000-0000-4000-8000-000000000202",
    source_finding_id: "10000000-0000-4000-8000-000000000101",
    source_finding_revision_id: "10000000-0000-4000-8000-000000000102",
    action_title: "Action ACT-000001",
    success_criterion: null,
    owner: null,
    due_at: null,
    application_state: "PENDING",
    resolution_state: null,
    verification_outcome: null,
    source_provenance: { ...BLOCK, classification: "UNKNOWN", state: "UNKNOWN" },
    links: {
      action:
        "/sites/KOBO-001/actions/10000000-0000-4000-8000-000000000201?event_id=10000000-0000-4000-8000-000000000202",
      source:
        "/sites/KOBO-001/findings/10000000-0000-4000-8000-000000000101?revision_id=10000000-0000-4000-8000-000000000102",
    },
    ...over,
  };
}

export function actionsBody(over: Partial<EstateActionsBody> = {}): EstateActionsBody {
  const rows = over.rows ?? [actionRow()];
  return {
    schema_version: "estate-action-index-1",
    scope: { tenant_id: "t", authorized_site_count: 2, covered_site_count: 2, access_basis: `sha256:${"b".repeat(64)}` },
    window: { from: FROM, to: TO, bounds: "[from, to)", known_at: KNOWN },
    status: "CURRENT",
    coverage: { state: "COMPLETE", sites: [site(SITE_A, "CURRENT"), site(SITE_B, "NOT_APPLICABLE")] },
    summary: { open_actions: 1, due_overdue: null, verification_window: 0, verified_in_30_days: 0, basis_count: rows.length },
    order: "created_at desc, action_id asc",
    total_count: rows.length,
    rows,
    next_cursor: null,
    selection_token: `sha256:${"d".repeat(64)}`,
    ...over,
  };
}

export function loaded<T>(value: T): EstateResult<T> {
  return { status: "loaded", value };
}

/** A fake client answering every read with the given results (Findings per lens). */
export function fakeClient(
  findings: (lens: EstateLens) => EstateResult<EstateFindingsBody>,
  actions: EstateResult<EstateActionsBody> = loaded(actionsBody()),
  scope: EstateResult<EstateScopeBody> | null = null,
): EstateClient & { calls: unknown[] } {
  const calls: unknown[] = [];
  return {
    calls,
    findings: (query) => {
      calls.push({ kind: "findings", ...query });
      return Promise.resolve(findings(query.lens));
    },
    actions: (query) => {
      calls.push({ kind: "actions", ...query });
      return Promise.resolve(actions);
    },
    // Q7: the Finding lenses read scope for Site names; no answer means the read failed (generic copy).
    scope: (query) => {
      calls.push({ kind: "scope", ...query });
      return scope === null ? Promise.reject(new Error("no scope answer")) : Promise.resolve(scope);
    },
    portfolio: () => Promise.reject(new Error("the W3-01 roots do not read the Portfolio")),
  };
}

/** Q7: a scope body naming the given Sites (site_id -> name) at the fixture cutoff. */
export function scopeBody(sites: [string, string][]): EstateScopeBody {
  return {
    schema_version: "estate-scope-1",
    sites: sites.map(([site_id, site_name], i) => ({ site_id, site_code: `S-${i + 1}`, site_name, coverage_state: "CURRENT" })),
    authorized_site_count: sites.length,
    covered_site_count: sites.length,
    access_basis: `sha256:${"b".repeat(64)}`,
    known_at: KNOWN,
  };
}
