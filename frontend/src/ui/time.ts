/**
 * POLISH §3 "Times" (PB-1, R650): the one place the frontend formats an instant for a client screen.
 *
 * - Forms: `29 Oct 2026`, `29 Oct 2026, 16:00`, `16:00`, `29 Oct 2026, 16:00–17:05` (same day; otherwise both ends
 *   in full). No ISO strings and no per-time "UTC" suffix: each page carries one `<TimeZoneNote/>` instead (D-4).
 * - Clock times are computed in UTC (Addendum 6 Q7: DTO instants carry no Site offset). Only a calendar due date the
 *   frontend formats itself passes `timeZone` (the declared Site zone); an absent or unknown zone falls back to UTC.
 * - `seconds: true` only where an existing ruling shows seconds (Addendum 7 Q2: R372 historical lines, Site health,
 *   EV energy, cold times that carry seconds). `year: false` gives the short `29 Oct, 16:00` form of §3.1.
 * - Unparseable input gives `Time not available yet`, never the raw string (Addendum 7 Q3). Callers keep their own
 *   word for a missing (null) value.
 */

export const TIME_NOT_AVAILABLE = "Time not available yet";

export interface TimeOptions {
  /** IANA zone for a calendar date; omitted, null or unknown means UTC. */
  timeZone?: string | null;
  /** Show `:ss` after the minutes. */
  seconds?: boolean;
  /** `false` drops the year from day forms (`29 Oct`). */
  year?: boolean;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

interface Parts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  second: number;
}

const formatters = new Map<string, Intl.DateTimeFormat>();

function formatterFor(timeZone: string): Intl.DateTimeFormat | null {
  const cached = formatters.get(timeZone);
  if (cached) return cached;
  try {
    const made = new Intl.DateTimeFormat("en-GB", {
      timeZone,
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
      hourCycle: "h23",
    });
    formatters.set(timeZone, made);
    return made;
  } catch {
    return null;
  }
}

/** Epoch ms of a wire instant or date; microsecond fractions are truncated to milliseconds. */
export function instantMs(value: string | number | Date | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value.getTime();
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const ms = Date.parse(value.trim().replace(/(\.\d{3})\d+/, "$1"));
  return Number.isNaN(ms) ? null : ms;
}

function partsOf(ms: number, timeZone: string | null | undefined): Parts {
  const zoned = timeZone && timeZone !== "UTC" ? formatterFor(timeZone) : null;
  if (zoned === null) {
    const d = new Date(ms);
    return {
      year: d.getUTCFullYear(),
      month: d.getUTCMonth(),
      day: d.getUTCDate(),
      hour: d.getUTCHours(),
      minute: d.getUTCMinutes(),
      second: d.getUTCSeconds(),
    };
  }
  const got: Record<string, number> = {};
  for (const p of zoned.formatToParts(new Date(ms))) if (p.type !== "literal") got[p.type] = Number(p.value);
  return {
    year: got.year ?? 0,
    month: (got.month ?? 1) - 1,
    day: got.day ?? 1,
    hour: (got.hour ?? 0) % 24,
    minute: got.minute ?? 0,
    second: got.second ?? 0,
  };
}

const pad = (n: number) => String(n).padStart(2, "0");

function dayText(p: Parts, year = true): string {
  return year ? `${p.day} ${MONTHS[p.month]} ${p.year}` : `${p.day} ${MONTHS[p.month]}`;
}

function timeText(p: Parts, seconds = false): string {
  return seconds ? `${pad(p.hour)}:${pad(p.minute)}:${pad(p.second)}` : `${pad(p.hour)}:${pad(p.minute)}`;
}

const sameDay = (a: Parts, b: Parts) => a.year === b.year && a.month === b.month && a.day === b.day;

/** `29 Oct 2026` (or `29 Oct` with `year: false`). */
export function formatDay(value: string | number | Date | null | undefined, options: TimeOptions = {}): string {
  const ms = instantMs(value);
  return ms === null ? TIME_NOT_AVAILABLE : dayText(partsOf(ms, options.timeZone), options.year !== false);
}

/** `29 Oct 2026, 16:00`. */
export function formatDayTime(value: string | number | Date | null | undefined, options: TimeOptions = {}): string {
  const ms = instantMs(value);
  if (ms === null) return TIME_NOT_AVAILABLE;
  const p = partsOf(ms, options.timeZone);
  return `${dayText(p, options.year !== false)}, ${timeText(p, options.seconds)}`;
}

/** `16:00`. */
export function formatTime(value: string | number | Date | null | undefined, options: TimeOptions = {}): string {
  const ms = instantMs(value);
  return ms === null ? TIME_NOT_AVAILABLE : timeText(partsOf(ms, options.timeZone), options.seconds);
}

/** `29 Oct 2026, 16:00–17:05` on one day; otherwise `29 Oct 2026, 23:00 – 30 Oct 2026, 01:00`. */
export function formatRange(
  start: string | number | Date | null | undefined,
  end: string | number | Date | null | undefined,
  options: TimeOptions = {},
): string {
  const a = instantMs(start);
  const b = instantMs(end);
  if (a === null || b === null) return TIME_NOT_AVAILABLE;
  const pa = partsOf(a, options.timeZone);
  const pb = partsOf(b, options.timeZone);
  if (sameDay(pa, pb)) return `${formatDayTime(a, options)}–${timeText(pb, options.seconds)}`;
  return `${formatDayTime(a, options)} – ${formatDayTime(b, options)}`;
}

/**
 * A whole-day window `[from, toExclusive)` by its included days (Addendum 7 Q5): `29 Oct 2026` for one day,
 * `23–29 Oct 2026` within a month, `28 Sep – 4 Oct 2026` across months, `28 Dec 2026 – 3 Jan 2027` across years.
 */
export function formatDayRange(
  from: string | number | Date | null | undefined,
  toExclusive: string | number | Date | null | undefined,
  options: Pick<TimeOptions, "timeZone"> = {},
): string {
  const a = instantMs(from);
  const b = instantMs(toExclusive);
  if (a === null || b === null || b <= a) return TIME_NOT_AVAILABLE;
  const first = partsOf(a, options.timeZone);
  const last = partsOf(b - 1, options.timeZone);
  if (sameDay(first, last)) return dayText(first);
  if (first.year !== last.year) return `${dayText(first)} – ${dayText(last)}`;
  if (first.month !== last.month) return `${dayText(first, false)} – ${dayText(last)}`;
  return `${first.day}–${dayText(last)}`;
}
