/**
 * post-W6 W1-a (Architect W1 rulings G3, Q10, Q17): Finding-page presentation of Site-local time.
 *
 * A thin wrapper over the canonical `siteTime.ts`; it adds no timezone algorithm. `siteTime` formats the instant in
 * the Site's zone; with a reference instant that is never the same local day, its text always carries the local
 * `D Mon` prefix, which this module reshapes for a status period (`YYYY-MM-DD HH:MM`) or a history cell
 * (`D Mon · HH:MM`). Stored instants and URL parameters stay UTC; the exact UTC instant is returned for detail.
 */
import { siteTime } from "./siteTime";

/** A reference instant whose local day can never equal a Finding instant's, so `siteTime` always prefixes the date. */
const NEVER_SAME_DAY = "1970-01-01T12:00:00Z";
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export interface FindingLocalTime {
  /** Local calendar day, `YYYY-MM-DD`. */
  day: string;
  /** Local `D Mon`. */
  dayMonth: string;
  /** Local `HH:MM` (seconds omitted). */
  clock: string;
  /** The exact stored instant, ISO 8601 UTC. */
  utc: string;
  /** `EAT`, `UTC`, ...; `UTC` when the Site timezone was missing or invalid. */
  zone: string;
  /** False when the Site timezone was missing or invalid and UTC was used. */
  siteZone: boolean;
}

export function findingLocalTime(value: string | null | undefined, timeZone: string | null | undefined): FindingLocalTime | null {
  const t = siteTime(value, timeZone, NEVER_SAME_DAY);
  if (t === null) return null;
  const match = /^(\d{1,2}) ([A-Z][a-z]{2}) (\d{2}):(\d{2}):\d{2}$/.exec(t.text);
  if (match === null) return null;
  const [, d, mon, hh, mm] = match;
  const month = MONTHS.indexOf(mon) + 1;
  // The local year is the UTC year except across a New Year boundary, which only the month can show.
  const instant = new Date(t.utc);
  const utcMonth = instant.getUTCMonth() + 1;
  const year = instant.getUTCFullYear() + (month === 1 && utcMonth === 12 ? 1 : month === 12 && utcMonth === 1 ? -1 : 0);
  return {
    day: `${year}-${String(month).padStart(2, "0")}-${d.padStart(2, "0")}`,
    dayMonth: `${d} ${mon}`,
    clock: `${hh}:${mm}`,
    utc: t.utc,
    zone: t.zone,
    siteZone: t.siteZone,
  };
}

/**
 * Q10 / R187: a Finding period in Site-local time, `YYYY-MM-DD HH:MM–HH:MM EAT`, or with both days when the period
 * crosses local midnight. Null when either instant is unreadable.
 */
export function findingLocalPeriod(
  start: string,
  end: string,
  timeZone: string | null | undefined,
): { text: string; zone: string; siteZone: boolean; startUtc: string; endUtc: string } | null {
  const a = findingLocalTime(start, timeZone);
  const b = findingLocalTime(end, timeZone);
  if (a === null || b === null) return null;
  const text = a.day === b.day ? `${a.day} ${a.clock}–${b.clock} ${a.zone}` : `${a.day} ${a.clock} – ${b.day} ${b.clock} ${a.zone}`;
  return { text, zone: a.zone, siteZone: a.siteZone, startUtc: a.utc, endUtc: b.utc };
}
