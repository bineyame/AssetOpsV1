/**
 * W5-01a C3: the cold Site Health page body (v6.9 `cold-health`), from the selected `/cold/health` depth read
 * (`.agent/W5-01-build-spec.md` literal ledger, C3 card, C3 Health DTO rendering and readiness pass 3).
 *
 * The server owns every condition string: card notes, observations and next evidence are the C1 `health.rows`
 * strings rendered verbatim. The UI maps only `condition_state` to the card value word. No value is a green or
 * otherwise positive physical condition; gateway contact never decides any of it.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DataTable, MetricCard, MetricCards, Notice, Panel } from "../ui";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import type { ColdDepthClient, ColdHealthCondition, ColdHealthRead, ColdHealthRow } from "./ColdDepthClient";
import { COLD_DEPTH_MALFORMED, COLD_DEPTH_REFUSAL_HEADING, COLD_DEPTH_STATE_NOTICE, COLD_DEPTH_UNREACHABLE } from "./ColdCooling";
import { type ColdSiteRoutes, RequestedWindowBar, SelectedWindowBar, coldUiHref } from "./coldSiteViews";

export const HEALTH_LOADING = "Loading the site's equipment condition read.";
export const HEALTH_EMPTY = "No condition observation is available for this window.";
/**
 * C3 condition notice (closure 2). Under Architect review: this one constant is the only place the sentence lives.
 */
export const HEALTH_CONDITION_NOTICE =
  "These records show what was observed at the selected assets. They do not establish physical equipment condition or diagnose a failed part.";

/** C3 card value by `condition_state` (`Needs attention` is the v6.9 `cold-health` card word). */
export const HEALTH_CARD_VALUE: Record<ColdHealthCondition, string> = {
  NEEDS_INVESTIGATION: "Needs attention",
  LIMITED: "Limited",
  UNKNOWN: "Unknown",
  NOT_CONFIGURED: "Not configured",
};

export const HEALTH_TABLE_HEADING_ID = "cold-health-condition-heading";

function useHealthRead(client: ColdDepthClient, siteCode: string, window: ColdWindowQuery, attempt: number) {
  const key = `${siteCode}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}|${attempt}`;
  const [state, setState] = useState<{ key: string; value: ColdRead<ColdHealthRead> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.getHealth(siteCode, window).then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // The key names exactly what is read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state !== null && state.key === key ? state.value : null;
}

function HealthRefusal({ read, onRetry }: { read: Exclude<ColdRead<ColdHealthRead>, { status: "loaded" }>; onRetry: () => void }) {
  return (
    <div className="page-refusal" role="status" data-page-refusal="cold-depth">
      <p className="page-refusal__title">
        <strong>{COLD_DEPTH_REFUSAL_HEADING}</strong>
      </p>
      {read.status === "refused" ? (
        <p data-cold-depth-error>
          <code data-vocabulary-exempt="source-reference">{read.code}</code>
          {read.message === null ? null : <> {read.message}</>}
        </p>
      ) : (
        <p data-cold-depth-error>{read.message === null ? COLD_DEPTH_UNREACHABLE : COLD_DEPTH_MALFORMED}</p>
      )}
      <button type="button" className="button" data-cold-retry onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

const assetName = (asset: ColdHealthRow["assets"][number]) => asset.display_name ?? asset.asset_code;

/** C3 Asset cell rule, in order of precedence. */
function AssetCell({ row }: { row: ColdHealthRow }) {
  if (row.asset_id !== null) {
    const match = row.assets.find((asset) => asset.asset_id === row.asset_id);
    return (
      <>
        {match === undefined ? null : <>{assetName(match)} </>}
        <code data-vocabulary-exempt="source-reference" data-health-asset-id>
          {row.asset_id}
        </code>
      </>
    );
  }
  if (row.assets.length > 0) return <>{row.assets.map(assetName).join(", ")}</>;
  return <>{row.label}</>;
}

/** The empty sentence shows only when no row cites evidence and no row is `NOT_CONFIGURED`. */
export function healthEmpty(rows: ColdHealthRow[]): boolean {
  return rows.every((row) => row.evidence_ids.length === 0 && row.condition_state !== "NOT_CONFIGURED");
}

function HealthBody({ read, routes }: { read: ColdHealthRead; routes: ColdSiteRoutes }) {
  const rows = read.health.rows;
  const state = read.selection.state;
  return (
    <>
      <SelectedWindowBar read={read} />
      {state === "CURRENT" ? null : <Notice data={{ "data-health-state-notice": state }}>{COLD_DEPTH_STATE_NOTICE[state]}</Notice>}
      <MetricCards columns={3} label="Equipment condition">
        {rows.map((row) => {
          const href = coldUiHref(row.link, routes);
          return (
            <MetricCard
              key={row.kind}
              word
              label={href === null ? row.label : <Link to={href}>{row.label}</Link>}
              value={HEALTH_CARD_VALUE[row.condition_state]}
              note={row.limitation}
              tone={row.condition_state === "NEEDS_INVESTIGATION" ? "amber" : undefined}
              data={{ "data-health-card": row.kind }}
            />
          );
        })}
      </MetricCards>
      <Panel heading="Condition and evidence" headingId={HEALTH_TABLE_HEADING_ID}>
        {healthEmpty(rows) ? (
          <p className="not-available-yet" data-health-empty>
            {HEALTH_EMPTY}
          </p>
        ) : null}
        <DataTable labelledBy={HEALTH_TABLE_HEADING_ID}>
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Supported assessment</th>
              <th scope="col">Next evidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.kind} data-health-row={row.kind}>
                <th scope="row">
                  <AssetCell row={row} />
                </th>
                <td>{row.observation}</td>
                <td>{row.next_evidence}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
      <Notice data={{ "data-health-condition-notice": "" }}>{HEALTH_CONDITION_NOTICE}</Notice>
    </>
  );
}

export interface ColdHealthDepthProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  window: ColdWindowQuery;
  client: ColdDepthClient;
  routes: ColdSiteRoutes;
}

/** The cold Health condition cards, `Condition and evidence` and the condition notice (the frame adds the S7 Data sources panel). */
export function ColdHealthDepth({ siteCode, window, client, routes }: ColdHealthDepthProps) {
  const [attempt, setAttempt] = useState(0);
  const read = useHealthRead(client, siteCode, window, attempt);
  if (read === null) return <p className="prose">{HEALTH_LOADING}</p>;
  if (read.status !== "loaded") {
    return (
      <>
        <RequestedWindowBar window={window} refusal={{ sentence: COLD_DEPTH_REFUSAL_HEADING, retry: true, key: read.status === "refused" && read.httpStatus === 422 ? "invalid-window" : "unavailable" }} />
        <HealthRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      </>
    );
  }
  return <HealthBody read={read.value} routes={routes} />;
}
