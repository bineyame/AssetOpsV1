/**
 * SR-8 page / SR-10c (rev 10 §10.4, rev 10b.2): what the mini-grid range views share. A range view reads one stored
 * route over the whole shared range and declares nothing to the date-range bar (rev 10b.2: the range view covers every
 * day of the range, so the bar keeps "All pages").
 *
 * - `useRangeRead`: one read per address; its 503 `SITE_*_RANGE_UNAVAILABLE` (or INFRA-1 `TEMPORARILY_UNAVAILABLE`)
 *   is retried after 2, 4 and 8 s with "Temporarily unavailable. Retrying…", then "Still unavailable. Refresh to try
 *   again." It is never rendered as a data state (SR-10 packet L-2).
 * - `gapLine`: the counted-days line in the D-E5.46 form (`5 of 7 days · 4 Nov: no readings`), one group per reason,
 *   more than 3 gap days read `{g} days without a usable result`.
 */
import { useEffect, useState, type ReactNode } from "react";

import { formatDay } from "../ui/time";
import type { MiniRead } from "./miniDepthClient";
import { RETRY_DELAYS_MS, RETRYING_COPY, STILL_UNAVAILABLE_COPY, TEMPORARILY_UNAVAILABLE } from "./temporarilyUnavailable";

export type RangeReadState<T> =
  | { phase: "loading" }
  | { phase: "retrying" }
  | { phase: "still-unavailable" }
  | { phase: "done"; read: MiniRead<T> };

const isRetryable = (read: MiniRead<unknown>, code: string): boolean =>
  read.status === "refused" && read.httpStatus === 503 && (read.code === code || read.code === TEMPORARILY_UNAVAILABLE);

/** One range read for `key`, retried while it answers the route's 503 unavailable code (`code`). */
export function useRangeRead<T>(
  load: () => Promise<MiniRead<T>>,
  key: string,
  code: string,
  attempt: number,
  delays: readonly number[] = RETRY_DELAYS_MS,
): RangeReadState<T> {
  const fullKey = `${key}#${attempt}`;
  const [state, setState] = useState<{ key: string; value: RangeReadState<T> } | null>(null);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let tries = 0;
    const run = () => {
      void load().then((read) => {
        if (!active) return;
        if (!isRetryable(read, code)) {
          setState({ key: fullKey, value: { phase: "done", read } });
        } else if (tries < delays.length) {
          setState({ key: fullKey, value: { phase: "retrying" } });
          timer = setTimeout(run, delays[tries]);
          tries += 1;
        } else {
          setState({ key: fullKey, value: { phase: "still-unavailable" } });
        }
      });
    };
    run();
    return () => {
      active = false;
      if (timer !== undefined) clearTimeout(timer);
    };
    // `load` is rebuilt every render; the key names what it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullKey]);
  return state !== null && state.key === fullKey ? state.value : { phase: "loading" };
}

/** The retry phases' words, never a data state. */
export function RangeRetrying({ phase }: { phase: "retrying" | "still-unavailable" }): ReactNode {
  return (
    <p className="not-available-yet" role="status" data-mini-range-retry={phase}>
      {phase === "retrying" ? RETRYING_COPY : STILL_UNAVAILABLE_COPY}
    </p>
  );
}

/** `4 Nov` for a Site-local date `YYYY-MM-DD` (the date as it is, never shifted by a zone). */
export const shortLocalDay = (day: string): string => formatDay(`${day}T00:00:00Z`, { year: false, timeZone: "UTC" });

/** D-E5.46 form: `{n} of {m} days · {days}: {reason}` per reason group; more than 3 gap days: `{g} days without a usable result`. */
export function gapLine(
  days: readonly { local_day: string; state: string }[],
  counted: (state: string) => boolean,
  reason: (state: string) => string,
): string {
  const gaps = days.filter((d) => !counted(d.state));
  const head = `${days.length - gaps.length} of ${days.length} days`;
  if (gaps.length === 0) return head;
  if (gaps.length > 3) return `${head} · ${gaps.length} days without a usable result`;
  const groups = new Map<string, string[]>();
  for (const d of gaps) {
    const words = reason(d.state);
    groups.set(words, [...(groups.get(words) ?? []), d.local_day]);
  }
  const parts = Array.from(groups, ([words, list]) => `${shortDays(list)}: ${words}`);
  return `${head} · ${parts.join(" · ")}`;
}

/** `3, 4 Nov` when the days share a month, else `30 Oct, 2 Nov`. */
function shortDays(list: readonly string[]): string {
  const months = new Set(list.map((d) => d.slice(0, 7)));
  if (months.size === 1 && list.length > 1) {
    const last = shortLocalDay(list[list.length - 1]);
    const month = last.split(" ").slice(1).join(" ");
    return `${list.map((d) => String(Number(d.slice(8, 10)))).join(", ")} ${month}`;
  }
  return list.map(shortLocalDay).join(", ");
}

/** A decimal text or number from a range body as a number; null when absent or not finite. */
export function rangeNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}
