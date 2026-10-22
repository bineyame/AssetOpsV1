/**
 * W5-01a C2 (Codex retrospective Q-C2-3, `.agent/W5-01-build-spec.md`): the cold Cooling `Recovery curves` graphic.
 *
 * The selected C1 `selected_points` carry a role and a source time but no temperature value, so each is an
 * unconnected, labelled mark on a categorical lane (compressor, chamber probe) across the selected window. No
 * numeric °C axis, no connecting path and no recovery curve is drawn: a curve needs an ordered accepted numeric
 * recovery series, which no selected read provides yet. With no point the frame is drawn empty.
 *
 * Registered in `tools/checks/shell-overflow.ps1` rule 5 as the only other module that may draw this svg; it renders
 * the `.cold-depth-graphic__scroll` region that owns the drawing's inline overflow (`ui/primitives.css`).
 */
import type { CoolingPoint } from "./ColdDepthClient";
import { date } from "./coldFormat";
import { recordLabel, utcClock } from "./coldSiteViews";

const W = 640;
const LANE_H = 44;
const PAD = { l: 150, r: 24, t: 14, b: 30 };
/** The C1 point roles in lane order (compressor first, then the chamber probe). */
const LANES = ["compressor_state", "chamber_temperature"] as const;
const QUARTER_HOUR_MS = 900_000;

const pad2 = (n: number) => String(n).padStart(2, "0");

export function CoolingObservationGraphic({
  from,
  to,
  points,
  label,
}: {
  from: string | null;
  to: string | null;
  points: CoolingPoint[];
  label: string;
}) {
  const lanes = [...LANES, ...Array.from(new Set(points.map((p) => p.role))).filter((r) => !(LANES as readonly string[]).includes(r))];
  const h = PAD.t + lanes.length * LANE_H + PAD.b;
  const a = date(from);
  const b = date(to);
  const span = a !== null && b !== null && b.getTime() > a.getTime() ? { a: a.getTime(), b: b.getTime() } : null;
  const x = (ms: number) => (span === null ? PAD.l : PAD.l + ((ms - span.a) / (span.b - span.a)) * (W - PAD.l - PAD.r));
  const laneY = (role: string) => PAD.t + lanes.indexOf(role) * LANE_H + LANE_H / 2;
  const ticks: number[] = [];
  if (span !== null) {
    for (let t = Math.ceil(span.a / QUARTER_HOUR_MS) * QUARTER_HOUR_MS; t <= span.b; t += QUARTER_HOUR_MS) ticks.push(t);
  }
  const marks = points
    .map((p, index) => ({ p, index, t: date(p.source_time) }))
    .filter((m): m is { p: CoolingPoint; index: number; t: Date } => m.t !== null && span !== null);
  return (
    <figure className="cold-depth-graphic" data-cooling-graphic={marks.length === 0 ? "empty" : "marks"}>
      <div className="cold-depth-graphic__scroll">
        <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label={label} preserveAspectRatio="xMinYMin meet">
          {lanes.map((role) => (
            <g key={role} data-cooling-lane={role}>
              <line className="cold-depth-graphic__lane" x1={PAD.l} x2={W - PAD.r} y1={laneY(role)} y2={laneY(role)} />
              <text className="cold-depth-graphic__lane-label" x={PAD.l - 10} y={laneY(role) + 4} textAnchor="end">
                {recordLabel(role)}
              </text>
            </g>
          ))}
          <line className="cold-depth-graphic__axis-line" x1={PAD.l} x2={W - PAD.r} y1={h - PAD.b} y2={h - PAD.b} />
          {ticks.map((t) => {
            const d = new Date(t);
            return (
              <text key={t} className="cold-depth-graphic__axis" x={x(t)} y={h - 10} textAnchor="middle">
                {`${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())} UTC`}
              </text>
            );
          })}
          {marks.map((m) => (
            <g key={`${m.p.role}|${m.p.source_time}|${m.index}`} data-cooling-mark={m.p.role}>
              <circle className="cold-depth-graphic__mark" cx={x(m.t.getTime())} cy={laneY(m.p.role)} r={5}>
                <title>{`${recordLabel(m.p.role)} · ${utcClock(m.p.source_time)} UTC`}</title>
              </circle>
              <text className="cold-depth-graphic__mark-label" x={x(m.t.getTime())} y={laneY(m.p.role) - 10} textAnchor="middle">
                {utcClock(m.p.source_time)}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </figure>
  );
}
