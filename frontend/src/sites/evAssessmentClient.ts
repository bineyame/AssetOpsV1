/**
 * Read-only client for an EV_CHARGING Site's selected session assessment (W2-06 commit 4 routes,
 * `.agent/W2-06-build-spec.md` "Commit 4", "Run 5 rulings (r5)" and "Run 7 rulings (r6)"):
 *
 *   GET /api/sites/{code}/ev/sessions             (from, to, known_at, cursor, limit)
 *   GET /api/sites/{code}/ev/sessions/{id}        (from, to, known_at)
 *   GET /api/sites/{code}/ev/findings             (from, to, known_at, cursor, limit)
 *   GET /api/sites/{code}/ev/findings/{id}        (from, to, known_at)
 *
 * The window is the cold route's strict-UTC `from`/`to` (both or neither) plus `known_at`. A window without an
 * exact selected assessment is a valid 200 `UNKNOWN` read with null counts and empty arrays; refusals are
 * `{error:{code,message}}`. `source_provenance.classification` is read, never the persisted result's `class`.
 */

import { coldWindowSearch, type ColdRead, type ColdWindowQuery } from "./coldAssessmentClient";
import { isObject } from "./evidenceRead";
import { SITES_API_PATH } from "./siteDirectoryClient";
import type { OutcomeCategories } from "./outcomeCategories";

export type EvRead<T> = ColdRead<T>;
export type EvWindowQuery = ColdWindowQuery;

export interface EvEnvelope {
  site_id: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  currentness: { state: string; as_of: string | null; limitation: string | null };
  /** W3-01 (Run 3 q3): the pending-or-selected alias; on a detail read, the represented row's own block. */
  source_provenance: EvSourceBlock;
  selected_source_provenance?: EvSourceBlock | null;
  pending_source_provenance?: EvSourceBlock | null;
  limitations: string[];
}

/** W3-01: the public source DTO (six keys plus optional `detail`). */
export type EvSourceBlock = { classification: string | null; state?: string; source_ids: string[]; evidence_ids: string[]; basis_sha256: string | null; reasons?: { code: string; accepted_evidence_ids: string[] }[]; detail?: Record<string, unknown> };

export interface EvStatus {
  state: string;
  claim_level: string | null;
  as_of: string | null;
  limitation: string | null;
}

export interface EvDenominator {
  started: number | null;
  completed: number | null;
  observed_abort: number | null;
  incomplete: number | null;
  contradictory: number | null;
  orphan: number | null;
  confirmed_delivery: number | null;
  fault_aborted: number | null;
  as_of: string | null;
  limitation: string | null;
}

export interface EvLinks {
  self: string | null;
  evidence: string | null;
  analysis: string | null;
  finding: string | null;
  financials: string | null;
}

export interface EvSessionItem {
  session_id: string;
  external_session_id: string;
  charger_asset_id: string;
  connector_asset_id: string;
  connector_display_name: string | null;
  revision_id: string;
  revision_no: number;
  basis_sha256: string;
  state: string;
  start_at: string | null;
  end_at: string | null;
  start_bounds: { earliest: string | null; latest: string | null };
  end_bounds: { earliest: string | null; latest: string | null };
  supported_kwh: string | null;
  energy_complete: boolean | null;
  unknown_meter_seconds: number | null;
  reason_codes: string[];
  fault_evidence_id: string | null;
  finding_id: string | null;
  completeness: { start: boolean; terminal: boolean; meter: boolean; clock: boolean };
  as_of: string | null;
  source_provenance: EvEnvelope["source_provenance"];
  links: EvLinks;
}

/** r9 M1-c: one accepted record excluded by its exact source/binding (full-window, independent of paging). */
export interface EvExcludedRecord {
  evidence_id: string;
  record_kind: string | null;
  reason: string;
}

export interface EvSessionsRead extends EvEnvelope {
  status: EvStatus;
  denominator: EvDenominator;
  excluded_records: EvExcludedRecord[];
  items: EvSessionItem[];
  next_cursor: string | null;
}

export interface EvSessionDetailRead extends EvEnvelope, EvSessionItem {
  status: EvStatus;
  denominator: EvDenominator;
  evidence: { evidence_id: string; content_sha256: string; use: string; reason: string | null; source_time: string | null; received_at: string | null }[];
  meter_intervals: { evidence_id: string; start_at: string; end_at: string; kwh: string; error_bound_kwh: string | null; use: string; reason: string | null }[];
  history: { revision_id: string; revision_no: number; basis_sha256: string; state: string; created_at: string }[];
}

export interface EvFindingItem {
  finding_id: string;
  /** OUT-A: the outcome categories (policy `outcome-map/1`); absent on an older body. */
  categories?: OutcomeCategories;
  revision_id: string;
  revision_no: number;
  basis_sha256: string;
  session_id: string | null;
  title: string;
  claim_level: string;
  lifecycle: string;
  as_of: string | null;
  links: EvLinks;
}

export interface EvFindingsRead extends EvEnvelope {
  items: EvFindingItem[];
  next_cursor: string | null;
}

export interface EvFindingClaim {
  session_id: string | null;
  external_session_id: string | null;
  connector_asset_id: string | null;
  start_at: string | null;
  abort_at: string | null;
  fault_evidence_id: string | null;
  /** r9 M3: read-time only; the selected session revision's exact SUPPORT START / ABORT cited by this Finding. */
  start_evidence_id: string | null;
  abort_evidence_id: string | null;
  supported_kwh: string | null;
  energy_complete: boolean | null;
}

export interface EvFindingDetailRead extends EvEnvelope, EvFindingItem {
  claim: EvFindingClaim;
  evidence: { evidence_id: string; content_sha256: string; source_time: string | null; received_at: string | null }[];
  history: { revision_id: string; revision_no: number; transition: string; lifecycle: string; created_at: string }[];
}

export interface EvAssessmentClient {
  listSessions(siteId: string, window: EvWindowQuery): Promise<EvRead<EvSessionsRead>>;
  getSession(siteId: string, sessionId: string, window: EvWindowQuery): Promise<EvRead<EvSessionDetailRead>>;
  listFindings(siteId: string, window: EvWindowQuery): Promise<EvRead<EvFindingsRead>>;
  getFinding(siteId: string, findingId: string, window: EvWindowQuery): Promise<EvRead<EvFindingDetailRead>>;
}

function isEnvelope(value: unknown): value is EvEnvelope {
  return (
    isObject(value) &&
    isObject(value.window) &&
    isObject(value.currentness) &&
    isObject(value.source_provenance) &&
    Array.isArray(value.limitations)
  );
}

const SHAPES = {
  sessions: (v: unknown) =>
    isEnvelope(v) && isObject((v as EvSessionsRead).status) && isObject((v as EvSessionsRead).denominator) &&
    Array.isArray((v as EvSessionsRead).excluded_records) &&
    Array.isArray((v as EvSessionsRead).items),
  session: (v: unknown) =>
    isEnvelope(v) && typeof (v as EvSessionDetailRead).session_id === "string" && Array.isArray((v as EvSessionDetailRead).history),
  findings: (v: unknown) => isEnvelope(v) && Array.isArray((v as EvFindingsRead).items),
  finding: (v: unknown) =>
    isEnvelope(v) && typeof (v as EvFindingDetailRead).finding_id === "string" && isObject((v as EvFindingDetailRead).claim),
};

async function read<T>(url: string, shape: (value: unknown) => boolean): Promise<EvRead<T>> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok) {
    return shape(body)
      ? { status: "loaded", value: body as T }
      : { status: "unavailable", message: "The EV assessment read answered in an unexpected shape." };
  }
  const error = isObject(body) && isObject(body.error) ? body.error : null;
  if (error !== null && typeof error.code === "string") {
    return {
      status: "refused",
      httpStatus: response.status,
      code: error.code,
      message: typeof error.message === "string" ? error.message : null,
    };
  }
  return { status: "unavailable", message: null };
}

export function createEvAssessmentClient(basePath: string = SITES_API_PATH): EvAssessmentClient {
  const base = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/ev`;
  return {
    listSessions: (siteId, window) => read(`${base(siteId)}/sessions${coldWindowSearch(window)}`, SHAPES.sessions),
    getSession: (siteId, sessionId, window) =>
      read(`${base(siteId)}/sessions/${encodeURIComponent(sessionId)}${coldWindowSearch(window)}`, SHAPES.session),
    listFindings: (siteId, window) => read(`${base(siteId)}/findings${coldWindowSearch(window)}`, SHAPES.findings),
    getFinding: (siteId, findingId, window) =>
      read(`${base(siteId)}/findings/${encodeURIComponent(findingId)}${coldWindowSearch(window)}`, SHAPES.finding),
  };
}
