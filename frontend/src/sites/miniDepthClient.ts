/**
 * W4-02: the mini-grid depth reads (`GET /api/sites/{site_code}/performance/mini/...`, build spec S6/S9/Q33 and the
 * q9 rulings). The route token is the public Site code (`site_id` in Site detail). Every MINIGRID read sends an
 * explicit `from`/`to` (site-local boundaries as UTC instants, computed here with the Site time zone, never the
 * browser's); `known_at` is optional.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { addressRange, focusDayOf, pageDay, rangeDays, rangeWindow, readSharedRange } from "../ui/sharedRange";

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
  /** D-SR.62: the count of missing (never assessed) hour windows; renewable only, so optional on the other domains. */
  missing_hours?: number;
}

export interface RenewableCards {
  capability_kw: MiniBound | null;
  used_kw: MiniBound | null;
  headroom_kw: MiniBound | null;
  /** D-SR.48: min low and min high over the ELIGIBLE hours (headroom available in every eligible hour); null with the card. */
  all_hours_headroom_kw?: MiniBound | null;
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

/* ---------- range reads (SR-8 `site-renewable-range-1`, SR-10b `site-fuel-range-1`) ---------- */

export interface MiniRangeSite {
  site_code: string;
  site_name: string | null;
  timezone: string | null;
}

export interface MiniRangeWindow {
  from: string;
  to: string;
  known_at: string | null;
}

/** One Site-local day of the renewable range (`sites/renewable_range.py range_days`, D-SR.27/47). */
export interface RenewableRangeDay {
  local_day: string;
  grade: string;
  /** The stored day value, decimal text, unrounded; null when the state shows no band. */
  low_kw: string | number | null;
  high_kw: string | number | null;
  decision: string | null;
  window_hours: number | null;
  covered_hours: number | null;
  operating_hours: number | null;
  state: string;
  partial: boolean;
  link: string;
}

export interface RenewableRangeTotals {
  days_requested: number;
  days_counted: number;
  average_low_kw: string | null;
  average_high_kw: string | null;
  average_label: string;
  partial: boolean;
}

export interface RenewableRangeRead {
  schema_version: string;
  site: MiniRangeSite;
  window: MiniRangeWindow;
  days: RenewableRangeDay[];
  totals: RenewableRangeTotals;
}

/** A summed band; `low`/`high` are numbers (`mini_depth/day_summary.py _band_sum`). */
export interface MiniBand {
  low: number;
  high: number;
}

/** One Site-local day of the fuel range (`mini_depth/day_summary.py range_days`, D-SR.51/70). Absent or NO_DATA days null every count. */
export interface FuelRangeDay {
  local_day: string;
  stored: boolean;
  hours_expected: number | null;
  hours_assessed: number | null;
  hours_pending: number | null;
  hours_missing: number | null;
  status_counts: Record<string, number> | null;
  limitations: string[] | null;
  expected_use_l: MiniBand | null;
  hours_with_use: number | null;
  state: string;
  partial: boolean;
  hour_link: string;
}

export interface FuelRangeTotals {
  days_counted: number;
  days_requested: number;
  partial: boolean;
  expected_use_l: MiniBand | null;
}

export interface FuelRangeRead {
  schema_version: string;
  site: MiniRangeSite;
  window: MiniRangeWindow;
  days: FuelRangeDay[];
  totals: FuelRangeTotals;
}

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
  /** SR-8: `GET /api/sites/{code}/renewable-range`. Optional so older fakes compile; a client without it reads unavailable. */
  getRenewableRange?(siteCode: string, window: MiniWindowQuery): Promise<MiniRead<RenewableRangeRead>>;
  /** SR-10b: `GET /api/sites/{code}/fuel-range`. Optional as above. */
  getFuelRange?(siteCode: string, window: MiniWindowQuery): Promise<MiniRead<FuelRangeRead>>;
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

const isRangeBody = (value: unknown): boolean => isObject(value) && Array.isArray(value.days) && isObject(value.totals);

export function createMiniDepthClient(basePath: string = SITES_API_PATH): MiniDepthClient {
  const base = (code: string) => `${basePath}/${encodeURIComponent(code)}/performance/mini`;
  return {
    getCapabilities: (code) =>
      read(`${base(code)}/capabilities`, (v) => Array.isArray(v) && v.every((i) => isObject(i) && typeof i.id === "string")),
    getRenewable: (code, window) => read(`${base(code)}/renewable${miniWindowSearch(window)}`, isEnvelope),
    getService: (code, window) => read(`${base(code)}/service${miniWindowSearch(window)}`, isEnvelope),
    getFuel: (code, window) => read(`${base(code)}/fuel${miniWindowSearch(window)}`, isEnvelope),
    getBackup: (code, window) => read(`${base(code)}/backup${miniWindowSearch(window)}`, isEnvelope),
    getRenewableRange: (code, window) =>
      read(`${basePath}/${encodeURIComponent(code)}/renewable-range${miniWindowSearch(window)}`, isRangeBody),
    getFuelRange: (code, window) => read(`${basePath}/${encodeURIComponent(code)}/fuel-range${miniWindowSearch(window)}`, isRangeBody),
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
 * The renewable page's window (Q5, q9-1; D-SR.59). The server reads 1-5 exact Site-local days (`hour_windows`), so:
 * an address that already is exact local midnights 1-5 days apart goes as it is (story links, FocusPicker); a shared
 * range of at most 5 days names the Site-local days of the same dates (`window_days` rule: `range.from` is the date
 * string itself); a longer range with no day named keeps its last 5 Site-local days; a named day, or no range, reads
 * one Site-local day, the local date of the shell's UTC day start (`?day=`, else the legacy `?date=`, else today; SR.3).
 * `known_at` is carried unchanged.
 */
export function renewableWindowFromParams(params: URLSearchParams, timeZone: string, now: Date = new Date()): MiniWindowQuery {
  const from = params.get("from");
  const to = params.get("to");
  const known_at = params.get("known_at");
  const focus = focusDayOf(params);
  if (from !== null && to !== null && exactLocalDays(timeZone, from, to) !== null) return { from, to, known_at };
  // D-SR.59 L-4: the range is measured through `readSharedRange`, never the raw bounds.
  const range = addressRange(params, now.getTime());
  // A reversed or unparseable pair goes as it is, so the page names why it is refused (R313).
  if (from !== null && to !== null && range === null && !(Date.parse(to) > Date.parse(from))) return { from, to, known_at };
  if (range !== null && focus === null) {
    const n = rangeDays(range);
    if (n <= MINI_RENEWABLE_DAYS) return { ...localDaysWindow(timeZone, range.from, n), known_at };
    // A longer range with no day named: its last 5 Site-local days, ending on the local date of its last UTC day.
    const lastLocal = range.to;
    return { ...localDaysWindow(timeZone, addDays(lastLocal, -(MINI_RENEWABLE_DAYS - 1)), MINI_RENEWABLE_DAYS), known_at };
  }
  // A named day (a story link; the shell adds the 7 days ending on it), or no range: that day, one Site-local day.
  const utcDay = pageDay(params, now.getTime());
  const first = utcDay;
  return { ...localDaysWindow(timeZone, first, 1), known_at };
}

/** An instant bound (`...T..Z`); a day-form bound is measured as a range, never passed through. */
const INSTANT_TOKEN = /^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/;

/** D-SR.59: the day count when `from`/`to` are exact Site-local midnights 1-5 days apart (as `hour_windows` checks), else `null`. */
function exactLocalDays(timeZone: string, from: string, to: string): number | null {
  if (!INSTANT_TOKEN.test(from) || !INSTANT_TOKEN.test(to)) return null;
  const lo = Date.parse(from);
  const hi = Date.parse(to);
  if (!(lo < hi)) return null;
  const first = localDateOf(timeZone, lo);
  if (localMidnightUtc(timeZone, first) !== lo) return null;
  for (let n = 1; n <= MINI_RENEWABLE_DAYS; n++) {
    if (localMidnightUtc(timeZone, addDays(first, n)) === hi) return n;
  }
  return null;
}

/**
 * SR-8 page / SR-10c (rev 10 §10.4, rev 10b.2): the whole-range window a range view reads, or `null` when the page
 * shows its one-day (Renewable) or one-hour (Fuel) view instead: the address names a day (`?day=`, a story link), the
 * address is a story window the one-day/one-hour read takes as it is (Renewable: exactly one Site-local day; Fuel: one Site-local clock hour, the range rows' `hour_link`), or there is no valid shared range. Otherwise
 * the shared range's UTC-midnight window (the server reads its days by the `window_days` rule, D-SR.45), with the
 * address `known_at`.
 */
export function miniRangeWindowFromParams(
  screen: "renewable" | "fuel",
  params: URLSearchParams,
  timeZone: string,
  now: Date = new Date(),
): MiniWindowQuery | null {
  if (focusDayOf(params) !== null) return null;
  const from = params.get("from");
  const to = params.get("to");
  if (from !== null && to !== null) {
    // D-SR.76 Q1: exactly one Site-local day keeps the one-day page; any longer range opens the range view.
    if (screen === "renewable" && exactLocalDays(timeZone, from, to) === 1) return null;
    if (screen === "fuel" && exactLocalHour(timeZone, from, to)) return null;
  }
  const range = addressRange(params, now.getTime());
  if (range === null) return null;
  return { ...rangeWindow(range), known_at: params.get("known_at") };
}

/** One Site-local clock hour exactly (the one-hour read's pass-through, D-SR.59). */
function exactLocalHour(timeZone: string, from: string, to: string): boolean {
  if (!INSTANT_TOKEN.test(from) || !INSTANT_TOKEN.test(to)) return false;
  const lo = Date.parse(from);
  const hi = Date.parse(to);
  return hi - lo === 3_600_000 && lo % 60_000 === 0 && localTimeOf(timeZone, lo).endsWith(":00");
}

/** SR-4b: the server's renewable read limit in days (backend `MINI_RENEWABLE_DAYS`). */
export const MINI_RENEWABLE_DAYS = 5;

/** `[local hour, local hour + 1 h)` of a site-local date as UTC tokens (one Site-local clock hour, Q4/Q5). */
export function localHourWindow(timeZone: string, day: string, hour: number): { from: string; to: string } {
  const start = localWallUtc(timeZone, day, hour);
  return { from: new Date(start).toISOString(), to: new Date(start + 3_600_000).toISOString() };
}

/** D-SR.59: `from`/`to` are instants exactly one Site-local clock hour apart (a story link or the hour picker). */
export function isOneLocalHour(timeZone: string, from: string, to: string): boolean {
  const lo = Date.parse(from);
  const hi = Date.parse(to);
  return INSTANT_TOKEN.test(from) && INSTANT_TOKEN.test(to) && hi - lo === 3_600_000 && lo % 60_000 === 0 &&
    localTimeOf(timeZone, lo).endsWith(":00");
}

/**
 * SR-7a / SR-11 (rev 10 §10.3, rev 10b.3): the range a Service or Backup tab shows as a day table. A valid shared range
 * with no page day (`day=`) and not one Site-local clock hour is the range view; anything else (a story hour, a
 * `day=` link, a reversed or one-sided pair, no range) keeps the one-hour page and its window rule.
 */
export function miniRangeView(
  params: URLSearchParams,
  timeZone: string,
  now: Date = new Date(),
): { from: string; to: string; known_at: string | null } | null {
  if (focusDayOf(params) !== null) return null;
  const from = params.get("from");
  const to = params.get("to");
  if (from !== null && to !== null && isOneLocalHour(timeZone, from, to)) return null;
  const state = readSharedRange(params, now.getTime());
  return state.status === "set" ? { ...rangeWindow(state), known_at: state.known_at } : null;
}

/** D-SR.76: the address names a `from`/`to` that is not whole UTC days, so the day table says it shows whole days. */
export function isPartialDayAddress(params: URLSearchParams): boolean {
  const from = params.get("from");
  const to = params.get("to");
  if (from === null || to === null) return false;
  const day = 86_400_000;
  return Date.parse(from) % day !== 0 || Date.parse(to) % day !== 0;
}

/** The service page's local hour when the address names none: 12:00-13:00 local (handoff Run 15, Q5). */
export const DEFAULT_SERVICE_HOUR = 12;

/**
 * The service page's window (Q5; D-SR.59), also Backup and Fuel. The server reads exactly one Site-local clock hour
 * (`hour_windows`), so only such an address goes as it is (story links, FocusPicker); a reversed or unparseable pair
 * also goes as it is, so the page names why it is refused. Any shared range, one day ("Yesterday") included, gives the
 * 12:00-13:00 local hour of the local date of the page's UTC day (`?day=`, else the range's last day, else today; SR.3).
 * `known_at` is carried unchanged.
 */
export function serviceWindowFromParams(params: URLSearchParams, timeZone: string, now: Date = new Date()): MiniWindowQuery {
  const from = params.get("from");
  const to = params.get("to");
  const known_at = params.get("known_at");
  if (from !== null && to !== null) {
    if (isOneLocalHour(timeZone, from, to)) return { from, to, known_at };
    if (!(Date.parse(to) > Date.parse(from)) && addressRange(params, now.getTime()) === null) return { from, to, known_at };
  }
  // D-SR.59 L-4: the day comes from `readSharedRange` (`pageDay`), never the raw bounds.
  const utcDay = pageDay(params, now.getTime());
  const day = utcDay;
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
