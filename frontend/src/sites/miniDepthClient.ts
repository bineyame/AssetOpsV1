/**
 * W4-02: the mini-grid depth reads (`GET /api/sites/{site_code}/performance/mini/...`, build spec S6/S9/Q33 and the
 * q9 rulings). The route token is the public Site code (`site_id` in Site detail). Every MINIGRID read sends an
 * explicit `from`/`to` (site-local boundaries as UTC instants, computed here with the Site time zone, never the
 * browser's); `known_at` is optional.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";

/** The served mini tabs, in the backend's order (S6). */
export const MINI_DOMAINS = ["service", "fuel", "renewable", "backup"] as const;
export type MiniDomain = (typeof MINI_DOMAINS)[number];

export function isMiniDomain(value: string | undefined): value is MiniDomain {
  return value !== undefined && (MINI_DOMAINS as readonly string[]).includes(value);
}

export interface MiniWindowQuery {
  from: string | null;
  to: string | null;
  known_at: string | null;
}

export interface MiniBound {
  low: number | null;
  high: number | null;
}

export interface MiniCoverage {
  required_seconds: number;
  observed_seconds: number;
  source_count: number;
  gaps: { from: string | null; to: string | null }[];
}

export interface MiniLimitation {
  code: string;
  evidence_ids: string[];
}

export interface MiniSourceBlock {
  classification: string | null;
  state?: string;
  source_ids?: string[];
  evidence_ids?: string[];
}

/** One requested hour's selection state (`currentness.windows[]`, q9-6). */
export interface MiniHourState {
  local_day: string;
  window_start: string;
  window_end: string;
  selection_id: number | null;
  assessment_revision_id: string | null;
  input_sha256: string | null;
  committed_watermark: string | null;
  state: string;
  job_state: string;
}

export interface MiniLinks {
  dispatch: string | null;
  evidence: string | null;
  financials: string | null;
  actions: string | null;
}

export interface MiniEnvelope<Cards, Row> {
  schema_version: string;
  domain: string;
  site: { id?: string; code: string; timezone: string | null };
  window: { from: string | null; to: string | null; known_at: string | null; bounds: string };
  currentness: { state: string; job_state: string; windows: MiniHourState[] };
  source_provenance: MiniSourceBlock | null;
  selected_source_provenance?: MiniSourceBlock | null;
  pending_source_provenance?: MiniSourceBlock | null;
  status: "SUPPORTED" | "LIMITED" | "UNKNOWN" | string;
  coverage: MiniCoverage | null;
  cards: Cards | null;
  rows: Row[];
  limitations: MiniLimitation[];
  basis: Record<string, unknown> | null;
  links: MiniLinks;
}

export interface RenewableCards {
  capability_kw: MiniBound | null;
  used_kw: MiniBound | null;
  headroom_kw: MiniBound | null;
  eligible_days: number | null;
  assessed_days: number | null;
}

export interface RenewableRow {
  day: string;
  from: string;
  to: string;
  opportunity_kwh: MiniBound | null;
  constraints: string[];
  decision: "ELIGIBLE" | "EXCLUDED" | "LIMITED" | "CONFLICT" | string;
  coverage: MiniCoverage | null;
  evidence_ids: string[];
}

export type RenewableRead = MiniEnvelope<RenewableCards, RenewableRow>;

export interface ServiceCards {
  delivered_load_kw: number | null;
  interruptions_seen: number | null;
  critical_delivered_kw: number | null;
  unserved_kwh: number | null;
}

/** One addressed load of the selected service hour (`mini_depth/projection.py:_service`). */
export interface ServiceRow {
  asset_id: string;
  asset_code: string;
  load_label: string;
  role: "CRITICAL" | "UNCLASSIFIED" | string;
  delivered_kw: number | null;
  requested_evidence_state: "ACCEPTED" | "MISSING" | "CONFLICT" | string;
  assessment: "SUPPORTED" | "LIMITED" | "UNKNOWN" | string;
  coverage: MiniCoverage | null;
  evidence_ids: string[];
}

export type ServiceRead = MiniEnvelope<ServiceCards, ServiceRow> & {
  /** Final review ruling 2 (M2): the pinned critical-delivered series' own coverage; null when not known. */
  critical_delivered_coverage?: MiniCoverage | null;
};

export interface FuelCards {
  opening_l: MiniBound | null;
  deliveries_l: MiniBound | null;
  expected_use_l: MiniBound | null;
  closing_l: MiniBound | null;
  residual_l: MiniBound | null;
}

/** The fixed fuel terms, in their stored order (`mini_depth/rules.py:FUEL_TERMS`). */
export const FUEL_TERMS = ["OPENING", "DELIVERIES", "USE", "CLOSING", "RESIDUAL"] as const;

/** One fixed balance term of the selected fuel hour (`mini_depth/projection.py:_fuel`). */
export interface FuelRow {
  term: (typeof FUEL_TERMS)[number] | string;
  basis: string;
  treatment: string;
  value: MiniBound | null;
  coverage: MiniCoverage | null;
  evidence_ids: string[];
}

export type FuelRead = MiniEnvelope<FuelCards, FuelRow>;

/** A judged recovery time against the pinned target (`mini_depth/projection.py:_backup.recovery`). */
export interface BackupRecovery {
  seconds: number | null;
  target_seconds: number | null;
}

export interface BackupCards {
  /** Always null in W4-02: instant supply reports cover zero seconds, so no count is proved (q3-8). */
  outage_count: number | null;
  start_success_count: number | null;
  last_witnessed_test_at: string | null;
  critical_recovery: BackupRecovery | null;
}

/** The ordered chain steps (`mini_depth/rules.py:BACKUP_STEPS`). */
export const BACKUP_STEPS = ["LOSS", "REQUEST", "START", "POWER", "LOAD", "SERVICE"] as const;

export interface BackupStep {
  code: (typeof BACKUP_STEPS)[number] | string;
  state: "OBSERVED" | "MISSING" | "CONFLICT" | string;
  at: string | null;
  evidence_ids: string[];
}

/** One correlated outage chain of the selected backup hour (`mini_depth/projection.py:_backup`). */
export interface BackupRow {
  chain_id: string;
  outage_start: string;
  steps: BackupStep[];
  service_outcome: "RECOVERED" | "MISSED_TARGET" | "UNKNOWN" | string;
  result: "PASS" | "FAIL" | "INCOMPLETE" | string;
  critical_recovery: BackupRecovery | null;
  coverage: MiniCoverage | null;
  evidence_ids: string[];
}

export type BackupRead = MiniEnvelope<BackupCards, BackupRow>;

export type MiniRead<T> =
  | { status: "loaded"; value: T }
  /** The server answered with a refusal envelope `{detail:{code,message}}`. */
  | { status: "refused"; httpStatus: number; code: string; message: string | null }
  /** No answer, or an answer that is not the documented shape. */
  | { status: "unavailable"; message: string | null };

export interface MiniCapability {
  id: string;
  display_name: string;
}

export interface MiniDepthClient {
  getCapabilities(siteCode: string): Promise<MiniRead<MiniCapability[]>>;
  getRenewable(siteCode: string, window: MiniWindowQuery): Promise<MiniRead<RenewableRead>>;
  getService(siteCode: string, window: MiniWindowQuery): Promise<MiniRead<ServiceRead>>;
  getFuel(siteCode: string, window: MiniWindowQuery): Promise<MiniRead<FuelRead>>;
  getBackup(siteCode: string, window: MiniWindowQuery): Promise<MiniRead<BackupRead>>;
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

export function miniWindowSearch(window: MiniWindowQuery): string {
  const params = new URLSearchParams();
  if (window.from !== null) params.set("from", window.from);
  if (window.to !== null) params.set("to", window.to);
  if (window.known_at !== null) params.set("known_at", window.known_at);
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

async function read<T>(url: string, shape: (value: unknown) => boolean): Promise<MiniRead<T>> {
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
      : { status: "unavailable", message: "The mini-grid read answered in an unexpected shape." };
  }
  const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
  if (detail !== null && typeof detail.code === "string") {
    return {
      status: "refused",
      httpStatus: response.status,
      code: detail.code,
      message: typeof detail.message === "string" ? detail.message : null,
    };
  }
  return { status: "unavailable", message: null };
}

const isEnvelope = (value: unknown): boolean =>
  isObject(value) && Array.isArray(value.rows) && isObject(value.currentness) && isObject(value.links);

export function createMiniDepthClient(basePath: string = SITES_API_PATH): MiniDepthClient {
  const base = (code: string) => `${basePath}/${encodeURIComponent(code)}/performance/mini`;
  return {
    getCapabilities: (code) =>
      read(`${base(code)}/capabilities`, (v) => Array.isArray(v) && v.every((i) => isObject(i) && typeof i.id === "string")),
    getRenewable: (code, window) => read(`${base(code)}/renewable${miniWindowSearch(window)}`, isEnvelope),
    getService: (code, window) => read(`${base(code)}/service${miniWindowSearch(window)}`, isEnvelope),
    getFuel: (code, window) => read(`${base(code)}/fuel${miniWindowSearch(window)}`, isEnvelope),
    getBackup: (code, window) => read(`${base(code)}/backup${miniWindowSearch(window)}`, isEnvelope),
  };
}

/* ---------- Site-local time (the Site's IANA zone; never the browser's) ---------- */

const DAY_MS = 86_400_000;

function zoneParts(timeZone: string, utcMs: number): Record<string, number> {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(new Date(utcMs));
  const out: Record<string, number> = {};
  for (const part of parts) if (part.type !== "literal") out[part.type] = Number(part.value);
  return out;
}

function offsetMs(timeZone: string, utcMs: number): number {
  const p = zoneParts(timeZone, utcMs);
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return asUtc - Math.floor(utcMs / 1000) * 1000;
}

/** The UTC instant of a site-local calendar date's midnight. */
export function localMidnightUtc(timeZone: string, isoDate: string): number {
  return localWallUtc(timeZone, isoDate, 0);
}

/** The UTC instant of a site-local wall-clock hour (`hour` 0-23) on a calendar date. */
export function localWallUtc(timeZone: string, isoDate: string, hour: number): number {
  const guess = Date.parse(`${isoDate}T${String(hour).padStart(2, "0")}:00:00Z`);
  const first = guess - offsetMs(timeZone, guess);
  return guess - offsetMs(timeZone, first);
}

/** The site-local calendar date (`YYYY-MM-DD`) of a UTC instant. */
export function localDateOf(timeZone: string, utcMs: number): string {
  const p = zoneParts(timeZone, utcMs);
  return `${p.year}-${String(p.month).padStart(2, "0")}-${String(p.day).padStart(2, "0")}`;
}

/** The site-local clock time (`HH:MM`) of a UTC instant. */
export function localTimeOf(timeZone: string, utcMs: number): string {
  const p = zoneParts(timeZone, utcMs);
  return `${String(p.hour).padStart(2, "0")}:${String(p.minute).padStart(2, "0")}`;
}

export function addDays(isoDate: string, days: number): string {
  return new Date(Date.parse(`${isoDate}T00:00:00Z`) + days * DAY_MS).toISOString().slice(0, 10);
}

/** `[local midnight of first, local midnight of first + days)` as UTC tokens. */
export function localDaysWindow(timeZone: string, first: string, days: number): { from: string; to: string } {
  return {
    from: new Date(localMidnightUtc(timeZone, first)).toISOString(),
    to: new Date(localMidnightUtc(timeZone, addDays(first, days))).toISOString(),
  };
}

/**
 * The renewable page's window (Q5, q9-1): the address's `from`/`to`/`known_at` when both bounds are present;
 * otherwise one site-local day, the local date of the shell's UTC day start (`?date=`, else today's UTC day).
 */
export function renewableWindowFromParams(params: URLSearchParams, timeZone: string, now: Date = new Date()): MiniWindowQuery {
  const from = params.get("from");
  const to = params.get("to");
  const known_at = params.get("known_at");
  if (from !== null && to !== null) return { from, to, known_at };
  const date = params.get("date");
  const utcDay = date !== null && /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : now.toISOString().slice(0, 10);
  const first = localDateOf(timeZone, Date.parse(`${utcDay}T00:00:00Z`));
  return { ...localDaysWindow(timeZone, first, 1), known_at };
}

/** `[local hour, local hour + 1 h)` of a site-local date as UTC tokens (one Site-local clock hour, Q4/Q5). */
export function localHourWindow(timeZone: string, day: string, hour: number): { from: string; to: string } {
  const start = localWallUtc(timeZone, day, hour);
  return { from: new Date(start).toISOString(), to: new Date(start + 3_600_000).toISOString() };
}

/** The service page's local hour when the address names none: 12:00-13:00 local (handoff Run 15, Q5). */
export const DEFAULT_SERVICE_HOUR = 12;

/**
 * The service page's window (Q5): the address's `from`/`to`/`known_at` when both bounds are present; otherwise the
 * local 12:00-13:00 hour of the local date of the shell's UTC day start (`?date=`, else today's UTC day).
 */
export function serviceWindowFromParams(params: URLSearchParams, timeZone: string, now: Date = new Date()): MiniWindowQuery {
  const from = params.get("from");
  const to = params.get("to");
  const known_at = params.get("known_at");
  if (from !== null && to !== null) return { from, to, known_at };
  const date = params.get("date");
  const utcDay = date !== null && /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : now.toISOString().slice(0, 10);
  const day = localDateOf(timeZone, Date.parse(`${utcDay}T00:00:00Z`));
  return { ...localHourWindow(timeZone, day, DEFAULT_SERVICE_HOUR), known_at };
}

const RENEWABLE_DOWNGRADED_CURRENTNESS = new Set(["PENDING_RECOMPUTE", "STALE_SOURCE", "UNKNOWN"]);
const RENEWABLE_DOWNGRADED_PROVENANCE = new Set(["UNKNOWN", "MIXED"]);

/**
 * q11-1: a currentness or source downgrade - currentness PENDING_RECOMPUTE/STALE_SOURCE/UNKNOWN, selected provenance
 * absent/UNKNOWN/MIXED, or a pending provenance UNKNOWN/MIXED - is evaluated before `Watch`.
 */
export function renewableDowngraded(read: Pick<RenewableRead, "currentness" | "selected_source_provenance" | "pending_source_provenance">): boolean {
  const selected = read.selected_source_provenance?.classification ?? null;
  const pending = read.pending_source_provenance?.classification ?? null;
  return (
    RENEWABLE_DOWNGRADED_CURRENTNESS.has(read.currentness.state) ||
    selected === null ||
    RENEWABLE_DOWNGRADED_PROVENANCE.has(selected) ||
    (pending !== null && RENEWABLE_DOWNGRADED_PROVENANCE.has(pending))
  );
}
