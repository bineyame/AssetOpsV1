import { useState } from "react";

import { DataTable, Fact, FactList, Panel } from "../ui";
import type { SiteDetailResult } from "../sites/siteReadModel";
import { HistoryCharts } from "./HistoryCharts";
import { HistoryTimeline } from "./HistoryTimeline";
import { IntervalDrawing } from "./IntervalDrawing";
import { IntervalInspection } from "./IntervalInspection";
import type { RunHistory, RunHistoryResult } from "./runHistory";
import type { RunElectricalStep } from "./runSetupClient";

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
 * The recorded history of one run, as coverage and exact values (T025c).
 *
 * A simple inspector, deliberately: it states where the history came from and
 * which families were recorded, then shows every record at ONE selected
 * boundary - the addressed samples with their phase, the interval decided
 * there, each observation attempt and each timeline entry. Selecting a
 * boundary reads the record; it executes nothing and moves no run.
 *
 * Absence is shown as absence. A family that was not recorded says so with its
 * reason; an attempt without a reading says which outcome it had; the first
 * boundary shows no preceding-interval sample because none exists.
 */
export function HistoryInspector({
  result,
  steps = null,
  timestepMinutes = null,
  site = null,
}: {
  result: RunHistoryResult | null;
  /** The execution projection's electrical steps, when the model has them. */
  steps?: RunElectricalStep[] | null;
  timestepMinutes?: number | null;
  /**
   * T025d: the Site read for the run-bound drawing, or null while it is in
   * flight or not asked for. The drawing binds only if it is the Site and
   * Foundation version the run froze.
   */
  site?: SiteDetailResult | null;
}) {
  if (result === null) {
    return (
      <Panel heading="Recorded history" headingId="run-history-heading">
        <p>Loading the recorded history.</p>
      </Panel>
    );
  }
  if (result.status !== "loaded") {
    return (
      <Panel heading="Recorded history" headingId="run-history-heading">
        <p data-history-unavailable>
          The recorded history could not be read
          {result.status === "unavailable" && result.message !== null
            ? `: ${result.message}`
            : "."}
        </p>
      </Panel>
    );
  }
  return (
    <LoadedHistory
      history={result.history}
      steps={steps}
      timestepMinutes={timestepMinutes}
      site={site}
    />
  );
}

function LoadedHistory({
  history,
  steps,
  timestepMinutes,
  site,
}: {
  history: RunHistory;
  steps: RunElectricalStep[] | null;
  timestepMinutes: number | null;
  site: SiteDetailResult | null;
}) {
  const last = history.boundaries[history.boundaries.length - 1];
  const [chosen, setChosen] = useState<number | null>(null);
  const selected =
    chosen !== null &&
    history.boundaries.some((b) => b.offset_minutes === chosen)
      ? chosen
      : (last?.offset_minutes ?? null);

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
          <Fact term="Trajectory digest">
            <code>{history.content_digest ?? "none"}</code>
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

      {selected === null ? null : (
        <HistoryCharts
          history={history}
          steps={steps}
          timestepMinutes={timestepMinutes}
          selected={selected}
          onSelect={setChosen}
        />
      )}

      {/*
        * T025d: the drawing, the control inspection and the timeline all read
        * the one selection above - the interval that ended at the selected
        * boundary - from the recorded history, never the latest step.
        */}
      {selected === null ? null : (
        <>
          <IntervalDrawing history={history} offset={selected} site={site} />
          <IntervalInspection history={history} offset={selected} />
          <HistoryTimeline history={history} offset={selected} />
        </>
      )}

      {selected === null ? null : (
        <BoundaryRecords
          history={history}
          offset={selected}
          onSelect={setChosen}
        />
      )}
    </>
  );
}

function BoundaryRecords({
  history,
  offset,
  onSelect,
}: {
  history: RunHistory;
  offset: number;
  onSelect: (offset: number) => void;
}) {
  const boundary = history.boundaries.find((b) => b.offset_minutes === offset);
  const samples = history.samples.filter((s) => s.offset_minutes === offset);
  const attempts = history.attempts.filter(
    (a) => a.at_offset_minutes === offset,
  );
  const decided = history.intervals.find((i) => i.from_offset === offset);
  const events = [
    ...history.applied_events
      .filter((e) => e.at_offset_minutes === offset)
      .map((e) => ({
        key: `applied-${e.event_id}-${e.address}-${e.phase_id}`,
        lane: "Applied event",
        text: `${e.event_id} ${e.direction} ${e.address}, share ${e.share} of ${e.declared}, phase ${e.phase_id} (${e.origin})`,
      })),
    ...history.bounded_transitions
      .filter((t) => t.at_offset_minutes === offset)
      .map((t) => ({
        key: `bounded-${t.address}-${t.bound_case_id}`,
        lane: "Bounded transition",
        text: `${t.address} ${t.bound_kind} ${t.bound_value}: requested ${t.requested}, accepted ${t.accepted}, refused ${t.refused}`,
      })),
    ...history.discrete_transitions
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
        <label>
          Boundary{" "}
          <select
            data-history-boundary-select
            value={String(offset)}
            onChange={(event) => onSelect(Number(event.target.value))}
          >
            {history.boundaries.map((b) => (
              <option key={b.offset_minutes} value={String(b.offset_minutes)}>
                {`${b.offset_minutes} min - ${b.simulation_time}`}
              </option>
            ))}
          </select>
        </label>
        <p data-history-selected={offset}>
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
}
