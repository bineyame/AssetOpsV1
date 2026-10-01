import { memo } from "react";

import { ConfiguredSingleLineDrawing } from "../sites/SiteSingleLineDiagram";
import type { SiteDetailResult } from "../sites/siteReadModel";
import { Panel } from "../ui";
import { bindDrawing, drawingSlots } from "./intervalDrawingModel";
import type {
  RunHistoryDrawingContext,
  RunHistoryInterval,
  RunHistorySample,
} from "./runHistory";

const HEADING_ID = "run-drawing-heading";

/**
 * The run-bound single line diagram at the selected boundary (T025d, C1).
 *
 * The Lab composes the values; the shared drawing only renders the slots it is
 * handed. When the Site read now is not the Foundation this run froze, or the
 * run's attachments cannot be confirmed, the drawing says it is unavailable
 * and why - the charts, the timeline and the control tables beside it are
 * unaffected, and no old value is put on a different diagram.
 */
export const IntervalDrawing = memo(function IntervalDrawing({
  drawingContext,
  offset,
  ended,
  samplesAt,
  samplesFrom,
  site,
  onKey,
}: {
  drawingContext: RunHistoryDrawingContext | null;
  /** The history cursor's boundary. */
  offset: number;
  /** The recorded interval that ended at `offset`, or null. */
  ended: RunHistoryInterval | null;
  /** The samples the boundary slice at `offset` holds. */
  samplesAt: RunHistorySample[];
  /** The samples the slice at the ended interval's decision boundary holds. */
  samplesFrom: RunHistorySample[];
  site: SiteDetailResult | null;
  /**
   * T025e: move the one history cursor. Arrow keys on the drawing step it a
   * recorded boundary back or forward; Home and End go to the first and the
   * last (End follows live). Lab-side: the shared drawing is not touched. A
   * stable callback, so a tick that leaves the cursor pinned leaves this
   * drawing's props - all per-boundary slice references - unchanged (AC11).
   */
  onKey?: (key: string) => boolean;
}) {
  const binding = bindDrawing(drawingContext, site);
  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (onKey !== undefined && onKey(event.key)) {
      event.preventDefault();
    }
  };
  const record = {
    intervals: ended === null ? [] : [ended],
    samples:
      samplesFrom === samplesAt ? samplesAt : [...samplesFrom, ...samplesAt],
  };

  return (
    <Panel
      heading="Single line diagram at the selected boundary"
      headingId={HEADING_ID}
    >
      <p className="run-cockpit__caption" data-drawing-boundary={offset}>
        {`History cursor at ${offset} min - the record, not the execution clock.`}
      </p>
      {binding.status === "unavailable" ? (
        <p data-drawing-unavailable={binding.code}>
          {`The drawing is unavailable for this run: ${binding.statement} The recorded values remain in the tables and charts.`}
        </p>
      ) : (
        <div
          data-drawing-bound={binding.site.site_id}
          tabIndex={onKey === undefined ? undefined : 0}
          aria-label="Single line diagram; arrow keys move the history cursor"
          onKeyDown={onKeyDown}
        >
          <ConfiguredSingleLineDrawing
            site={binding.site}
            slots={drawingSlots(binding, record, offset)}
            headingId={HEADING_ID}
            idPrefix="run-sld"
          />
        </div>
      )}
    </Panel>
  );
});
