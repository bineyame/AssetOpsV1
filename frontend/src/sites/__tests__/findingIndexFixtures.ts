/**
 * S4-04 phase 2 test fixtures: Site Finding index bodies and fake clients.
 * Shapes follow `backend/assetops_backend/analytics/finding_index.py` (`site-finding-index-1`).
 */
import { vi } from "vitest";

import type {
  FindingIndexBody,
  FindingIndexClient,
  FindingIndexResult,
  FindingIndexRow,
  FindingIndexScope,
} from "../findingIndexClient";

/** A legacy (not imported) Site: the frame keeps the older Site Findings summary. */
export const NOT_IMPORTED_INDEX: FindingIndexClient = {
  getFindingIndex: () => Promise.resolve({ status: "not_imported", message: "No imported Site." }),
};

export const FID_A = "0a0a0a0a-0000-4000-8000-00000000000a";
export const FID_B = "0b0b0b0b-0000-4000-8000-00000000000b";
export const RID_A = "1a1a1a1a-0000-4000-8000-00000000001a";
export const RID_B = "1b1b1b1b-0000-4000-8000-00000000001b";
export const TOKEN = "sfi1-abc123";

export function indexRow(id: string, revision: string, start: string, end: string,
  over: Partial<FindingIndexRow> = {}): FindingIndexRow {
  const base = `/sites/KOBO-001/findings/${id}`;
  return {
    key: { tenant_id: "t", site_id: "s", finding_id: id },
    finding_id: id,
    canonical_finding_id: id,
    finding_revision_id: revision,
    revision_no: 2,
    title: "Generator support merits review: bounded candidate avoidable running",
    episode: { start, end },
    lifecycle: "SUPPORTED",
    transition: "OPENED",
    claim_level: "CANDIDATE_AVOIDABLE",
    assessment: {
      assessment_revision_id: "ar",
      analytic_run_id: "99999999-0000-4000-8000-000000000099",
      model_version: "dispatch-3.1",
      matcher_version: "finding-episode-1",
      cohort_sha256: null,
    },
    cited: { accepted_evidence_ids: ["e1"], configuration: [{ run_id: "r" }] },
    limitations: [],
    relations: { merged_from: [], recurs_after: null, recurred_by: [], split_from: null, split_parts: [] },
    links: {
      selected_revision: `${base}?revision_id=${revision}`,
      canonical: base,
      api_history: `/api${base}/history?revision_id=${revision}`,
      api_selected_revision: `/api${base}?revision_id=${revision}`,
    },
    amount: { state: "UNAVAILABLE", reason: "No current amount: exact-revision money provenance is not in this read yet." },
    ...over,
  };
}

export function indexBody(over: Partial<FindingIndexBody> = {}): FindingIndexBody {
  return {
    schema_version: "site-finding-index-1",
    site_code: "KOBO-001",
    site_id: "s",
    access_basis: "development",
    domain: { requested: "mini-grid-dispatch", finding_domain: "mini_grid", analytic_id: "dispatch", matcher_version: "m" },
    window: { from: "2026-10-25T00:00:00Z", to: "2026-10-26T00:00:00Z", bounds: "[from, to)", intersection: "x" },
    display_timezone: "UTC",
    status: "CURRENT",
    status_reasons: [],
    is_current: true,
    selection_token: TOKEN,
    knowledge_at: "2026-10-30T08:00:00Z",
    knowledge_at_label: "label",
    built_at: "2026-10-30T09:00:00Z",
    discovery: { days: ["2026-10-25"], requested_days: ["2026-10-25"], continuity_tolerance_minutes: 20, limit_days: 62 },
    watermarks: {
      matcher: { match_pass_id: "88888888-0000-4000-8000-000000000088", matched_through_selection_seq: 7 },
      days: [
        {
          day: "2026-10-25",
          status: "CURRENT",
          reasons: [],
          s3: {
            status: "CURRENT",
            selection_seq: 7,
            run_id: "99999999-0000-4000-8000-000000000099",
            window_assessment_revision_id: "w",
            model_version: "dispatch-3.1",
            knowledge_cutoff: "2026-10-30T08:00:00Z",
            selected_at: "2026-10-30T08:05:00Z",
          },
          s4: { matched: true, matcher_version: "m" },
        },
      ],
    },
    order: "episode_start descending, then Finding UUID ascending",
    rows: [],
    total_count: 0,
    next_cursor: null,
    rows_statement: null,
    ...over,
  };
}

export function notCurrent(status: FindingIndexBody["status"], reason: string): FindingIndexBody {
  return indexBody({
    status,
    is_current: false,
    status_reasons: [`2026-10-25: ${reason}`],
    rows: [],
    total_count: null,
    rows_statement: "No rows and no count: this index is not current. This is not a no-Findings verdict.",
  });
}

export function indexClient(answer: (scope: FindingIndexScope) => FindingIndexResult) {
  const getFindingIndex = vi.fn((_site: string, scope: FindingIndexScope) => Promise.resolve(answer(scope)));
  return { client: { getFindingIndex } as FindingIndexClient, getFindingIndex };
}
