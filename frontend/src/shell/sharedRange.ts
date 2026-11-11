/**
 * SR-1 (proposal 2026-11-10 "Item 12.5", SR.3): the one shared date range. It lives in the address only (D-UI.2):
 * `from`, `to` and an optional `known_at`. Nothing is kept in `localStorage` or on the server; the last range chosen
 * in this browser tab is remembered in `sessionStorage` only to fill an address that has none.
 *
 * Two address forms are read:
 * - the short day form, `from=2026-11-02&to=2026-11-08` (calendar days, `to` included);
 * - the instant form every page already reads, `from=2026-11-02T00:00:00Z&to=2026-11-09T00:00:00Z` (`to` excluded).
 * Both name the same range. The range is carried (rail, `withRange`, Apply) in the instant form, so every page reads
 * it exactly as it reads its links today and each page's API request for a range is unchanged (MOCK DEVIATION SR-1-1
 * in `SharedRangeBar.tsx`).
 */
import { useSearchParams } from "react-router-dom";

const DAY_MS = 24 * 60 * 60 * 1000;
/** The longest range any shared-range page accepts (estate and Work: 1-31 days). */
export const RANGE_MAX_DAYS = 31;
export const SHARED_RANGE_SESSION_KEY = "assetops.sharedRange";

export type RangePreset = "yesterday" | "7d" | "30d" | "month" | "lastmonth" | "custom";
export type FixedPreset = Exclude<RangePreset, "custom">;

/** SR.3: Yesterday, Last 7 days, Last 30 days, This month, Last month and Custom. "Today" is a partial day, so it is not a preset. */
export const RANGE_PRESETS: readonly { key: RangePreset; label: string }[] = [
  { key: "yesterday", label: "Yesterday" },
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
  { key: "month", label: "This month" },
  { key: "lastmonth", label: "Last month" },
  { key: "custom", label: "Custom" },
];

export const presetLabel = (preset: RangePreset): string => RANGE_PRESETS.find((p) => p.key === preset)?.label ?? "Custom";

/** Calendar days `YYYY-MM-DD`; `to` is included. */
export interface DayRange {
  from: string;
  to: string;
}

export interface SharedRange extends DayRange {
  known_at: string | null;
  preset: RangePreset;
}

export type SharedRangeState = ({ status: "set" } & SharedRange) | { status: "absent" } | { status: "invalid" };

const DAY = /^\d{4}-\d{2}-\d{2}$/;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$/;

const dayMs = (day: string): number => Date.parse(`${day}T00:00:00Z`);
const dayOf = (ms: number): string => new Date(ms).toISOString().slice(0, 10);
/** A real calendar day in the short form (`2026-02-30` is not one). */
export const validDay = (day: string): boolean => DAY.test(day) && !Number.isNaN(dayMs(day)) && dayOf(dayMs(day)) === day;

/** One bound as a calendar day: a day as it is, an instant `from` by its day, an instant `to` by the day before it. */
function boundDay(value: string, end: boolean): string | null {
  if (DAY.test(value)) return validDay(value) ? value : null;
  if (!INSTANT.test(value)) return null;
  const ms = Date.parse(value);
  if (Number.isNaN(ms)) return null;
  return dayOf(end ? ms - 1 : ms);
}

function todayMs(now: number): number {
  const d = new Date(now);
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
}

/** A preset as full UTC days ending yesterday ("This month" includes today only on the 1st, when nothing else is in it). */
export function presetRange(preset: FixedPreset, now: number = Date.now()): DayRange {
  const today = todayMs(now);
  const yesterday = dayOf(today - DAY_MS);
  const d = new Date(today);
  switch (preset) {
    case "yesterday":
      return { from: yesterday, to: yesterday };
    case "7d":
      return { from: dayOf(today - 7 * DAY_MS), to: yesterday };
    case "30d":
      return { from: dayOf(today - 30 * DAY_MS), to: yesterday };
    case "month": {
      const first = dayOf(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1));
      return { from: first, to: yesterday < first ? first : yesterday };
    }
    case "lastmonth":
      return {
        from: dayOf(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - 1, 1)),
        to: dayOf(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) - DAY_MS),
      };
  }
}

/** The preset a range is, today; `custom` when none matches. */
export function presetOf(from: string, to: string, now: number = Date.now()): RangePreset {
  for (const { key } of RANGE_PRESETS) {
    if (key === "custom") continue;
    const range = presetRange(key, now);
    if (range.from === from && range.to === to) return key;
  }
  return "custom";
}

/** The number of days in a range, `to` included. */
export const rangeDays = (range: DayRange): number => (dayMs(range.to) - dayMs(range.from)) / DAY_MS + 1;

/**
 * The shared range in an address. No `from` and no `to` is `absent`. One bound, a bound in neither form, a first day
 * after the last, more than 31 days or a malformed `known_at` is `invalid`, which never carries the dates.
 */
export function readSharedRange(params: URLSearchParams, now: number = Date.now()): SharedRangeState {
  const froms = params.getAll("from");
  const tos = params.getAll("to");
  if (froms.length === 0 && tos.length === 0) return { status: "absent" };
  if (froms.length !== 1 || tos.length !== 1) return { status: "invalid" };
  const from = boundDay(froms[0], false);
  const to = boundDay(tos[0], true);
  if (from === null || to === null || from > to || rangeDays({ from, to }) > RANGE_MAX_DAYS) return { status: "invalid" };
  const knowns = params.getAll("known_at");
  if (knowns.length > 1) return { status: "invalid" };
  const known_at = knowns.length === 1 ? knowns[0] : null;
  if (known_at !== null && (!INSTANT.test(known_at) || Number.isNaN(Date.parse(known_at)))) return { status: "invalid" };
  return { status: "set", from, to, known_at, preset: presetOf(from, to, now) };
}

/** The range's half-open instant window: `from` 00:00Z and the day after `to` 00:00Z. */
export function rangeWindow(range: DayRange): { from: string; to: string } {
  return { from: `${range.from}T00:00:00Z`, to: `${dayOf(dayMs(range.to) + DAY_MS)}T00:00:00Z` };
}

/** The shared parameters, in the instant form: `from`, `to` and `known_at` when set. */
export function rangeParams(range: DayRange & { known_at: string | null }): URLSearchParams {
  const window = rangeWindow(range);
  const params = new URLSearchParams({ from: window.from, to: window.to });
  if (range.known_at) params.set("known_at", range.known_at);
  return params;
}

/** The rail `search`: `?from=..&to=..[&known_at=..]` for a valid address range, `""` otherwise. Page-only parameters never travel. */
export function rangeSearch(params: URLSearchParams): string {
  const state = readSharedRange(params);
  return state.status === "set" ? `?${rangeParams(state).toString()}` : "";
}

/** An in-app path with the current shared range added. A path that names its own range keeps it. */
export function withRange(path: string, params: URLSearchParams): string {
  const search = rangeSearch(params);
  if (search === "") return path;
  const [pathname, query = ""] = path.split("?", 2);
  const own = new URLSearchParams(query);
  if (own.has("from") || own.has("to")) return path;
  return query === "" ? `${pathname}${search}` : `${pathname}?${query}&${search.slice(1)}`;
}

/** SR.3: the shared range of the current address. */
export function useSharedRange(): SharedRangeState {
  const [params] = useSearchParams();
  return readSharedRange(params);
}

/**
 * The pages the shell fills on entry in SR-1: the estate pages, whose default today is already the one default (the
 * last 7 full UTC days ending yesterday, S17), so filling the address changes no request. Work and Site pages keep
 * their own defaults until SR-2 moves them onto the range (R338, Site-local days, Cold/EV selected event).
 */
const FILLED_PAGES = /^\/(?:portfolio(?:\/[^/]+)?|findings(?:\/(?:cost|risks|opportunities))?|actions|evidence|financials)\/?$/;
export const fillsRangeOnEntry = (pathname: string): boolean => FILLED_PAGES.test(pathname);

/**
 * SR-1 review (Medium): the pages whose content follows the shared range. The bar says "All pages" only on these.
 * Everywhere else (the Site directory and Site pages, whose boards show one day, one hour or one analysed event; a
 * record page) the bar says the range is not used on this page, so it never claims a range over content that ignores
 * it. SR-2 adds a page here when it moves onto the range.
 */
const RANGE_PAGES =
  /^\/(?:portfolio(?:\/[^/]+)?|findings(?:\/(?:cost|risks|opportunities))?|actions|evidence|financials|incidents|maintenance(?:\/preventive)?|operational-records)\/?$/;
export const readsSharedRange = (pathname: string): boolean => RANGE_PAGES.test(pathname);

/** The range to fill an empty address with: the last one chosen in this tab, else Last 7 days. Blocked storage falls back to the default. */
export function entryRange(now: number = Date.now()): URLSearchParams {
  let stored: string | null = null;
  try {
    stored = window.sessionStorage.getItem(SHARED_RANGE_SESSION_KEY);
  } catch {
    stored = null;
  }
  if (stored !== null) {
    const state = readSharedRange(new URLSearchParams(stored), now);
    if (state.status === "set") return rangeParams({ from: state.from, to: state.to, known_at: null });
  }
  return rangeParams({ ...presetRange("7d", now), known_at: null });
}

/**
 * Remembers a range the user chose in the bar (its days only, never `known_at`) for this browser tab. SR-1 review
 * (Low): only Apply calls this, never a range that merely arrived in an address (a Cold analysed-period link would
 * otherwise make a bare `/portfolio` open one day).
 */
export function rememberRange(params: URLSearchParams): void {
  const state = readSharedRange(params);
  if (state.status !== "set") return;
  try {
    window.sessionStorage.setItem(SHARED_RANGE_SESSION_KEY, rangeParams({ from: state.from, to: state.to, known_at: null }).toString());
  } catch {
    // Storage blocked: the next empty address uses the default.
  }
}
