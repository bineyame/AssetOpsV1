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
}: {
  history: RunHistory;
  offset: number;
  site: SiteDetailResult | null;
}) {
  const binding = bindDrawing(history.drawing_context, site);

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
        <div data-drawing-bound={binding.site.site_id}>
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
