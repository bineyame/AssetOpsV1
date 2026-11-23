/**
 * IA-P P0 (spec-period.md P.9, D-IAP.24): a block fed by a capped read says which part of the range it shows, in the
 * bar's words. It renders only when the window differs from the range (a range of 31 days or fewer shows nothing).
 */
import { FOCUS_INSIDE, focusSpanLabel } from "./rangeFocus";
import { capWindow, type DayRange } from "./sharedRange";

/** The note's words, or null when the window is the whole range (IA-P P4b: also the Sites list's column note). */
export function rangePartWords(range: DayRange | null): string | null {
  if (range === null) return null;
  const window = capWindow(range);
  if (window.from === range.from) return null;
  return `Showing ${focusSpanLabel(window.from, window.to)} ${FOCUS_INSIDE}`;
}

export function RangePartNote({ range }: { range: DayRange | null }) {
  const words = rangePartWords(range);
  if (words === null) return null;
  return (
    <p className="range-part" role="note">
      {words}
    </p>
  );
}
