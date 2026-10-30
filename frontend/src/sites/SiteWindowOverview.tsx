/**
 * S5-01 phase 2: the imported-Site selected-window Overview (`site-window-summary-1`).
 *
 * One UTC day `[00:00Z, next 00:00Z)`: the day's dispatch objective and status, the accepted-reading context and
 * timeline, and one bounded optional Finding fuel-cost card, each with exact drill-down links. Every state,
 * reason, amount and identifier is the server's (`site_overview/read.py`); this module only chooses words for the
 * server's state names and lays the day out. It derives no status and no amount, and it never sums Findings.
 *
 * - The money card shows an amount only when the server sends `PRICED` with both display bounds. Every other state
 *   is named, with its limiting state, the shared money gate's own raw state and the upstream status shown
 *   separately (Architect LR-01 deviations item 2): after a clock attestation and before the next schedule pass the
 *   card reads "upstream out of date" while the gate reads "pending reassessment".
 * - The Site Finding list is unavailable until the Site Finding index is delivered; it never claims to be empty.
 * - Unsupported v6.9 `mini` panels (Site totals, savings, battery or service health, renewable opportunity,
 *   recommendations) are absent, not drawn from the mock.
 *
 * The shell supplies the destination builders, because the substrate does not know routes.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  currentnessWords,
  DataTable,
  Disclosure,
  ExactReferences,
  Fact,
  FactList,
  CausalTimeline,
  ChartNote,
  moneyWords,
  ProductStatus,
  StatusBar,
  ValueBars,
  type ExactReference,
  type ProductWords,
} from "../ui";
import { SourceProvenanceNotice, SourceProvenanceRecord } from "./sourceProvenance";
import { clock, idWords, isDay, limitationCode, limitationWords, roleWords, shiftDay, stamp } from "./dispatchWords";
import { portionWords } from "./findingWords";
import { OUTCOME_WORDS } from "./findingPresentation";
import type { SiteWindowSummary, WindowMoney } from "./siteOverviewClient";
import type { FindingIndexClient, FindingIndexScope } from "./findingIndexClient";
import { OverviewFindingList } from "./OverviewFindingList";
import { HourNotSelected, OverviewGrid } from "./overviewSlots";
import { OutcomeBoard } from "./OutcomeBoard";
import type { OutcomeBoardClient } from "./outcomeBoardClient";
import {
  DEFAULT_SERVICE_HOUR,
  localDateOf,
  localDaysWindow,
  localHourWindow,
  type FuelRead,
  type MiniDepthClient,
  type MiniRead,
  type MiniWindowQuery,
  type RenewableRead,
  type ServiceRead,
} from "./miniDepthClient";
import "./w1ux02-site.css";

export interface WindowOverviewLinks {
  /** Performance > Dispatch for one UTC day, optionally opening one exact assessment revision. */
  dispatchDay: (day: string, revisionId?: string | null) => string;
  /** The Finding page at one exact Finding version. */
  finding: (findingId: string, revisionId: string) => string;
  /** Site > Financials pinned to one Finding version and, when known, one exact fuel-cost version. */
  financials: (findingId: string, revisionId: string, consequenceRevisionId: string | null) => string;
  /** Site > Financials > Assumptions at one exact assumption revision. */
  assumption: (revisionId: string) => string;
  /** Site > Evidence inspector for one accepted record. */
  evidenceRecord: (evidenceId: string) => string;
  /** S5-02: the full Site Findings page for one index scope (the same window, domain and page). */
  findingList?: (scope: FindingIndexScope) => string;
  /** post-W6 W1-a Q2 / R157: the Site's mounted Assets page, the Battery card's detail. */
  assets?: string;
  /** post-W6 W1-a Q3 / R159: the Foundation single line diagram at one instant (null: the bare mounted route). */
  sld?: (at: string | null) => string;
}

/** W4-02 B3: the mini-grid domains whose Overview cards read the mini depth endpoints (Backup has no card). */
export type OverviewMiniDomain = "service" | "fuel" | "renewable";

/** W4-02 B3: what a MINIGRID Overview needs to read its Service, Fuel and Renewable cards. */
export interface OverviewMiniReads {
  client: MiniDepthClient;
  /** The public Site code (S9). */
  siteCode: string;
  /** The Site's IANA zone: the cards read the Site-local day and its local noon hour. */
  timeZone: string;
  /** The Performance tab for one domain at the exact window and cutoff the card read. */
  detailHref: (domain: OverviewMiniDomain, window: MiniWindowQuery) => string;
}

export interface SiteWindowOverviewProps {
  summary: SiteWindowSummary;
  links: WindowOverviewLinks;
  /** Select another UTC day (the parent writes it to the address, dropping any Finding pin). */
  onSelectDay: (day: string) => void;
  /** S5-02: the Site Finding index read, handed in by the shell; without it the list stays unavailable. */
  findingIndex?: FindingIndexClient;
  /** S5-02: read the Overview again (the list's reload affordance). */
  onReload?: () => void;
  /** W4-02 B3: the mini reads; without them the Service, Fuel and Renewable cards keep their no-read state. */
  mini?: OverviewMiniReads;
  /** OUT-B B5: the Site outcome board read; the board replaces the Service, Fuel and Renewable cards. */
  outcomeBoard?: OutcomeBoardClient;
}

/**
 * W1-UX-02: why the money card shows no amount, by the server's state name (packet "S5 no-amount states").
 * The shared money words own the states they cover; the rest are Overview domain states kept here as
 * `ProductWords`. An unrecognised state falls back to the shared neutral words, never a positive claim.
 */
function localMoney(label: string, sentence: string, tone: ProductWords["tone"], next?: string): ProductWords {
  return { label, sentence, tone, code: null, unrecognised: false, ...(next === undefined ? {} : { next }) };
}

const LOCAL_MONEY_WORDS: Record<string, ProductWords> = {
  PRICED: localMoney(
    "Current amount",
    "This range uses the current version of this Finding and a recorded diesel price.",
    "positive",
  ),
  ABSENT: localMoney(
    "No Finding on this day",
    "A complete, current search found no Finding overlapping this day, so there is no fuel cost to show.",
    "neutral",
  ),
  SOURCE_CLOSED: localMoney(
    "No current amount: source not open",
    "The source of these readings is not open for current use, so only records kept for the audit are shown. This is not zero.",
    "limited",
  ),
  UPSTREAM_UNASSESSED: localMoney(
    "No amount: day not checked",
    "This day has not been assessed, so no amount is shown. This is not zero.",
    "neutral",
  ),
  UPSTREAM_PENDING: localMoney(
    "No amount yet: checks still waiting",
    "A check this day depends on is still waiting, or changed while it was read, so no amount is shown. This is not zero.",
    "waiting",
    "Look again after the day has been checked.",
  ),
  UPSTREAM_STALE: localMoney(
    "Upstream out of date",
    "Something this day depends on is out of date, or its checks have stopped, so no amount is shown. This is not zero.",
    "limited",
    "Treat the day as out of date until it is checked again.",
  ),
  UPSTREAM_FAILED: localMoney(
    "No amount: a check did not finish",
    "A check this day depends on did not finish, so no amount is shown. This is not zero.",
    "problem",
  ),
  SUPERSEDED: localMoney(
    "Earlier Finding version",
    "A newer version of this Finding exists, so no current amount is shown for this earlier one.",
    "neutral",
  ),
  CONSEQUENCE_PENDING: localMoney(
    "Fuel cost still being worked out",
    "The fuel cost for this Finding version is still being worked out, so no amount is shown yet. This is not zero.",
    "waiting",
  ),
  CONSEQUENCE_STALE: localMoney(
    "Fuel cost out of date",
    "The fuel cost for this Finding version is out of date, so no current amount is shown. This is not zero.",
    "limited",
  ),
  QUANTITY_UNAVAILABLE: localMoney(
    "Fuel quantity not known",
    "The generator power readings do not bound a fuel quantity for this Finding, so no amount is shown. This is not zero.",
    "limited",
  ),
  MINOR_UNIT_UNKNOWN: localMoney(
    "Currency unit not known",
    "The currency's smallest unit is not known, so no amount is displayed. This is not zero.",
    "limited",
  ),
};

/** Shared money states (W1-UX-01 `moneyWords`) the card uses as they are. */
const SHARED_MONEY_STATES = ["PENDING_REASSESSMENT", "WITHHELD_GENERATOR_SERIES", "UNPRICED", "MIXED_OR_UNKNOWN_SOURCE"];

/** Every money state the card names, by the server's state name. */
export const MONEY_STATE_WORDS: Record<string, ProductWords> = {
  ...LOCAL_MONEY_WORDS,
  ...Object.fromEntries(SHARED_MONEY_STATES.map((state) => [state, moneyWords(state)])),
};

/** Words for one money state: the card's own, the shared map's, or the shared neutral fallback. */
export function overviewMoneyWords(state: string): ProductWords {
  const own = Object.prototype.hasOwnProperty.call(MONEY_STATE_WORDS, state) ? MONEY_STATE_WORDS[state] : undefined;
  return own === undefined ? moneyWords(state) : { ...own, code: state };
}

/** The shared LR-01 money gate's own state, shown beside the card's state. */
const GATE_WORDS: Record<string, string> = {
  ELIGIBLE: "Eligible",
  PENDING_REASSESSMENT: "Pending reassessment",
  WITHHELD_GENERATOR_SERIES: "Withheld: generator power series",
};

function Code({ value }: { value: string | null | undefined }) {
  return (
    <code data-vocabulary-exempt="source-reference">{value ?? "none"}</code>
  );
}

/** One labelled exact value per recorded reason. */
function reasonReferences(label: string, reasons: readonly string[] | null | undefined): ExactReference[] {
  return (reasons ?? []).map((reason, i) => ({ label: `${label} ${i + 1}`, value: reason }));
}

/** The day's plain scope, used by every state line on this page. */
function dayScope(summary: SiteWindowSummary): string {
  return `${summary.window.utc_date}, one UTC day at this site`;
}

/** Position of an instant within the selected day, as a percentage (layout only). */
function dayPercent(instant: string | null, start: string): number | null {
  if (instant === null) {
    return null;
  }
  const t = Date.parse(instant);
  const s = Date.parse(start);
  if (Number.isNaN(t) || Number.isNaN(s)) {
    return null;
  }
  return Math.min(100, Math.max(0, ((t - s) / 86_400_000) * 100));
}

function DaySelector({ summary, onSelectDay }: { summary: SiteWindowSummary; onSelectDay: (day: string) => void }) {
  const day = summary.window.utc_date;
  return (
    <>
    <div className="v69-chips window-day" data-window-date={day}>
      <label className="dispatch-day__label">
        <span>UTC day</span>
        <input
          className="v69-chip-control"
          type="date"
          value={day}
          data-window-date-input
          onChange={(event) => {
            if (isDay(event.target.value)) {
              onSelectDay(event.target.value);
            }
          }}
        />
      </label>
      {/* Day navigation is navigation: links to the same page with another `date` (and no Finding pin). */}
      <Link className="button" to={`?date=${shiftDay(day, -1)}`} data-window-day-link="previous">
        Previous day
      </Link>
      <Link className="button" to={`?date=${shiftDay(day, 1)}`} data-window-day-link="next">
        Next day
      </Link>
      {/* W1-F2 compaction: the day's bounds sit in the chip row (one line), not a separate note. */}
      <span className="v69-chart-note window-day__bounds" data-window-bounds>
        {stamp(summary.window.start)} to {stamp(summary.window.end)} UTC, start included, end excluded.
      </span>
    </div>
    </>
  );
}

/**
 * W1-UX-02: whether the day's answer is current, in the shared words, with the source's open state beside it.
 * The recorded reasons and exact read references move to the closed disclosure.
 */
function FreshnessStrip({ summary }: { summary: SiteWindowSummary }) {
  const f = summary.freshness;
  const a = summary.assessment;
  const accepted = summary.watermarks.accepted_source;
  // Review fix M3: the readings state is said once. When its words equal the statusbar's (same "as of"), the
  // statusbar carries it and this line keeps only the source sentence.
  const sameAsStatusbar = currentnessWords(f.state).label === objectiveWords(a.state).label;
  return (
    <div className="window-freshness" data-freshness-card>
        {/* W1-F2: one note-size line (readings state and source state), not a second state block in panel 1. */}
        <p className="v69-chart-note" data-freshness-state={f.state} data-freshness-in-statusbar={sameAsStatusbar ? "yes" : "no"}>
          {sameAsStatusbar ? null : (
            <>
              <ProductStatus inline words={currentnessWords(f.state)} scope={dayScope(summary)} asOf={summary.db_now} />{" "}
            </>
          )}
          <span data-source-open={f.source_open ? "open" : "closed"}>
            {f.source_open
              ? "The source of these readings is open for current use."
              : "The source of these readings is closed for current use: only records kept for the audit are shown."}
          </span>
        </p>
        <div data-window-reasons="freshness">
          <ExactReferences
            name="window-assessment"
            variant="tech"
            references={[
              { label: "Day assessment", value: a.window_assessment_revision_id },
              { label: "Assessment pass", value: a.run_id },
              { label: "Assessment state", value: a.state },
              ...(a.status_reasons ?? []).map((reason, i) => ({ label: `Recorded reason ${i + 1}`, value: reason })),
              { label: "Day state", value: f.state },
              // post-W6 W1-a Q4 / R164: the Finding's reasons carry their own label, unique beside the assessment's.
              ...reasonReferences("Finding reason", f.reasons),
              { label: "Source state", value: f.source_reason },
              {
                label: "Accepted records counted",
                value: accepted === null ? null : String(accepted.count),
              },
              {
                label: accepted === null ? "Why the records could not be counted" : "Accepted records reference",
                value: accepted === null ? summary.watermarks.accepted_source_reason : accepted.sha256,
              },
              { label: "Input reference", value: summary.watermarks.input_sha256 },
              { label: "Finding match reference", value: summary.watermarks.match_pass_id },
              { label: "Access reference", value: summary.access_basis },
            ]}
          />
        </div>
    </div>
  );
}

function coverageRoles(coverage: unknown): string {
  if (coverage === null || typeof coverage !== "object") return "assessment coverage is not available for this day.";
  const n = Object.keys(coverage as Record<string, unknown>).length;
  return n === 0 ? "assessment coverage is not available for this day." : `${n} measured ${n === 1 ? "role" : "roles"} covered.`;
}

/**
 * W1-UX-01: the day's objective on the shared answer card. The state words
 * come from the shared map; CLOSED stays a domain state here. Nothing is
 * derived: the headline says only what the assessment read states.
 */
function objectiveWords(state: string): ProductWords {
  if (state === "CLOSED") {
    return {
      label: "Not open for current use",
      sentence: "The source of these readings is not open for current use, so no current answer is shown.",
      tone: "limited",
      code: state,
      unrecognised: false,
    };
  }
  if (state === "UNKNOWN") {
    return { ...currentnessWords("UNKNOWN"), sentence: "No assessment is selected for this day, so nothing is concluded about it." };
  }
  return currentnessWords(state);
}

/**
 * W1-F2: the mock's statusbar - the day's assessment state, scope and "as of" - above the panels. It is a state
 * line, not a panel, and it claims nothing beyond the dispatch assessment this Overview reads.
 */
function DayStatus({ summary, links, reads }: { summary: SiteWindowSummary; links: WindowOverviewLinks; reads: OverviewReadable | null }) {
  const a = summary.assessment;
  const day = summary.window.utc_date;
  return (
    <StatusBar
      data={{ "data-overview-status": a.state }}
      other={
        reads === null
          ? "Assessed for this day: dispatch only · the other objectives have no read on this Overview"
          : overviewReadsStrip(reads)
      }
      action={
        a.state === "CLOSED" ? undefined : (
          <Link to={links.dispatchDay(day, a.window_assessment_revision_id)} data-window-dispatch-link={day}>
            Open this day in Performance &gt; Dispatch
          </Link>
        )
      }
    >
      <span data-assessment-state={a.state}>
        <ProductStatus inline words={objectiveWords(a.state)} scope={dayScope(summary)} asOf={summary.db_now} />
      </span>
    </StatusBar>
  );
}

/** Final review ruling 1 (H3): which objective reads on a MINIGRID Overview completed with a well-formed answer. */
export interface OverviewReadable {
  service: boolean;
  dispatch: boolean;
  fuel: boolean;
  renewable: boolean;
}

/** Ruling 1: the readable names in Service, Dispatch, Fuel, Renewable order; never a value inferred from readability. */
export function overviewReadsStrip(reads: OverviewReadable): string {
  const names = (
    [
      ["Service", reads.service],
      ["Dispatch", reads.dispatch],
      ["Fuel", reads.fuel],
      ["Renewable", reads.renewable],
    ] as const
  )
    .filter(([, readable]) => readable)
    .map(([name]) => name);
  if (names.length === 0) return "No objective read is available for this selection.";
  return `Reads on this Overview: ${names.join(", ")}. Each card shows what its selected period supports.`;
}

/**
 * Ruling 1: a mini read is readable when it completed with an authorized, well-formed response (an UNKNOWN envelope
 * included); loading, refused (409/503/401/403) and unavailable or malformed reads are not. Dispatch is the loaded
 * Overview summary itself, so it is readable whenever this Overview renders.
 */
function overviewReadable(state: OverviewMiniState | null): OverviewReadable {
  const ok = (read: MiniRead<unknown> | null | undefined) => read !== null && read !== undefined && read.status === "loaded";
  return { service: ok(state?.service), dispatch: true, fuel: ok(state?.fuel), renewable: ok(state?.renewable) };
}

export const MINIGRID_OBJECTIVE =
  "Objective: serve residential, clinic and productive loads while protecting the battery reserve. Check each card for the supported result and its limits.";

/** The mock's objective line: the assessment states no operating objective, so none is shown. */
function ObjectiveLine({ summary, minigrid }: { summary: SiteWindowSummary; minigrid: boolean }) {
  if (minigrid) {
    return (
      <p className="v69-objective" data-objective-statement="minigrid">
        {MINIGRID_OBJECTIVE}
      </p>
    );
  }
  if (summary.assessment.state === "CLOSED") {
    return <p className="v69-objective">Objective: nothing here is a current answer.</p>;
  }
  return (
    <p className="v69-objective" data-objective-statement="not-stated">
      Objective: the assessment does not state an operating objective for this day, so none is shown here.
    </p>
  );
}

interface OverviewMiniState {
  key: string;
  localDay: string;
  hour: MiniWindowQuery;
  day: MiniWindowQuery;
  service: MiniRead<ServiceRead> | null;
  fuel: MiniRead<FuelRead> | null;
  renewable: MiniRead<RenewableRead> | null;
}

/**
 * Q24/B3: one renewable read for the Site-local day of the selected UTC day's start, and one service and one fuel
 * read for that local day's noon hour, all sharing one `known_at` fixed when the reads start. No backup read.
 */
function useOverviewMini(mini: OverviewMiniReads | undefined, utcDay: string): OverviewMiniState | null {
  const client = mini?.client;
  const siteCode = mini?.siteCode;
  const timeZone = mini?.timeZone;
  const key = `${siteCode}|${timeZone}|${utcDay}`;
  const [state, setState] = useState<OverviewMiniState | null>(null);
  useEffect(() => {
    if (client === undefined || siteCode === undefined || timeZone === undefined) {
      setState(null);
      return;
    }
    let current = true;
    const known_at = new Date().toISOString();
    const localDay = localDateOf(timeZone, Date.parse(`${utcDay}T00:00:00Z`));
    const hour = { ...localHourWindow(timeZone, localDay, DEFAULT_SERVICE_HOUR), known_at };
    const day = { ...localDaysWindow(timeZone, localDay, 1), known_at };
    setState({ key, localDay, hour, day, service: null, fuel: null, renewable: null });
    const settle = <K extends "service" | "fuel" | "renewable">(name: K, read: OverviewMiniState[K]) => {
      if (current) setState((prev) => (prev === null || prev.key !== key ? prev : { ...prev, [name]: read }));
    };
    void client.getService(siteCode, hour).then((r) => settle("service", r));
    void client.getFuel(siteCode, hour).then((r) => settle("fuel", r));
    void client.getRenewable(siteCode, day).then((r) => settle("renewable", r));
    return () => {
      current = false;
    };
  }, [client, siteCode, timeZone, utcDay, key]);
  return state !== null && state.key === key ? state : null;
}

/** Panel 1 body: the day's assessed reading, its limitations and the exact references, in the mock's prose slot. */
function DayReading({ summary }: { summary: SiteWindowSummary }) {
  const a = summary.assessment;
  const closed = a.state === "CLOSED";
  return (
    <div className="v69-prose">
      {closed ? <ChartNote>Nothing in this panel is a current answer.</ChartNote> : null}
      {closed || a.claim_level === null ? (
        closed ? null : <ChartNote data={{ "data-assessment-claim": "none" }}>No assessed reading is selected for this day.</ChartNote>
      ) : (
        <ChartNote data={{ "data-assessment-claim": a.claim_level }}>
          Day reading: {OUTCOME_WORDS[a.claim_level] ?? "Assessed"}. {a.dispatch_intervals.length}{" "}
          {a.dispatch_intervals.length === 1 ? "operating period" : "operating periods"} assessed;{" "}
          {coverageRoles(a.coverage)}
        </ChartNote>
      )}
      {/* W1-F2 compaction: each recorded limitation, in its words, on one note line (none dropped). */}
      {a.limitations.length === 0 ? null : (
        <ChartNote data={{ "data-assessment-limitations": String(a.limitations.length) }}>
          {[...new Set(a.limitations.map((l) => limitationCode(String(l))))].map((code, n) => (
            <span key={code} data-assessment-limitation={code}>
              {n === 0 ? "" : " · "}
              {limitationWords(code)}
            </span>
          ))}
        </ChartNote>
      )}
      {/* Review fix M3: the day reading's references join the freshness references in panel 1's one disclosure. */}
    </div>
  );
}

/**
 * The mock's causal strip, from the read's assessed periods only: when each started and ended and what the
 * assessment concluded for the generator. Each opens the period in Dispatch.
 */
function PeriodStrip({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const day = summary.window.utc_date;
  const intervals = summary.assessment.dispatch_intervals;
  if (intervals.length === 0) {
    return <p data-window-periods="none">No assessed period is selected for this day.</p>;
  }
  return (
    <CausalTimeline
      label={`Assessed operating periods on ${day}`}
      events={intervals.map((i) => ({
        key: i.revision_id,
        time: `${clock(i.start)} to ${clock(i.end)}`,
        title: `Generator ${portionWords(i.claim_level ?? "").toLowerCase()}`,
        tone: (i.claim_level ?? "").toUpperCase() === "INDETERMINATE" ? "gap" : undefined,
        detail: (
          <Link to={links.dispatchDay(day, i.revision_id)} data-window-interval={i.revision_id}>
            Open in Dispatch
          </Link>
        ),
      }))}
    />
  );
}

/** Plain names for the assessed-period fills the timeline draws (the bar classes in primitives.css). */
const TIMELINE_LEGEND: { key: string; label: string }[] = [
  { key: "necessary", label: "Generator needed" },
  { key: "candidate_avoidable", label: "Generator possibly avoidable" },
  { key: "indeterminate", label: "Not clear" },
  { key: "other", label: "Other" },
];

/**
 * W1-UX-02: the day as a visual timeline - assessed periods and when each kind of reading arrived - with a
 * readable legend and a text description. It draws only the read's periods and reading spans; a not-current
 * day says so beside the drawing.
 */
function Timeline({ summary }: { summary: SiteWindowSummary }) {
  const day = summary.window.utc_date;
  const intervals = summary.assessment.dispatch_intervals;
  const coverage = summary.context.coverage ?? [];
  const current = summary.freshness.state === "CURRENT";
  const shownKeys = new Set(intervals.map((i) => (i.claim_level ?? "other").toLowerCase()));
  const legend = TIMELINE_LEGEND.filter((l) => shownKeys.has(l.key));
  const description =
    intervals.length === 0
      ? `No assessed period is drawn for ${day}.`
      : intervals
          .map((i) => `${clock(i.start)} to ${clock(i.end)}: generator ${portionWords(i.claim_level ?? "").toLowerCase()}`)
          .join("; ");
  return (
    <>
      <figure
        className="window-timeline-figure"
        data-window-timeline-figure
        aria-label={`Day timeline for ${day}, 00:00 to 24:00 UTC. ${description}`}
      >
        <figcaption className="window-timeline-figure__caption">
          When the generator was in use and when readings arrived on {day}, 00:00 to 24:00 UTC.
          {current ? "" : " These periods come from an answer that is not current; see the state line above."}
        </figcaption>
        <div className="window-timeline" data-window-timeline={intervals.length}>
          <div className="window-timeline__axis" aria-hidden="true">
            <span>00:00</span>
            <span>06:00</span>
            <span>12:00</span>
            <span>18:00</span>
            <span>24:00</span>
          </div>
          <div className="window-timeline__row">
            <span className="window-timeline__label">Assessed periods</span>
            <div className="window-timeline__track">
              {intervals.map((i) => {
                const lo = dayPercent(i.start, summary.window.start) ?? 0;
                const hi = dayPercent(i.end, summary.window.start) ?? 100;
                return (
                  <span
                    key={i.revision_id}
                    className={`window-timeline__bar window-timeline__bar--${(i.claim_level ?? "other").toLowerCase()}`}
                    style={{ left: `${lo}%`, width: `${Math.max(0.5, hi - lo)}%` }}
                    title={`${clock(i.start)} to ${clock(i.end)}: generator ${portionWords(i.claim_level ?? "")}`}
                  />
                );
              })}
            </div>
          </div>
          {coverage.map((c) => {
            // Review Low 7c: a reading kind that repeats is told apart by its device, in words.
            const name = c.role ? roleWords(c.role) : "Unnamed reading";
            const repeats = coverage.filter((o) => (o.role ? roleWords(o.role) : "Unnamed reading") === name).length > 1;
            const lo = dayPercent(c.first_source_time, summary.window.start);
            const hi = dayPercent(c.last_source_time, summary.window.start);
            return (
              <div className="window-timeline__row" key={`${c.device_id}/${c.signal_id}`}>
                <span className="window-timeline__label">{repeats ? `${name} · ${idWords(c.device_id)}` : name}</span>
                <div className="window-timeline__track">
                  {lo === null || hi === null ? null : (
                    <span
                      className="window-timeline__bar window-timeline__bar--readings"
                      style={{ left: `${lo}%`, width: `${Math.max(0.5, hi - lo)}%` }}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
        {legend.length === 0 && coverage.length === 0 ? null : (
          <ul className="window-timeline-legend" data-window-timeline-legend>
            {legend.map((l) => (
              <li className="window-timeline-legend__item" key={l.key}>
                <span
                  className={`window-timeline-legend__swatch window-timeline__bar window-timeline__bar--${l.key}`}
                  aria-hidden="true"
                />
                {l.label}
              </li>
            ))}
            {coverage.length === 0 ? null : (
              <li className="window-timeline-legend__item">
                <span
                  className="window-timeline-legend__swatch window-timeline__bar window-timeline__bar--readings"
                  aria-hidden="true"
                />
                Readings received
              </li>
            )}
          </ul>
        )}
      </figure>
    </>
  );
}

/** MOCK DEVIATION D1 (R388): the mock's operating-context lanes stay as the W1-F5b-ruled timeline/context rows. */
function Context({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const c = summary.context;
  if (c.series === null || c.coverage === null) {
    return (
      <p data-window-context="unavailable">
        Accepted readings for this day could not be read: <Code value={c.reason ?? null} />
      </p>
    );
  }
  return (
    <>
      <ChartNote data={{ "data-window-context": String(c.series.length) }}>
        {c.total ?? c.series.length} accepted readings on this day
        {c.truncated ? `; the first ${c.series.length} are listed` : ""}.
        {c.coverage.length === 0 ? " No accepted reading covers this day." : ""}
      </ChartNote>
      {/* Review fix M5(a): the server's gap reason is never shown verbatim; its meaning is stated in plain words. */}
      {c.gaps_reason ? (
        <ChartNote data={{ "data-window-gaps": "" }}>
          No rule yet says which gaps in the readings matter here; the reading counts are shown instead.
        </ChartNote>
      ) : null}
      {/* W1-F2 compaction: the per-input table and the record links are reference detail, in one closed disclosure. */}
      {c.coverage.length === 0 && c.series.length === 0 ? null : (
        <Disclosure summary="Readings per input, with links to each record" name="window-coverage" variant="tech">
      {c.coverage.length === 0 ? null : (
        <DataTable labelledBy="site-window-context-heading">
          <thead>
            <tr>
              <th scope="col">Reading</th>
              <th scope="col">Records</th>
              <th scope="col">Good</th>
              <th scope="col">First</th>
              <th scope="col">Last</th>
            </tr>
          </thead>
          <tbody>
            {c.coverage.map((row) => (
              <tr key={`${row.device_id}/${row.signal_id}`}>
                <td>
                  {row.role ? roleWords(row.role) : row.signal_id}{" "}
                  <span className="cell-secondary" data-vocabulary-exempt="source-reference">
                    {row.device_id}/{row.signal_id}
                  </span>
                </td>
                <td>{row.records}</td>
                <td>{row.good}</td>
                <td>{clock(row.first_source_time)}</td>
                <td>{clock(row.last_source_time)}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      {c.series.length === 0 ? null : (
        <div data-disclosure-part="window-readings">
          <ul className="cell-list" data-window-readings={c.series.length}>
            {c.series.map((r) => (
              <li key={r.evidence_id}>
                <Link to={links.evidenceRecord(r.evidence_id)} data-window-evidence-link={r.evidence_id}>
                  {clock(r.time)} {r.role ? roleWords(r.role) : r.signal_id}: {r.value ?? "no value"} {r.unit ?? ""}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
        </Disclosure>
      )}
    </>
  );
}

function MoneyLinks({ money, links, day }: { money: WindowMoney; links: WindowOverviewLinks; day: string }) {
  const fid = money.finding_id;
  const rid = money.finding_revision_id;
  if (fid === null || rid === null) {
    return null;
  }
  const assumptions = Object.keys(money.links.assumption_revisions ?? {});
  const evidence = Object.keys(money.links.evidence_records ?? {});
  const assessments = Object.keys(money.links.assessment_revisions ?? {});
  return (
    <ul className="cell-list" data-window-money-links>
      <li>
        <Link to={links.financials(fid, rid, money.consequence_revision_id)} data-window-financials-link>
          Fuel cost for this Finding version
        </Link>
      </li>
      {assumptions.map((a) => (
        <li key={a}>
          <Link to={links.assumption(a)} data-window-assumption-link={a}>
            Price assumption revision
          </Link>
        </li>
      ))}
      {assessments.map((a) => (
        <li key={a}>
          <Link to={links.dispatchDay(day, a)} data-window-lineage-assessment={a}>
            Assessment this amount uses
          </Link>
        </li>
      ))}
      {evidence.length === 0 ? null : (
        <li>
          {evidence.length} accepted records this amount uses:{" "}
          {evidence.slice(0, 20).map((e, n) => (
            <span key={e}>
              {n === 0 ? "" : ", "}
              <Link to={links.evidenceRecord(e)} data-window-lineage-evidence={e}>
                record {n + 1}
              </Link>
            </span>
          ))}
          {evidence.length > 20 ? ` and ${evidence.length - 20} more on the fuel cost page` : ""}
        </li>
      )}
    </ul>
  );
}

/**
 * W1-UX-02: the bounded money card. An amount (and its low/high bars) appears only for `PRICED` with both display
 * bounds; every other state is named in the shared or local words, never as zero. The plain "as of" bound sits
 * beside the state; Finding, fuel-cost and method references, limiting states and the recorded label move to the
 * closed disclosure.
 */
function Money({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const m = summary.money;
  const gate = m.eligibility?.state ?? null;
  const priced = m.state === "PRICED" && m.amount_low !== null && m.amount_high !== null;
  // A PRICED read missing a bound has no amount to call current: use the shared non-positive fallback words.
  const w = m.state === "PRICED" && !priced ? { ...moneyWords("PRICED"), code: "PRICED" } : overviewMoneyWords(m.state);
  const low = priced ? Number(m.amount_low) : Number.NaN;
  const high = priced ? Number(m.amount_high) : Number.NaN;
  const scope = m.finding_id ? `One Finding overlapping ${summary.window.utc_date}` : dayScope(summary);
  return (
      <div
        className="window-money"
        data-money-state={m.state}
        data-money-gate={gate ?? "none"}
        data-consequence-revision-id={m.consequence_revision_id ?? ""}
      >
        {priced ? (
          <p className="window-money__amount v69-money" data-money-amount>
            {m.amount_low} to {m.amount_high} {m.currency}
          </p>
        ) : (
          <p className="window-money__none v69-money v69-money--word" data-money-amount="none">
            No current amount.
          </p>
        )}
        {/* W1-F2 compaction: the state line stays visible in the strip's inline form (same words and bound). */}
        {/* Review fix M3: the money state differs from the statusbar's, so it stays as one note-size line. */}
        <p className="window-money__state v69-chart-note" data-money-state-line>
          <ProductStatus inline words={w} scope={scope} asOf={summary.db_now} />
        </p>
        {m.finding_id ? (
          <SourceProvenanceNotice provenance={m.source_provenance} subject="cost" name="overview-money" compact record="elsewhere" />
        ) : null}
        {m.finding_id ? (
          <ChartNote data={{ "data-money-qualifier": "" }}>
            A modelled range of possible extra fuel cost for one Finding, not money lost or saved.
          </ChartNote>
        ) : null}
        {/* W1-F2 compaction: the bars, gate and upstream facts, links and exact references, in one closed disclosure. */}
        <Disclosure summary={m.finding_id && m.source_provenance ? "Cost range, money gate, source record and links" : "Cost range, money gate and links"} name="window-money-detail" variant="tech">
        {priced && Number.isFinite(low) && Number.isFinite(high) ? (
          <ValueBars
            title="Possible extra fuel cost for this Finding"
            items={[
              { label: "Lower bound", key: "low", value: low, valueText: `${m.amount_low} ${m.currency ?? ""}`.trim() },
              { label: "Upper bound", key: "high", value: high, valueText: `${m.amount_high} ${m.currency ?? ""}`.trim() },
            ]}
          />
        ) : null}
        <FactList>
          <Fact term="Money gate">
            <span data-money-gate-state={gate ?? "none"}>
              {gate === null ? "Not read" : (GATE_WORDS[gate] ?? "Not recognised")}
            </span>
          </Fact>
          <Fact term="Upstream">
            <span data-money-upstream={m.upstream.status}>{currentnessWords(m.upstream.status).label}</span>
          </Fact>
        </FactList>
        <MoneyLinks money={m} links={links} day={summary.window.utc_date} />
        <ExactReferences
          name="window-money"
          references={[
            { label: "Amount state", value: m.state },
            { label: "Finding reference", value: m.finding_id },
            { label: "Finding version reference", value: m.finding_revision_id },
            { label: "Fuel cost version reference", value: m.consequence_revision_id },
            { label: "Cost method reference", value: m.model_version },
            { label: "Money gate state", value: gate },
            ...reasonReferences("Limiting reason", m.limitation),
            { label: "Upstream state", value: m.upstream.status },
            ...reasonReferences("Upstream reason", m.upstream.reasons),
            { label: "Money gate note", value: m.eligibility?.note ?? null },
            { label: "Recorded cost label", value: m.label },
          ]}
        />
        {/* W1-F5b (carry 8): the source record folds into this one closed row, not a second one. */}
        {m.finding_id && m.source_provenance ? (
          <div className="window-money__source-record" data-source-record="overview-money">
            <p>
              <strong>Source record for this cost</strong>
            </p>
            <SourceProvenanceRecord provenance={m.source_provenance} />
          </div>
        ) : null}
        </Disclosure>
      </div>
  );
}

/** W1-F2 compaction: the mock's "Open financial bridge" link, in the money panel's header, for the Finding's fuel cost. */
function MoneyAction({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const m = summary.money;
  if (m.finding_id === null || m.finding_revision_id === null) return null;
  return (
    <Link to={links.financials(m.finding_id, m.finding_revision_id, m.consequence_revision_id)} data-window-financials-action>
      Open fuel cost →
    </Link>
  );
}

/** What happened to the Finding version named in the address, by the server's reason. */
const PIN_WORDS: Record<string, string> = {
  NOT_IN_SELECTED_DAY: "The Finding in the address does not overlap this day, so it is not shown for it.",
  EXACT_REVISION_REQUIRED_WHILE_SOURCE_CLOSED:
    "While the Performance source is closed, only an exact Finding version can be shown, for audit.",
  SETTLED_DISCOVERY_FOUND_NO_FINDING: "This day has settled and no longer selects the Finding in the address.",
  SETTLED_CHOICE_IS_ANOTHER_FINDING: "This day has settled on another Finding than the one in the address.",
  NEWER_REVISION_OF_THE_SAME_FINDING: "A newer version of the Finding in the address is shown.",
};

function KnownFinding({
  summary,
  links,
  findingIndex,
  onReload,
}: {
  summary: SiteWindowSummary;
  links: WindowOverviewLinks;
  findingIndex?: FindingIndexClient;
  onReload?: () => void;
}) {
  const findingList = links.findingList;
  const k = summary.known_finding;
  const pin = summary.previous_pin ?? k?.previous_pin ?? null;
  const choiceReferences = k === null
    ? []
    : [
        { label: "How it was chosen", value: k.selected_by },
        { label: "Choice rule", value: k.selection_rule },
        { label: "Finding reference", value: k.id },
        { label: "Finding version reference", value: k.revision_id },
      ];
  const chosenNode =
    k === null ? (
      <p data-known-finding="none">No Finding is selected for this day.</p>
    ) : (
      <div data-known-finding={k.id} data-known-finding-revision={k.revision_id}>
        <p>
          <Link to={links.finding(k.id, k.revision_id)} data-window-finding-link={k.id}>
            Finding from {stamp(k.episode.start)} to {k.episode.end === null ? "open" : stamp(k.episode.end)} UTC
          </Link>
          {k.audit_only ? " (kept for audit; not current)" : ""}
        </p>
        {k.audit_only ? (
          <div data-known-finding-state="audit-only">
            <ProductStatus
              words={currentnessWords("AUDIT_ONLY")}
              scope={`The Finding chosen for ${summary.window.utc_date}`}
              asOf={summary.db_now}
            />
          </div>
        ) : null}
        {k.several_intersect ? <p>{k.note}</p> : null}
        <ExactReferences name="window-finding-choice" variant="tech" references={choiceReferences} />
      </div>
    );
  return (
    <>
      {pin ? (
        <p data-previous-pin={pin.reason}>{PIN_WORDS[pin.reason] ?? "The Finding in the address is not the one shown."}</p>
      ) : null}
      {findingIndex && findingList ? (
        // Review fix M4: the list owns the chosen line, so it can be list item 1 when they are the same version.
        <OverviewFindingList
          summary={summary}
          client={findingIndex}
          links={{ finding: links.finding, findingList }}
          onReload={onReload ?? (() => undefined)}
          chosen={{
            node: chosenNode,
            omittable: k !== null && !k.audit_only && !k.several_intersect,
            references: choiceReferences,
          }}
        />
      ) : (
        <>
          {chosenNode}
          <p data-finding-list={summary.finding_list.state}>{summary.finding_list.reason}</p>
        </>
      )}
    </>
  );
}

/** Panel 5: the next steps the read supports - the selected Finding and the day in Dispatch - or none. */
function NextStep({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const k = summary.known_finding;
  const day = summary.window.utc_date;
  const closed = summary.assessment.state === "CLOSED";
  if (k === null && closed) {
    return <p data-overview-next="none">No supported next action.</p>;
  }
  return (
    <div className="v69-prose" data-overview-next={k === null ? "dispatch" : "finding"}>
      {k === null ? (
        <ChartNote>No Finding is selected for this day, so no recommendation is offered. Review the day in Dispatch.</ChartNote>
      ) : (
        <>
          <h3>Review the Finding for this day</h3>
          <ChartNote>
            The Finding records what the assessment concluded about generator operation. No recommendation is
            recorded on this Overview; any next action starts from the Finding.
          </ChartNote>
        </>
      )}
      {/* W1-F2 compaction: the Finding button and the Dispatch link share one line. */}
      <p className="overview-next__actions">
        {k === null ? null : (
          <Link className="button" to={links.finding(k.id, k.revision_id)} data-overview-next-finding={k.id}>
            Open the Finding
          </Link>
        )}
        {closed ? null : (
          <Link to={links.dispatchDay(day, summary.assessment.window_assessment_revision_id)} data-overview-next-dispatch={day}>
            Open this day in Dispatch →
          </Link>
        )}
      </p>
    </div>
  );
}

export function SiteWindowOverview({
  summary,
  links,
  onSelectDay,
  findingIndex,
  onReload,
  mini,
  outcomeBoard,
}: SiteWindowOverviewProps) {
  const day = summary.window.utc_date;
  const miniState = useOverviewMini(mini, day);
  const minigrid = mini !== undefined;
  return (
    <div className="site-window-overview" data-overview-state="window" data-window-site={summary.site_code}>
      <OverviewGrid
        lead={
          <>
            {/* Review Low 7b: the app-only day chooser is the v69 chip row above the statusbar, the same place as
                on Dispatch and Evidence. */}
            <DaySelector summary={summary} onSelectDay={onSelectDay} />
            <DayStatus summary={summary} links={links} reads={minigrid ? overviewReadable(miniState) : null} />
            <ObjectiveLine summary={summary} minigrid={minigrid} />
            {/* OUT-B B5: the outcome board replaces the old objective cards (doc §6.4 deviation 1, R540). It reads the
                same selected day (and Finding pin) the overview read. */}
            {outcomeBoard === undefined ? null : (
              <OutcomeBoard
                client={outcomeBoard}
                siteCode={summary.site_code}
                query={{
                  date: day,
                  finding_id: summary.known_finding?.id ?? null,
                  finding_revision_id: summary.known_finding?.revision_id ?? null,
                }}
              />
            )}
          </>
        }
        happened={{
          description: `Selected day ${day} · plain sequence of the assessed periods · the dispatch view has the detail`,
          body: (
            <>
              <HourNotSelected scope={`one whole UTC day (${day})`} />
              <PeriodStrip summary={summary} links={links} />
              <DayReading summary={summary} />
              <FreshnessStrip summary={summary} />
            </>
          ),
        }}
        context={{
          description: "Selected day · when readings arrived; context for the cards, not a status source",
          // post-W6 W1-a Q3 / R159: the panel-head link to the single line diagram at the selected window's end.
          actions:
            links.sld === undefined ? undefined : (
              <Link to={links.sld(summary.window.end)} data-overview-sld-link>
                Single line diagram →
              </Link>
            ),
          body: (
            <>
              <Timeline summary={summary} />
              <Context summary={summary} links={links} />
            </>
          ),
        }}
        attention={{
          description: "The Finding chosen for this day and the day's Finding list",
          body: <KnownFinding summary={summary} links={links} findingIndex={findingIndex} onReload={onReload} />,
        }}
        money={{ body: <Money summary={summary} links={links} />, actions: <MoneyAction summary={summary} links={links} /> }}
        next={{ body: <NextStep summary={summary} links={links} /> }}
      />
    </div>
  );
}
