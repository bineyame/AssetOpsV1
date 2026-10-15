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

import { Badge, DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import { clock, isDay, limitationCode, limitationWords, roleWords, shiftDay, stamp } from "./dispatchWords";
import { portionWords } from "./findingWords";
import type { SiteWindowSummary, WindowMoney } from "./siteOverviewClient";

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
}

export interface SiteWindowOverviewProps {
  summary: SiteWindowSummary;
  links: WindowOverviewLinks;
  /** Select another UTC day (the parent writes it to the address, dropping any Finding pin). */
  onSelectDay: (day: string) => void;
}

/** Freshness of the whole day, by the server's state name. `UNASSESSED` reads Unknown, never success. */
const FRESHNESS_WORDS: Record<string, { label: string; sentence: string }> = {
  UNASSESSED: {
    label: "Unknown",
    sentence: "No assessment is selected for this day, so whether the site met its objective is unknown.",
  },
  PENDING: { label: "Pending", sentence: "Work for this day is still waiting; nothing below is presented as current." },
  STALE_PROJECTION: {
    label: "Out of date",
    sentence: "Something this day depends on has changed or stopped; what is shown is kept for reference only.",
  },
  FAILED: { label: "Failed", sentence: "Work for this day failed; nothing below is presented as current." },
  CURRENT: { label: "Current", sentence: "Every upstream step for this day has settled." },
};

/** The day's dispatch objective, by the server's assessment state name. */
const ASSESSMENT_WORDS: Record<string, { label: string; sentence: string }> = {
  UNKNOWN: { label: "Unknown", sentence: "No assessment is selected for this day. Nothing is shown in its place." },
  CLOSED: {
    label: "Closed",
    sentence: "The Performance source is not open for current use, so no current objective is shown.",
  },
  CURRENT: { label: "Up to date", sentence: "This result uses every accepted record for the day." },
  PENDING: { label: "Being assessed", sentence: "Records for this day are waiting to be assessed." },
  STALE_PROJECTION: { label: "Out of date", sentence: "This result was made before newer records; it is kept for reference." },
  FAILED: { label: "Reassessment failed", sentence: "The latest reassessment of this day failed; any earlier result is not current." },
};

/** Why the money card shows no amount, by the server's no-amount state name (packet "S5 no-amount states"). */
export const MONEY_STATE_WORDS: Record<string, { label: string; sentence: string }> = {
  PRICED: { label: "Current amount", sentence: "Every gate for this Finding version passed." },
  ABSENT: {
    label: "No Finding on this day",
    sentence: "A complete, current search found no Finding whose time overlaps this day.",
  },
  PENDING_REASSESSMENT: {
    label: "Pending reassessment",
    sentence: "New source-time information arrived for this Finding's generator power and it has not been reassessed yet.",
  },
  WITHHELD_GENERATOR_SERIES: {
    label: "Withheld: generator power series",
    sentence: "A generator power reading arrived late or out of order for this Finding, so no amount is shown.",
  },
  SOURCE_CLOSED: {
    label: "Source closed",
    sentence: "The Performance source is not open for current use; only pinned records are shown, for audit.",
  },
  UPSTREAM_UNASSESSED: { label: "Day not assessed", sentence: "The day has not been assessed, so no amount is shown." },
  UPSTREAM_PENDING: {
    label: "Upstream pending",
    sentence: "Assessment, Finding or schedule work this day depends on is still waiting, or moved while it was read.",
  },
  UPSTREAM_STALE: {
    label: "Upstream out of date",
    sentence: "Something this day depends on is out of date or the schedule has stopped, so no amount is shown.",
  },
  UPSTREAM_FAILED: { label: "Upstream failed", sentence: "Work this day depends on failed, so no amount is shown." },
  SUPERSEDED: { label: "Earlier Finding version", sentence: "A newer version of this Finding exists." },
  CONSEQUENCE_PENDING: { label: "Fuel cost pending", sentence: "The fuel cost for this Finding version is still being worked out." },
  CONSEQUENCE_STALE: { label: "Fuel cost out of date", sentence: "The fuel cost for this Finding version is out of date." },
  QUANTITY_UNAVAILABLE: {
    label: "Fuel quantity unavailable",
    sentence: "The generator power readings do not bound a fuel quantity for this Finding.",
  },
  UNPRICED: { label: "No price", sentence: "No diesel price covers this Finding's time." },
  MINOR_UNIT_UNKNOWN: { label: "Currency unit unknown", sentence: "The currency's minor unit is not known, so no amount is displayed." },
  MIXED_OR_UNKNOWN_SOURCE: {
    label: "Source not confirmed",
    sentence: "The origin of this Finding's data could not be confirmed, so no amount is shown.",
  },
};

/** The shared LR-01 money gate's own state, shown raw beside the card's state. */
const GATE_WORDS: Record<string, string> = {
  ELIGIBLE: "Eligible",
  PENDING_REASSESSMENT: "Pending reassessment",
  WITHHELD_GENERATOR_SERIES: "Withheld: generator power series",
};

function words<T extends { label: string }>(table: Record<string, T>, state: string): T | { label: string; sentence: string } {
  return table[state] ?? { label: state.toLowerCase().replace(/_/g, " "), sentence: "" };
}

function Code({ value }: { value: string | null | undefined }) {
  return (
    <code data-vocabulary-exempt="source-reference">{value ?? "none"}</code>
  );
}

function Reasons({ reasons, name }: { reasons: string[]; name: string }) {
  if (reasons.length === 0) {
    return <span>none</span>;
  }
  return (
    <ul className="cell-list" data-window-reasons={name}>
      {reasons.map((r) => (
        <li key={r}>
          <Code value={r} />
        </li>
      ))}
    </ul>
  );
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

function FreshnessStrip({ summary }: { summary: SiteWindowSummary }) {
  const f = summary.freshness;
  const w = words(FRESHNESS_WORDS, f.state);
  return (
    <Panel heading="This day" headingId="site-window-freshness-heading">
      <p data-freshness-state={f.state}>
        <Badge tone="neutral">{w.label}</Badge> {w.sentence}
      </p>
      <p data-source-open={f.source_open ? "open" : "closed"}>
        {f.source_open
          ? "The Performance source is open for current use."
          : "The Performance source is closed for current use: only pinned records are shown, for audit."}
      </p>
      <Disclosure summary="Why, and the exact read basis" name="window-freshness">
        <FactList>
          <Fact term="Reasons">
            <Reasons reasons={f.reasons} name="freshness" />
          </Fact>
          <Fact term="Source gate">
            <span data-vocabulary-exempt="source-reference">{f.source_reason}</span>
          </Fact>
          <Fact term="Database time">{stamp(summary.db_now)}</Fact>
          <Fact term="Accepted records in the read bracket">
            {summary.watermarks.accepted_source === null ? (
              <span>
                Unreadable: <Code value={summary.watermarks.accepted_source_reason} />
              </span>
            ) : (
              <span>
                {summary.watermarks.accepted_source.count} (<Code value={summary.watermarks.accepted_source.sha256} />)
              </span>
            )}
          </Fact>
          <Fact term="Input digest">
            <Code value={summary.watermarks.input_sha256} />
          </Fact>
          <Fact term="Finding match pass">
            <Code value={summary.watermarks.match_pass_id} />
          </Fact>
          <Fact term="Access basis">
            <Code value={summary.access_basis} />
          </Fact>
        </FactList>
      </Disclosure>
    </Panel>
  );
}

function Objective({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const a = summary.assessment;
  const w = words(ASSESSMENT_WORDS, a.state);
  const day = summary.window.utc_date;
  return (
    <Panel heading="Operating objective" headingId="site-window-objective-heading">
      <p data-assessment-state={a.state}>
        <Badge tone="neutral">{w.label}</Badge> {w.sentence}
      </p>
      {a.state === "CLOSED" ? null : (
        <p>
          <Link to={links.dispatchDay(day, a.window_assessment_revision_id)} data-window-dispatch-link={day}>
            Open this day in Performance &gt; Dispatch
          </Link>
        </p>
      )}
      {a.limitations.length === 0 ? null : (
        <ul className="cell-list" data-assessment-limitations={a.limitations.length}>
          {[...new Set(a.limitations.map((l) => limitationCode(String(l))))].map((code) => (
            <li key={code}>{limitationWords(code)}</li>
          ))}
        </ul>
      )}
      <Disclosure summary="Exact assessment identifiers" name="window-assessment">
        <FactList>
          <Fact term="Day assessment">
            <Code value={a.window_assessment_revision_id} />
          </Fact>
          <Fact term="Assessment pass">
            <Code value={a.run_id} />
          </Fact>
          <Fact term="Status reasons">
            <Reasons reasons={a.status_reasons ?? []} name="assessment" />
          </Fact>
        </FactList>
      </Disclosure>
    </Panel>
  );
}

function Timeline({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const day = summary.window.utc_date;
  const intervals = summary.assessment.dispatch_intervals;
  const coverage = summary.context.coverage ?? [];
  return (
    <Panel heading="Day timeline" headingId="site-window-timeline-heading">
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
              <span className="window-timeline__label">{c.role ? roleWords(c.role) : `${c.device_id} ${c.signal_id}`}</span>
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

function Money({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
  const m = summary.money;
  const w = words(MONEY_STATE_WORDS, m.state);
  const gate = m.eligibility?.state ?? null;
  const priced = m.state === "PRICED" && m.amount_low !== null && m.amount_high !== null;
  return (
    <Panel heading="Potential fuel-cost exposure, one Finding" headingId="site-window-money-heading">
      <div
        className="window-money"
        data-money-state={m.state}
        data-money-gate={gate ?? "none"}
        data-consequence-revision-id={m.consequence_revision_id ?? ""}
      >
        {m.demonstration ? (
          <p className="notice notice--info" data-financials-demonstration={m.demonstration.case_id}>
            <strong>{m.demonstration.label}.</strong> {m.demonstration.statement}
          </p>
        ) : null}
        {priced ? (
          <p className="window-money__amount" data-money-amount>
            {m.amount_low} to {m.amount_high} {m.currency}
          </p>
        ) : (
          <p className="window-money__none" data-money-amount="none">
            No current amount.
          </p>
        )}
        <p>
          <Badge tone="neutral">{w.label}</Badge> {w.sentence}
        </p>
        <FactList>
          <Fact term="Money gate">
            <span data-money-gate-state={gate ?? "none"}>{gate === null ? "Not read" : (GATE_WORDS[gate] ?? gate)}</span>
          </Fact>
          <Fact term="Upstream">
            <span data-money-upstream={m.upstream.status}>{words(FRESHNESS_WORDS, m.upstream.status).label}</span>
          </Fact>
        </FactList>
        <p className="overview-note">{m.label}</p>
        <MoneyLinks money={m} links={links} day={summary.window.utc_date} />
        <Disclosure summary="Exact identifiers and limiting states" name="window-money">
          <FactList>
            <Fact term="Finding">
              <Code value={m.finding_id} />
            </Fact>
            <Fact term="Finding version">
              <Code value={m.finding_revision_id} />
            </Fact>
            <Fact term="Fuel cost version">
              <Code value={m.consequence_revision_id} />
            </Fact>
            <Fact term="Model">
              <Code value={m.model_version} />
            </Fact>
            <Fact term="Limiting states">
              <Reasons reasons={m.limitation ?? []} name="money" />
            </Fact>
            <Fact term="Upstream reasons">
              <Reasons reasons={m.upstream.reasons} name="money-upstream" />
            </Fact>
            <Fact term="Gate note">
              <span data-vocabulary-exempt="source-reference">{m.eligibility?.note ?? "none"}</span>
            </Fact>
          </FactList>
        </Disclosure>
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

function KnownFinding({ summary, links }: { summary: SiteWindowSummary; links: WindowOverviewLinks }) {
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
          {k.several_intersect ? <p>{k.note}</p> : null}

          <Disclosure summary="How this Finding was chosen" name="window-finding-choice">
            <FactList>
              <Fact term="Chosen by">
                <Code value={k.selected_by} />
              </Fact>
              <Fact term="Rule">
                <span data-vocabulary-exempt="source-reference">{k.selection_rule}</span>
              </Fact>
              <Fact term="Finding">
                <Code value={k.id} />
              </Fact>
              <Fact term="Finding version">
                <Code value={k.revision_id} />
              </Fact>
            </FactList>
          </Disclosure>
        </div>
      )}
      {pin ? (
        <p data-previous-pin={pin.reason}>{PIN_WORDS[pin.reason] ?? "The Finding in the address is not the one shown."}</p>
      ) : null}
      <p data-finding-list={summary.finding_list.state}>{summary.finding_list.reason}</p>
    </Panel>
  );
}

export function SiteWindowOverview({ summary, links, onSelectDay }: SiteWindowOverviewProps) {
  return (
    <div className="site-window-overview" data-overview-state="window" data-window-site={summary.site_code}>
      <DaySelector summary={summary} onSelectDay={onSelectDay} />
      <div className="site-window-overview__grid">
        <FreshnessStrip summary={summary} />
        <Objective summary={summary} links={links} />
        <Money summary={summary} links={links} />
        <KnownFinding summary={summary} links={links} />
      </div>
      <Timeline summary={summary} links={links} />
      <Context summary={summary} links={links} />
    </div>
  );
}
