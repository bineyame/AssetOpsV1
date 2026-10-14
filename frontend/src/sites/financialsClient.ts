/**
 * S4-02a: the Site price reads and the Finding Financials bridge.
 *
 * `GET /api/sites/{site}/financial-assumptions` (current or at a recorded cutoff), the exact
 * `/financial-assumptions/{revision_id}` read and `GET /api/sites/{site}/findings/{id}/financials`. Status
 * mapping is the Finding read's: 401, 403, 404, 409 cutover closed, and 503 or a network failure as
 * unavailable. A bad or foreign revision is `not_found`; the latest price is never substituted.
 */
import { hasKeys, isObject } from "./evidenceRead";
import type { FindingReadResult } from "./findingClient";
import { SITES_API_PATH } from "./siteDirectoryClient";

export type FinancialReadResult<T> = FindingReadResult<T>;

export interface Interval {
  from: string;
  to: string | null;
  bounds: "[)";
}

export interface PriceRevision {
  revision_id: string;
  revision_no: number;
  prior_revision_id: string | null;
  assumption_key: string;
  /** The authored decimal, as a string: never parsed into a float for display. */
  value: string;
  currency: string;
  unit: string;
  basis: "AUTHORED_ESTIMATE" | "CONTRACT_RATE" | "RECORDED_PURCHASE" | string;
  source_reference: string;
  authored_valid: Interval;
  recorded_at: string;
  change_kind: "INITIAL" | "SUCCESSION" | "CORRECTION" | string;
  correction_reason: string | null;
  actor: { kind: string; id: string; author_id: string | null };
  channel: string;
  authorization_basis: string;
  provenance: Record<string, unknown>;
  idempotency_key: string;
  request_sha256: string;
}

export interface PriceAssignment {
  assignment_id: string;
  revision_id: string;
  publication_revision_id: string;
  valid: Interval;
  recorded: Interval;
}

export type PriceSelection =
  | ({ state: "PRICED"; valid_at: string; revision_id: string; price: PriceRevision } & PriceAssignment)
  | { state: "NO_PRICE"; valid_at: string; revision_id: null; assignment_id: null; note: string }
  | { state: "CONFLICT"; valid_at: string; revision_id: null; assignment_id: null };

export interface AssumptionSeriesBody {
  site_code: string;
  access_basis: string;
  assumption_key: string;
  unit: string;
  state: "PUBLISHED" | "NO_PRICE";
  cutoff: { recorded_at: string | null; selected_by: "CURRENT" | "RECORDED_CUTOFF"; basis: string };
  selection: PriceSelection | null;
  timeline: (PriceAssignment & { price: PriceRevision })[];
  revisions: PriceRevision[];
  revision_page: { after_revision_no: number; limit: number; total: number; next_after_revision_no: number | null };
}

export interface AssumptionRevisionBody {
  site_code: string;
  selection: { revision_id: string; selected_by: "EXACT_REVISION_ID" };
  revision: PriceRevision;
  assignments: PriceAssignment[];
  recorded_by_this_publication: PriceAssignment[];
}

export interface FindingConsequence {
  state: "QUANTITY_UNAVAILABLE" | "UNPRICED";
  quantity_source: string;
  amount: null;
  currency: null;
  price_revision_id: null;
  reason: string;
}

export interface FindingFinancialsBody {
  site_code: string;
  audit_only: { non_current: boolean; statement: string } | null;
  finding: { id: string };
  selection: { revision_id: string; revision_no: number; is_latest: boolean; selected_by: string };
  revision: { id: string; revision_no: number; title: string; lifecycle: string; claim_level: string };
  window: { start: string; end: string | null };
  consequence: FindingConsequence;
}

export interface SeriesQuery {
  validAt?: string | null;
  recordedAt?: string | null;
  afterRevisionNo?: number;
  limit?: number;
}

export interface FinancialsClient {
  getAssumptions(siteId: string, query: SeriesQuery): Promise<FinancialReadResult<AssumptionSeriesBody>>;
  getAssumptionRevision(siteId: string, revisionId: string): Promise<FinancialReadResult<AssumptionRevisionBody>>;
  getFindingFinancials(
    siteId: string,
    findingId: string,
    revisionId: string | null,
  ): Promise<FinancialReadResult<FindingFinancialsBody>>;
}

function isSeries(value: unknown): value is AssumptionSeriesBody {
  return (
    hasKeys(value, ["state", "cutoff", "timeline", "revisions", "revision_page"]) &&
    Array.isArray((value as { timeline: unknown }).timeline) &&
    Array.isArray((value as { revisions: unknown }).revisions)
  );
}

function isRevision(value: unknown): value is AssumptionRevisionBody {
  return hasKeys(value, ["selection", "revision", "assignments"]);
}

function isBridge(value: unknown): value is FindingFinancialsBody {
  return (
    hasKeys(value, ["finding", "selection", "revision", "window", "consequence"]) &&
    isObject((value as { consequence: unknown }).consequence)
  );
}

async function readFinancial<T>(path: string, valid: (value: unknown) => value is T): Promise<FinancialReadResult<T>> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok && valid(body)) {
    return { status: "loaded", value: body };
  }
  const detail = isObject(body) ? body.detail : null;
  const message =
    typeof detail === "string"
      ? detail
      : isObject(detail) && typeof detail.message === "string"
        ? detail.message
        : null;
  switch (response.status) {
    case 401:
      return { status: "unauthenticated", message };
    case 403:
      return { status: "forbidden", message };
    case 404:
    case 422:
      return { status: "not_found", message };
    case 409:
      if (isObject(detail) && detail.code === "PERFORMANCE_CUTOVER_CLOSED") {
        return { status: "closed", message, note: typeof detail.note === "string" ? detail.note : null };
      }
      return { status: "unavailable", message };
    default:
      return { status: "unavailable", message };
  }
}

export function createFinancialsClient(basePath: string = SITES_API_PATH): FinancialsClient {
  const site = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}`;
  return {
    getAssumptions(siteId, query) {
      const params = new URLSearchParams({ key: "diesel_price_per_litre" });
      if (query.validAt) params.set("valid_at", query.validAt);
      if (query.recordedAt) params.set("recorded_at", query.recordedAt);
      if (query.afterRevisionNo) params.set("after_revision_no", String(query.afterRevisionNo));
      if (query.limit) params.set("limit", String(query.limit));
      return readFinancial(`${site(siteId)}/financial-assumptions?${params.toString()}`, isSeries);
    },
    getAssumptionRevision(siteId, revisionId) {
      return readFinancial(
        `${site(siteId)}/financial-assumptions/${encodeURIComponent(revisionId)}`,
        isRevision,
      );
    },
    getFindingFinancials(siteId, findingId, revisionId) {
      const pin = revisionId ? `?revision_id=${encodeURIComponent(revisionId)}` : "";
      return readFinancial(`${site(siteId)}/findings/${encodeURIComponent(findingId)}/financials${pin}`, isBridge);
    },
  };
}
