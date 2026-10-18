/**
 * W2-03: UTC time, window and decimal formatting shared by the cold assessment views and the cold temperature chart.
 */

export const NOT_RECORDED = "Not recorded";
export const NOT_ASSESSED = "Not assessed";


const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const pad = (n: number) => String(n).padStart(2, "0");

export function date(value: string | null | undefined): Date | null {
  if (value === null || value === undefined) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "19:15" (UTC), or "19:11:05" when the instant has seconds. */
export function hm(value: string | null | undefined): string {
  const d = date(value);
  if (d === null) return "—";
  const base = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
  return d.getUTCSeconds() === 0 ? base : `${base}:${pad(d.getUTCSeconds())}`;
}

export function dayHm(value: string | null | undefined): string {
  const d = date(value);
  return d === null ? "—" : `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${hm(value)}`;
}

export function windowText(from: string | null, to: string | null): string {
  const a = date(from);
  const b = date(to);
  if (a === null || b === null) return "No window selected";
  const sameDay = a.toISOString().slice(0, 10) === new Date(b.getTime() - 1).toISOString().slice(0, 10);
  const end = sameDay ? hm(to) : dayHm(to);
  return `${a.getUTCDate()} ${MONTHS[a.getUTCMonth()]} ${a.getUTCFullYear()} ${hm(from)}–${end} UTC`;
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

export function between(earliest: string | null, latest: string | null): string {
  if (earliest === null && latest === null) return NOT_RECORDED;
  if (earliest === null) return `by ${hm(latest)}`;
  if (latest === null || earliest === latest) return hm(earliest);
  return `${hm(earliest)}–${hm(latest)}`;
}
