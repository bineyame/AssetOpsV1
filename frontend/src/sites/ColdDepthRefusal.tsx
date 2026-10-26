/**
 * Post-W6 recapture fix F2 (R244, B14-01): the shared refusal of the three cold depth pages (cooling, cold health,
 * cold scenarios), mirroring the EV depth refusal (`EvDepthRefusal`). A refused read keeps the page frame: the
 * requested-window line (never for an invalid window), the refusal strip, the page's panels with the one plain
 * sentence in the first and `Not assessed` in the rest, and the exact technical disclosure. A window refusal offers
 * the same page without the selected window (never a dead Retry); Reload shows only where retrying can help.
 */
import { Link, useLocation } from "react-router-dom";
import { MetricCard, MetricCards, Panel } from "../ui";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import { RefusalReferences, refusalText } from "./ColdAssessmentViews";
import { NOT_ASSESSED } from "./coldFormat";
import { RefusedStrip, RequestedWindowBar } from "./coldSiteViews";

export interface ColdDepthRefusalProps {
  read: Exclude<ColdRead<unknown>, { status: "loaded" }>;
  window: ColdWindowQuery;
  /** The strip's accessible name. */
  label: string;
  /** The page's tile labels, each `Not assessed`; omitted when the labels depend on the read. */
  tiles?: string[];
  /** The page's panels: the first carries the refusal sentence, the others say `Not assessed`. */
  panels: { heading: string; headingId: string; className?: string }[];
  /** The page's own sentences for a read with no answer / an answer of the wrong shape (a refusal uses the shared matrix). */
  unavailable: { unreachable: string; malformed: string };
  onRetry: () => void;
}

export function ColdDepthRefusal({ read, window, label, tiles, panels, unavailable, onRetry }: ColdDepthRefusalProps) {
  const location = useLocation();
  const shared = refusalText(read);
  const text = read.status === "unavailable" ? { ...shared, body: read.message === null ? unavailable.unreachable : unavailable.malformed } : shared;
  const windowRefusal = text.key === "invalid-window";
  const hasWindow = window.from !== null || window.to !== null;
  // The same page without the selected window, keeping the evidence cutoff.
  const correction =
    windowRefusal && hasWindow ? `${location.pathname}${window.known_at === null ? "" : `?known_at=${encodeURIComponent(window.known_at)}`}` : null;
  const recoverable = read.status === "unavailable" || read.httpStatus === 503 || read.httpStatus === 409;
  return (
    <div data-page-refusal="cold-depth">
      <RequestedWindowBar window={window} refusal={{ sentence: text.body, retry: false, key: text.key }} />
      <RefusedStrip label={label} title={text.title} />
      {tiles === undefined ? null : (
        <MetricCards label={`${label} tiles`}>
          {tiles.map((t) => (
            <MetricCard key={t} label={t} value={NOT_ASSESSED} tone="muted" word data={{ "data-cold-refused-card": t }} />
          ))}
        </MetricCards>
      )}
      {panels.map((panel, index) => (
        <Panel key={panel.headingId} heading={panel.heading} headingId={panel.headingId} className={panel.className}>
          {index === 0 ? (
            <>
              <p className="not-available-yet v69-chart-note" role="alert" data-panel-gap="cold-depth-refusal" data-cold-depth-error>
                {text.body}
              </p>
              <RefusalReferences read={read} window={window} />
            </>
          ) : (
            <p className="not-available-yet v69-chart-note" data-panel-gap="cold-depth-refusal">
              {NOT_ASSESSED}
            </p>
          )}
        </Panel>
      ))}
      {correction === null && !recoverable ? null : (
        <p className="ev-depth-refusal__actions" data-cold-depth-refusal-actions="">
          {correction === null ? null : (
            <Link to={correction} className="ev-depth-refusal__link" data-cold-depth-correction="">
              Read without a selected window
            </Link>
          )}
          {recoverable ? (
            <button type="button" className="button" data-cold-retry onClick={onRetry}>
              Reload
            </button>
          ) : null}
        </p>
      )}
    </div>
  );
}
