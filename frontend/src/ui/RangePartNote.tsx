/**
 * IA-P P0 (spec-period.md P.9, D-IAP.24): a block fed by a capped read says which part of the range it shows, in the
 * bar's words. It renders only when the window differs from the range (a range of 31 days or fewer shows nothing).
 */
import { FOCUS_INSIDE, focusSpanLabel } from "./rangeFocus";
import { capWindow, type DayRange } from "./sharedRange";

export function RangePartNote({ range }: { range: DayRange | null }) {
  if (range === null) return null;
  const window = capWindow(range);
  if (window.from === range.from) return null;
  return (
    <p className="range-part" role="note">
      {`Showing ${focusSpanLabel(window.from, window.to)} ${FOCUS_INSIDE}`}
    </p>
  );
}
