/**
 * post-W6 W2-EV (Architect W2-EV/W2-cold ruling Q11/Q18, time-basis ruling): the shared Site-timezone formatter.
 *
 * Site-scoped reads show the Site's timezone as primary, with the exact UTC instant available as detail. Stored
 * instants and URL parameters stay UTC. A missing or unrecognised timezone falls back to UTC and says so.
 */

/** Zones whose mock abbreviation Intl does not supply (it prints `GMT+3`). */
const ZONE_ABBREVIATION: Record<string, string> = {
  "Africa/Addis_Ababa": "EAT",
  "Africa/Nairobi": "EAT",
  "Africa/Dar_es_Salaam": "EAT",
  "Africa/Kampala": "EAT",
  "Africa/Asmara": "EAT",
  "Africa/Djibouti": "EAT",
  "Africa/Mogadishu": "EAT",
  "Etc/UTC": "UTC",
  UTC: "UTC",
  "Etc/GMT": "UTC",
};

export interface SiteTime {
  /** Local `HH:MM:SS`, prefixed `D Mon ` when its local day differs from the reference instant's local day. */
  text: string;
  /** The exact stored instant, ISO 8601 UTC (for `title` or a technical disclosure). */
  utc: string;
  /** The zone label for headers, such as `EAT` or `UTC`. `UTC` when the timezone was missing or invalid. */
  zone: string;
  /** False when the Site timezone was missing or invalid and UTC was used instead. */
  siteZone: boolean;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function parse(value: string | null | undefined): Date | null {
  if (value === null || value === undefined || value === "") return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function validZone(timeZone: string | null | undefined): string | null {
  if (!timeZone) return null;
  try {
    new Intl.DateTimeFormat("en-GB", { timeZone });
    return timeZone;
  } catch {
    return null;
  }
}

function parts(d: Date, timeZone: string): { y: number; m: number; day: number; hh: string; mm: string; ss: string } {
  const f = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  const get = (type: string) => f.formatToParts(d).find((p) => p.type === type)?.value ?? "";
  return { y: Number(get("year")), m: Number(get("month")), day: Number(get("day")), hh: get("hour"), mm: get("minute"), ss: get("second") };
}

/** The header label for a Site timezone (`EAT`, `UTC`, or Intl's short name); `UTC` when missing or invalid. */
export function siteZoneLabel(timeZone: string | null | undefined, at?: string | null): string {
  const zone = validZone(timeZone);
  if (zone === null) return "UTC";
  const known = ZONE_ABBREVIATION[zone];
  if (known !== undefined) return known;
  const d = parse(at) ?? new Date();
  const name = new Intl.DateTimeFormat("en-GB", { timeZone: zone, timeZoneName: "short" }).formatToParts(d).find((p) => p.type === "timeZoneName")?.value;
  return name ?? zone;
}

/**
 * Format `value` in the Site's timezone with seconds. When `reference` is given and its local day differs from the
 * value's local day, the text is prefixed with the local date (`24 Oct 16:08:42`). Returns null for a missing or
 * unparseable instant.
 */
export function siteTime(value: string | null | undefined, timeZone: string | null | undefined, reference?: string | null): SiteTime | null {
  const d = parse(value);
  if (d === null) return null;
  const zone = validZone(timeZone);
  const used = zone ?? "UTC";
  const p = parts(d, used);
  const r = parse(reference);
  const rp = r === null ? null : parts(r, used);
  const otherDay = rp !== null && (rp.y !== p.y || rp.m !== p.m || rp.day !== p.day);
  const clock = `${p.hh}:${p.mm}:${p.ss}`;
  return {
    text: otherDay ? `${p.day} ${MONTHS[p.m - 1]} ${clock}` : clock,
    utc: d.toISOString(),
    zone: zone === null ? "UTC" : siteZoneLabel(zone, value),
    siteZone: zone !== null,
  };
}
