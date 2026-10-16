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

import { Link } from "react-router-dom";

import {
  currentnessWords,
  DataTable,
  Disclosure,
  ExactReferences,
  Fact,
  FactList,
  HeadlineVisualCard,
  moneyWords,
  Panel,
  ProductStatus,
  ValueBars,
  type ExactReference,
  type ProductWords,
} from "../ui";
import { SourceProvenanceNotice } from "./sourceProvenance";
import { clock, isDay, limitationCode, limitationWords, roleWords, shiftDay, stamp } from "./dispatchWords";
import { portionWords } from "./findingWords";
import { OUTCOME_WORDS } from "./findingPresentation";
import type { SiteWindowSummary, WindowMoney } from "./siteOverviewClient";
import type { FindingIndexClient, FindingIndexScope } from "./findingIndexClient";
import { OverviewFindingList } from "./OverviewFindingList";
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
    <div className="window-day" data-window-date={day}>
      <label className="window-day__field">
        <span>UTC day</span>
        <input
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
      <Link className="dispatch-day__button" to={`?date=${shiftDay(day, -1)}`} data-window-day-link="previous">
        Previous day
      </Link>
      <Link className="dispatch-day__button" to={`?date=${shiftDay(day, 1)}`} data-window-day-link="next">
        Next day
      </Link>
      <p className="window-day__bounds">
        {stamp(summary.window.start)} to {stamp(summary.window.end)} UTC, start included, end excluded.
      </p>
    </div>
  );
}

/**
 * W1-UX-02: whether the day's answer is current, in the shared words, with the source's open state beside it.
 * The recorded reasons and exact read references move to the closed disclosure.
 */
function FreshnessStrip({ summary }: { summary: SiteWindowSummary }) {
  const f = summary.freshness;
  const accepted = summary.watermarks.accepted_source;
  return (
    <Panel heading="This day" headingId="site-window-freshness-heading">
      <div className="window-freshness" data-freshness-card>
        <div data-freshness-state={f.state}>
          <ProductStatus words={currentnessWords(f.state)} scope={dayScope(summary)} asOf={summary.db_now} />
        </div>
        <p data-source-open={f.source_open ? "open" : "closed"}>
          {f.source_open
            ? "The source of these readings is open for current use."
            : "The source of these readings is closed for current use: only records kept for the audit are shown."}
        </p>
        <div data-window-reasons="freshness">
          <ExactReferences
            name="window-freshness"
            references={[
              { label: "Day state", value: f.state },
              ...reasonReferences("Recorded reason", f.reasons),
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
    </Panel>
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

function Objective({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const a = summary.assessment;
  const w = objectiveWords(a.state);
  const day = summary.window.utc_date;
  const closed = a.state === "CLOSED";
  return (
    <HeadlineVisualCard
      dataName="overview-objective"
      headingId="site-window-objective-heading"
      question="Is the mini-grid meeting its operating objective?"
      headline={a.state === "CURRENT" ? "No operating objective is stated for this day" : "No current answer for this day"}
      status={
        <div data-assessment-state={a.state}>
          <ProductStatus words={w} scope={`${day}, one UTC day at this site`} asOf={summary.db_now} />
        </div>
      }
      meaning={
        <>
          {closed ? (
            <p>Nothing on this card is a current answer.</p>
          ) : (
            <p data-objective-statement="not-stated">
              The assessment does not state an operating objective for this day, so none is shown here.
            </p>
          )}
          {closed || a.claim_level === null ? null : (
            <p data-assessment-claim={a.claim_level}>
              Day reading: {OUTCOME_WORDS[a.claim_level] ?? "Assessed"}. {a.dispatch_intervals.length}{" "}
              {a.dispatch_intervals.length === 1 ? "operating period" : "operating periods"} assessed;{" "}
              {coverageRoles(a.coverage)}
            </p>
          )}
          {a.limitations.length === 0 ? null : (
            <ul className="cell-list" data-assessment-limitations={a.limitations.length}>
              {[...new Set(a.limitations.map((l) => limitationCode(String(l))))].map((code) => (
                <li key={code}>{limitationWords(code)}</li>
              ))}
            </ul>
          )}
        </>
      }
      todo={w.next === undefined ? undefined : <p>{w.next}</p>}
      destination={
        closed ? undefined : (
          <Link to={links.dispatchDay(day, a.window_assessment_revision_id)} data-window-dispatch-link={day}>
            Open this day in Performance &gt; Dispatch
          </Link>
        )
      }
      references={
        <ExactReferences
          name="window-assessment"
          references={[
            { label: "Day assessment", value: a.window_assessment_revision_id },
            { label: "Assessment pass", value: a.run_id },
            { label: "Assessment state", value: a.state },
            ...(a.status_reasons ?? []).map((reason, i) => ({ label: `Recorded reason ${i + 1}`, value: reason })),
          ]}
        />
      }
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
function Timeline({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
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
    <Panel heading="Day timeline" headingId="site-window-timeline-heading">
      <figure
        className="window-timeline-figure"
        data-window-timeline-figure
        aria-label={`Day timeline for ${day}, 00:00 to 24:00 UTC. ${description}`}
      >
        <figcaption className="window-timeline-figure__caption">
          When the generator was in use and when readings arrived on {day}, 00:00 to 24:00 UTC.
          {current ? "" : " These periods come from an answer that is not current; see This day."}
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
            const lo = dayPercent(c.first_source_time, summary.window.start);
            const hi = dayPercent(c.last_source_time, summary.window.start);
            return (
              <div className="window-timeline__row" key={`${c.device_id}/${c.signal_id}`}>
                <span className="window-timeline__label">{c.role ? roleWords(c.role) : "Unnamed reading"}</span>
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
      {intervals.length === 0 ? (
        <p>No assessed period is selected for this day.</p>
      ) : (
        <DataTable labelledBy="site-window-timeline-heading">
          <thead>
            <tr>
              <th scope="col">From</th>
              <th scope="col">To</th>
              <th scope="col">Generator</th>
              <th scope="col">Detail</th>
            </tr>
          </thead>
          <tbody>
            {intervals.map((i) => (
              <tr key={i.revision_id} data-window-interval={i.revision_id}>
                <td>{clock(i.start)}</td>
                <td>{clock(i.end)}</td>
                <td>{portionWords(i.claim_level ?? "")}</td>
                <td>
                  <Link to={links.dispatchDay(day, i.revision_id)}>Open</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
    </Panel>
  );
}

function Context({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const c = summary.context;
  if (c.series === null || c.coverage === null) {
    return (
      <Panel heading="Operating context" headingId="site-window-context-heading">
        <p data-window-context="unavailable">
          Accepted readings for this day could not be read: <Code value={c.reason ?? null} />
        </p>
      </Panel>
    );
  }
  return (
    <Panel heading="Operating context" headingId="site-window-context-heading">
      <p data-window-context={c.series.length}>
        {c.total ?? c.series.length} accepted readings on this day
        {c.truncated ? `; the first ${c.series.length} are listed` : ""}.
      </p>
      {c.coverage.length === 0 ? (
        <p>No accepted reading covers this day.</p>
      ) : (
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
      {c.gaps_reason ? <p className="overview-note">{c.gaps_reason}</p> : null}
      {c.series.length === 0 ? null : (
        <Disclosure summary="Accepted readings, with links to each record" name="window-readings">
          <ul className="cell-list" data-window-readings={c.series.length}>
            {c.series.map((r) => (
              <li key={r.evidence_id}>
                <Link to={links.evidenceRecord(r.evidence_id)} data-window-evidence-link={r.evidence_id}>
                  {clock(r.time)} {r.role ? roleWords(r.role) : r.signal_id}: {r.value ?? "no value"} {r.unit ?? ""}
                </Link>
              </li>
            ))}
          </ul>
        </Disclosure>
      )}
    </Panel>
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
  const w = overviewMoneyWords(m.state);
  const gate = m.eligibility?.state ?? null;
  const priced = m.state === "PRICED" && m.amount_low !== null && m.amount_high !== null;
  const low = priced ? Number(m.amount_low) : Number.NaN;
  const high = priced ? Number(m.amount_high) : Number.NaN;
  const scope = m.finding_id ? `One Finding overlapping ${summary.window.utc_date}` : dayScope(summary);
  return (
    <Panel heading="Potential fuel-cost exposure, one Finding" headingId="site-window-money-heading">
      <div
        className="window-money"
        data-money-state={m.state}
        data-money-gate={gate ?? "none"}
        data-consequence-revision-id={m.consequence_revision_id ?? ""}
      >
        {priced ? (
          <p className="window-money__amount" data-money-amount>
            {m.amount_low} to {m.amount_high} {m.currency}
          </p>
        ) : (
          <p className="window-money__none" data-money-amount="none">
            No current amount.
          </p>
        )}
        <ProductStatus words={w} scope={scope} asOf={summary.db_now} />
        {m.finding_id ? (
          <SourceProvenanceNotice provenance={m.source_provenance} subject="cost" name="overview-money" />
        ) : null}
        {priced && Number.isFinite(low) && Number.isFinite(high) ? (
          <ValueBars
            title="Possible extra fuel cost for this Finding"
            items={[
              { label: "Lower bound", key: "low", value: low, valueText: `${m.amount_low} ${m.currency ?? ""}`.trim() },
              { label: "Upper bound", key: "high", value: high, valueText: `${m.amount_high} ${m.currency ?? ""}`.trim() },
            ]}
          />
        ) : null}
        {m.finding_id ? (
          <p className="overview-note" data-money-qualifier>
            A modelled range of possible extra fuel cost for one Finding, not money lost or saved.
          </p>
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
      </div>
    </Panel>
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
  return (
    <Panel heading="Findings" headingId="site-window-findings-heading">
      {k === null ? (
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
          <ExactReferences
            name="window-finding-choice"
            references={[
              { label: "How it was chosen", value: k.selected_by },
              { label: "Choice rule", value: k.selection_rule },
              { label: "Finding reference", value: k.id },
              { label: "Finding version reference", value: k.revision_id },
            ]}
          />
        </div>
      )}
      {pin ? (
        <p data-previous-pin={pin.reason}>{PIN_WORDS[pin.reason] ?? "The Finding in the address is not the one shown."}</p>
      ) : null}
      {findingIndex && findingList ? (
        <OverviewFindingList
          summary={summary}
          client={findingIndex}
          links={{ finding: links.finding, findingList }}
          onReload={onReload ?? (() => undefined)}
        />
      ) : (
        <p data-finding-list={summary.finding_list.state}>{summary.finding_list.reason}</p>
      )}
    </Panel>
  );
}

export function SiteWindowOverview({ summary, links, onSelectDay, findingIndex, onReload }: SiteWindowOverviewProps) {
  return (
    <div className="site-window-overview" data-overview-state="window" data-window-site={summary.site_code}>
      <DaySelector summary={summary} onSelectDay={onSelectDay} />
      <div className="site-window-overview__lead">
        <Objective summary={summary} links={links} />
      </div>
      <div className="site-window-overview__grid">
        <FreshnessStrip summary={summary} />
        <Money summary={summary} links={links} />
        <KnownFinding summary={summary} links={links} findingIndex={findingIndex} onReload={onReload} />
      </div>
      <Timeline summary={summary} links={links} />
      <Context summary={summary} links={links} />
    </div>
  );
}
