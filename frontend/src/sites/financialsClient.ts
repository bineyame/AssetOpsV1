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
import type { SourceProvenance, SourceProvenancePair } from "./sourceProvenance";

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

/** S4-02b: the read's currentness of one FindingRevision's stored consequence (review M1 adds AUDIT_ONLY). */
export type ConsequenceCurrentness = "CURRENT" | "STALE" | "PENDING" | "HISTORICAL" | "AUDIT_ONLY";

/** LR-01: one generator-series refusal behind a withheld amount, with the exact lineage that refused it. */
export interface MoneySeriesLimit {
  kind: string;
  role: string;
  start: string;
  end: string;
  evidence_ids: string[];
  clock: string | null;
  attestation_refs: string[];
  window_assessment_revision_id?: string | null;
  analytic_run_id?: string | null;
  relation?: string;
  source?: "FINDING_REVISION" | "SELECTED_WINDOW";
}

/** LR-01: the shared, read-derived money eligibility gate (`money-eligibility-1`). ELIGIBLE is not an amount. */
export interface MoneyEligibility {
  version: string;
  state: "ELIGIBLE" | "WITHHELD_GENERATOR_SERIES" | "PENDING_REASSESSMENT";
  note: string;
  finding_id: string;
  latest_finding_revision_id: string | null;
  latest_revision_no?: number | null;
  end_reason?: string | null;
  pending_reasons: string[];
  series_limits: MoneySeriesLimit[];
  windows: { day: string; s3_status: string; analytic_run_id: string | null; window_assessment_revision_id: string | null }[];
  head_consequence_revision_id?: string | null;
}

/** The bridge's typed summary: an amount only for a CURRENT PRICED head that the money gate lets through. */
export interface FindingConsequence {
  state:
    | "WITHHELD_GENERATOR_SERIES"
    | "PENDING_REASSESSMENT"
    | "MIXED_OR_UNKNOWN_SOURCE"
    | "PRICED"
    | "UNPRICED"
    | "QUANTITY_UNAVAILABLE"
    | "STALE"
    | "PENDING"
    | "HISTORICAL"
    | "AUDIT_ONLY"
    | "UNAVAILABLE";
  currentness: ConsequenceCurrentness | null;
  quantity_source: string;
  quantity: { low: string; high: string; unit: string } | null;
  /** Display strings, low rounded down and high rounded up; never parsed into a float. */
  amount: { low: string; high: string } | null;
  currency: string | null;
  price_revision_id: string | null;
  consequence_revision_id: string | null;
  quantity_reason: string | null;
  price_reason: string | null;
  recalculation_queued?: boolean;
  currentness_reasons?: string[];
  reason: string;
  /** LR-01: the gate behind the state, and the recorded (not current) head it withholds. */
  money_eligibility?: MoneyEligibility | null;
  recorded_consequence_revision_id?: string | null;
  /** S4-05b phase 2: the stored source gate and every failed typed gate at once. */
  source_gate?: SourceGate | null;
  withheld_reasons?: string[];
}

/** S4-05b phase 2: only a positive stored class may carry a current amount; otherwise `MIXED_OR_UNKNOWN_SOURCE`. */
export interface SourceGate {
  state: string;
  permits_current_money: boolean;
  reason: "MIXED_OR_UNKNOWN_SOURCE" | null;
}

export interface FindingFinancialsBody {
  site_code: string;
  audit_only: { non_current: boolean; statement: string } | null;
  finding: { id: string };
  selection: { revision_id: string; revision_no: number; is_latest: boolean; selected_by: string };
  revision: { id: string; revision_no: number; title: string; lifecycle: string; claim_level: string };
  window: { start: string; end: string | null };
  /** S4-05b: the stored source provenance of the exact Finding version and the summarised consequence version. */
  source_provenance?: SourceProvenancePair | null;
  consequence: FindingConsequence;
}

export interface PowerIntervalLineage {
  evidence_id: string;
  interval_start: string;
  interval_end: string;
  mean_kw: string;
  duration_seconds: number;
  sfc_l_per_kwh: string;
  foundation_revision_id: string;
  binding_revision_id: string;
  envelope_sha256: string;
  covered_spans: unknown;
  containment: string;
}

/** One stored `fuel-cost-1` consequence revision, as the S4-02b read returns it. */
export interface ConsequenceRevision {
  id: string;
  revision_no: number;
  prior_consequence_revision_id: string | null;
  finding_id: string;
  finding_revision_id: string;
  consequence_type: string;
  basis_kind: string;
  state: "PRICED" | "UNPRICED" | "QUANTITY_UNAVAILABLE" | string;
  window: { start: string; end: string; bounds: string };
  overlap_group: string;
  recorded_at: string;
  actor_id: string;
  model: {
    model_id: string;
    formula_version: string;
    parameter_version: string;
    parameter_sha256: string;
    sfc_upper_multiplier: string | null;
    parameter_is_reviewed: boolean;
  };
  quantity: {
    state: string;
    reason: string | null;
    detail: unknown;
    unit: string;
    low: string | null;
    high: string | null;
    high_exact: unknown;
    high_display: string | null;
  };
  price: {
    state: string;
    reason: string | null;
    revision_id: string | null;
    value: string | null;
    currency: string | null;
    unit: string;
    considered: string[][];
  };
  amount: { low: string | null; high: string | null; currency: string | null; unrounded: boolean };
  display: {
    state: string;
    currency: string;
    amount_low: string | null;
    amount_high: string | null;
  } | null;
  limitations: string[];
  digests: { technical_input_sha256: string; consequence_basis_sha256: string };
  lineage: {
    assessments: { assessment_revision_id: string; analytic_run_id: string; is_primary: boolean }[];
    assumptions: { assumption_revision_id: string; assignment_id: string; role: string }[];
    power_intervals: PowerIntervalLineage[];
    evidence_ids: string[];
  };
  is_head?: boolean;
  presented_as_current?: boolean;
  historical?: boolean;
  /** S4-05b: this consequence version's own union provenance (its Finding version's cited set and power IDs). */
  source_provenance?: SourceProvenance | null;
}

export interface FindingConsequencesBody {
  site_code: string;
  audit_only: { non_current: boolean; statement: string } | null;
  finding: { id: string };
  selection: { revision_id: string; revision_no: number; is_latest: boolean };
  window: { start: string; end: string | null };
  /** S4-05b: the stored source provenance of the exact Finding version and the selected consequence version. */
  source_provenance?: SourceProvenancePair | null;
  consequence_selection: {
    selected_by: "EXACT_CONSEQUENCE_REVISION_ID" | "HEAD";
    consequence_revision_id: string | null;
    head_consequence_revision_id: string | null;
    finding_revision_id: string;
    finding_revision_is_latest: boolean;
    source_open?: boolean;
  };
  currentness: {
    state: ConsequenceCurrentness;
    reasons: string[];
    pending_work: { work_id: string; cause: string; attempts: number; last_error_code: string | null }[];
    current_amount_shown: boolean;
    derived_now: unknown;
    money_eligibility?: MoneyEligibility["state"];
    source_gate?: SourceGate;
    withheld_reasons?: string[];
  };
  money_eligibility?: MoneyEligibility;
  consequence: ConsequenceRevision | null;
  history: {
    revisions: ConsequenceRevision[];
    total: number;
    page: { after_revision_no: number; limit: number; next_after_revision_no: number | null };
  };
  exclusions: string[];
  links: { evidence_records?: Record<string, string>; price_revisions?: Record<string, string> };
}

/** S4-08: one stored consequence revision at a recorded cutoff (`financials/consequence_history.py`). */
export type HistoryAmountDisposition =
  | "SHOWN"
  | "SOURCE_CLOSED"
  | "MIXED_OR_UNKNOWN_SOURCE"
  | "UNPRICED"
  | "QUANTITY_UNAVAILABLE"
  | "MINOR_UNIT_UNKNOWN"
  | "LINEAGE_INCONSISTENT";

export interface HistoryPriceAssignment {
  assumption_revision_id: string;
  assignment_id: string;
  used: boolean;
  valid: { from: string | null; to: string | null; bounds: string };
  recorded: { from: string | null; to: string | null; bounds: string };
}

export interface ConsequenceHistoryRow {
  finding_id: string;
  finding_revision_id: string;
  finding_revision_no: number | null;
  finding_title: string | null;
  finding_window: { from: string | null; to: string | null; bounds: string } | null;
  consequence_revision_id: string;
  revision_no: number;
  prior_consequence_revision_id: string | null;
  recorded_at: string;
  window: { from: string | null; to: string | null; bounds: string };
  at_cutoff: "CURRENT_AT_CUTOFF" | "HISTORICAL_AT_CUTOFF";
  state: "PRICED" | "UNPRICED" | "QUANTITY_UNAVAILABLE";
  quantity: { state: string; reason: string | null; unit: string; high: string | null };
  price: {
    state: "LINKED" | "NO_PRICE_LINK" | "NOT_EVALUATED" | "LINEAGE_INCONSISTENT";
    price_revision_id: string | null;
    reason: string | null;
    value: string | null;
    currency: string | null;
    assignments: HistoryPriceAssignment[];
  };
  change_from_prior: "FIRST_VERSION" | "PRICE_ONLY" | "SAME_INPUTS" | "MEASURED_RESULT_CHANGED" | "PRIOR_UNREADABLE";
  recorded_amount: {
    disposition: HistoryAmountDisposition;
    label: string | null;
    amount: { low: string | null; high: string | null; currency: string } | null;
    is_current_amount: false;
  };
  source_provenance: SourceProvenance | null;
  links: { finding: string; finding_financials: string; price_revision: string | null; api_consequence: string };
}

export interface ConsequenceHistoryBody {
  site_code: string;
  cutoff: { recorded_at: string; selected_by: "SERVER_DEFAULT" | "RECORDED_CUTOFF"; clock: string; membership: string };
  current_amount_shown: false;
  source_gate: { open: boolean; reason: string | null };
  classification: string;
  rows: ConsequenceHistoryRow[];
  next_cursor: string | null;
  page: { limit: number; shown: number; is_first: boolean };
  zero_statement: string | null;
  exclusions: string[];
}

export interface HistoryQuery {
  /** The server's cutoff string, passed through unchanged (review L-R1); null fixes a new one. */
  recordedAt: string | null;
  after?: string | null;
  limit?: number;
}

/** A history page, or the typed 409 telling the reader to reload page one without a cursor. */
export type ConsequenceHistoryResult =
  | FinancialReadResult<ConsequenceHistoryBody>
  | { status: "basis_changed"; message: string | null };

export interface ConsequencePin {
  revisionId: string | null;
  consequenceRevisionId?: string | null;
  afterRevisionNo?: number;
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
  getFindingConsequences(
    siteId: string,
    findingId: string,
    pin: ConsequencePin,
  ): Promise<FinancialReadResult<FindingConsequencesBody>>;
  /** S4-08: the Site's recorded fuel cost versions at one cutoff. */
  getConsequenceHistory(siteId: string, query: HistoryQuery): Promise<ConsequenceHistoryResult>;
}

function isHistory(value: unknown): value is ConsequenceHistoryBody {
  return (
    hasKeys(value, ["cutoff", "rows", "current_amount_shown", "page"]) &&
    Array.isArray((value as { rows: unknown }).rows) &&
    isObject((value as { cutoff: unknown }).cutoff) &&
    typeof ((value as { cutoff: { recorded_at?: unknown } }).cutoff.recorded_at) === "string" &&
    (value as { current_amount_shown: unknown }).current_amount_shown === false
  );
}

function isConsequences(value: unknown): value is FindingConsequencesBody {
  if (!hasKeys(value, ["selection", "consequence_selection", "currentness", "history"])) return false;
  const history = (value as { history: unknown }).history;
  return isObject(history) && Array.isArray(history.revisions) && isObject((value as { currentness: unknown }).currentness);
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

async function readWith<T>(
  path: string,
  valid: (value: unknown) => value is T,
  conflict?: (detail: unknown) => boolean,
): Promise<FinancialReadResult<T> | { status: "basis_changed"; message: string | null }> {
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
    case 400:
      return { status: "not_found", message };
    case 409:
      if (conflict?.(detail)) return { status: "basis_changed", message };
      if (isObject(detail) && detail.code === "PERFORMANCE_CUTOVER_CLOSED") {
        return { status: "closed", message, note: typeof detail.note === "string" ? detail.note : null };
      }
      return { status: "unavailable", message };
    default:
      return { status: "unavailable", message };
  }
}

/** Without a conflict reader no response is `basis_changed`, so the narrower result type holds. */
function readFinancial<T>(path: string, valid: (value: unknown) => value is T): Promise<FinancialReadResult<T>> {
  return readWith(path, valid) as Promise<FinancialReadResult<T>>;
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
    getFindingConsequences(siteId, findingId, pin) {
      const params = new URLSearchParams();
      if (pin.revisionId) params.set("revision_id", pin.revisionId);
      if (pin.consequenceRevisionId) params.set("consequence_revision_id", pin.consequenceRevisionId);
      if (pin.afterRevisionNo) params.set("after_revision_no", String(pin.afterRevisionNo));
      const query = params.toString();
      return readFinancial(
        `${site(siteId)}/findings/${encodeURIComponent(findingId)}/financial-consequences${query ? `?${query}` : ""}`,
        isConsequences,
      );
    },
    getConsequenceHistory(siteId, query) {
      const params = new URLSearchParams();
      if (query.recordedAt) params.set("recorded_at", query.recordedAt);
      if (query.after) params.set("after", query.after);
      if (query.limit) params.set("limit", String(query.limit));
      const text = params.toString();
      return readWith(
        `${site(siteId)}/financial-assumptions/consequences${text ? `?${text}` : ""}`,
        isHistory,
        (detail) => isObject(detail) && detail.code === "CONSEQUENCE_HISTORY_BASIS_CHANGED",
      );
    },
  };
}
