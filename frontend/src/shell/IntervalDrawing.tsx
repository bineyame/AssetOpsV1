import { ConfiguredSingleLineDrawing } from "../sites/SiteSingleLineDiagram";
import type { SiteDetailResult } from "../sites/siteReadModel";
import { Panel } from "../ui";
import { bindDrawing, drawingSlots } from "./intervalDrawingModel";
import type { RunHistory } from "./runHistory";

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
export function IntervalDrawing({
  history,
  offset,
  site,
  onSelect,
}: {
  history: RunHistory;
  offset: number;
  site: SiteDetailResult | null;
  /**
   * T025e: move the one history cursor. Arrow keys on the drawing step it a
   * recorded boundary back or forward; Home and End go to the first and the
   * last (End follows live). Lab-side: the shared drawing is not touched.
   */
  onSelect?: (offset: number) => void;
}) {
  const binding = bindDrawing(history.drawing_context, site);
  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (onSelect === undefined) {
      return;
    }
    const offsets = history.boundaries.map((b) => b.offset_minutes);
    const at = offsets.indexOf(offset);
    const target =
      event.key === "ArrowLeft"
        ? offsets[Math.max(0, at - 1)]
        : event.key === "ArrowRight"
          ? offsets[Math.min(offsets.length - 1, at + 1)]
          : event.key === "Home"
            ? offsets[0]
            : event.key === "End"
              ? offsets[offsets.length - 1]
              : undefined;
    if (target !== undefined) {
      event.preventDefault();
      onSelect(target);
    }
  };

  return (
    <Panel heading="Single line diagram at the selected boundary" headingId={HEADING_ID}>
      <p data-drawing-boundary={offset}>
        {`Selected history boundary: ${offset} min. This is the history cursor, not the execution clock; moving it reads the record and executes nothing.`}
      </p>
      {binding.status === "unavailable" ? (
        <p data-drawing-unavailable={binding.code}>
          {`The drawing is unavailable for this run: ${binding.statement} The recorded values remain in the tables and charts.`}
        </p>
      ) : (
        <div
          data-drawing-bound={binding.site.site_id}
          tabIndex={onSelect === undefined ? undefined : 0}
          aria-label="Single line diagram; arrow keys move the history cursor"
          onKeyDown={onKeyDown}
        >
          <ConfiguredSingleLineDrawing
            site={binding.site}
            slots={drawingSlots(binding, history, offset)}
            headingId={HEADING_ID}
            idPrefix="run-sld"
          />
        </div>
      )}
    </Panel>
  );
}
