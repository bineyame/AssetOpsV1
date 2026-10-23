/**
 * W5-03a E3 (Codex retrospective "RESTORE TO MOCK" and the pre-flight E3 ruling, `.agent/W5-03-build-spec.md`): the
 * EV Energy `Import power and configured limit` chart (v6.9 `lineChart('ev')`).
 *
 * Each selected accepted `ev_site_import` sample is one unconnected 5px mark at its interval-end UTC time; equal-time
 * samples stay separate marks. No connecting path is drawn: the accepted samples do not establish continuous coverage
 * (MOCK DEVIATION (D1) R06). The time-valid declared limit is a dashed horizontal line only when configured. Axes are
 * derived from the selected window and values, never the mock's 08:00-16:00 or 76/80 kW (MOCK DEVIATION (D4) R55).
 * With no sample the axes and the empty plot frame remain.
 *
 * Registered in `tools/checks/shell-overflow.ps1` rule 5 as the only module that may draw this svg; it renders the
 * `.ev-depth-graphic__scroll` region that owns the drawing's inline overflow (`ui/primitives.css`).
 */
import type { ImportSample } from "./evDepthClient";

export const EV_CHART_W = 640;
export const EV_CHART_H = 220;
export const EV_CHART_PAD = { l: 48, r: 12, t: 12, b: 32 } as const;
export const EV_CHART_LABEL = "Site import and power limit";
const PLOT_W = EV_CHART_W - EV_CHART_PAD.l - EV_CHART_PAD.r;
const PLOT_H = EV_CHART_H - EV_CHART_PAD.t - EV_CHART_PAD.b;

const pad2 = (n: number) => String(n).padStart(2, "0");
const ms = (value: string) => Date.parse(value.replace(/\.(\d{3})\d*Z$/, ".$1Z"));
const hhmm = (t: number) => {
  const d = new Date(t);
  return `${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())}`;
};
const hhmmss = (t: number) => {
  const d = new Date(t);
  return `${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())}:${pad2(d.getUTCSeconds())}`;
};

/** The ruled Y maximum: `max(100, ceil(max(sample kW, limit kW) / 25) * 25)`. */
export function yMax(samples: ImportSample[], limitKw: string | null): number {
  const values = samples.map((s) => Number(s.import_kw));
  if (limitKw !== null) values.push(Number(limitKw));
  const top = values.length === 0 ? 0 : Math.max(...values);
  return Math.max(100, Math.ceil(top / 25) * 25);
}

/** Seven equally spaced UTC instants from window start to end. */
export function xTicks(fromMs: number, toMs: number): number[] {
  return Array.from({ length: 7 }, (_, i) => fromMs + ((toMs - fromMs) * i) / 6);
}

export function EvDepthPowerChart({
  from,
  to,
  samples,
  limitKw,
}: {
  from: string | null;
  to: string | null;
  samples: ImportSample[];
  limitKw: string | null;
}) {
  const a = from === null ? NaN : ms(from);
  const b = to === null ? NaN : ms(to);
  const span = Number.isFinite(a) && Number.isFinite(b) && b > a ? { a, b } : null;
  const max = yMax(samples, limitKw);
  const x = (t: number) => (span === null ? EV_CHART_PAD.l : EV_CHART_PAD.l + ((t - span.a) / (span.b - span.a)) * PLOT_W);
  const y = (v: number) => EV_CHART_PAD.t + PLOT_H - (v / max) * PLOT_H;
  const yTicks = [0, 1, 2, 3, 4].map((i) => (max * i) / 4);
  const marks = span === null ? [] : samples.filter((s) => Number.isFinite(ms(s.source_time)));
  const limit = limitKw === null ? null : Number(limitKw);
  return (
    <figure className="ev-depth-graphic" data-ev-chart={marks.length === 0 ? "empty" : "marks"}>
      <div className="legend ev-depth-graphic__legend">
        <span className="legend-item">
          <span className="ev-depth-graphic__swatch ev-depth-graphic__swatch--import" aria-hidden="true" />
          Site import
        </span>
        {limit === null ? null : (
          <span className="legend-item">
            <span className="ev-depth-graphic__swatch ev-depth-graphic__swatch--limit" aria-hidden="true" />
            Site power limit
          </span>
        )}
      </div>
      <div className="ev-depth-graphic__scroll">
        <svg viewBox={`0 0 ${EV_CHART_W} ${EV_CHART_H}`} role="img" aria-label={EV_CHART_LABEL} preserveAspectRatio="xMinYMin meet">
          <rect className="ev-depth-graphic__frame" x={EV_CHART_PAD.l} y={EV_CHART_PAD.t} width={PLOT_W} height={PLOT_H} />
          {yTicks.map((v) => (
            <g key={v} data-ev-y-tick={v}>
              <line className="ev-depth-graphic__grid" x1={EV_CHART_PAD.l} x2={EV_CHART_W - EV_CHART_PAD.r} y1={y(v)} y2={y(v)} />
              <text className="ev-depth-graphic__axis" x={EV_CHART_PAD.l - 6} y={y(v) + 4} textAnchor="end">
                {`${v} kW`}
              </text>
            </g>
          ))}
          {span === null
            ? null
            : xTicks(span.a, span.b).map((t, i) => (
                <text key={i} className="ev-depth-graphic__axis" x={x(t)} y={EV_CHART_H - 10} textAnchor="middle" data-ev-x-tick={hhmm(t)}>
                  {hhmm(t)}
                </text>
              ))}
          {limit === null || !Number.isFinite(limit) ? null : (
            <g data-ev-limit-line={limitKw ?? ""}>
              <line className="ev-depth-graphic__limit" x1={EV_CHART_PAD.l} x2={EV_CHART_W - EV_CHART_PAD.r} y1={y(limit)} y2={y(limit)} strokeDasharray="6 4" />
              <text className="ev-depth-graphic__limit-label" x={EV_CHART_W - EV_CHART_PAD.r - 4} y={y(limit) - 6} textAnchor="end">
                {`${limitKw} kW limit`}
              </text>
            </g>
          )}
          {marks.map((s) => (
            <circle key={s.evidence_id} className="ev-depth-graphic__mark" cx={x(ms(s.source_time))} cy={y(Number(s.import_kw))} r={5} data-ev-mark={s.evidence_id}>
              <title>{`Site import ${s.import_kw} kW · ${hhmmss(ms(s.source_time))} UTC`}</title>
            </circle>
          ))}
        </svg>
      </div>
    </figure>
  );
}
