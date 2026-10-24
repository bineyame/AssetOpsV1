/**
 * W3-01 commit 3: the typed client for the three estate reads (`.agent/W3-01-build-spec.md`, "Public API and
 * examples", Run 8 ruling 3 and Run 12 ruling 3). The Findings envelope is `estate-finding-index-2`; Actions and
 * scope stay `-1`. The cursor is opaque: the client passes it back unchanged (it carries `page_one_mode` and the
 * full-precision cutoff), and any lens, state or window change restarts at page one without it.
 */

export const ESTATE_API_PATH = "/api/estate";

export const FINDINGS_SCHEMA = "estate-finding-index-2";
export const ACTIONS_SCHEMA = "estate-action-index-1";
export const SCOPE_SCHEMA = "estate-scope-1";

export type EstateLens = "all" | "cost" | "risks" | "opportunities";
export type EstateStateFilter = "all" | "supported" | "unconfirmed" | "no_longer_supported" | "merged";
export type EstateSiteState =
  | "CURRENT"
  | "PENDING_RECOMPUTE"
  | "STALE_SOURCE"
  | "HISTORICAL"
  | "UNKNOWN"
  | "NOT_APPLICABLE";
export type EstateLifecycle = "SUPPORTED" | "UNCONFIRMED" | "NO_LONGER_SUPPORTED" | "MERGED";

/** The public provenance block (shared DTO, `D-2026-10-20-shared-provenance-dto`); read by `sourceProvenance.tsx`. */
export interface EstateSourceBlock {
  classification?: string;
  state: string;
  source_ids?: string[];
  evidence_ids?: string[];
  basis_sha256?: string | null;
  reasons?: { code: string; accepted_evidence_ids: string[] }[];
  [key: string]: unknown;
}

export interface EstateCoverageSite {
  site_id: string;
  state: EstateSiteState;
  committed_watermark: string | null;
  selection_id: string | null;
  match_state: string;
  job_state: string;
  source_freshness: string;
}

export interface EstateEnvelope {
  schema_version: string;
  scope: { tenant_id: string | null; authorized_site_count: number; covered_site_count: number; access_basis: string };
  window: { from: string; to: string; bounds: string; known_at: string };
  status: EstateSiteState;
  coverage: { state: "COMPLETE" | "PARTIAL" | "UNKNOWN"; sites: EstateCoverageSite[] };
  total_count: number | null;
  next_cursor: string | null;
  selection_token: string;
}

export interface EstateConsequence {
  state: "PRICED" | "UNPRICED" | "UNKNOWN";
  amount: string | null;
  amount_low: string | null;
  amount_high: string | null;
  currency: string | null;
  source_revision_id: string | null;
}

export interface EstateFindingRow {
  finding_id: string;
  finding_revision_id: string;
  site_id: string;
  site_code: string;
  site_name: string;
  finding_label: string;
  title: string;
  priority: string | null;
  confidence: string | null;
  confidence_reasons: unknown[];
  lifecycle: EstateLifecycle;
  lens_flags: ("COST" | "RISK" | "OPPORTUNITY")[];
  consequence: EstateConsequence;
  source_provenance: EstateSourceBlock;
  episode_start: string;
  /** The row's Site basis state (Run 12 ruling 1): page one's basis mode, never the page-two response label. */
  status: EstateSiteState;
  links: { finding: string; site: string };
}

export interface EstateFindingsBody extends EstateEnvelope {
  lens: EstateLens;
  state_filter: EstateStateFilter;
  summary: {
    high_priority: number | null;
    low_confidence: number | null;
    awaiting_verification: number | null;
    basis_count: number | null;
    supported_findings: number | null;
    as_of?: string;
  };
  order: string;
  rows: EstateFindingRow[];
}

export interface EstateActionRow {
  action_id: string;
  action_code: string;
  site_id: string;
  site_code: string;
  site_name: string;
  created_at: string;
  selected_event_id: string;
  source_finding_id: string;
  source_finding_revision_id: string;
  action_title: string;
  success_criterion: string | null;
  owner: string | null;
  due_at: string | null;
  application_state: "NONE_AT_CUTOFF" | "PENDING" | "APPLIED";
  resolution_state: "RESOLVED" | "RESOLUTION_WITHDRAWN" | null;
  verification_outcome: string | null;
  source_provenance: EstateSourceBlock;
  links: { action: string; source: string | null };
}

export interface EstateActionsBody extends EstateEnvelope {
  summary: {
    open_actions: number | null;
    due_overdue: number | null;
    verification_window: number | null;
    verified_in_30_days: number | null;
    basis_count: number | null;
    as_of?: string;
  };
  order: string;
  rows: EstateActionRow[];
}

export interface EstateScopeBody {
  schema_version: string;
  sites: { site_id: string; site_code: string; site_name: string; coverage_state: EstateSiteState }[];
  authorized_site_count: number;
  covered_site_count: number;
  access_basis: string;
  known_at: string;
}

/**
 * W3-03 run 2 (Lane A; `.agent/W3-03-build-spec.md` r0a L3, r1a reading 6, r1b2 R5-R12): the Portfolio root.
 * Its status and F/E/M coverage are typed here without widening `EstateSiteState` or `EstateEnvelope` for the
 * existing roots. Display slots the API leaves null are built by the page with the W3-02 money words.
 */
export const PORTFOLIO_SCHEMA = "estate-portfolio-1";

export type EstatePortfolioStatus = "CURRENT" | "HISTORICAL" | "PENDING" | "UNKNOWN" | "EMPTY_SCOPE";
export type EstateRootCoverageState = "EMPTY" | "COMPLETE" | "PARTIAL" | "UNKNOWN";
export type EstateDomain = "MINIGRID" | "COLDCHAIN" | "EV_CHARGING";
export type EstateApplicationState = "NONE_AT_CUTOFF" | "PENDING" | "APPLIED";
export type EstateResolutionState = "RESOLVED" | "RESOLUTION_WITHDRAWN";
export type EstateWireDecimal = string | number | null;
export interface EstateWireAmount {
  low: EstateWireDecimal;
  high: EstateWireDecimal;
  currency: string | null;
}

export interface EstatePortfolioCoverage {
  state: EstateRootCoverageState;
  finding_state: EstateRootCoverageState;
  evidence_state: EstateRootCoverageState;
  money_state: EstateRootCoverageState;
  /** The exact seven-key W3-01 `site_coverage` item per authorized Site. */
  sites: EstateCoverageSite[];
}

export interface EstatePortfolioRow {
  site_id: string;
  site_code: string;
  site_name: string;
  domain: EstateDomain;
  finding_id: string;
  finding_revision_id: string;
  finding_label: string;
  title: string;
  mechanism: string | null;
  episode_start: string | null;
  episode_end: string | null;
  lifecycle: EstateLifecycle;
  lens_flags: ("COST" | "RISK" | "OPPORTUNITY")[];
  priority: string | null;
  confidence: string | null;
  confidence_reasons: unknown[];
  consequence: EstateConsequence;
  action_id: string | null;
  action_title: string | null;
  action_state: EstateApplicationState | null;
  application_state: EstateApplicationState | null;
  resolution_state: EstateResolutionState | null;
  verification_outcome: string | null;
  /** Server-built, one of the seven S7 literals; the page renders it verbatim. */
  workflow_label: string;
  next_move: string | null;
  source_provenance: EstateSourceBlock;
  links: { site: string | null; finding: string | null; action: string | null };
}

export type EstateValueCardKey = "OPERATING_COST" | "SERVICE_PRODUCT_RISK" | "PRODUCTIVE_USE" | "ASSET_LIFE" | "VERIFIED_RECOVERY";
export type EstateValueCardState =
  | "COMPARABLE_GROUP"
  | "SITE_OWNED"
  | "UNPRICED"
  | "WITHHELD"
  | "NO_LINE"
  | "COUNT"
  | "UNKNOWN"
  | "UNSUPPORTED"
  | "NOT_ESTABLISHED";

export interface EstateValueCard {
  key: EstateValueCardKey;
  state: EstateValueCardState;
  display_value: string | null;
  currency: string | null;
  line_keys: string[];
  group_key: string | null;
  basis: string | null;
  destination: string | null;
  detail: string | null;
  basis_text: string;
  tone: "amber" | "blue" | "neutral";
}

export type EstateObjectiveKey = "SERVICE_PRODUCT" | "BACKUP" | "ASSET_CONDITION" | "COST_CONTROL" | "EVIDENCE";
export type EstateObjectiveState = "FULL" | "LIMITED" | "NONE" | "REVIEW" | "UNASSESSED" | "UNKNOWN" | "NOT_APPLICABLE";

export interface EstateObjective {
  site_id: string;
  site_code: string;
  site_name: string;
  domain: EstateDomain;
  cells: { key: EstateObjectiveKey; state: EstateObjectiveState; label: string; reason: string; destination: string | null }[];
}

export interface EstateEvidencePrompt {
  state: "AVAILABLE" | "NO_GAP" | "COVERAGE_INCOMPLETE";
  text: string;
  site_id: string | null;
  site_code: string | null;
  gap_code: string | null;
  destination: string;
}

/** r1b2 R10: the ten required progress-row fields. */
export interface EstateProgressRow {
  action_id: string;
  action_code: string;
  selected_action_event_id: string | null;
  verification_plan_id: string | null;
  verification_outcome_id: string | null;
  application_state: EstateApplicationState | null;
  resolution_state: EstateResolutionState | null;
  verification_outcome: string | null;
  recorded_at: string | null;
  /** False when this exact origin Finding revision is not among the selected Finding revisions. */
  origin_revision_selected: boolean;
}

/** One unpaged W3-02 Financials line DTO (the fields the Portfolio page reads). */
export interface EstatePortfolioMoneyLine {
  line_key: string;
  site_id: string;
  site_code: string;
  site_name: string;
  category: string;
  window_start: string | null;
  window_end: string | null;
  quantity: { low: EstateWireDecimal; high: EstateWireDecimal; unit: string | null };
  amount: EstateWireAmount | null;
  eligibility: string;
  group_key: string | null;
  [key: string]: unknown;
}

export interface EstatePortfolioMoneyGroup {
  group_key: string | null;
  category: string;
  currency: string | null;
  window_start: string | null;
  window_end: string | null;
  state: string;
  line_keys: string[];
  amount: EstateWireAmount | null;
  reason_codes: string[];
  [key: string]: unknown;
}

export interface EstatePortfolioExclusion {
  line_key: string;
  group_key: string | null;
  reason_codes: string[];
}

export interface EstatePortfolioBody extends Omit<EstateEnvelope, "status" | "coverage"> {
  status: EstatePortfolioStatus;
  coverage: EstatePortfolioCoverage;
  lens: EstateLens;
  summary: {
    finding_count: number | null;
    priority_site_count: number | null;
    opportunity_count: number | null;
    evidence_gap_site_count: number | null;
    accepted_action_count: number | null;
    verified_resolution_count: number | null;
    combined_value: null;
    combined_value_state: "NOT_COMPARABLE";
  };
  value_cards: EstateValueCard[];
  objectives: EstateObjective[];
  evidence_prompt: EstateEvidencePrompt;
  opportunity: { state: "UNSUPPORTED"; finding_id: null; scenario_amount: null; headroom: null; destination: null };
  progress: {
    state: "NO_COMPARABLE_BASELINE";
    completed_activity_count: null;
    pending_trial_count: number | null;
    verified_resolution_count: number | null;
    recovered_value: null;
    rows: EstateProgressRow[];
  };
  footer: {
    line_key: string;
    site_name: string;
    quantity_display: string | null;
    amount_display: string | null;
    source_provenance: EstateSourceBlock;
    window_start: string | null;
    window_end: string | null;
    destination: string;
  } | null;
  selected_lines: EstatePortfolioMoneyLine[];
  money: {
    groups: EstatePortfolioMoneyGroup[];
    exclusions: EstatePortfolioExclusion[];
    diagnostics: { category: string; code: string; line_keys: string[] }[];
    estate_total: null;
  };
  scope_disclosure: {
    sites: {
      site_id: string;
      site_code: string;
      site_name: string;
      domain: EstateDomain;
      window: { from: string; to: string };
      coverage: EstateCoverageSite;
      selected_revision_ids: string[];
      source_provenance: EstateSourceBlock | null;
    }[];
    exclusions: EstatePortfolioExclusion[];
  };
  order: string;
  rows: EstatePortfolioRow[];
}

/** The Portfolio query: a lens and no state filter; the opaque cursor is passed back unchanged. */
export interface EstatePortfolioQuery extends EstateQuery {
  lens: EstateLens;
}

/** The refusal table (spec "Refusal table and cursor"): one exact UI sentence per code. */
export const REFUSAL_COPY: Readonly<Record<string, string>> = {
  UNAUTHENTICATED: "Sign in to see estate records.",
  ESTATE_BASIS_CHANGED: "The list changed. Reload the first page.",
  ESTATE_SELECTION_INCONSISTENT: "Some records are being updated. Reload the list.",
  INVALID_WINDOW: "The selected window is invalid.",
  INVALID_KNOWN_AT: "Choose a valid evidence cutoff.",
  INVALID_LENS: "Choose a supported Findings lens.",
  INVALID_LIMIT: "Choose a page size from 1 to 100.",
  INVALID_CURSOR: "Reload the first page.",
  ESTATE_STORE_UNAVAILABLE: "Estate records are unavailable right now. Try again.",
};

/**
 * Post-W6 W3-estate Q14 / cross-card item 5: the one estate window refusal set. The backend sends one
 * `INVALID_WINDOW` code for malformed, reversed and over-31-day windows, so the page query classifies it.
 */
export const WINDOW_REVERSED_COPY = "The selected window needs both a start and an end, with the start before the end.";
export const WINDOW_TOO_LONG_COPY = "The selected window is longer than 31 days.";
export const WINDOW_INVALID_COPY = "The selected window is invalid.";
export const WINDOW_REFUSAL_TITLE = "Window cannot be read";
export const WINDOW_NOT_VALID = "Window not valid";
const MAX_WINDOW_MS = 31 * 24 * 60 * 60 * 1000;

/** The cross-card sentence for an estate `INVALID_WINDOW` refusal of the window `{from, to}`. */
export function invalidWindowCopy(window: { from?: string | null; to?: string | null }): string {
  const from = window.from ? Date.parse(window.from) : Number.NaN;
  const to = window.to ? Date.parse(window.to) : Number.NaN;
  const fromMissing = !window.from;
  const toMissing = !window.to;
  if (fromMissing !== toMissing) return WINDOW_REVERSED_COPY;
  if (Number.isNaN(from) || Number.isNaN(to)) return WINDOW_INVALID_COPY;
  if (from >= to) return WINDOW_REVERSED_COPY;
  if (to - from > MAX_WINDOW_MS) return WINDOW_TOO_LONG_COPY;
  return WINDOW_INVALID_COPY;
}

/** Codes whose UI copy asks the reader to start again at page one (the page offers that link). */
export const FIRST_PAGE_CODES: ReadonlySet<string> = new Set(["ESTATE_BASIS_CHANGED", "INVALID_CURSOR"]);

export type EstateResult<T> =
  | { status: "loaded"; value: T }
  | { status: "refused"; httpStatus: number; code: string; copy: string };

export interface EstateQuery {
  from: string;
  to: string;
  /** Omitted means the read's own DB time (live). */
  known_at: string | null;
  limit?: number | null;
  cursor: string | null;
}

export interface EstateFindingsQuery extends EstateQuery {
  lens: EstateLens;
  state: EstateStateFilter;
}

export interface EstateClient {
  findings(query: EstateFindingsQuery): Promise<EstateResult<EstateFindingsBody>>;
  actions(query: EstateQuery): Promise<EstateResult<EstateActionsBody>>;
  scope(query: Pick<EstateQuery, "from" | "to" | "known_at">): Promise<EstateResult<EstateScopeBody>>;
  /** W3-03: `/api/estate/portfolio`; never sends `state`, passes the opaque cursor unchanged. */
  portfolio(query: EstatePortfolioQuery): Promise<EstateResult<EstatePortfolioBody>>;
}

function unavailable<T>(): EstateResult<T> {
  return {
    status: "refused",
    httpStatus: 503,
    code: "ESTATE_STORE_UNAVAILABLE",
    copy: REFUSAL_COPY.ESTATE_STORE_UNAVAILABLE,
  };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Query string for an estate read; null/absent parameters are left out. */
export function estateQueryString(query: Partial<EstateFindingsQuery>): string {
  const params = new URLSearchParams();
  for (const key of ["from", "to", "known_at", "lens", "state", "limit", "cursor"] as const) {
    const value = query[key];
    if (value === null || value === undefined) continue;
    if ((key === "lens" || key === "state") && value === "all") continue;
    params.set(key, String(value));
  }
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

async function readEstate<T>(
  path: string,
  schema: string,
  window?: { from?: string | null; to?: string | null },
): Promise<EstateResult<T>> {
  let response: Response;
  try {
    response = await fetch(path, { headers: { Accept: "application/json" } });
  } catch {
    return unavailable();
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    return unavailable();
  }
  if (response.ok) {
    if (isObject(body) && body.schema_version === schema) return { status: "loaded", value: body as T };
    return unavailable();
  }
  const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
  const code = detail !== null && typeof detail.code === "string" ? detail.code : "";
  const copy = code === "INVALID_WINDOW" && window !== undefined ? invalidWindowCopy(window) : REFUSAL_COPY[code];
  if (copy === undefined) return unavailable();
  return { status: "refused", httpStatus: response.status, code, copy };
}

export function createEstateClient(basePath: string = ESTATE_API_PATH): EstateClient {
  return {
    findings: (query) => readEstate(`${basePath}/findings${estateQueryString(query)}`, FINDINGS_SCHEMA, query),
    actions: (query) =>
      readEstate(`${basePath}/actions${estateQueryString({ ...query, lens: undefined, state: undefined })}`, ACTIONS_SCHEMA, query),
    scope: (query) =>
      readEstate(
        `${basePath}/scope${estateQueryString({ from: query.from, to: query.to, known_at: query.known_at })}`,
        SCOPE_SCHEMA,
        query,
      ),
    portfolio: (query) =>
      readEstate(
        `${basePath}/portfolio${estateQueryString({
          from: query.from,
          to: query.to,
          known_at: query.known_at,
          lens: query.lens,
          limit: query.limit,
          cursor: query.cursor,
        })}`,
        PORTFOLIO_SCHEMA,
        query,
      ),
  };
}
