/**
 * SR-1 (proposal 2026-11-10 "Item 12.5", SR.3; v71 `portfolio-tabs.html` Change 0b, approved; the "All pages" top bar
 * of `estate-outcomes-scale.html`): the one date range, in the shell's top bar, on every page.
 *
 * - The button names the whole state ("Date range for every page: Last 7 days, ... Change"), with `aria-expanded`
 *   and `aria-controls`. At 760 px and below it shows the dates only and is 44 px high.
 * - The picker is a labelled non-modal dialog (a bottom sheet on phones). Focus moves to the selected preset; Escape
 *   and Cancel close it and return focus to the button. Nothing changes until Apply (WCAG 3.2.2). Presets are
 *   `aria-pressed` toggles; the custom dates and the earlier point in time have visible labels.
 * - After Apply a polite live region says "Every page now shows ..." and focus stays on the button.
 * - While `known_at` is set, "As known at {time} · every page" and "Return to latest" show beside the button.
 *
 * MOCK DEVIATION SR-1-1: the bar writes the instant form (`from=2026-09-30T00:00:00Z&to=2026-10-07T00:00:00Z`), not
 *   the mock's short day form. Every page reads the instant form today and SR-2 moves the pages onto the hook, so each
 *   page's API request for a range stays byte-identical (the demo's pre-built responses keep matching). The hook
 *   reads both forms.
 * MOCK DEVIATION SR-1-2: the v7.0 top bar's estate name, "Find a screen" search and avatar are not drawn: the product
 *   has no data or route behind them. The top bar holds the range only.
 * MOCK DEVIATION SR-1-3: the picker note says days are UTC days and does not yet claim Site-local days; Site and Work
 *   pages move onto the range in SR-2. Until then a page whose address has no range says "This page's own dates".
 */
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Navigate, Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { WINDOW_NOT_VALID } from "../estate/estateClient";
import { formatDay, formatDayRange, formatDayTime } from "../ui/time";
import {
  RANGE_MAX_DAYS,
  RANGE_PRESETS,
  isWorkPage,
  entryRange,
  fillsRangeOnEntry,
  presetLabel,
  readSharedRange,
  presetRange,
  rangeDays,
  readsSharedRange,
  rangeParams,
  rangeWindow,
  rememberRange,
  useSharedRange,
  type DayRange,
  type RangePreset,
  dayInRange,
  focusDayOf,
  isSiteContentPage,
  weekEnding,
} from "./sharedRange";
import { useRangeFocus, type RangeNotUsedNote } from "../ui/rangeFocus";
import "./sharedRangeBar.css";

export const RANGE_ERROR = `Choose a first day on or before the last day, ${RANGE_MAX_DAYS} days at most.`;
export const OWN_DATES = "This page's own dates";
/** SR-1 review (Medium): the tag on a page whose content does not follow the shared range (`readsSharedRange`). */
export const NOT_THIS_PAGE = "Not used on this page";
const NOT_THIS_PAGE_SPOKEN = "This page shows its own dates, not this range";
/**
 * MOCK DEVIATION R718/R719 (v71 Change 0b shows only "All pages"; build sheet D-SR.6/SR-4c).
 * SR-2 / SR-4c (D-SR.6, R718/R719): the tag on a page that shows one day or part of the range: "Showing 9 Nov of the
 * range" / "Showing 5–9 Nov of the range"; outside the range "Showing 24 Oct · range not used". On a point-in-time
 * page: "Range not used · shows now" (or "· current settings", "· prices valid now").
 */
export const FOCUS_INSIDE = "of the range";
export const FOCUS_OUTSIDE = "range not used";
export const RANGE_NOT_USED = "Range not used";
/** The spoken form of each "now" note ("This page shows <it>"); the tag keeps the short note. */
const NOW_SPOKEN: Record<RangeNotUsedNote, string> = {
  "shows now": "the present state",
  "current settings": "the current settings",
  "prices valid now": "the prices valid now",
};
const focusDayLabel = (day: string): string => formatDay(`${day}T00:00:00Z`, { year: false });
/** `9 Nov` or `5–9 Nov` (`30 Oct – 2 Nov` across months). */
const focusSpanLabel = (from: string, to: string): string => {
  if (from === to) return focusDayLabel(from);
  const last = focusDayLabel(to);
  const first = focusDayLabel(from);
  return from.slice(0, 7) === to.slice(0, 7) ? `${first.split(" ")[0]}–${last}` : `${first} – ${last}`;
};
const focusSpanSpoken = (from: string, to: string): string =>
  from === to ? formatDay(`${from}T00:00:00Z`) : `${formatDay(`${from}T00:00:00Z`)} to ${formatDay(`${to}T00:00:00Z`)}`;
const LATEST_ANNOUNCEMENT = "Every page now shows the latest information";

/** `30 Sep – 6 Oct 2026` (one day: `6 Oct 2026`). */
const longLabel = (range: DayRange): string => {
  const window = rangeWindow(range);
  return formatDayRange(window.from, window.to);
};

/** `30 Sep – 6 Oct` (one day: `6 Oct`). */
const shortLabel = (range: DayRange): string => {
  const first = formatDay(`${range.from}T00:00:00Z`, { year: false });
  return range.from === range.to ? first : `${first} – ${formatDay(`${range.to}T00:00:00Z`, { year: false })}`;
};

/** Words for a screen reader: `30 Sep 2026 to 6 Oct 2026` (one day: `6 Oct 2026`). */
const spokenLabel = (range: DayRange): string => {
  const first = formatDay(`${range.from}T00:00:00Z`);
  return range.from === range.to ? first : `${first} to ${formatDay(`${range.to}T00:00:00Z`)}`;
};

/** A `datetime-local` value as the UTC instant the pages read (the picker says times are UTC). */
const cutoffInstant = (value: string): string => `${value.length === 16 ? `${value}:00` : value.replace(/\.0+$/, "")}Z`;

/**
 * SR.3 "An address with no range": the shell's outlet. On an estate page (`fillsRangeOnEntry`) whose address has no
 * range, it replaces the address with the same path plus the tab's last range (else Last 7 days), with no history
 * entry, before the page mounts; the page then reads once, for the range the address shows. Otherwise the page.
 */
export function SharedRangeOutlet() {
  const location = useLocation();
  const [params] = useSearchParams();
  // SR-4a (D-SR.3): the range of the previous in-app address, kept on every render whose address carries a valid one.
  const previous = useRef<URLSearchParams | null>(null);
  const state = readSharedRange(params);
  if (state.status === "set") previous.current = rangeParams(state);
  if (state.status !== "absent") return <Outlet />;
  let next: URLSearchParams;
  if (fillsRangeOnEntry(location.pathname)) {
    next = entryRange();
  } else if (isSiteContentPage(location.pathname)) {
    // SR-4a safety net: a Site content page reached by `navigate()` or a data-built link takes, in order, the previous
    // in-app range, the 7 days ending on the address's day, or the entry range (the bar's presets, so WARM-1 still hits).
    const day = focusDayOf(params);
    next = previous.current
      ? new URLSearchParams(previous.current)
      : day !== null
        ? rangeParams({ ...weekEnding(day), known_at: null })
        : entryRange();
  } else {
    return <Outlet />;
  }
  // D-SR.59 L-1 (D-SR.42d/D-SR.57): per key, the address's own `from`/`to`/`known_at` wins over the copied range, so
  // the result never holds a key twice.
  for (const key of ["from", "to", "known_at"]) if (params.has(key)) next.delete(key);
  for (const [key, value] of params) next.append(key, value);
  return <Navigate replace to={`${location.pathname}?${next.toString()}${location.hash}`} state={location.state} />;
}

export function SharedRangeBar() {
  const state = useSharedRange();
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const dialogId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  const set = state.status === "set" ? state : null;
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<RangePreset>("7d");
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [earlier, setEarlier] = useState(false);
  const [cutoff, setCutoff] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("");

  // SR-2: a page showing one day inside the range (FocusPicker) is never "All pages": the tag names its day, and says
  // the range is not used when the day lies outside it.
  const focus = useRangeFocus();
  const span = focus?.kind === "span" ? focus : null;
  const now = focus?.kind === "now" ? focus : null;
  const focusInside = span !== null && set !== null && dayInRange(span.from, set) && dayInRange(span.to, set);
  const here = focus === null && readsSharedRange(location.pathname, params);

  const close = (returnFocus: boolean) => {
    setOpen(false);
    if (returnFocus) buttonRef.current?.focus();
  };

  const openPicker = () => {
    const shown = set ?? { ...presetRange("7d"), known_at: null, preset: "7d" as RangePreset };
    setPending(shown.preset);
    setFirst(shown.from);
    setLast(shown.to);
    setEarlier(shown.known_at !== null);
    // SR-1 review (Low): keep the seconds, so reopening the picker and pressing Apply leaves the cutoff as it was.
    setCutoff(shown.known_at ? shown.known_at.slice(0, 19) : "");
    setError(null);
    setOpen(true);
  };

  useEffect(() => {
    if (!open) return undefined;
    dialogRef.current?.querySelector<HTMLButtonElement>('[aria-pressed="true"]')?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close(true);
    };
    const onPointer = (event: MouseEvent) => {
      if (wrapRef.current && event.target instanceof Node && !wrapRef.current.contains(event.target)) close(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
    };
    // Focus moves once, when the picker opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const go = (next: URLSearchParams, words: string) => {
    next.delete("cursor"); // a new range or cutoff restarts at page one
    next.delete("record"); // and an old record's detail must not stay open under the new period (SR-2b L1)
    navigate({ pathname: location.pathname, search: `?${next.toString()}` }, { state: location.state });
    setAnnouncement(words);
  };

  const apply = () => {
    const range: DayRange = pending === "custom" ? { from: first, to: last } : presetRange(pending);
    if (!range.from || !range.to || range.from > range.to || rangeDays(range) > RANGE_MAX_DAYS) {
      setError(RANGE_ERROR);
      return;
    }
    const known_at = earlier && cutoff ? cutoffInstant(cutoff) : null;
    const next = new URLSearchParams(params);
    next.delete("known_at");
    for (const [key, value] of rangeParams({ ...range, known_at })) next.set(key, value);
    rememberRange(next);
    go(next, `Every page now shows ${longLabel(range)}${known_at ? `, as known at ${formatDayTime(known_at)}` : ""}`);
    close(true);
  };

  const returnToLatest = () => {
    const next = new URLSearchParams(params);
    next.delete("known_at");
    go(next, LATEST_ANNOUNCEMENT);
  };

  let name: ReactNode = null;
  let dates: string;
  let short: string;
  let spoken: string;
  if (set !== null) {
    name = presetLabel(set.preset);
    dates = longLabel(set);
    short = shortLabel(set);
    spoken = `${presetLabel(set.preset)}, ${spokenLabel(set)}${set.known_at ? `, as known at ${formatDayTime(set.known_at)}` : ""}`;
    if (span !== null) {
      spoken = `${spoken}. ${
        focusInside
          ? span.from === span.to
            ? `This page shows one day of it: ${focusSpanSpoken(span.from, span.to)}`
            : `This page shows part of it: ${focusSpanSpoken(span.from, span.to)}`
          : `This page shows ${focusSpanSpoken(span.from, span.to)}, outside this range; the range is not used here`
      }`;
    } else if (now !== null) {
      spoken = `${spoken}. This page shows ${NOW_SPOKEN[now.note]}; the range is not used here`;
    } else if (!here) spoken = `${spoken}. ${NOT_THIS_PAGE_SPOKEN}`;
  } else if (state.status === "invalid") {
    dates = short = spoken = WINDOW_NOT_VALID;
  } else {
    dates = short = spoken = OWN_DATES;
  }

  return (
    <div className="shared-range" ref={wrapRef}>
      {set?.known_at ? (
        <span className="shared-range__asof" data-shared-range-asof>
          <span>
            As known at <b>{formatDayTime(set.known_at)}</b> · {here ? "every page" : "other pages"}
          </span>
          <button type="button" onClick={returnToLatest}>
            Return to latest
          </button>
        </span>
      ) : null}
      <button
        ref={buttonRef}
        type="button"
        className="shared-range__button"
        aria-expanded={open}
        aria-controls={dialogId}
        aria-label={`${set === null || here ? "Date range for every page" : "Date range for the other pages"}: ${spoken}. Change`}
        onClick={() => (open ? close(true) : openPicker())}
        data-shared-range-button
      >
        {name === null ? null : <span className="shared-range__name">{name}</span>}
        <span className="shared-range__dates">{dates}</span>
        <span className="shared-range__short">{short}</span>
        {set === null ? null : span !== null ? (
          <span
            className={focusInside ? "shared-range__tag" : "shared-range__tag shared-range__tag--elsewhere"}
            data-shared-range-focus={focusInside ? "inside" : "outside"}
          >
            {focusInside
              ? `Showing ${focusSpanLabel(span.from, span.to)} ${FOCUS_INSIDE}`
              : `Showing ${focusSpanLabel(span.from, span.to)} · ${FOCUS_OUTSIDE}`}
          </span>
        ) : now !== null ? (
          <span className="shared-range__tag shared-range__tag--elsewhere" data-shared-range-focus="now">
            {`${RANGE_NOT_USED} · ${now.note}`}
          </span>
        ) : here ? (
          <span className="shared-range__tag">All pages</span>
        ) : (
          <span className="shared-range__tag shared-range__tag--elsewhere" data-shared-range-elsewhere>
            {NOT_THIS_PAGE}
          </span>
        )}
        <span aria-hidden="true">▾</span>
      </button>
      <div
        ref={dialogRef}
        id={dialogId}
        className="shared-range__pop"
        role="dialog"
        aria-label="Date range for every page"
        hidden={!open}
      >
        {open ? (
          <>
            <p className="shared-range__eyebrow">Date range · used by every page</p>
            <div className="shared-range__presets" role="group" aria-label="Quick ranges">
              {RANGE_PRESETS.filter((preset) => preset.key !== "7dwork" || isWorkPage(location.pathname) || set?.preset === "7dwork").map((preset) => (
                <button
                  key={preset.key}
                  type="button"
                  className="v69-chip"
                  aria-pressed={pending === preset.key}
                  onClick={() => {
                    setPending(preset.key);
                    setError(null);
                  }}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            {pending === "custom" ? (
              <div className="shared-range__custom">
                <label>
                  From <input type="date" value={first} onChange={(e) => setFirst(e.target.value)} />
                </label>
                <label>
                  to (included) <input type="date" value={last} onChange={(e) => setLast(e.target.value)} />
                </label>
              </div>
            ) : null}
            <details className="shared-range__earlier" open={earlier} onToggle={(e) => setEarlier(e.currentTarget.open)}>
              <summary>View an earlier point in time</summary>
              <label>
                As known at{" "}
                <input type="datetime-local" step={1} value={cutoff} onChange={(e) => setCutoff(e.target.value)} />
              </label>
              <p className="shared-range__note">Every page then shows what AssetOps knew at that moment, until you return to latest.</p>
            </details>
            <p className="shared-range__note">
              One range for the whole app. Left-menu links keep it, and the page address holds it, so a copied link opens
              exactly this view. Days and times are UTC.
            </p>
            {error === null ? null : (
              <p className="shared-range__error" role="alert">
                {error}
              </p>
            )}
            <div className="shared-range__actions">
              <button type="button" className="v69-chip" onClick={apply}>
                Apply
              </button>
              <button type="button" className="shared-range__cancel" onClick={() => close(true)}>
                Cancel
              </button>
            </div>
          </>
        ) : null}
      </div>
      <p className="shared-range__live" aria-live="polite" data-shared-range-live>
        {announcement}
      </p>
    </div>
  );
}
