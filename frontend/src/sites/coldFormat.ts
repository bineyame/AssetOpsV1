/**
 * W2-03: UTC time, window and decimal formatting shared by the cold assessment views and the cold temperature chart.
 */
import { formatDayTime, formatRange, formatTime } from "../ui/time";

export const NOT_RECORDED = "Not recorded";
export const NOT_ASSESSED = "Not assessed";



export function date(value: string | null | undefined): Date | null {
  if (value === null || value === undefined) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "19:15", or "19:11:05" when the instant has seconds (POLISH §3 Times; UTC, named by the page note). */
export function hm(value: string | null | undefined): string {
  const d = date(value);
  if (d === null) return "—";
  return formatTime(d, { seconds: d.getUTCSeconds() !== 0 });
}

/** "29 Oct, 19:15" (the §3.1 short form). */
export function dayHm(value: string | null | undefined): string {
  const d = date(value);
  return d === null ? "—" : formatDayTime(d, { year: false, seconds: d.getUTCSeconds() !== 0 });
}

/** "29 Oct 2026, 16:00–17:05", or both ends in full across days; seconds shown when either bound has them (as `hm`). */
export function windowText(from: string | null, to: string | null): string {
  const a = date(from);
  const b = date(to);
  if (a === null || b === null) return "No window selected";
  return formatRange(a, b, { seconds: a.getUTCSeconds() !== 0 || b.getUTCSeconds() !== 0 });
}

export function num(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function decimal(value: string | number | null | undefined): string | null {
  const n = num(value);
  return n === null ? null : String(Number(n.toFixed(4)));
}

export const deg = (value: string | number | null | undefined) => {
  const d = decimal(value);
  return d === null ? NOT_RECORDED : `${d} °C`;
};

export function range(low: string | null, high: string | null, unit: string): string {
  const lo = decimal(low);
  const hi = decimal(high);
  if (lo === null && hi === null) return NOT_ASSESSED;
  if (hi === null) return `At least ${lo} ${unit}`;
  if (lo === null || lo === hi) return `${hi} ${unit}`;
  return `${lo}–${hi} ${unit}`;
}

/**
 * W2-F M6/S8: a stored degree-minute bound pair. Null bounds are `Not assessed`; an open upper bound is stated as not
 * established, never implied. Callers name the basis (`Observed excursion estimate` or `Consequence basis`).
 */
export function degreeMinutes(low: string | null, high: string | null): string {
  const lo = decimal(low);
  const hi = decimal(high);
  if (lo === null && hi === null) return NOT_ASSESSED;
  if (hi === null) return `at least ${lo} °C·min (degrees × minutes); the full extent is not known yet`;
  if (lo === null || lo === hi) return `${hi} °C·min`;
  return `${lo}–${hi} °C·min`;
}

export function between(earliest: string | null, latest: string | null): string {
  if (earliest === null && latest === null) return NOT_RECORDED;
  if (earliest === null) return `by ${hm(latest)}`;
  if (latest === null || earliest === latest) return hm(earliest);
  return `${hm(earliest)}–${hm(latest)}`;
}
