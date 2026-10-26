/**
 * W5-03b E4: the EV Site Health page body (v6.9 `ev-health`, `index.html:689-691`), from the selected `/ev/health`
 * depth read (`.agent/W5-03-build-spec.md` E4 card, literal ledger, the W5-03b pre-flight E4 correction and
 * `.agent/W5-03b-ui-preflight-rulings.md` points 2 and 5-8).
 *
 * Composition: optional currentness notice (R15), one card per selected connector then `Stationary battery`, the
 * sole `Condition and evidence` panel, then the condition notice (R16). No completed session proves hardware health,
 * no Site-meter row claims a respected power limit, and the frame mounts no S7 Data sources panel (R60 withdrawn).
 *
 * MOCK DEVIATION (D4) R95: connector cards use the selected Foundation labels, not the mock `Connector 1/2`.
 * MOCK DEVIATION (D2) R96: one card per selected connector (zero, one or more), then the battery card.
 * MOCK DEVIATION (D4) R57: card notes carry the selected fault-record count or the honest no-assessment note.
 * MOCK DEVIATION (D1) R56: the battery is always `Unknown` with the Foundation limitation, never `Not applicable`.
 * MOCK DEVIATION (D4) R59: a selected Site meter says `Power limit not assessed from selected samples`.
 * MOCK DEVIATION (D2) R58: a selected non-fault connector adds a third, no-assessment table row.
 * MOCK DEVIATION (D1) R97: a meter without a selected Site-import role has no Site-meter row.
 * MOCK DEVIATION (D4) R103: the page subtitle is the neutral `Health · site-level asset-condition summary` (`V69Layout.tsx`
 * `SITE_SCREEN_DESCRIPTIONS.health`), not the mock `2 × 60 kW connectors · 80 kW site limit · no stationary battery`.
 * MOCK DEVIATION (D2) R15/R16: the amber currentness notice above the cards and the condition notice below the table.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useReportSelectedWindow } from "./evSelectedWindow";
import { DataTable, MetricCard, MetricCards, Notice, Panel } from "../ui";
import { type ColdRead, type ColdWindowQuery, coldWindowSearch } from "./coldAssessmentClient";
import { EvDepthRefusal } from "./EvAvailability";
import { type EvDepthClient, type EvDepthWindow, type EvHealthRead, type EvHealthRow, depthStateNotice } from "./evDepthClient";
import "./evHealthDepth.css";

export const HEALTH_LOADING = "Loading the site's charger condition read.";
export const HEALTH_EMPTY = "No charger condition observation is available for this window.";
export const HEALTH_CONDITION_NOTICE =
  "Session and fault records show what was observed at each connector. They do not establish charger condition or diagnose a fault's cause.";
export const BATTERY_LABEL = "Stationary battery";
export const CONNECTOR_UNKNOWN_NOTE = "No charger condition assessment";
export const FAULT_ASSESSMENT = "Session interruption; hardware fault not established";
export const METER_ASSESSMENT = "Power limit not assessed from selected samples";
export const CONNECTOR_NO_ASSESSMENT = "No connector condition assessment";
export const CONNECTOR_NEXT = "Diagnostic event + witnessed session";
export const METER_NEXT = "Continuous coverage for interval-wide claims";
export const HEALTH_TABLE_HEADING_ID = "ev-health-condition-heading";

/** Ruling 5: the selected fault-record count (distinct selected fault IDs), never a session count. */
export const faultNote = (n: number) =>
  n === 1 ? "1 selected fault record; cause not diagnosed" : `${n} selected fault records; cause not diagnosed`;

const isFault = (row: EvHealthRow) => row.kind === "CONNECTOR" && row.condition_state === "NEEDS_INVESTIGATION";

/** Ruling 7: fault connectors, then selected Site meters, then non-fault connectors, each in DTO order. */
export function conditionRows(rows: EvHealthRow[]): EvHealthRow[] {
  return [
    ...rows.filter(isFault),
    ...rows.filter((row) => row.kind === "SITE_METER"),
    ...rows.filter((row) => row.kind === "CONNECTOR" && !isFault(row)),
  ];
}

/** The Sessions list with the read's echoed window, only when that window is a returned pair (ruling 5). */
export function sessionsHref(sessionsPath: string, window: EvDepthWindow): string | null {
  if (window.from === null || window.to === null) return null;
  return `${sessionsPath}${coldWindowSearch({ from: window.from, to: window.to, known_at: window.known_at })}`;
}

function useHealthRead(client: EvDepthClient, siteCode: string, window: ColdWindowQuery, attempt: number) {
  const key = `${siteCode}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}|${attempt}`;
  const [state, setState] = useState<{ key: string; value: ColdRead<EvHealthRead> } | null>(null);
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

function AssetCell({ row }: { row: EvHealthRow }) {
  return (
    <>
      {row.label}
      <span className="ev-health-ref" data-vocabulary-exempt="source-reference" data-ev-health-asset-id="">
        {row.asset_id}
      </span>
    </>
  );
}

function AssessmentCell({ row, sessions }: { row: EvHealthRow; sessions: string | null }) {
  const words = row.kind === "SITE_METER" ? METER_ASSESSMENT : isFault(row) ? FAULT_ASSESSMENT : CONNECTOR_NO_ASSESSMENT;
  return (
    <>
      {words}
      {row.session_id === null ? null : (
        <>
          <span className="ev-health-ref" data-vocabulary-exempt="source-reference" data-ev-health-session="">
            {`Session ${row.session_id}`}
          </span>
          {sessions === null ? null : (
            <>
              {" "}
              <Link to={sessions} data-ev-health-open-sessions="">
                Open Sessions →
              </Link>
            </>
          )}
        </>
      )}
    </>
  );
}

function HealthBody({ read, sessionsPath }: { read: EvHealthRead; sessionsPath: string }) {
  const state = read.selection.state;
  const notice = depthStateNotice(state);
  const connectors = read.health.rows.filter((row) => row.kind === "CONNECTOR");
  const table = conditionRows(read.health.rows);
  const sessions = sessionsHref(sessionsPath, read.window);
  return (
    <>
      {notice === null ? null : <Notice data={{ "data-ev-depth-state-notice": state }}>{notice}</Notice>}
      <MetricCards columns={3} label="Charger condition">
        {connectors.map((row) => (
          <MetricCard
            key={row.asset_id}
            assessment
            label={row.label}
            value={isFault(row) ? "Needs attention" : "Unknown"}
            note={isFault(row) ? faultNote(row.evidence_ids.length) : CONNECTOR_UNKNOWN_NOTE}
            tone={isFault(row) ? "amber" : "muted"}
            link={sessions === null ? undefined : <Link to={sessions}>View detail →</Link>}
            data={{ "data-ev-health-card": row.asset_id }}
          />
        ))}
        {/* The mock battery card is a plain (non-assessment) metric with a large value; only its words change (R56). */}
        <MetricCard
          label={BATTERY_LABEL}
          value="Unknown"
          note={read.health.battery.limitation}
          tone="muted"
          data={{ "data-ev-health-card": "battery" }}
        />
      </MetricCards>
      <Panel heading="Condition and evidence" headingId={HEALTH_TABLE_HEADING_ID} className="ev-health-condition">
        {connectors.length === 0 ? (
          <p className="not-available-yet" data-ev-health-empty="">
            {HEALTH_EMPTY}
          </p>
        ) : null}
        {table.length === 0 ? null : (
          <DataTable labelledBy={HEALTH_TABLE_HEADING_ID} stickyFirstColumn>
            <thead>
              <tr>
                <th scope="col">Asset</th>
                <th scope="col">Supported assessment</th>
                <th scope="col">Next evidence</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row) => (
                <tr key={row.asset_id} data-ev-health-row={row.kind === "SITE_METER" ? "meter" : isFault(row) ? "fault" : "connector"}>
                  <th scope="row">
                    <AssetCell row={row} />
                  </th>
                  <td>
                    <AssessmentCell row={row} sessions={sessions} />
                  </td>
                  <td>{row.kind === "SITE_METER" ? METER_NEXT : CONNECTOR_NEXT}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>
      <Notice data={{ "data-ev-health-condition-notice": "" }}>{HEALTH_CONDITION_NOTICE}</Notice>
    </>
  );
}

export interface EvHealthDepthProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  /** The address window; a bare route reads with no window and the server selects and echoes one (ruling 2). */
  window: ColdWindowQuery;
  client: EvDepthClient;
  /** The EV Sessions UI path (no query). */
  sessionsPath: string;
}

export function EvHealthDepth({ siteCode, window, client, sessionsPath }: EvHealthDepthProps) {
  const [attempt, setAttempt] = useState(0);
  const read = useHealthRead(client, siteCode, window, attempt);
  useReportSelectedWindow(read !== null && read.status === "loaded" ? read.value : null);
  if (read === null) return <p className="prose">{HEALTH_LOADING}</p>;
  if (read.status !== "loaded") {
    return <EvDepthRefusal read={read} window={window} label="Charger condition" panel={{ heading: "Condition and evidence", headingId: HEALTH_TABLE_HEADING_ID }} onRetry={() => setAttempt((n) => n + 1)} />;
  }
  return <HealthBody read={read.value} sessionsPath={sessionsPath} />;
}
