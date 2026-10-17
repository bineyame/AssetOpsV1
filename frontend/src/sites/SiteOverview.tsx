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
 * signal has no record a metric can use in the window (none, none GOOD, no
 * interval span, or only overlapping records) shows no value and names the gap
 * with the backend's reason; the card lists the gap from the backend's
 * coverage, not from the profile. The timeline is context, not a status source.
 *
 * Evidence links open the Site > Evidence record inspector at the address
 * `evidenceHref` builds (`/sites/{id}/evidence?signal=DEV/SIG&record=MSG`);
 * the shell supplies the builder, because the substrate does not know routes.
 */

import { HourNotSelected, OverviewGrid, OverviewRefused } from "./overviewSlots";
import { awaitingMigration } from "./siteEvidenceClient";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { SiteWindowOverview, type WindowOverviewLinks } from "./SiteWindowOverview";
import type { FindingIndexClient } from "./findingIndexClient";

import { Badge, ChartNote, KeyValues, MetricCard, MetricCards, StatusBar } from "../ui";
import { AssessedPeriodTimeline, FuelRange } from "./assessmentGraphics";
import {
  capabilityPresentation,
  orderedOverviewCards,
  presentationProfileFor,
  type DomainPresentationProfile,
} from "./presentationProfile";
import type { EvidenceRead } from "./siteEvidenceClient";
import type {
  OverviewCard,
  OverviewInstantPoint,
  OverviewIntervalPoint,
  OverviewMetric,
  OverviewSeries,
  OverviewSelection,
  SiteOverviewClient,
  SiteOverviewReadModel,
  SiteWindowSummary,
} from "./siteOverviewClient";
import { isSiteWindowSummary } from "./siteOverviewClient";

export const SITE_OVERVIEW_LOADING = "Loading the site's overview.";

export interface SiteOverviewProps {
  siteId: string;
  client: SiteOverviewClient;
  /** The inspector address for one accepted record of one signal. */
  evidenceHref: (signal: string, messageId: string) => string;
  /** The Site > Evidence destination. */
  evidencePageHref: string;
  /** T028: the Finding detail address for one assessment id. */
  findingHref?: (assessmentId: string) => string;
  /** T028: Performance > Dispatch, optionally selecting one interval. */
  dispatchHref?: (assessmentId?: string) => string;
  /**
   * The Analysis of an assessed period: the Finding's Analysis tab, or
   * Dispatch's Analysis view for a Needed period without a Finding.
   */
  analysisHref?: (assessmentId: string, isFinding: boolean) => string;
  /** S5-01: destinations for an imported Site's selected-window Overview. */
  windowLinks?: WindowOverviewLinks;
  /** S5-02: the Site Finding index read for the selected day's list, handed in by the shell (imported Sites only). */
  findingIndex?: FindingIndexClient;
}

/** S5-01: the address parameters an imported Site's Overview keeps across reloads. */
const SELECTION_KEYS = ["date", "finding_id", "finding_revision_id"] as const;

function selectionOf(params: URLSearchParams): OverviewSelection {
  return {
    date: params.get("date"),
    finding_id: params.get("finding_id"),
    finding_revision_id: params.get("finding_revision_id"),
  };
}

function selectionKey(selection: OverviewSelection): string {
  return SELECTION_KEYS.map((k) => selection[k] ?? "").join("|");
}

/** What the served day and Finding would read as in the address (the server's values, copied). */
function servedSelection(summary: SiteWindowSummary): OverviewSelection {
  return {
    date: summary.window.utc_date,
    finding_id: summary.known_finding?.id ?? null,
    finding_revision_id: summary.known_finding?.revision_id ?? null,
  };
}

export function SiteOverview({
  siteId,
  client,
  evidenceHref,
  evidencePageHref,
  findingHref,
  dispatchHref,
  analysisHref,
  windowLinks,
  findingIndex,
}: SiteOverviewProps) {
  const [result, setResult] =
    useState<EvidenceRead<SiteOverviewReadModel | SiteWindowSummary> | null>(null);
  const [params, setParams] = useSearchParams();
  const selection = selectionOf(params);
  const key = selectionKey(selection);
  // The selection the shown result already answers: writing the served day and Finding into the address must
  // not read the same thing again.
  const answered = useRef<string | null>(null);
  // S5-02: the Finding list's reload reads the Overview again even when the address is unchanged.
  const [reloads, setReloads] = useState(0);
  const reload = () => {
    answered.current = null;
    setReloads((n) => n + 1);
  };

  useEffect(() => {
    if (answered.current === `${siteId}#${key}`) {
      return;
    }
    let current = true;
    setResult(null);
    client.getOverview(siteId, {}, selection).then((read) => {
      if (!current) {
        return;
      }
      setResult(read);
      if (read.status === "loaded" && isSiteWindowSummary(read.value)) {
        // Date change and reload keep the served day and the selected Finding version (packet "Outcome").
        const served = servedSelection(read.value);
        const servedKey = selectionKey(served);
        answered.current = `${siteId}#${servedKey}`;
        if (servedKey !== key) {
          const next = new URLSearchParams(params);
          for (const k of SELECTION_KEYS) {
            const v = served[k];
            if (v) {
              next.set(k, v);
            } else {
              next.delete(k);
            }
          }
          setParams(next, { replace: true });
        }
      } else {
        answered.current = null;
      }
    });
    return () => {
      current = false;
    };
    // `params` is read through `key`, which names every parameter this read uses.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, siteId, key, reloads]);

  const selectDay = (day: string) => {
    const next = new URLSearchParams(params);
    next.set("date", day);
    next.delete("finding_id");
    next.delete("finding_revision_id");
    setParams(next);
  };

  if (result === null) {
    return <p>{SITE_OVERVIEW_LOADING}</p>;
  }
  if (awaitingMigration(result)) {
    return (
      <OverviewRefused
        name="awaiting-migration"
        title="Awaiting evidence migration"
        reason={
          <span data-evidence-state="awaiting_migration">
            This site&apos;s configuration has moved to its stored Foundation versions. Its overview is awaiting
            evidence migration, so earlier results are not shown beside the updated configuration.
          </span>
        }
        gapText="Not shown: this Overview is awaiting evidence migration. This is not an empty result."
      />
    );
  }
  if (result.status !== "loaded") {
    return (
      <OverviewRefused
        name="unavailable"
        title="Overview unavailable"
        reason={
          <>
            The Overview could not be read
            {result.status === "unavailable" && result.message !== null
              ? `: ${result.message}`
              : "."}{" "}
            This is a statement about the read, not about the site&apos;s
            evidence.
          </>
        }
      />
    );
  }

  if (isSiteWindowSummary(result.value)) {
    if (windowLinks === undefined) {
      return (
        <OverviewRefused
          name="no-destinations"
          title="Overview unavailable"
          reason="This screen has no destinations for the selected-day Overview."
        />
      );
    }
    return (
      <SiteWindowOverview
        summary={result.value}
        links={windowLinks}
        onSelectDay={selectDay}
        findingIndex={findingIndex}
        onReload={reload}
      />
    );
  }
  const overview = result.value;
  const profile = presentationProfileFor(overview.site_type);
  const cards = orderedOverviewCards(profile, overview.cards);
  const link = (signal: string, messageId: string) =>
    evidenceHref(signal, messageId);
  // The Overview links to the backend's Findings; it never recomputes one.
  const findings = overview.findings as OverviewFinding[];
  const findingIds = new Set(
    findings.flatMap((f) => (f.finding_id === null ? [] : [f.finding_id])),
  );

  const empty = overview.window.start === null;
  return (
    <div
      className="site-overview site-window-overview"
      data-overview-state={empty ? "empty" : "populated"}
    >
      <OverviewGrid
        lead={
          <>
            <StatusBar other="Assessed for this window: the domain cards below only · no site-wide objective status">
              <Badge tone="neutral">{overview.objective.assessment.label}</Badge>{" "}
              <span className="overview-note">{overview.objective.assessment.reason}</span>
            </StatusBar>
            {cards.length === 0 ? null : (
              <MetricCards columns={cards.length >= 5 ? 5 : cards.length === 3 ? 3 : 4} label="Domains">
                {cards.map(({ label, card }) => (
                  <DomainCard
                    key={card.domain_id}
                    label={label}
                    card={card}
                    profile={profile}
                    link={link}
                    findingIds={findingIds}
                    findingHref={findingHref}
                    dispatchHref={dispatchHref}
                    analysisHref={analysisHref}
                  />
                ))}
              </MetricCards>
            )}
          </>
        }
        happened={{
          description: "Selected window · what the accepted evidence assessed, by domain",
          body: (
            <>
              <HourNotSelected scope={empty ? "no window yet" : "the selected evidence window"} />
              {cards.map(({ label, card }) => (
                <DomainPeriods key={card.domain_id} label={label} card={card} profile={profile} />
              ))}
              <p className="overview-note">{overview.interval_statement}</p>
            </>
          ),
        }}
        context={{
          description: "Selected window · context for the domains, not a status source",
          body: (
            <>
              <ObjectiveStrip overview={overview} evidencePageHref={evidencePageHref} link={link} />
              <Timeline overview={overview} />
              {cards.map(({ label, card }) => (
                <DomainContext key={card.domain_id} label={label} card={card} link={link} />
              ))}
            </>
          ),
        }}
        attention={{
          body: (
            <>
              <p>{overview.findings_statement}</p>
              {findings.length === 0 || findingHref === undefined ? null : (
                <ul className="cell-list" data-overview-findings>
                  {findings.map((finding) => (
                    <li key={finding.assessment_id}>
                      <Link
                        to={findingHref(finding.assessment_id)}
                        data-overview-finding-link={finding.assessment_id}
                      >
                        {finding.reading === undefined
                          ? "Assessed generator period"
                          : `${finding.reading.outcome}: ${finding.reading.headline}`}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ),
        }}
        money={{
          body: (
            <p data-overview-gap="money">
              No current amount: this Site&apos;s Overview has no money consequence read. This is not zero.
            </p>
          ),
        }}
        next={{
          body: (
            <div className="v69-prose" data-overview-next="evidence">
              <p>No supported next action is recorded on this Overview.</p>
              <p>
                <Link to={evidencePageHref}>Open Site evidence →</Link>
              </p>
            </div>
          ),
        }}
      />
    </div>
  );
}

type LinkBuilder = (signal: string, messageId: string) => string;

/** The Overview's `findings`: the backend's lineage summaries, as `/findings` lists them. */
interface OverviewFinding {
  assessment_id: string;
  finding_id: string | null;
  label: string;
  summary: string;
  /** The backend's plain reading (`plain.reading`), read time. */
  reading?: { outcome: string; headline: string };
}

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
    <div data-overview-objective>
      <KeyValues
        label="Operating objective"
        rows={[
          [
            "Service delivered",
            objective.service_delivered === null ? (
              "Not measured for this site type"
            ) : (
              <>
                <span className="overview-metric__label">{objective.service_delivered.label}</span>
                <MetricValue metric={objective.service_delivered} link={link} />
              </>
            ),
            "service",
          ],
          [
            "Window",
            empty
              ? "No window: no evidence has been accepted for this site."
              : `${window.start} to ${window.end} (${window.hours} h, ${
                  window.basis === "REQUESTED" ? "requested" : "latest release"
                })`,
            "window",
          ],
          [
            "Evidence",
            <>
              {`${overview.accepted_in_window} accepted records from ${overview.source_gateway_pairs_in_window} ${
                overview.source_gateway_pairs_in_window === 1 ? "source and gateway pair" : "source and gateway pairs"
              } in this window. `}
              <Link to={evidencePageHref}>Open Site evidence</Link>
            </>,
            "evidence",
          ],
        ]}
      />
    </div>
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
      {metric.window_note === null ? null : (
        <span className="overview-metric__window">{metric.window_note}</span>
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

interface DomainCardProps {
  label: string;
  card: OverviewCard;
  profile: DomainPresentationProfile | null;
  link: LinkBuilder;
  findingIds: Set<string>;
  findingHref?: (assessmentId: string) => string;
  dispatchHref?: (assessmentId?: string) => string;
  /**
   * The Analysis of an assessed period: the Finding's Analysis tab, or
   * Dispatch's Analysis view for a Needed period without a Finding.
   */
  analysisHref?: (assessmentId: string, isFinding: boolean) => string;
}

function capabilityOf(card: OverviewCard, profile: DomainPresentationProfile | null) {
  const assessment = card.assessment;
  return assessment.capability_id === undefined
    ? null
    : capabilityPresentation(
        profile,
        assessment.capability_id,
        assessment.capability_display_name ?? assessment.capability_id,
      );
}

/**
 * W1-F2: one domain as the mock's objective card (label, large state word, one note and its destination).
 * The domain's metrics and coverage are context, in Operating context; its assessed periods are in panel 1.
 */
function DomainCard({ label, card, profile, findingIds, findingHref, dispatchHref, analysisHref }: DomainCardProps) {
  const assessment = card.assessment;
  const capability = capabilityOf(card, profile);
  return (
    <MetricCard
      label={label}
      word
      tone="muted"
      value={<Badge tone="neutral">{assessment.label}</Badge>}
      data={{
        "data-overview-card": card.domain_id,
        "data-overview-gaps": String(card.gaps.length),
        "data-overview-values": String(card.metrics.filter((m) => m.value !== null).length),
      }}
      note={
        <>
          {capability === null ? null : (
            <span
              className="overview-card__capability"
              data-overview-capability={capability.id}
              data-emphasis={capability.emphasis}
            >
              {`${capability.label}: `}
            </span>
          )}
          {capability === null ? null : (
            <span data-overview-assessment-status={assessment.status}>{assessment.reason}</span>
          )}
          {card.gaps.length === 0 ? null : (
            <span className="overview-card__gap" role="note">
              {` Coverage gap: ${card.gaps.map((gap) => `${signalOf(gap)} ${gap.reason}`).join("; ")}.`}
            </span>
          )}
          {capability === null || assessment.lead_assessment_id === undefined ? null : (
            <span className="overview-card__assessment-link">
              {" "}
              {findingIds.has(assessment.lead_assessment_id) && findingHref !== undefined ? (
                <Link
                  to={findingHref(assessment.lead_assessment_id)}
                  data-overview-card-finding={assessment.lead_assessment_id}
                >
                  Open the Finding
                </Link>
              ) : dispatchHref !== undefined ? (
                <Link
                  to={dispatchHref(assessment.lead_assessment_id)}
                  data-overview-card-dispatch={assessment.lead_assessment_id}
                >
                  See it on Performance &gt; Dispatch
                </Link>
              ) : null}
              {analysisHref === undefined ? null : (
                <>
                  {" "}
                  <Link
                    to={analysisHref(assessment.lead_assessment_id, findingIds.has(assessment.lead_assessment_id))}
                    data-overview-card-analysis={assessment.lead_assessment_id}
                  >
                    View analysis
                  </Link>
                </>
              )}
            </span>
          )}
        </>
      }
    />
  );
}

/** A domain's assessed periods (panel 1), drawn only when the read carries its lead timeline. */
function DomainPeriods({ label, card, profile }: { label: string; card: OverviewCard; profile: DomainPresentationProfile | null }) {
  const assessment = card.assessment;
  if (capabilityOf(card, profile) === null || assessment.lead_timeline === undefined) return null;
  return (
    <div className="overview-card__timeline" data-overview-card-timeline={assessment.lead_assessment_id}>
      <AssessedPeriodTimeline
        compact
        source={assessment.lead_timeline}
        outcomes={assessment.lead_timeline.segments.map((s) => s.outcome)}
        assessmentId={assessment.lead_assessment_id}
      />
      {assessment.lead_timeline.fuel.status === "BOUNDED" ? (
        <FuelRange compact fuel={assessment.lead_timeline.fuel} reading={assessment.lead_timeline.fuel} />
      ) : null}
      <ChartNote>{label}: assessed periods in the selected window.</ChartNote>
    </div>
  );
}

/** A domain's metrics and record coverage (Operating context), as the mock's key-value list. */
function DomainContext({ label, card, link }: { label: string; card: OverviewCard; link: LinkBuilder }) {
  return (
    <div data-overview-domain-context={card.domain_id}>
      <KeyValues
        label={`${label} readings`}
        rows={card.metrics.map((metric) => [metric.label, <MetricValue metric={metric} link={link} />, metric.metric_id])}
      />
      <ChartNote>
        {`${label} coverage: `}
        {card.coverage
          .map((row) => `${signalOf(row)} ${row.records} records, ${row.good} good, ${row.unavailable} unavailable`)
          .join("; ")}
      </ChartNote>
    </div>
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
              item.kind === "INTERVAL_MEAN" ? "averaged readings" : "samples"
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
    <>
      <p className="overview-note" id="site-overview-timeline-heading">{overview.timeline_statement}</p>
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
    </>
  );
}
