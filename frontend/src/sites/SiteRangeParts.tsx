/**
 * SR-7 / SR-11: the parts the per-day range pages share — the read hook with its retry state, the not-loaded copy,
 * Site-local day words, and the D-E5.45 day-gap label (`{n} of {m} days analysed · {day list}: {short reason}`, one
 * group per reason, grouped days, more than 3 gap days as `{g} days without a usable result`; build sheet gap table).
 */
import { useEffect, useState, type ReactNode } from "react";
import { useLocation, useSearchParams } from "react-router-dom";

import { RangeLink as Link } from "../ui/RangeLink";
import { formatDay } from "../ui/time";
import { focusDayOf, rangeSearch } from "../ui/sharedRange";
import { RETRYING_COPY, STILL_UNAVAILABLE_COPY } from "./temporarilyUnavailable";
import type { RangeRead } from "./siteRangeClient";

export const RANGE_LOADING = "Loading the days of the date range.";
export const BACK_TO_RANGE = "Back to the whole range";
/** D-SR.76: an address that is not whole days opens the day table with this frame, so a short range is not read as a full-day claim. */
export const WHOLE_DAYS_FRAME = "Whole days that include the selected time";

export const OPEN_NOON_HOUR = "Open the 12:00 hour";

/** `4 Nov` for a `YYYY-MM-DD` Site-local day (the date as written, never shifted by a zone). */
export const dayWords = (day: string): string => formatDay(`${day}T00:00:00Z`, { timeZone: "UTC", year: false });

/** The read and whether it is waiting to retry a `SITE_*_RANGE_UNAVAILABLE` (the page shows "Retrying…"). */
export function useRangeRead<T>(
  load: (onRetrying: () => boolean) => Promise<RangeRead<T>>,
  key: string,
): { read: RangeRead<T> | null; retrying: boolean } {
  const [state, setState] = useState<{ key: string; read: RangeRead<T> | null; retrying: boolean }>({ key, read: null, retrying: false });
  useEffect(() => {
    let live = true;
    setState({ key, read: null, retrying: false });
    void load(() => {
      if (live) setState({ key, read: null, retrying: true });
      return live;
    }).then((read) => {
      if (live) setState({ key, read, retrying: false });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` names everything `load` reads
  }, [key]);
  return state.key === key ? { read: state.read, retrying: state.retrying } : { read: null, retrying: false };
}

/** Refusal words for a range read; never a code, never a data state. */
export function rangeRefusalCopy(read: Exclude<RangeRead<unknown>, { status: "loaded" }>, notApplicable: string): string {
  if (read.status === "unavailable") return STILL_UNAVAILABLE_COPY;
  switch (read.httpStatus) {
    case 401:
      return "Sign in to see this range.";
    case 403:
      return "Your account does not have access to this site.";
    case 404:
      return read.code === "SITE_NOT_FOUND" ? "This site was not found." : notApplicable;
    case 409:
      return read.code === "PERFORMANCE_CUTOVER_CLOSED"
        ? "Assessment results are not released for this site yet, so no limit is shown."
        : "This range cannot be shown right now.";
    case 422:
      return "Choose a valid date range of at most 31 days.";
    default:
      return "This range cannot be shown right now.";
  }
}

/** Loading, retrying or refused: one status line. `null` once loaded. */
export function RangeNotLoaded({
  read,
  retrying,
  notApplicable,
  name,
}: {
  read: RangeRead<unknown> | null;
  retrying: boolean;
  notApplicable: string;
  name: string;
}): ReactNode {
  if (read !== null && read.status === "loaded") return null;
  if (read === null) {
    return (
      <p role="status" data-range-read={name} data-range-state={retrying ? "retrying" : "loading"}>
        {retrying ? RETRYING_COPY : RANGE_LOADING}
      </p>
    );
  }
  return (
    <p role="status" data-range-read={name} data-range-state={read.status} data-range-code={read.code ?? ""}>
      {rangeRefusalCopy(read, notApplicable)}
    </p>
  );
}

/**
 * D-E5.45 (amended by the gap table): `· 4 Nov: no readings · 5, 6 Nov: still being prepared`, one group per short
 * reason in first-day order; more than 3 gap days read `· {g} days without a usable result`. Empty when no gap day.
 */
export function gapDaysText(gaps: ReadonlyArray<{ day: string; reason: string }>): string {
  if (gaps.length === 0) return "";
  if (gaps.length > 3) return ` · ${gaps.length} days without a usable result`;
  const groups = new Map<string, string[]>();
  for (const gap of gaps) groups.set(gap.reason, [...(groups.get(gap.reason) ?? []), gap.day]);
  return Array.from(groups, ([reason, days]) => ` · ${groupDays(days)}: ${reason}`).join("");
}

/** `3, 4 Nov` for days of one month, else `30 Oct, 2 Nov`. */
function groupDays(days: string[]): string {
  const words = days.map(dayWords);
  const months = new Set(words.map((w) => w.split(" ")[1]));
  if (months.size === 1) return `${words.map((w) => w.split(" ")[0]).join(", ")} ${[...months][0]}`;
  return words.join(", ");
}

/**
 * "Back to the whole range" on a one-hour or one-day drill-in (rev 10 §10.3, 10a.2). A `day=` drill-in drops `day`
 * (and `revision`) and keeps the address range. An hour opened from a range page carries that range in the link's
 * history state; an hour reached any other way goes back to the range the address names (its own day).
 */
export function BackToRange({ path, drop = [] }: { path: string; drop?: string[] }): ReactNode {
  const [params] = useSearchParams();
  const location = useLocation();
  const carried = (location.state as { wholeRange?: unknown } | null)?.wholeRange;
  let search: string;
  if (focusDayOf(params) !== null) {
    const next = new URLSearchParams(params);
    for (const key of ["day", "date", ...drop]) next.delete(key);
    search = next.toString() === "" ? "" : `?${next.toString()}`;
  } else if (typeof carried === "string" && carried.startsWith("?")) {
    search = carried;
  } else {
    search = rangeSearch(params);
  }
  if (search === "") return null;
  return (
    <span className="range-back" data-range-back>
      <Link to={`${path}${search}`}>{BACK_TO_RANGE}</Link>
    </span>
  );
}

/** The history state an hour link carries so the hour page can go back to the whole range. */
export function useWholeRangeState(): { wholeRange: string } {
  const [params] = useSearchParams();
  return { wholeRange: rangeSearch(params) };
}
