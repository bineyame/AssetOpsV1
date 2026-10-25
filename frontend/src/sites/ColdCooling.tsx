/**
 * W5-01a C2: the cold Site Cooling page body (v6.9 `cooling`), from the selected `/cold/cooling` depth read
 * (`.agent/W5-01-build-spec.md` literal ledger, C2 card, C2 state matrix and readiness pass 3).
 *
 * The W2 selected start chain does not establish an ordered recovery, so the four cards never show a measured
 * recovery time or difference; `Recovery curves` lists the selected first observations only (no chart).
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AttentionList, Badge, DataTable, MetricCard, MetricCards, Notice, Panel, StatusBar } from "../ui";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import {
  type ColdCoolingRead,
  type ColdDepthClient,
  type ColdDepthState,
  type CoolingContextRow,
  type CoolingRecoveryState,
  coolingCardLabels,
} from "./ColdDepthClient";
import { CoolingObservationGraphic } from "./coldDepthGraphics";
import { type ColdSiteRoutes, RequestedWindowBar, SelectedWindowBar, coldUiHref, recordLabel, utcClock } from "./coldSiteViews";

export const COOLING_LOADING = "Loading the site's cooling read.";
export const COLD_DEPTH_REFUSAL_HEADING = "Cold depth unavailable";
export const COLD_DEPTH_UNREACHABLE = "The cold depth read could not be reached.";
export const COLD_DEPTH_MALFORMED = "The cold depth read answered in an unexpected shape.";
export const COOLING_MATCH_NOT_ESTABLISHED = "Not established";
export const COOLING_EMPTY = "No accepted recovery sequence in this window.";
export const COOLING_NOTICE =
  "These records do not establish cooling degradation or compressor failure. Record loading and door activity and compare a later recovery under similar conditions.";

/** Shared-ledger state sentences; `CURRENT` renders none. */
export const COLD_DEPTH_STATE_NOTICE: Record<Exclude<ColdDepthState, "CURRENT">, string> = {
  PENDING_RECOMPUTE: "New evidence is waiting to be assessed. Earlier selected observations are shown, not a current conclusion.",
  HISTORICAL: "Read at an earlier evidence cutoff; newer committed evidence exists.",
  STALE_SOURCE: "The selected source is stale for this window.",
  UNKNOWN: "No selected cold assessment covers this window yet.",
};

/**
 * post-W6 W5-cold R336 (B14-07): with selected rows on screen, the UNKNOWN notice says what those rows are. The claim
 * is unchanged (no assessment covers the window); other states, and UNKNOWN with no rows, keep the ledger sentence.
 */
export const COLD_DEPTH_UNKNOWN_WITH_ROWS =
  "No selected cold assessment covers this window. The rows below are accepted records only, not an assessed conclusion.";

export function coldDepthStateNotice(state: Exclude<ColdDepthState, "CURRENT">, hasRows: boolean): string {
  return state === "UNKNOWN" && hasRows ? COLD_DEPTH_UNKNOWN_WITH_ROWS : COLD_DEPTH_STATE_NOTICE[state];
}

/** The C2 literal state matrix. */
export const COOLING_STATE_COPY: Record<CoolingRecoveryState, { status: string; confidence: string; subtitle: string; comparable: string }> = {
  LIMITED: {
    status: "Comparison limited",
    confidence: "Low",
    subtitle: "Observed cooling response is incomplete; ambient, loading and defrost context is missing.",
    comparable: "Ambient, loading and defrost records missing",
  },
  CONTRADICTORY: {
    status: "Comparison contradictory",
    confidence: "Unknown",
    subtitle: "Selected cooling observations conflict; no recovery comparison is supported.",
    comparable: "Conflicting selected observations prevent a comparison",
  },
  UNKNOWN: {
    status: "Comparison unknown",
    confidence: "Unknown",
    subtitle: "No selected cooling assessment establishes a recovery comparison for this window.",
    comparable: "No selected comparison basis",
  },
};

/** Q-C2-2 `{d}`: under 60 s `{s} s`; otherwise `{m} min`, or `{m} min {r} s`. */
export function doorDuration(seconds: number): string {
  if (seconds < 60) return `${seconds} s`;
  const m = Math.floor(seconds / 60);
  const r = seconds % 60;
  return r === 0 ? `${m} min` : `${m} min ${r} s`;
}

/**
 * post-W6 W5-cold B14-04 (closes the cold instance of R309; W4 Q1/Q2 shared `status-tone--*` classes): tones from the
 * stored enums only, always beside the word. Recovery LIMITED/CONTRADICTORY and Confidence Low are amber; UNKNOWN and
 * Confidence Unknown are neutral; the context Match `Not established` is amber, as the mock's Limited/Not excluded.
 */
export const COOLING_RECOVERY_TONE: Record<CoolingRecoveryState, "amber" | "neutral"> = { LIMITED: "amber", CONTRADICTORY: "amber", UNKNOWN: "neutral" };
export const coolingConfidenceTone = (confidence: string): "amber" | "neutral" => (confidence === "Low" ? "amber" : "neutral");
export const COOLING_MATCH_TONE = "amber" as const;

/** R336: cooling shows selected rows when it has selected points or an Observed context row. */
export function coolingHasRows(cooling: { selected_points: readonly unknown[]; context: readonly CoolingContextRow[] }): boolean {
  return cooling.selected_points.length > 0 || cooling.context.some((row) => row.state === "Observed");
}

/** Q-C2-2 Evidence cell for one context row; no evidence IDs are printed. */
export function contextEvidence(row: CoolingContextRow): string {
  const observed = row.state === "Observed";
  switch (row.label) {
    case "Ambient temperature":
      return "Not selected by the cooling assessment";
    case "Power availability": {
      const n = row.evidence_ids.length;
      if (!observed) return "No accepted grid power record";
      return n === 1 ? "1 accepted grid power record" : `${n} accepted grid power records`;
    }
    case "Door-open duration":
      return observed && row.duration_seconds !== null ? `Door open for ${doorDuration(row.duration_seconds)}` : "No matched door open/close pair";
    case "Loading / batch":
      return "No loading record role";
    case "Defrost":
      return "No defrost record role";
  }
}

function useCoolingRead(client: ColdDepthClient, siteCode: string, window: ColdWindowQuery, attempt: number) {
  const key = `${siteCode}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}|${attempt}`;
  const [state, setState] = useState<{ key: string; value: ColdRead<ColdCoolingRead> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.getCooling(siteCode, window).then((value) => {
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

function LinkOrText({ href, children, data }: { href: string | null; children: string; data: Record<string, string> }) {
  return href === null ? (
    <span {...data}>{children}</span>
  ) : (
    <Link to={href} {...data}>
      {children}
    </Link>
  );
}

function CoolingRefusal({ read, onRetry }: { read: Exclude<ColdRead<ColdCoolingRead>, { status: "loaded" }>; onRetry: () => void }) {
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

const POINTS_HEADING_ID = "cold-cooling-recovery-heading";
const CONTEXT_HEADING_ID = "cold-cooling-context-heading";

function CoolingBody({ read, routes }: { read: ColdCoolingRead; routes: ColdSiteRoutes }) {
  const cooling = read.cooling;
  const copy = COOLING_STATE_COPY[cooling.recovery_state];
  const labels = coolingCardLabels(cooling.policy_high_deg_c);
  const state = read.selection.state;
  return (
    <>
      <SelectedWindowBar read={read} />
      <StatusBar
        label="Cooling comparison"
        action={
          <LinkOrText href={coldUiHref(read.links.temperature, routes)} data={{ "data-cooling-basis": "" }}>
            Inspect recovery basis →
          </LinkOrText>
        }
      >
        <Badge tone="neutral" className={`status-tone--${COOLING_RECOVERY_TONE[cooling.recovery_state]}`}>{copy.status}</Badge>{" "}
        <Badge tone="neutral" className={`status-tone--${coolingConfidenceTone(copy.confidence)}`}>{`Confidence: ${copy.confidence}`}</Badge> {copy.subtitle}
      </StatusBar>
      {state === "CURRENT" ? null : <Notice data={{ "data-cooling-state-notice": state }}>{coldDepthStateNotice(state, coolingHasRows(cooling))}</Notice>}
      <MetricCards label="Cooling comparison">
        <MetricCard word label={labels.usual} value="Unknown" note="No matched earlier window" data={{ "data-cooling-card": "usual" }} />
        <MetricCard word label={labels.current} value="Not established" note="No ordered compressor-to-policy recovery assessment" data={{ "data-cooling-card": "current" }} />
        <MetricCard word label="Difference" value="Unknown" note="A comparison is not supported" data={{ "data-cooling-card": "difference" }} />
        <MetricCard word label="Comparable?" value="Not yet" note={copy.comparable} data={{ "data-cooling-card": "comparable" }} />
      </MetricCards>
      <div className="panel-pair">
        <Panel heading="Recovery curves" headingId={POINTS_HEADING_ID} description="Selected first observations only; not a recovery curve.">
          {/* Codex retrospective Q-C2-3: selected marks on lanes, never a curve; the table is the source detail. */}
          <CoolingObservationGraphic from={read.window.from} to={read.window.to} points={cooling.selected_points} label="Selected first observations by step" />
          <p className="not-available-yet" data-cooling-empty>
            {COOLING_EMPTY}
          </p>
          {cooling.selected_points.length === 0 ? null : (
            <DataTable labelledBy={POINTS_HEADING_ID}>
              <thead>
                <tr>
                  <th scope="col">Step</th>
                  <th scope="col">Time (UTC)</th>
                  <th scope="col">Evidence</th>
                </tr>
              </thead>
              <tbody>
                {cooling.selected_points.map((point, index) => (
                  <tr key={`${point.role}|${point.source_time}|${index}`} data-cooling-point={point.role}>
                    <th scope="row">{recordLabel(point.role)}</th>
                    <td>{utcClock(point.source_time)}</td>
                    <td>
                      <code data-vocabulary-exempt="source-reference">{point.evidence_ids.join(", ")}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
        </Panel>
        <Panel heading="Context normalization" headingId={CONTEXT_HEADING_ID} className="cold-cooling-context">
          <DataTable labelledBy={CONTEXT_HEADING_ID}>
            <thead>
              <tr>
                <th scope="col">Factor</th>
                <th scope="col">Evidence</th>
                <th scope="col">Match</th>
              </tr>
            </thead>
            <tbody>
              {cooling.context.map((row) => (
                <tr key={row.label} data-cooling-context={row.label}>
                  <th scope="row">{row.label}</th>
                  <td>{contextEvidence(row)}</td>
                  <td>
                    {/* Codex retrospective Q-C2-2: no comparator is supported (CONTEXT_MISSING), so no factor is matched. */}
                    <Badge tone="neutral" className={`status-tone--${COOLING_MATCH_TONE}`}>{COOLING_MATCH_NOT_ESTABLISHED}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      </div>
      <Notice data={{ "data-cooling-notice": "" }}>{COOLING_NOTICE}</Notice>
      <Panel heading="Next best evidence" headingId="cold-cooling-next-heading">
        <AttentionList
          label="Next best evidence"
          items={[
            { key: "record", title: "Record a comparable recovery", body: "Keep load, door, ambient, defrost and cooling-energy records." },
            {
              key: "backup",
              title: "Inspect the backup sequence",
              body: null,
              action: (
                <LinkOrText href={coldUiHref(read.links.backup, routes)} data={{ "data-cooling-backup": "" }}>
                  Open Backup →
                </LinkOrText>
              ),
            },
          ]}
        />
      </Panel>
    </>
  );
}

export interface ColdCoolingProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  window: ColdWindowQuery;
  client: ColdDepthClient;
  routes: ColdSiteRoutes;
}

export function ColdCooling({ siteCode, window, client, routes }: ColdCoolingProps) {
  const [attempt, setAttempt] = useState(0);
  const read = useCoolingRead(client, siteCode, window, attempt);
  if (read === null) return <p className="prose">{COOLING_LOADING}</p>;
  if (read.status !== "loaded") {
    return (
      <>
        <RequestedWindowBar window={window} refusal={{ sentence: COLD_DEPTH_REFUSAL_HEADING, retry: true, key: read.status === "refused" && read.httpStatus === 422 ? "invalid-window" : "unavailable" }} />
        <CoolingRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      </>
    );
  }
  return <CoolingBody read={read.value} routes={routes} />;
}
