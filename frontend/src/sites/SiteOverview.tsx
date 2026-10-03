/**
 * The mini-grid Site Overview body (T027 phase 2, AC11, AC22).
 *
 * "Is this site meeting its operating objective, and what matters now?" in the
 * v6.9 8.18 frame: the objective strip, one card per profile domain, the
 * selected-window timeline, then Findings. Everything shown is the backend
 * Overview read model's, computed from accepted evidence only; the profile
 * decides which cards render and in which order, never their state.
 *
 * No analytic exists yet, so every card and the objective strip show the
 * neutral "No assessment yet". "Unknown" is never used for that. A metric whose
 * signal has no GOOD accepted record in the window shows no value and names the
 * gap; the card lists the gap from the backend's coverage, not from the
 * profile. The timeline is context, not a status source.
 *
 * Evidence links open the Site > Evidence record inspector at the address
 * `evidenceHref` builds (`/sites/{id}/evidence?signal=DEV/SIG&record=MSG`);
 * the shell supplies the builder, because the substrate does not know routes.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Badge, Fact, FactList, Panel } from "../ui";
import {
  orderedOverviewCards,
  presentationProfileFor,
} from "./presentationProfile";
import type { EvidenceRead } from "./siteEvidenceClient";
import type {
  OverviewCard,
  OverviewInstantPoint,
  OverviewIntervalPoint,
  OverviewMetric,
  OverviewSeries,
  SiteOverviewClient,
  SiteOverviewReadModel,
} from "./siteOverviewClient";

export const SITE_OVERVIEW_LOADING = "Loading the site's overview.";

export interface SiteOverviewProps {
  siteId: string;
  client: SiteOverviewClient;
  /** The inspector address for one accepted record of one signal. */
  evidenceHref: (signal: string, messageId: string) => string;
  /** The Site > Evidence destination. */
  evidencePageHref: string;
}

export function SiteOverview({
  siteId,
  client,
  evidenceHref,
  evidencePageHref,
}: SiteOverviewProps) {
  const [result, setResult] =
    useState<EvidenceRead<SiteOverviewReadModel> | null>(null);

  useEffect(() => {
    let current = true;
    setResult(null);
    client.getOverview(siteId, {}).then((read) => {
      if (current) {
        setResult(read);
      }
    });
    return () => {
      current = false;
    };
  }, [client, siteId]);

  if (result === null) {
    return <p>{SITE_OVERVIEW_LOADING}</p>;
  }
  if (result.status !== "loaded") {
    return (
      <Panel
        heading="Overview unavailable"
        headingId="site-overview-unavailable-heading"
      >
        <p>
          The Overview could not be read
          {result.status === "unavailable" && result.message !== null
            ? `: ${result.message}`
            : "."}{" "}
          This is a statement about the read, not about the site&apos;s
          evidence.
        </p>
      </Panel>
    );
  }

  const overview = result.value;
  const cards = orderedOverviewCards(
    presentationProfileFor(overview.site_type),
    overview.cards,
  );
  const link = (signal: string, messageId: string) =>
    evidenceHref(signal, messageId);

  return (
    <div
      className="site-overview"
      data-overview-state={
        overview.window.start === null ? "empty" : "populated"
      }
    >
      <ObjectiveStrip
        overview={overview}
        evidencePageHref={evidencePageHref}
        link={link}
      />
      {cards.length === 0 ? null : (
        <section
          className="overview-cards"
          aria-labelledby="site-overview-domains-heading"
        >
          <h2
            className="overview-cards__heading"
            id="site-overview-domains-heading"
          >
            Domains
          </h2>
          <div className="overview-cards__grid">
            {cards.map(({ label, card }) => (
              <DomainCard
                key={card.domain_id}
                label={label}
                card={card}
                link={link}
              />
            ))}
          </div>
          <p className="overview-note">{overview.interval_statement}</p>
        </section>
      )}
      <Timeline overview={overview} />
      <Panel heading="Findings" headingId="site-overview-findings-heading">
        <p>{overview.findings_statement}</p>
      </Panel>
    </div>
  );
}

type LinkBuilder = (signal: string, messageId: string) => string;

function ObjectiveStrip({
  overview,
  evidencePageHref,
  link,
}: {
  overview: SiteOverviewReadModel;
  evidencePageHref: string;
  link: LinkBuilder;
}) {
  const { window, objective } = overview;
  const empty = window.start === null;
  return (
    <Panel
      heading="Operating objective"
      headingId="site-overview-objective-heading"
    >
      <FactList>
        <Fact term="Site assessment">
          <Badge tone="neutral">{objective.assessment.label}</Badge>{" "}
          <span className="overview-note">{objective.assessment.reason}</span>
        </Fact>
        <Fact term="Service delivered">
          {objective.service_delivered === null ? (
            "Not measured for this site type"
          ) : (
            <MetricValue metric={objective.service_delivered} link={link} />
          )}
        </Fact>
        <Fact term="Window">
          {empty
            ? "No window: no evidence has been accepted for this site."
            : `${window.start} to ${window.end} (${window.hours} h, ${
                window.basis === "REQUESTED" ? "requested" : "latest release"
              })`}
        </Fact>
        <Fact term="Evidence">
          {`${overview.accepted_in_window} accepted records from ${overview.sources_in_window} ${
            overview.sources_in_window === 1 ? "source" : "sources"
          } in this window. `}
          <Link to={evidencePageHref}>Open Site evidence</Link>
        </Fact>
      </FactList>
    </Panel>
  );
}

function signalOf(item: { device_id: string; signal_id: string }): string {
  return `${item.device_id}/${item.signal_id}`;
}

function MetricValue({
  metric,
  link,
}: {
  metric: OverviewMetric;
  link: LinkBuilder;
}) {
  if (metric.value === null) {
    return (
      <span className="overview-metric__gap">
        Not available. {metric.unavailable_because}
      </span>
    );
  }
  return (
    <span className="overview-metric">
      <span className="overview-metric__value">
        {metric.value} {metric.unit}
      </span>
      {metric.at === null ? null : (
        <span className="overview-note"> at {metric.at}</span>
      )}
      <span className="overview-metric__basis">{metric.basis}</span>
      {metric.evidence.length === 0 ? null : (
        <span className="overview-metric__evidence">
          Evidence:{" "}
          {metric.evidence.map((item, index) => (
            <span key={item.message_id}>
              {index === 0 ? null : ", "}
              <Link
                data-overview-evidence
                to={link(signalOf(item), item.message_id)}
                aria-label={`Inspect the ${signalOf(item)} record behind ${metric.label}`}
              >
                {signalOf(item)}
              </Link>
            </span>
          ))}
        </span>
      )}
    </span>
  );
}

function DomainCard({
  label,
  card,
  link,
}: {
  label: string;
  card: OverviewCard;
  link: LinkBuilder;
}) {
  const headingId = `site-overview-card-${card.domain_id.toLowerCase()}`;
  return (
    <Panel heading={label} headingId={headingId} headingLevel={3}>
      <p
        className="overview-card__assessment"
        data-overview-card={card.domain_id}
        data-overview-gaps={card.gaps.length}
        data-overview-values={
          card.metrics.filter((m) => m.value !== null).length
        }
      >
        <Badge tone="neutral">{card.assessment.label}</Badge>
      </p>
      {card.gaps.length === 0 ? null : (
        <p className="overview-card__gap" role="note">
          {`Coverage gap: ${card.gaps
            .map(
              (gap) =>
                `${signalOf(gap)} ${
                  gap.status === "NOT_REPORTED"
                    ? "reported no accepted record"
                    : "has no GOOD accepted record"
                }`,
            )
            .join("; ")} in this window.`}
        </p>
      )}
      <FactList>
        {card.metrics.map((metric) => (
          <Fact key={metric.metric_id} term={metric.label}>
            <MetricValue metric={metric} link={link} />
          </Fact>
        ))}
      </FactList>
      <p className="overview-card__coverage">
        {"Coverage: "}
        {card.coverage
          .map(
            (row) =>
              `${signalOf(row)} ${row.records} records, ${row.good} good, ${row.unavailable} unavailable`,
          )
          .join("; ")}
      </p>
    </Panel>
  );
}

const CHART_WIDTH = 720;
const CHART_HEIGHT = 150;
const MARGIN = { left: 44, right: 12, top: 10, bottom: 24 };
const DASH = [undefined, "6 4", "2 3"];

function isInterval(
  point: OverviewIntervalPoint | OverviewInstantPoint,
): point is OverviewIntervalPoint {
  return "start" in point;
}

function TimelinePanel({
  series,
  unit,
  start,
  end,
}: {
  series: OverviewSeries[];
  unit: string;
  start: number;
  end: number;
}) {
  const values = series.flatMap((item) =>
    item.points.map((point) => Number(point.value)),
  );
  const top = Math.max(unit === "%" ? 100 : 1, ...values);
  const plotWidth = CHART_WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = CHART_HEIGHT - MARGIN.top - MARGIN.bottom;
  const x = (time: string) =>
    MARGIN.left +
    ((Date.parse(time) - start) / Math.max(end - start, 1)) * plotWidth;
  const y = (value: string) =>
    MARGIN.top + plotHeight * (1 - Number(value) / top);
  const label = `${series.map((item) => item.label).join(", ")} (${unit}) over the window`;
  return (
    <figure className="overview-timeline__figure">
      <div className="overview-timeline__scroll">
        <svg
          className="overview-timeline__chart"
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          role="img"
          aria-label={label}
        >
          <line
            className="overview-timeline__axis"
            x1={MARGIN.left}
            x2={CHART_WIDTH - MARGIN.right}
            y1={MARGIN.top + plotHeight}
            y2={MARGIN.top + plotHeight}
          />
          <text
            className="overview-timeline__tick"
            x={MARGIN.left - 6}
            y={MARGIN.top + 8}
            textAnchor="end"
          >
            {Number(top.toFixed(1))}
          </text>
          <text
            className="overview-timeline__tick"
            x={MARGIN.left - 6}
            y={MARGIN.top + plotHeight}
            textAnchor="end"
          >
            0
          </text>
          <text
            className="overview-timeline__tick"
            x={MARGIN.left}
            y={CHART_HEIGHT - 6}
          >
            {new Date(start).toISOString().slice(11, 16)}Z
          </text>
          <text
            className="overview-timeline__tick"
            x={CHART_WIDTH - MARGIN.right}
            y={CHART_HEIGHT - 6}
            textAnchor="end"
          >
            {new Date(end).toISOString().slice(11, 16)}Z
          </text>
          {series.map((item, index) => (
            <g
              key={item.series_id}
              className={`overview-timeline__series overview-timeline__series--${item.series_id}`}
              strokeDasharray={DASH[index]}
            >
              {item.points.map((point) =>
                isInterval(point) ? (
                  <line
                    key={`${point.start}-${point.end}`}
                    x1={x(point.start)}
                    x2={Math.max(x(point.end), x(point.start) + 2)}
                    y1={y(point.value)}
                    y2={y(point.value)}
                  >
                    <title>{`${item.label}: ${point.value} ${item.unit}, ${point.start} to ${point.end}`}</title>
                  </line>
                ) : (
                  <circle
                    key={point.at}
                    cx={x(point.at)}
                    cy={y(point.value)}
                    r={2.5}
                  >
                    <title>{`${item.label}: ${point.value} ${item.unit} at ${point.at}`}</title>
                  </circle>
                ),
              )}
            </g>
          ))}
        </svg>
      </div>
      <figcaption className="overview-timeline__legend">
        {series.map((item) => (
          <span
            key={item.series_id}
            className={`overview-timeline__key overview-timeline__key--${item.series_id}`}
          >
            {`${item.label} (${item.unit}): ${item.points.length} ${
              item.kind === "INTERVAL_MEAN" ? "measured intervals" : "samples"
            }. ${item.basis}`}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}

function Timeline({ overview }: { overview: SiteOverviewReadModel }) {
  const { window, timeline } = overview;
  const plotted = timeline.filter((series) => series.points.length > 0);
  return (
    <Panel
      heading="Selected-window timeline"
      headingId="site-overview-timeline-heading"
    >
      <p className="overview-note">{overview.timeline_statement}</p>
      {window.start === null || window.end === null || plotted.length === 0 ? (
        <p>
          No accepted measurement in this window, so there is nothing to place
          on the timeline.
        </p>
      ) : (
        <div className="overview-timeline">
          {[...new Set(timeline.map((series) => series.unit))].map((unit) => {
            const group = timeline.filter((series) => series.unit === unit);
            return (
              <TimelinePanel
                key={unit}
                series={group}
                unit={unit}
                start={Date.parse(window.start as string)}
                end={Date.parse(window.end as string)}
              />
            );
          })}
        </div>
      )}
    </Panel>
  );
}
