import { memo, useCallback, useRef } from "react";

import { DataTable, Fact, FactList, Panel } from "../ui";
import type { SiteDetailResult } from "../sites/siteReadModel";
import { HistoryCharts } from "./HistoryCharts";
import { HistoryTimeline } from "./HistoryTimeline";
import { IntervalDrawing } from "./IntervalDrawing";
import { IntervalInspection } from "./IntervalInspection";
import { completedIntervalAt } from "./intervalDrawingModel";
import type { BoundarySlice } from "./liveHistory";
import type { HeldHistory } from "./runFrameState";
import type { RunHistory, RunHistoryInterval, RunHistorySample } from "./runHistory";

/**
 * One exact value, shown exactly. Unlike the summary panels' `ExactQuantity`,
 * which shows a ratio as a rounded decimal with the exact text in its title,
 * an inspector's job is the exact text itself: a ratio is shown as the ratio,
 * with its decimal beside it only as a reading aid.
 */
function ExactQuantity({ value, unit }: { value: string | null; unit?: string }) {
  if (value === null) {
    return <>not available</>;
  }
  if (unit === "state") {
    return <span data-discrete={value}>{value}</span>;
  }
  const suffix = unit === undefined || unit === "" ? "" : ` ${unit}`;
  const ratio = /^(-?\d+)\/(\d+)$/.exec(value);
  const aid =
    ratio === null
      ? ""
      : ` (about ${(Number(ratio[1]) / Number(ratio[2])).toFixed(2)})`;
  return (
    <span data-exact={value}>
      {`${value}${suffix}${aid}`}
    </span>
  );
}

/**
 * The recorded cockpit (T025e AC9): the run-bound drawing beside the interval
 * inspection, the one history cursor, the day curves and the Applied timeline,
 * all at the history cursor's boundary and all read from the recorded history.
 *
 * Its geometry does not depend on the tick: before a boundary is recorded
 * every region is already laid out (the cursor disabled, the drawing and
 * inspection saying nothing is recorded yet, the curves' region reserved), so
 * the first recorded boundary fills regions rather than adding them. The
 * drawing, the inspection and the raw records are memoised on the boundary
 * slices (`HeldHistory.frame.slices`), so a tick that leaves the cursor pinned
 * re-renders only the cursor's slots, the charts and the timeline (AC11).
 */
export function HistoryCockpit({
  held,
  selected,
  behindLive = 0,
  lag = null,
  onSelect,
  onReturnToLive,
  timestepMinutes = null,
  site = null,
}: {
  held: HeldHistory | null;
  /**
   * T025e: the one history cursor's boundary, owned by the run page (live:
   * the last recorded boundary; pinned: the reader's). Null when none.
   */
  selected: number | null;
  /** Recorded boundaries after a pinned cursor; 0 while live. */
  behindLive?: number;
  /** The recorded count and the execution clock when the history lags it. */
  lag?: { recorded: number; clock: number } | null;
  onSelect: (offset: number) => void;
  onReturnToLive: () => void;
  timestepMinutes?: number | null;
  /**
   * T025d: the Site read for the run-bound drawing, or null while it is in
   * flight or not asked for. The drawing binds only if it is the Site and
   * Foundation version the run froze.
   */
  site?: SiteDetailResult | null;
}) {
  const loaded = held !== null && held.status === "loaded" ? held : null;
  const history = loaded === null ? null : loaded.history;
  const at = loaded === null || selected === null ? null : atCursor(loaded, selected);

  // Arrow keys on the drawing move the cursor. The handler is stable and
  // reads the latest boundaries through a ref, so it never breaks the
  // drawing's memo.
  const latest = useRef({ offsets: [] as number[], selected, onSelect });
  latest.current = {
    offsets: history === null ? [] : history.boundaries.map((b) => b.offset_minutes),
    selected,
    onSelect,
  };
  const onKey = useCallback((key: string): boolean => {
    const { offsets, selected: now, onSelect: select } = latest.current;
    if (offsets.length === 0 || now === null) {
      return false;
    }
    const index = offsets.indexOf(now);
    const target =
      key === "ArrowLeft"
        ? offsets[Math.max(0, index - 1)]
        : key === "ArrowRight"
          ? offsets[Math.min(offsets.length - 1, index + 1)]
          : key === "Home"
            ? offsets[0]
            : key === "End"
              ? offsets[offsets.length - 1]
              : undefined;
    if (target === undefined) {
      return false;
    }
    select(target);
    return true;
  }, []);

  return (
    <section
      className="run-cockpit__record"
      aria-labelledby="run-cockpit-heading"
      data-cockpit-record
    >
      <h2 id="run-cockpit-heading" className="run-cockpit__heading">
        Recorded history at the history cursor
      </h2>
      {held === null ? (
        <p className="run-cockpit__caption" data-history-reading>
          Reading the recorded history.
        </p>
      ) : held.status !== "loaded" ? (
        <p className="run-cockpit__caption" data-history-unavailable>
          The recorded history could not be read
          {held.status === "unavailable" && held.message !== null
            ? `: ${held.message}`
            : "."}
        </p>
      ) : null}
      <div className="run-cockpit__stage">
        <div className="run-cockpit__drawing">
          {history === null || at === null ? (
            <Panel
              heading="Single line diagram at the selected boundary"
              headingId="run-drawing-heading"
            >
              <p className="run-cockpit__caption" data-drawing-empty>
                No boundary is recorded yet; the drawing fills at the first one.
              </p>
            </Panel>
          ) : (
            <IntervalDrawing
              drawingContext={history.drawing_context}
              offset={at.offset}
              ended={at.ended}
              samplesAt={at.samplesAt}
              samplesFrom={at.samplesFrom}
              site={site}
              onKey={onKey}
            />
          )}
        </div>
        <div className="run-cockpit__inspection">
          {at === null ? (
            <Panel
              heading="Requested and accepted control"
              headingId="run-interval-control-heading"
            >
              <p className="run-cockpit__caption" data-interval-empty>
                No interval is recorded yet.
              </p>
            </Panel>
          ) : (
            <IntervalInspection interval={at.ended} offset={at.offset} />
          )}
        </div>
      </div>
      <HistoryCursor
        history={history}
        selected={selected}
        behindLive={behindLive}
        lag={lag}
        onSelect={onSelect}
        onReturnToLive={onReturnToLive}
      />
      <div className="run-cockpit__charts">
        {history === null || selected === null ? (
          <Panel heading="Recorded day curves" headingId="run-history-charts-heading">
            <p data-charts-empty>
              No boundary is recorded yet; the curves fill from the first one.
            </p>
          </Panel>
        ) : (
          <HistoryCharts
            history={history}
            timestepMinutes={timestepMinutes}
            selected={selected}
            onSelect={onSelect}
          />
        )}
      </div>
      <div className="run-cockpit__timeline">
        {history === null || selected === null ? (
          <Panel heading="Applied timeline" headingId="run-timeline-heading">
            <p data-timeline-empty="all">No boundary is recorded yet.</p>
          </Panel>
        ) : (
          <HistoryTimeline history={history} offset={selected} onSelect={onSelect} />
        )}
      </div>
    </section>
  );
}

interface AtCursor {
  offset: number;
  slice: BoundarySlice | null;
  ended: RunHistoryInterval | null;
  samplesAt: RunHistorySample[];
  samplesFrom: RunHistorySample[];
}

const NO_SAMPLES: RunHistorySample[] = [];

/**
 * What the cursor's boundary reads, by reference: its slice, the slice of the
 * boundary before it (which decided the interval that ended here), and that
 * interval. Every value is a row or array the held history already owns, so a
 * memoised consumer sees the same references until the cursor moves or a
 * whole read replaces the history.
 */
function atCursor(
  loaded: Extract<HeldHistory, { status: "loaded" }>,
  offset: number,
): AtCursor {
  const { history, frame } = loaded;
  const index = history.boundaries.findIndex((b) => b.offset_minutes === offset);
  const slice =
    index < 0 ? null : (frame.slices.get(history.boundaries[index].step_index) ?? null);
  const previous =
    index < 1
      ? null
      : (frame.slices.get(history.boundaries[index - 1].step_index) ?? null);
  const decidedBefore = previous === null ? null : previous.interval;
  const ended =
    decidedBefore !== null && decidedBefore.to_offset === offset
      ? decidedBefore
      : completedIntervalAt(history, offset);
  return {
    offset,
    slice,
    ended,
    samplesAt: slice === null ? NO_SAMPLES : slice.samples,
    samplesFrom: previous === null ? NO_SAMPLES : previous.samples,
  };
}

/**
 * The raw records at the cursor, for the page's closed disclosure (T025e
 * AC10). They follow the one cursor and are memoised on its boundary slice.
 */
export function HistoryRecordsAtCursor({
  held,
  selected,
}: {
  held: HeldHistory | null;
  selected: number | null;
}) {
  if (held === null || held.status !== "loaded" || selected === null) {
    return <p>No boundary is recorded, so there is no record to show.</p>;
  }
  const at = atCursor(held, selected);
  return <BoundaryRecords slice={at.slice} offset={selected} />;
}

/** The history's provenance and coverage, for a closed disclosure. */
export function HistoryFacts({ held }: { held: HeldHistory | null }) {
  if (held === null) {
    return (
      <Panel heading="Recorded history" headingId="run-history-heading">
        <p>Loading the recorded history.</p>
      </Panel>
    );
  }
  if (held.status !== "loaded") {
    return (
      <Panel heading="Recorded history" headingId="run-history-heading">
        <p>
          The recorded history could not be read
          {held.status === "unavailable" && held.message !== null
            ? `: ${held.message}`
            : "."}
        </p>
      </Panel>
    );
  }
  const history = held.history;
  return (
    <>
      <Panel heading="Recorded history" headingId="run-history-heading">
        <p data-history-source={history.source}>{history.statement}</p>
        {history.notes.map((note) => (
          <p key={note} data-history-note>
            {note}
          </p>
        ))}
        <FactList>
          <Fact term="Recorded boundaries">
            <span data-history-recorded>
              {`${history.boundaries_recorded} of ${history.boundaries_total}`}
            </span>
            {history.recorded_through_offset_minutes === null
              ? ""
              : `, through offset ${history.recorded_through_offset_minutes} min`}
          </Fact>
          <Fact term="History schema">
            {history.history_schema_version === null
              ? "none recorded"
              : String(history.history_schema_version)}
          </Fact>
          <Fact term="History digest">
            <code data-history-digest>{history.history_digest ?? "none"}</code>
          </Fact>
          {history.failure === null ? null : (
            <Fact term="Recorded failure">
              <span data-history-failure={history.failure.kind}>
                {`${history.failure.kind} at ${history.failure.subject}`}
                {history.failure.at_offset_minutes === null
                  ? ""
                  : `, offset ${history.failure.at_offset_minutes} min`}
              </span>
              {`: ${history.failure.statement}`}
            </Fact>
          )}
        </FactList>
      </Panel>

      <Panel
        heading="Recorded coverage"
        headingId="run-history-coverage-heading"
        flush
      >
        <DataTable labelledBy="run-history-coverage-heading">
          <thead>
            <tr>
              <th scope="col">Family</th>
              <th scope="col">Availability</th>
              <th scope="col">What it holds, or why not</th>
            </tr>
          </thead>
          <tbody>
            {history.coverage.map((entry) => (
              <tr
                key={entry.family}
                data-history-family={entry.family}
                data-availability={entry.availability}
              >
                <th scope="row">{entry.family}</th>
                <td>{entry.availability}</td>
                <td>{entry.statement}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </>
  );
}

/**
 * The one history cursor (T025e AC7), kept apart from the execution clock.
 *
 * The range selects a recorded boundary: an earlier one pins the cursor, the
 * last one (or `End`) follows live. Return to live has a reserved slot beside
 * the label, so pinning moves nothing; the lag statement has one too. Before
 * a boundary is recorded the cursor is present and disabled, so the first
 * recorded boundary adds nothing to the layout.
 */
function HistoryCursor({
  history,
  selected,
  behindLive,
  lag,
  onSelect,
  onReturnToLive,
}: {
  history: RunHistory | null;
  selected: number | null;
  behindLive: number;
  lag: { recorded: number; clock: number } | null;
  onSelect: (offset: number) => void;
  onReturnToLive: () => void;
}) {
  const boundaries = history === null ? [] : history.boundaries;
  const offsets = boundaries.map((b) => b.offset_minutes);
  const index = selected === null ? 0 : Math.max(0, offsets.indexOf(selected));
  const boundary = boundaries[index];
  const empty = selected === null || offsets.length === 0;
  const when = boundary === undefined ? "" : boundary.simulation_time;
  return (
    <div
      className="history-cursor"
      data-history-cursor={behindLive > 0 ? "pinned" : "live"}
    >
      <label htmlFor="history-cursor-range">History cursor</label>
      <input
        id="history-cursor-range"
        type="range"
        min={0}
        max={Math.max(0, offsets.length - 1)}
        step={1}
        value={index}
        disabled={empty}
        aria-valuetext={empty ? "no boundary recorded" : `${selected} min, ${when}`}
        onChange={(event) => onSelect(offsets[Number(event.target.value)])}
      />
      <span className="history-cursor__at" data-cursor-offset={selected ?? ""}>
        {empty ? "no boundary recorded yet" : `offset ${selected} min, ${when}`}
      </span>
      <span className="history-cursor__live" data-return-to-live-slot>
        {behindLive > 0 ? (
          <button type="button" className="action" onClick={onReturnToLive}>
            {`Return to live (${behindLive} ${behindLive === 1 ? "boundary" : "boundaries"} behind live)`}
          </button>
        ) : (
          "Following live"
        )}
      </span>
      <span data-history-lag={lag === null ? "none" : "behind"}>
        {lag === null
          ? ""
          : `History recorded through boundary ${lag.recorded}; execution at ${lag.clock}.`}
      </span>
    </div>
  );
}

const BoundaryRecords = memo(function BoundaryRecords({
  slice,
  offset,
}: {
  /** The cursor boundary's slice: the rows it owns, by reference. */
  slice: BoundarySlice | null;
  offset: number;
}) {
  const boundary = slice === null ? undefined : slice.boundary;
  const samples = (slice === null ? [] : slice.samples).filter(
    (s) => s.offset_minutes === offset,
  );
  const attempts = (slice === null ? [] : slice.attempts).filter(
    (a) => a.at_offset_minutes === offset,
  );
  const decided =
    slice !== null && slice.interval !== null && slice.interval.from_offset === offset
      ? slice.interval
      : undefined;
  const events = [
    ...(slice === null ? [] : slice.applied_events)
      .filter((e) => e.at_offset_minutes === offset)
      .map((e) => ({
        key: `applied-${e.event_id}-${e.address}-${e.phase_id}`,
        lane: "Applied event",
        text: `${e.event_id} ${e.direction} ${e.address}, share ${e.share} of ${e.declared}, phase ${e.phase_id} (${e.origin})`,
      })),
    ...(slice === null ? [] : slice.bounded_transitions)
      .filter((t) => t.at_offset_minutes === offset)
      .map((t) => ({
        key: `bounded-${t.address}-${t.bound_case_id}`,
        lane: "Bounded transition",
        text: `${t.address} ${t.bound_kind} ${t.bound_value}: requested ${t.requested}, accepted ${t.accepted}, refused ${t.refused}`,
      })),
    ...(slice === null ? [] : slice.discrete_transitions)
      .filter((t) => t.at_offset_minutes === offset)
      .map((t) => ({
        key: `discrete-${t.address}-${t.next}-${t.phase}`,
        lane: "Discrete transition",
        text: `${t.address} ${t.previous} to ${t.next}, phase ${t.phase}: ${t.cause}`,
      })),
  ];

  return (
    <>
      <Panel
        heading="Records at one boundary"
        headingId="run-history-boundary-heading"
      >
        <p data-history-selected={offset}>
          {`At the history cursor: interval decided at ${offset} min. `}
          {boundary === undefined
            ? ""
            : `${boundary.simulation_time}. `}
          State at this instant is after its events. An interval measurement
          here describes the step that ended here; a control decided here
          governs the step that begins here.
          {boundary !== undefined && !boundary.has_preceding_interval
            ? " No step ended at this boundary, so it has no interval measurement."
            : ""}
        </p>
      </Panel>

      <Panel
        heading="Private state samples"
        headingId="run-history-samples-heading"
        flush
      >
        {samples.length === 0 ? (
          <p data-history-no-samples>No state sample is recorded here.</p>
        ) : (
          <DataTable labelledBy="run-history-samples-heading">
            <thead>
              <tr>
                <th scope="col">Address</th>
                <th scope="col">Phase</th>
                <th scope="col">Exact value</th>
              </tr>
            </thead>
            <tbody>
              {samples.map((s) => (
                <tr
                  key={`${s.address}-${s.phase}`}
                  data-history-sample={s.address}
                  data-phase={s.phase}
                >
                  <th scope="row">{s.address}</th>
                  <td>{s.phase}</td>
                  <td>
                    <ExactQuantity value={s.value} unit={s.unit} />
                    {s.unit === "" ? " (model unit)" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>

      <Panel
        heading="The interval decided here"
        headingId="run-history-interval-heading"
        flush
      >
        {decided === undefined ? (
          <p data-history-no-interval>
            No resolved interval begins at this boundary.
          </p>
        ) : (
          <>
            <p data-history-interval={`${decided.from_offset}-${decided.to_offset}`}>
              {`[${decided.from_offset}, ${decided.to_offset}) min. Power is the mean over the step in kW; energy is over the step in kWh.`}
            </p>
            <DataTable labelledBy="run-history-interval-heading">
              <thead>
                <tr>
                  <th scope="col">Load</th>
                  <th scope="col">Demand</th>
                  <th scope="col">Served</th>
                  <th scope="col">Unserved</th>
                </tr>
              </thead>
              <tbody>
                {decided.loads.map((load) => (
                  <tr key={load.address} data-history-load={load.address}>
                    <th scope="row">{load.address}</th>
                    <td>
                      <ExactQuantity value={load.demand_power} unit="kW" />
                    </td>
                    <td>
                      <ExactQuantity value={load.served_power} unit="kW" />
                    </td>
                    <td>
                      <ExactQuantity value={load.unserved_power} unit="kW" />
                    </td>
                  </tr>
                ))}
                {decided.flows.map((flow) => (
                  <tr key={flow.flow_id} data-history-flow={flow.flow_id}>
                    <th scope="row">{`${flow.flow_id} (${flow.from_address} to ${flow.to_address})`}</th>
                    <td colSpan={3}>
                      <ExactQuantity value={flow.mean_power} unit="kW" />
                      {", "}
                      <ExactQuantity value={flow.energy} unit="kWh" />
                    </td>
                  </tr>
                ))}
                {decided.controls.map((control) => (
                  <tr
                    key={`${control.address}-${control.quantity}`}
                    data-history-control={control.address}
                  >
                    <th scope="row">{`${control.quantity} at ${control.address}`}</th>
                    <td colSpan={3}>
                      {"requested "}
                      <ExactQuantity value={control.requested} unit={control.unit} />
                      {", accepted "}
                      <ExactQuantity value={control.accepted} unit={control.unit} />
                      {control.limited_by.length === 0
                        ? ""
                        : `, limited by ${control.limited_by.join("; ")}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </>
        )}
      </Panel>

      <Panel
        heading="Observation attempts here"
        headingId="run-history-attempts-heading"
        flush
      >
        {attempts.length === 0 ? (
          <p data-history-no-attempts>
            No signal was due at this boundary. That is its cadence, not a
            dropout.
          </p>
        ) : (
          <DataTable labelledBy="run-history-attempts-heading">
            <thead>
              <tr>
                <th scope="col">Device and signal</th>
                <th scope="col">Address</th>
                <th scope="col">Outcome</th>
                <th scope="col">Reported</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((a) => (
                <tr
                  key={`${a.device_id}-${a.signal_id}-${a.address}`}
                  data-history-attempt={a.address}
                  data-outcome={a.outcome}
                >
                  <th scope="row">{`${a.device_id} ${a.signal_id}`}</th>
                  <td>{a.address}</td>
                  <td>{a.outcome}</td>
                  <td>
                    {a.reported_value === null ? (
                      <span data-history-no-reading>
                        {`no reading (${a.suppression_reason ?? a.outcome})`}
                      </span>
                    ) : (
                      <ExactQuantity
                        value={a.reported_value}
                        unit={a.canonical_unit}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>

      <Panel
        heading="Timeline entries here"
        headingId="run-history-timeline-heading"
      >
        {events.length === 0 ? (
          <p data-history-no-events>
            No event or transition is recorded at this boundary.
          </p>
        ) : (
          <ul>
            {events.map((entry) => (
              <li key={entry.key} data-history-event={entry.lane}>
                {`${entry.lane}: ${entry.text}`}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </>
  );
});
