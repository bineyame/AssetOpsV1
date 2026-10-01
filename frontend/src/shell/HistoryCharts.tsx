import { useEffect, useMemo, useRef, useState } from "react";

import { DataTable, Disclosure, Panel } from "../ui";
import {
  type ChartModel,
  type ChartPanel,
  type IntervalValue,
  type ReportedTrack,
  type StatePanel,
  type TruthSeries,
  chartModel,
  plotted,
  readingAt,
  reportedRuns,
} from "./historyChartModel";
import type { RunHistory, RunHistoryAttempt } from "./runHistory";

/**
 * Addressed day curves over one run's recorded history (T025c phase 2).
 *
 * One shared selection - the boundary the inspector below also shows - drives
 * a cursor on every panel and the exact-value table beside them. Selecting
 * reads the record; it never executes, steps or moves the run.
 *
 * Every drawing here is a recorded value placed on a common time axis. Units
 * never share an axis: kW, % and L are separate panels. Colour is never the
 * only carrier: each truth series has its own dash pattern and a legend entry,
 * reported readings are ring markers joined by a thin ink line, and each due
 * attempt that produced no reading is a glyph with its outcome in words.
 */

const DASH: Record<TruthSeries["dash"], string | undefined> = {
  solid: undefined,
  dashed: "6 4",
  dotted: "2 3",
  dashdot: "8 3 2 3",
};

const GLYPH: Record<string, string> = {
  DROPPED: "×",
  SUPPRESSED_BY_GAP: "□",
  NO_PRECEDING_INTERVAL: "–",
  NO_VALUE_AT_BOUNDARY: "–",
};

const HEIGHT = 168;
const LANE = 24;
const MARGIN = { left: 52, right: 12, top: 10, bottom: 26 };
const MIN_WIDTH = 320;

function glyph(outcome: string): string {
  return GLYPH[outcome] ?? "?";
}

/** The width the drawing has, measured when the browser can measure it. */
function useWidth(): [React.RefObject<HTMLDivElement>, number] {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(720);
  useEffect(() => {
    const element = ref.current;
    if (element === null || typeof ResizeObserver === "undefined") {
      return undefined;
    }
    const observer = new ResizeObserver((entries) => {
      const measured = Math.floor(entries[0]?.contentRect.width ?? 0);
      if (measured > 0) {
        setWidth(Math.max(MIN_WIDTH, measured));
      }
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

export function niceTicks(min: number, max: number): number[] {
  const span = max - min || 1;
  const raw = span / 4;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step =
    [1, 2, 2.5, 5, 10].map((m) => m * power).find((s) => s >= raw) ?? raw;
  // From the step at or below the minimum to the step at or ABOVE the
  // maximum: the axis must contain every value, or the top of a curve is
  // drawn outside its own plot.
  const ticks: number[] = [];
  let t = Math.floor(min / step) * step;
  ticks.push(Number(t.toFixed(6)));
  while (t < max - step * 1e-9) {
    t += step;
    ticks.push(Number(t.toFixed(6)));
  }
  return ticks;
}

/** Headroom above the recorded extreme when no range is declared. */
const HEADROOM = 1.25;

/**
 * The value axis of one panel (T025e AC8). Where the frozen inputs declare a
 * range (state of charge 0-100 %, a held rating) that range is the axis,
 * widened only if a recorded value lies outside it. Otherwise the axis is a
 * "nice" ratchet with headroom over the recorded extremes. Because a live
 * history only grows at its end, the extremes - and so the axis - only ever
 * widen, in the same commit as the point that widened them; never shrink.
 */
export function valueTicks(
  panel: { bound?: { min: number; max: number } },
  values: number[],
): number[] {
  const low = Math.min(0, ...values);
  const high = Math.max(0, ...values);
  if (panel.bound !== undefined) {
    return niceTicks(Math.min(panel.bound.min, low), Math.max(panel.bound.max, high));
  }
  return niceTicks(low * HEADROOM, Math.max(low + 1, high * HEADROOM));
}

function hours(offset: number): string {
  const h = Math.floor(offset / 60);
  const m = offset % 60;
  return m === 0 ? `${h} h` : `${h} h ${m}`;
}

interface Axis {
  x: (offset: number) => number;
  width: number;
  plotRight: number;
  domain: [number, number];
}

function timeAxis(model: ChartModel, width: number): Axis {
  const [d0, d1] = model.domain;
  const plot = width - MARGIN.left - MARGIN.right;
  return {
    x: (offset) => MARGIN.left + ((offset - d0) / (d1 - d0 || 1)) * plot,
    width,
    plotRight: width - MARGIN.right,
    domain: model.domain,
  };
}

function timeTicks(domain: [number, number]): number[] {
  const span = domain[1] - domain[0];
  const step = span > 12 * 60 ? 240 : span > 4 * 60 ? 60 : span > 90 ? 30 : 15;
  const ticks: number[] = [];
  for (let t = domain[0]; t <= domain[1]; t += step) {
    ticks.push(t);
  }
  return ticks;
}

function nearest(offsets: number[], target: number): number {
  let best = offsets[0];
  for (const offset of offsets) {
    if (Math.abs(offset - target) < Math.abs(best - target)) {
      best = offset;
    }
  }
  return best;
}

function intervalPath(
  values: IntervalValue[],
  x: (o: number) => number,
  y: (v: number) => number,
): string {
  let path = "";
  let previous: IntervalValue | null = null;
  for (const value of values) {
    if (previous !== null && previous.to === value.from) {
      path += ` V${y(value.value)} H${x(value.to)}`;
    } else {
      path += ` M${x(value.from)} ${y(value.value)} H${x(value.to)}`;
    }
    previous = value;
  }
  return path.trim();
}

function attemptTitle(track: ReportedTrack, attempt: RunHistoryAttempt): string {
  const who = `${track.device_id} ${track.signal_id} (${track.address})`;
  if (attempt.reported_value === null) {
    return `${who}: no reading at ${attempt.source_sample_time}, ${attempt.outcome}${
      attempt.suppression_reason === null ? "" : ` - ${attempt.suppression_reason}`
    }`;
  }
  const unit = track.unit === "state" ? "" : ` ${track.unit}`;
  return `${who}: reported ${attempt.reported_value}${unit} at source time ${attempt.source_sample_time}`;
}

/** The frame both kinds of drawing share: cursor, the step that ended, time ticks. */
function Frame({
  axis,
  height,
  selected,
  timestep,
  recordedThrough,
  onSelect,
  offsets,
  label,
  children,
}: {
  axis: Axis;
  height: number;
  selected: number;
  timestep: number;
  recordedThrough: number;
  onSelect: (offset: number) => void;
  offsets: number[];
  label: string;
  children: React.ReactNode;
}) {
  const bottom = height - MARGIN.bottom;
  const unrecordedFrom = axis.x(recordedThrough);
  return (
    <div className="history-chart__scroll">
      <svg
        className="history-chart"
        width={axis.width}
        height={height}
        viewBox={`0 0 ${axis.width} ${height}`}
        role="img"
        aria-label={label}
        onClick={(event) => {
          const box = event.currentTarget.getBoundingClientRect();
          if (box.width === 0 || offsets.length === 0) {
            return;
          }
          const px = ((event.clientX - box.left) / box.width) * axis.width;
          const [d0, d1] = axis.domain;
          const offset =
            d0 + ((px - MARGIN.left) / (axis.plotRight - MARGIN.left)) * (d1 - d0);
          onSelect(nearest(offsets, offset));
        }}
      >
        {unrecordedFrom < axis.plotRight - 1 ? (
          <g data-chart-unrecorded>
            <rect
              className="history-chart__unrecorded"
              x={unrecordedFrom}
              y={MARGIN.top}
              width={axis.plotRight - unrecordedFrom}
              height={bottom - MARGIN.top}
            />
            <text
              className="history-chart__note"
              x={Math.min(unrecordedFrom + 4, axis.plotRight - 70)}
              y={MARGIN.top + 12}
            >
              not recorded
            </text>
          </g>
        ) : null}
        {selected > axis.domain[0] ? (
          <rect
            className="history-chart__ended"
            x={axis.x(selected - timestep)}
            y={MARGIN.top}
            width={Math.max(1, axis.x(selected) - axis.x(selected - timestep))}
            height={bottom - MARGIN.top}
          />
        ) : null}
        {timeTicks(axis.domain).map((tick) => (
          <g key={tick}>
            <line
              className="history-chart__tick"
              x1={axis.x(tick)}
              x2={axis.x(tick)}
              y1={bottom}
              y2={bottom + 4}
            />
            <text
              className="history-chart__label"
              x={axis.x(tick)}
              y={bottom + 16}
              textAnchor="middle"
            >
              {hours(tick)}
            </text>
          </g>
        ))}
        <line
          className="history-chart__axis"
          x1={MARGIN.left}
          x2={axis.plotRight}
          y1={bottom}
          y2={bottom}
        />
        {children}
        <line
          className="history-chart__cursor"
          data-chart-cursor={selected}
          x1={axis.x(selected)}
          x2={axis.x(selected)}
          y1={MARGIN.top}
          y2={bottom}
        />
      </svg>
    </div>
  );
}

function Legend({
  series,
  reported,
}: {
  series: { label: string; slot: number; dash: TruthSeries["dash"] }[];
  reported: ReportedTrack[];
}) {
  const outcomes = [
    ...new Set(
      reported.flatMap((track) =>
        track.attempts
          .filter((a) => a.outcome !== "REPORTED")
          .map((a) => a.outcome),
      ),
    ),
  ];
  return (
    <ul className="history-legend">
      {series.map((item) => (
        <li key={item.label}>
          <span
            className={`history-legend__swatch history-legend__swatch--${item.dash}`}
            style={{ borderTopColor: `var(--series-${item.slot})` }}
            aria-hidden="true"
          />
          {item.label}
        </li>
      ))}
      {reported.map((track) => (
        <li key={`${track.device_id}-${track.signal_id}-${track.address}`}>
          <span className="history-legend__ring" aria-hidden="true" />
          {`Reported by ${track.device_id} ${track.signal_id}`}
          {track.cadence_minutes === null
            ? ""
            : `, due every ${track.cadence_minutes} min`}
        </li>
      ))}
      {outcomes.map((outcome) => (
        <li key={outcome} data-legend-outcome={outcome}>
          <span className="history-legend__glyph" aria-hidden="true">
            {glyph(outcome)}
          </span>
          {`Due, no reading: ${outcome}`}
        </li>
      ))}
    </ul>
  );
}

function MissingGlyphs({
  track,
  axis,
  y,
}: {
  track: ReportedTrack;
  axis: Axis;
  y: number;
}) {
  return (
    <>
      {track.attempts
        .filter((a) => a.outcome !== "REPORTED" || a.reported_value === null)
        .map((attempt) => (
          <text
            key={`missing-${attempt.at_offset_minutes}`}
            className="history-chart__glyph"
            data-chart-missing={attempt.outcome}
            data-offset={attempt.at_offset_minutes}
            x={axis.x(attempt.at_offset_minutes)}
            y={y}
            textAnchor="middle"
          >
            {glyph(attempt.outcome)}
            <title>{attemptTitle(track, attempt)}</title>
          </text>
        ))}
    </>
  );
}

function NumericChart({
  panel,
  model,
  axis,
  selected,
  recordedThrough,
  offsets,
  onSelect,
}: {
  panel: ChartPanel;
  model: ChartModel;
  axis: Axis;
  selected: number;
  recordedThrough: number;
  offsets: number[];
  onSelect: (offset: number) => void;
}) {
  const values = [
    ...panel.series.flatMap((s) =>
      s.kind === "instant" ? s.points.map((p) => p.value) : s.values.map((v) => v.value),
    ),
    ...panel.reported.flatMap((t) =>
      t.attempts
        .filter((a) => a.reported_value !== null)
        .map((a) => plotted(a.reported_value ?? "")),
    ),
  ].filter((v) => Number.isFinite(v));
  const ticks = valueTicks(panel, values);
  const lo = ticks[0];
  const hi = ticks[ticks.length - 1];
  const bottom = HEIGHT - MARGIN.bottom;
  const y = (v: number) =>
    bottom - ((v - lo) / (hi - lo || 1)) * (bottom - MARGIN.top);

  return (
    <figure className="history-chart__figure" data-chart-panel={panel.id}>
      <figcaption className="history-chart__caption">
        <strong>{`${panel.title} (${panel.unit})`}</strong>{" "}
        <span className="cell-secondary">{panel.statement}</span>
      </figcaption>
      <Legend series={panel.series} reported={panel.reported} />
      <Frame
        axis={axis}
        height={HEIGHT}
        selected={selected}
        timestep={model.timestep}
        recordedThrough={recordedThrough}
        onSelect={onSelect}
        offsets={offsets}
        label={`${panel.title} in ${panel.unit} over the run`}
      >
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              className={tick === 0 && panel.signed ? "history-chart__zero" : "history-chart__grid"}
              x1={MARGIN.left}
              x2={axis.plotRight}
              y1={y(tick)}
              y2={y(tick)}
            />
            <text
              className="history-chart__label"
              x={MARGIN.left - 6}
              y={y(tick) + 4}
              textAnchor="end"
            >
              {String(tick)}
            </text>
          </g>
        ))}
        {panel.series.map((series) => (
          <path
            key={series.id}
            className={
              series.detail === true
                ? "history-chart__line history-chart__line--detail"
                : "history-chart__line"
            }
            data-chart-series={series.id}
            data-series-role={series.detail === true ? "detail" : "total"}
            data-points={
              series.kind === "instant" ? series.points.length : series.values.length
            }
            d={
              series.kind === "instant"
                ? series.points
                    .map((p, i) => `${i === 0 ? "M" : "L"}${axis.x(p.offset)} ${y(p.value)}`)
                    .join(" ")
                : intervalPath(series.values, axis.x, y)
            }
            stroke={`var(--series-${series.slot})`}
            strokeDasharray={DASH[series.dash]}
          />
        ))}
        {panel.reported.map((track) => (
          <g
            key={`${track.device_id}-${track.signal_id}`}
            data-chart-reported={track.address}
          >
            {reportedRuns(track).map((run) => (
              <path
                key={`run-${run[0].at_offset_minutes}`}
                className="history-chart__reported-line"
                data-chart-reported-run={`${run[0].at_offset_minutes}-${run[run.length - 1].at_offset_minutes}`}
                d={run
                  .map(
                    (a, i) =>
                      `${i === 0 ? "M" : "L"}${axis.x(a.at_offset_minutes)} ${y(plotted(a.reported_value ?? ""))}`,
                  )
                  .join(" ")}
              />
            ))}
            {track.attempts
              .filter((a) => a.outcome === "REPORTED" && a.reported_value !== null)
              .map((attempt) => (
                <circle
                  key={attempt.at_offset_minutes}
                  className="history-chart__reported"
                  data-chart-report={attempt.at_offset_minutes}
                  data-value={attempt.reported_value ?? ""}
                  cx={axis.x(attempt.at_offset_minutes)}
                  cy={y(plotted(attempt.reported_value ?? ""))}
                  r={3.5}
                >
                  <title>{attemptTitle(track, attempt)}</title>
                </circle>
              ))}
            <MissingGlyphs track={track} axis={axis} y={bottom - 4} />
          </g>
        ))}
      </Frame>
    </figure>
  );
}

function stateClass(value: string): string {
  if (value === "RUNNING") return "history-state history-state--running";
  if (value === "STARTING") return "history-state history-state--starting";
  return "history-state";
}

/**
 * Whether a reported member's label fits before the next change of member. A
 * label that would collide is left out; the marker's tooltip and the exact
 * value table still name it.
 */
function roomForLabel(
  reported: RunHistoryAttempt[],
  index: number,
  axis: Axis,
): boolean {
  const here = reported[index];
  const next = reported
    .slice(index + 1)
    .find((a) => a.reported_value !== here.reported_value);
  const end = next === undefined ? axis.plotRight : axis.x(next.at_offset_minutes);
  return end - axis.x(here.at_offset_minutes) >= 60;
}

function StateChart({
  panel,
  model,
  axis,
  selected,
  recordedThrough,
  offsets,
  onSelect,
}: {
  panel: StatePanel;
  model: ChartModel;
  axis: Axis;
  selected: number;
  recordedThrough: number;
  offsets: number[];
  onSelect: (offset: number) => void;
}) {
  const lanes = [...panel.lanes.map((lane) => lane.label), ...panel.reported.map(() => "Reported status")];
  const height = MARGIN.top + lanes.length * (LANE + 6) + MARGIN.bottom;
  const top = (index: number) => MARGIN.top + index * (LANE + 6);
  return (
    <figure className="history-chart__figure" data-chart-panel={panel.id}>
      <figcaption className="history-chart__caption">
        <strong>{panel.title}</strong>{" "}
        <span className="cell-secondary">
          Lane one is the physical state at each boundary, after its events;
          lane two is the state the model held over the step that begins
          there. They differ where a transition takes effect at a boundary.
          A reported status is what the device published, at its source time.
        </span>
      </figcaption>
      <Legend series={[]} reported={panel.reported} />
      <Frame
        axis={axis}
        height={height}
        selected={selected}
        timestep={model.timestep}
        recordedThrough={recordedThrough}
        onSelect={onSelect}
        offsets={offsets}
        label={`${panel.title} over the run`}
      >
        {panel.lanes.map((lane, index) => (
          <g key={lane.id} data-chart-lane={lane.phase}>
            <text className="history-chart__label" x={4} y={top(index) + 15}>
              {index === 0 ? "at T" : "step"}
            </text>
            {lane.runs.map((run) => {
              const x0 = axis.x(run.from);
              const x1 =
                lane.phase === "POST_EVENT" ? axis.x(run.to) : axis.x(run.to);
              const width = Math.max(3, x1 - x0);
              return (
                <g key={`${run.from}-${run.value}`} data-chart-state={run.value} data-from={run.from}>
                  <rect
                    className={stateClass(run.value)}
                    x={x0 - (lane.phase === "POST_EVENT" ? 1.5 : 0)}
                    y={top(index)}
                    width={width}
                    height={LANE}
                  >
                    <title>{`${lane.label}: ${run.value} from ${run.from} min${
                      lane.phase === "POST_EVENT" ? ` through ${run.to} min` : ` until ${run.to} min`
                    }`}</title>
                  </rect>
                  {width > 58 ? (
                    <text className="history-state__text" x={x0 + 4} y={top(index) + 16}>
                      {run.value}
                    </text>
                  ) : null}
                </g>
              );
            })}
          </g>
        ))}
        {panel.reported.map((track, index) => {
          const row = top(panel.lanes.length + index);
          return (
            <g key={`${track.device_id}-${track.signal_id}`} data-chart-reported={track.address}>
              <text className="history-chart__label" x={4} y={row + 15}>
                rep.
              </text>
              {reportedRuns(track).map((run) => (
                <path
                  key={`run-${run[0].at_offset_minutes}`}
                  className="history-chart__reported-line"
                  data-chart-reported-run={`${run[0].at_offset_minutes}-${run[run.length - 1].at_offset_minutes}`}
                  d={`M${axis.x(run[0].at_offset_minutes)} ${row + LANE / 2} H${axis.x(run[run.length - 1].at_offset_minutes)}`}
                />
              ))}
              {track.attempts
                .filter((a) => a.outcome === "REPORTED" && a.reported_value !== null)
                .map((attempt, i, reported) => (
                  <g key={attempt.at_offset_minutes}>
                    <circle
                      className="history-chart__reported"
                      data-chart-report={attempt.at_offset_minutes}
                      data-value={attempt.reported_value ?? ""}
                      cx={axis.x(attempt.at_offset_minutes)}
                      cy={row + LANE / 2}
                      r={3.5}
                    >
                      <title>{attemptTitle(track, attempt)}</title>
                    </circle>
                    {(i === 0 || reported[i - 1].reported_value !== attempt.reported_value) &&
                    roomForLabel(reported, i, axis) ? (
                      <text
                        className="history-state__text"
                        x={axis.x(attempt.at_offset_minutes) + 5}
                        y={row + 8}
                      >
                        {attempt.reported_value}
                      </text>
                    ) : null}
                  </g>
                ))}
              <MissingGlyphs track={track} axis={axis} y={row + LANE / 2 + 5} />
            </g>
          );
        })}
      </Frame>
    </figure>
  );
}

// --- The exact values at the selection ----------------------------------------

interface InspectorRow {
  key: string;
  panel: string;
  series: string;
  applies: string;
  value: React.ReactNode;
}

function Exact({ value, unit }: { value: string; unit: string }) {
  const ratio = /^(-?\d+)\/(\d+)$/.exec(value);
  const aid =
    ratio === null ? "" : ` (about ${(Number(ratio[1]) / Number(ratio[2])).toFixed(2)})`;
  return (
    <span data-exact={value}>{`${value}${unit === "" || unit === "state" ? "" : ` ${unit}`}${aid}`}</span>
  );
}

function reportedCell(track: ReportedTrack, offset: number): React.ReactNode {
  const held = readingAt(track, offset);
  const stale = (last: RunHistoryAttempt | null) =>
    last === null ? (
      <span data-reading-quality="UNAVAILABLE"> Nothing has been reported yet (UNAVAILABLE).</span>
    ) : (
      <span data-reading-quality="STALE">
        {" Last reading "}
        <Exact value={last.reported_value ?? ""} unit={track.unit} />
        {` from source time ${last.source_sample_time} (STALE).`}
      </span>
    );
  if (held.kind === "reported") {
    return (
      <span data-reading-quality="GOOD">
        <Exact value={held.attempt.reported_value ?? ""} unit={track.unit} />
        {` at source time ${held.attempt.source_sample_time} (GOOD)`}
      </span>
    );
  }
  if (held.kind === "missing") {
    return (
      <span data-reading-missing={held.attempt.outcome}>
        {`Due, no reading: ${held.attempt.outcome}.`}
        {stale(held.last)}
      </span>
    );
  }
  return (
    <span data-reading-not-due>
      {`Not due at this boundary${
        track.cadence_minutes === null ? "" : ` (due every ${track.cadence_minutes} min)`
      }; that is cadence, not a dropout.`}
      {held.last === null ? null : (
        <>
          {" Held reading "}
          <Exact value={held.last.reported_value ?? ""} unit={track.unit} />
          {` from source time ${held.last.source_sample_time} (STALE).`}
        </>
      )}
    </span>
  );
}

/**
 * What the reading a reported row shows applies to: its OWN support.
 *
 * T025d (backlog C1). A held STALE reading describes the instant or interval
 * of its own source time, not the selected boundary's; labelling it with the
 * selected interval put a reading about `[70, 75)` under `[75, 80)`.
 */
function reportedApplies(
  track: ReportedTrack,
  offset: number,
  timestep: number,
): string {
  const held = readingAt(track, offset);
  const reading = held.kind === "reported" ? held.attempt : held.last;
  if (reading === null) {
    return "nothing has been reported yet";
  }
  const at = reading.at_offset_minutes;
  const own =
    at === offset ? "" : "; the held reading's own support, not the selected boundary's";
  return track.reading_class === "INTERVAL_SIGNAL"
    ? `source time ${reading.source_sample_time}; describes the step [${at - timestep}, ${at}) that ended at ${at} min${own}`
    : `source time ${reading.source_sample_time}; state at that instant, ${at} min${own}`;
}

function inspectorRows(
  model: ChartModel,
  offset: number,
  timestep: number,
  first: boolean,
): InspectorRow[] {
  const rows: InspectorRow[] = [];
  const ended = `step [${offset - timestep}, ${offset}) that ended here`;
  const begins = `step [${offset}, ${offset + timestep}) that begins here`;
  for (const panel of model.panels) {
    for (const series of panel.series) {
      let applies: string;
      let value: React.ReactNode;
      if (series.kind === "instant") {
        applies = "at this instant, after its events";
        const point = series.points.find((p) => p.offset === offset);
        value =
          point === undefined ? (
            <span data-no-value>not recorded at this instant</span>
          ) : (
            <Exact value={point.exact} unit={panel.unit} />
          );
      } else if (series.kind === "governing") {
        applies = `control in effect over the ${begins}`;
        const held = series.values.find((v) => v.from <= offset && offset < v.to);
        value =
          held === undefined ? (
            <span data-no-value>no step begins here in the record</span>
          ) : (
            <Exact value={held.exact} unit={panel.unit} />
          );
      } else {
        applies = first ? "no step ended at the first boundary" : `mean over the ${ended}`;
        const done = series.values.find((v) => v.to === offset);
        value =
          done === undefined ? (
            <span data-no-value>
              {first
                ? "absent: no interval has completed yet"
                : "no resolved step ended here in the record"}
            </span>
          ) : (
            <Exact value={done.exact} unit={panel.unit} />
          );
      }
      rows.push({
        key: `${panel.id}-${series.id}`,
        panel: `${panel.title} (${panel.unit})`,
        series: series.label,
        applies,
        value,
      });
    }
    for (const track of panel.reported) {
      rows.push({
        key: `${panel.id}-${track.device_id}-${track.signal_id}`,
        panel: `${panel.title} (${panel.unit})`,
        series: `Reported by ${track.device_id} ${track.signal_id}`,
        applies: reportedApplies(track, offset, timestep),
        value: reportedCell(track, offset),
      });
    }
  }
  for (const panel of model.states) {
    for (const lane of panel.lanes) {
      const run = lane.runs.find((r) =>
        lane.phase === "FOR_STEP"
          ? r.from <= offset && offset < r.to
          : r.from <= offset && offset <= r.to,
      );
      rows.push({
        key: `${panel.id}-${lane.id}`,
        panel: panel.title,
        series: lane.label,
        applies:
          lane.phase === "POST_EVENT"
            ? "at this instant, after its events"
            : `over the ${begins}`,
        value:
          run === undefined ? (
            <span data-no-value>not recorded</span>
          ) : (
            <span data-discrete={run.value}>{run.value}</span>
          ),
      });
    }
    for (const track of panel.reported) {
      rows.push({
        key: `${panel.id}-${track.device_id}-${track.signal_id}`,
        panel: panel.title,
        series: `Reported by ${track.device_id} ${track.signal_id}`,
        applies: reportedApplies(track, offset, timestep),
        value: reportedCell(track, offset),
      });
    }
  }
  return rows;
}

export function HistoryCharts({
  history,
  timestepMinutes,
  selected,
  onSelect,
}: {
  history: RunHistory;
  /** The run's frozen timestep; the curves themselves are the history's. */
  timestepMinutes: number | null;
  selected: number;
  onSelect: (offset: number) => void;
}) {
  // T025e (closes C3): every curve comes from the recorded history alone, so
  // no fresh per-step execution data can run ahead of the rest.
  const model = useMemo(
    () => chartModel(history, timestepMinutes),
    [history, timestepMinutes],
  );
  const [ref, width] = useWidth();
  const axis = timeAxis(model, width);
  const offsets = history.boundaries.map((b) => b.offset_minutes);
  const boundary = history.boundaries[Math.max(0, offsets.indexOf(selected))];
  // The last recorded boundary, or the end of the last recorded step decided
  // at it, whichever is later: a step decided at the last boundary is recorded.
  const recordedThrough = Math.max(
    history.recorded_through_offset_minutes ?? 0,
    ...history.intervals.map((i) => i.to_offset),
  );
  const rows = inspectorRows(
    model,
    selected,
    model.timestep,
    boundary !== undefined && !boundary.has_preceding_interval,
  );

  const unavailable = history.coverage.filter(
    (c) =>
      (c.family === "state_samples" || c.family === "intervals" || c.family === "observation_attempts") &&
      c.availability !== "RECORDED",
  );

  return (
    <Panel heading="Recorded day curves" headingId="run-history-charts-heading">
      <p className="run-cockpit__caption">
        Read from the recorded history; nothing is recomputed. Rings are reports
        at their source time.
      </p>
      <Disclosure name="charts-how-to-read" summary="How to read these curves">
        <p>
          Every curve below is read from this run&apos;s recorded history; none is
          recomputed here. Reported readings are rings at their source time; a
          thin line joins consecutive readings of one signal only to show that no
          due attempt failed between them, and is not a value between them.
          Choosing a boundary moves the history cursor on every chart and the
          exact values beside them. It reads the record and never advances the
          run.
        </p>
        <p>
          {`The time axis is the offset from the interval start, over the whole window; each step is ${model.timestep} min. The shaded band is the step that ended at the selected boundary: an interval report at T describes it, while a control accepted at T governs the next step. Past the last recorded boundary the window is not recorded yet.`}
        </p>
      </Disclosure>
      {unavailable.length === 0 ? null : (
        <ul className="cell-list" data-charts-unavailable>
          {unavailable.map((c) => (
            <li key={c.family}>
              {`${c.family} is ${c.availability}: ${c.availability_statement} No curve is drawn from it.`}
            </li>
          ))}
        </ul>
      )}
      {offsets.length === 0 ? (
        <p data-charts-empty>No boundary is recorded, so there is nothing to chart.</p>
      ) : (
        <>
          <div className="history-cockpit">
            <div className="history-cockpit__charts" ref={ref}>
              {model.panels.map((panel) => (
                <NumericChart
                  key={panel.id}
                  panel={panel}
                  model={model}
                  axis={axis}
                  selected={selected}
                  recordedThrough={recordedThrough}
                  offsets={offsets}
                  onSelect={onSelect}
                />
              ))}
              {model.states.map((panel) => (
                <StateChart
                  key={panel.id}
                  panel={panel}
                  model={model}
                  axis={axis}
                  selected={selected}
                  recordedThrough={recordedThrough}
                  offsets={offsets}
                  onSelect={onSelect}
                />
              ))}
              {model.unpaired.length === 0 ? null : (
                <p data-charts-unpaired>
                  {`Reported but not charted, because no recorded quantity on these charts is the one they measure: ${model.unpaired
                    .map((t) => `${t.device_id} ${t.signal_id} (${t.address})`)
                    .join("; ")}. Their attempts are in the boundary inspector below.`}
                </p>
              )}
            </div>
            <div className="history-cockpit__values">
              <h3 id="run-history-values-heading" className="history-cockpit__heading">
                {`Exact values at offset ${selected} min`}
              </h3>
              <DataTable labelledBy="run-history-values-heading">
                <thead>
                  <tr>
                    <th scope="col">Series</th>
                    <th scope="col">What it describes</th>
                    <th scope="col">Recorded value</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.key} data-value-row={row.key}>
                      <th scope="row">
                        {row.series}
                        <span className="cell-note">{row.panel}</span>
                      </th>
                      <td className="cell-secondary">{row.applies}</td>
                      <td>{row.value}</td>
                    </tr>
                  ))}
                </tbody>
              </DataTable>
            </div>
          </div>
        </>
      )}
    </Panel>
  );
}
