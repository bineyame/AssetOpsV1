/**
 * SR-2 (proposal 2026-11-10 "Item 12.5", SR.3 "Finer views inside the range"; v71 `portfolio-tabs.html` Change 0b):
 * the one day picker for a page that shows one day inside the shared range (the Kobo/Kisiwa board, Dispatch, the
 * claim limit, the Service hour's day). It is the only place besides the shell bar with a date input
 * (`tools/checks/page-range-forms.ps1` exempts it).
 *
 * - It offers the days of the shared range (`min`/`max`) and says which day is shown: "Day shown: 8 Nov (inside
 *   2 Nov – 8 Nov)".
 * - It tells the shell the day it shows, so the top bar says "Day shown" or "range not used", never "All pages".
 * - A day outside the range (an edited or old link) is still the day shown, said in words, with a "Show 8 Nov"
 *   button that widens the shared range to include it. The page never changes the range without saying so.
 *
 * MOCK DEVIATION SR-2-1: SR.3 says a `day` outside the range shows the last day of the range instead. The page keeps
 *   the day its address names, so every old `date=` story link reads exactly the day (and the API request) it read
 *   before; the line says the day is outside the range.
 * MOCK DEVIATION SR-2-2: with a range and no `day`, the page shows the day its read serves by default (the latest
 *   day) rather than the range's last day, so an address's API request is unchanged; the line names the day shown.
 */
import { type InputHTMLAttributes } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";

import { formatDay } from "./time";
import { useDeclareRangeFocus } from "./rangeFocus";
import { dayInRange, rangeParams, useSharedRange, validDay, widenToDay } from "./sharedRange";

const shortDay = (day: string): string => formatDay(`${day}T00:00:00Z`, { year: false });

export interface FocusPickerProps {
  /** The day the page shows (`YYYY-MM-DD`), or `null` while it is not known yet. */
  day: string | null;
  /** The visible label of the input. */
  label?: string;
  labelClassName?: string;
  /** The input's own attributes (value, onChange, class, data attributes). `type`, `min` and `max` are set here. */
  inputProps: Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "min" | "max"> & Record<`data-${string}`, unknown>;
}

export function FocusPicker({ day, label = "Day", labelClassName = "dispatch-day__label", inputProps }: FocusPickerProps) {
  const state = useSharedRange();
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const shown = day !== null && validDay(day) ? day : null;
  useDeclareRangeFocus(shown);
  const range = state.status === "set" ? state : null;
  const inside = range !== null && shown !== null && dayInRange(shown, range);
  const widen = () => {
    if (range === null || shown === null) return;
    const next = new URLSearchParams(params);
    for (const [key, value] of rangeParams({ ...widenToDay(range, shown), known_at: range.known_at })) next.set(key, value);
    navigate({ pathname: location.pathname, search: `?${next.toString()}` }, { state: location.state });
  };
  return (
    <>
      <label className={labelClassName}>
        <span>{label}</span>
        <input {...inputProps} type="date" min={range?.from} max={range?.to} />
      </label>
      {range === null || shown === null ? null : inside ? (
        <span className="focus-picker__line" data-focus-picker="inside">
          Day shown: {shortDay(shown)} (inside {shortDay(range.from)} – {shortDay(range.to)})
        </span>
      ) : (
        <span className="focus-picker__line" data-focus-picker="outside">
          {shortDay(shown)} is outside the date range ({shortDay(range.from)} – {shortDay(range.to)}), so this page does
          not use the range.{" "}
          <button type="button" className="button" onClick={widen} data-focus-picker-widen>
            Show {shortDay(shown)}
          </button>
        </span>
      )}
    </>
  );
}
