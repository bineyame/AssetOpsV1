/*
 * PF-T (2026-11-11): Portfolio section tabs, layout `frontend/mockups/v71/portfolio-tabs.html`; proposal
 * `.agent/architect-proposal-portfolio-layout-2026-11-10.md` §6, §11.
 * MOCK DEVIATION PF-T-1: the product shell has no top bar, so the Portfolio date bar (`EstateDateBar`) sits at the top
 *   of the page, above the title, and stays in view while scrolling (sticky). The v71 shared top-bar range picker is
 *   card SR, not PF-T.
 * MOCK DEVIATION PF-T-2: the v71 coverage line above the tabs and the "Readings per site" table are card PF-C; the
 *   context row keeps today's per-Site partial notes and the Scope & coverage tab holds today's "Assessment scope &
 *   periods" drawer and the business-context footer.
 * MOCK DEVIATION PF-T-3: the Overview top-3 rows show the placement group, not v71's High/Medium priority badge
 *   (CC-R2-Q3: the table ranks by placement, not priority).
 * MOCK DEVIATION PF-T-5: the What changed "Inspect basis" stays the inline disclosure (its change-and-verification basis
 *   table is in the panel), not v71's link to the Scope tab, because the basis table belongs to this panel's data.
 * MOCK DEVIATION PF-T-4: the Act first count is the read's `total_count` for the lens being read (the panel eyebrow's
 *   count), so it follows the lens on Act first.
 */
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { displayCode } from "../ui/displayCode";
import { formatDayRange, formatDayTime } from "../ui/time";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { linkFor } from "../shell/operatorSiteRoutes";
import { Badge, DataTable, Disclosure, PageHeader } from "../ui";
import { TechnicalDetails } from "../ui/TechnicalDetails";
import { useCurrentTabInView } from "../ui/useCurrentTabInView";
import {
  createEstateClient,
  type EstateClient,
  type EstateEnvelope,
  type EstateLens,
  type EstateOutcomeSummaryBody,
  type EstatePortfolioBody,
  portfolioOpportunity,
  REFUSAL_COPY,
  type EstatePortfolioQuery,
  type EstatePortfolioRow,
  type EstatePortfolioScopeIdsBody,
  type EstateQuery,
  type EstateResult,
  type EstateSourceBlock,
} from "./estateClient";
import { EstateDateBar, EstateRefusal, estateHref, queryFromParams } from "./estateShared";
import { moneyText, moneyWindowText, NOT_DISPLAYABLE, quantityText } from "./estateFinancialsWords";
import {
  ACTION_WINDOW_NOTE,
  ASSESSMENT_IDS,
  coverageStateWords,
  gapReasonClause,
  exclusionLineLabel,
  exclusionReasonWords,
  selectedAssessmentWords,
  CATEGORIES_SEPARATE,
  contextWords,
  CURRENT_SITE_VIEW,
  DOMAIN_WORD,
  domainSummary,
  ENERGY_UNAVAILABLE,
  EV_COVERAGE_WARNING,
  EVIDENCE_ASIDE,
  LENS_LABELS,
  NO_ENERGY_TOTAL,
  NO_SNAPSHOT_NOTICE,
  OPPORTUNITY_NOTE,
  OPPORTUNITY_PANEL,
  OUTCOME_NOTE,
  PORTFOLIO_PAGE_SIZE,
  PORTFOLIO_SUBTITLE,
  PORTFOLIO_TABS,
  PORTFOLIO_TABS_LABEL,
  PORTFOLIO_TITLE,
  portfolioTabFrom,
  portfolioTabPath,
  type PortfolioTab,
  TOP3_SEE_ALL,
  TOP3_SUBTITLE,
  PLACEMENT_CONFIDENCE_WORDS,
  PLACEMENT_GROUP_LABEL,
  PLACEMENT_POLICY_FOOTER,
  PLACEMENT_POLICY_LINES,
  PLACEMENT_POLICY_SUMMARY,
  PRIORITY_BOTTOM_LINE,
  PRIORITY_PANEL,
  mechanismWords,
  PRIORITY_SUBTITLE,
  PROGRESS_PANEL,
  PROGRESS_REFERENCE,
  PULSE_NOTE,
  SCOPE_NOTICE,
  SCOPE_RULE,
  VALUE_OWNERSHIP,
} from "./portfolioWords";
import "./estatePortfolio.css";
import { CategoryTags } from "../sites/outcomeCategories";
import { EarlyWarningList } from "../sites/EarlyWarnings";
import type { OutcomeWarning } from "../sites/outcomeBoardClient";
import { amountOf, CategoryCards, OUTCOME_MATRIX_LABEL, OUTCOME_MATRIX_NOTE, OutcomeMatrixBody } from "./PortfolioOutcomes";
import { PortfolioCoverage } from "./PortfolioCoverage";
import { RETRYING_COPY, TEMPORARILY_UNAVAILABLE } from "../sites/temporarilyUnavailable";

/** INFRA-1 (D-E5.47): the summary read while it waits to retry a 503 `TEMPORARILY_UNAVAILABLE`. */
const SUMMARY_RETRYING: EstateResult<EstateOutcomeSummaryBody> = {
  status: "refused",
  httpStatus: 503,
  code: TEMPORARILY_UNAVAILABLE,
  copy: RETRYING_COPY,
};

/**
 * W3-03 run 2: the estate Portfolio page (v69 `portfolio`). Every value comes from the one `/api/estate/portfolio`
 * response; the page never re-sorts, re-selects or sums. Page one reads 50 Findings; `Load more Findings` appends
 * only Finding rows. A refusal on any page replaces everything previously shown (401, 409, 503 clear stale rows).
 */

type Window = Pick<EstateQuery, "from" | "to" | "known_at">;
const LENSES: readonly EstateLens[] = ["all", "cost", "risks", "opportunities"];
const EV_INCOMPLETE = new Set(["UNKNOWN", "PENDING_RECOMPUTE", "STALE_SOURCE"]);

function lensFrom(params: URLSearchParams): EstateLens {
  const lens = params.get("lens");
  return LENSES.includes(lens as EstateLens) ? (lens as EstateLens) : "all";
}

/**
 * A Portfolio URL: the tab's address with the accepted window and explicit cutoff, never a cursor. PF-T: a
 * non-default lens travels on Act first only.
 */
export function portfolioHref(window: Window, lens: EstateLens, tab: PortfolioTab = "overview"): string {
  const href = estateHref(portfolioTabPath(tab), window);
  return lens === "all" || tab !== "act-first" ? href : `${href}&lens=${lens}`;
}

/** The shared date bar reads only `status` and `window`; its HISTORICAL line keys off the same status word. */
function barBody(body: EstatePortfolioBody | null): EstateEnvelope | null {
  return body === null ? null : (body as unknown as EstateEnvelope);
}

const countText = (value: number | null, missing: string) => (value === null ? missing : String(value));
/** WALK1-1 (WN-2, R670): on a partly checked estate a zero count is a claim on the checked days only. */
export const NONE_ON_CHECKED_DAYS = "None found on the days assessed";
function PulseCount({ value, missing, label, checkedDays, data, to }: { value: number | null; missing: string; label: string; checkedDays: boolean; data?: string; to: string }) {
  const attrs = data === undefined ? {} : { [data]: "" };
  if (value === 0 && checkedDays) {
    // MOCK DEVIATION (R670): the label leads so the qualified "none" reads as a sentence; v70 shows "{n} {label}".
    return (
      <span {...attrs}>
        <Link to={to}>
          {label[0].toUpperCase() + label.slice(1)}: <strong>{NONE_ON_CHECKED_DAYS}</strong>
        </Link>
      </span>
    );
  }
  return (
    <span {...attrs}>
      <Link to={to}>
        <strong>{countText(value, missing)}</strong> {label}
      </Link>
    </span>
  );
}

/**
 * COV-PARTIAL: a Site with incomplete days never shows an amount on its rows (the backend sends none). PF-C (proposal
 * §4 C7) shortens the words to the reason alone; PF-W (D-E5.46) says "incomplete days", never "checked".
 */
export const VALUE_WITHHELD = "Value not shown while this site has incomplete days";
export function partialConsequence(c: { state: string; source_revision_id: string | null }): string {
  return c.source_revision_id === null ? "No consequence recorded" : c.state === "UNPRICED" ? "Unpriced" : VALUE_WITHHELD;
}

function consequenceFirst(row: EstatePortfolioRow, siteState: string | undefined): string {
  const c = row.consequence;
  if (siteState === "PARTIAL" && !(c.state === "PRICED" && (c.amount_low ?? c.amount) != null)) return partialConsequence(c);
  const base =
    c.source_revision_id === null && c.state !== "PRICED"
      ? "No consequence recorded"
      : c.state === "PRICED"
        ? moneyText({ low: c.amount_low ?? c.amount, high: c.amount_high ?? c.amount, currency: c.currency }, "outward") ?? NOT_DISPLAYABLE
        : c.state === "UNPRICED"
          ? "Unpriced"
          : "Source not checked";
  // Closure 1: a pending or historical Site prefixes the first line only and never shows a current amount.
  if (siteState === "PENDING_RECOMPUTE") return `Updating · ${c.state === "PRICED" ? "Value withheld" : base}`;
  if (siteState === "HISTORICAL") return `Historical · ${c.state === "PRICED" ? "Value withheld" : base}`;
  return base;
}

/** PB-3 review M1: an open episode shows its recorded start; "No time recorded yet" only when neither end is held. */
function episodeText(row: EstatePortfolioRow): string {
  return (
    moneyWindowText(row.episode_start, row.episode_end) ??
    (row.episode_start !== null ? `From ${formatDayTime(row.episode_start)} · no end time yet` : "No time recorded yet")
  );
}

function FindingRow({ row, siteState }: { row: EstatePortfolioRow; siteState: string | undefined }) {
  const episode = episodeText(row);
  // CH5a2-R4(c): every row link renders from its `link_refs` sibling; a row without one renders no link.
  const links = {
    site: linkFor(row.link_refs?.site),
    finding: linkFor(row.link_refs?.finding),
    action: linkFor(row.link_refs?.action),
  };
  const threadState = row.action_id === null && row.workflow_label !== "No action agreed yet";
  return (
    <tr data-portfolio-row={`${row.finding_id}|${row.finding_revision_id}`}>
      <td>
        {links.site !== null ? (
          <Link to={links.site} data-portfolio-site-link>
            <strong>{row.site_name}</strong>
          </Link>
        ) : (
          <strong>Site detail unavailable</strong>
        )}
        <small>{DOMAIN_WORD[row.domain] ?? row.domain}</small>
        {links.site !== null ? <small data-portfolio-current-view>{CURRENT_SITE_VIEW}</small> : null}
      </td>
      <td>
        {links.finding !== null ? (
          <Link to={links.finding} data-portfolio-finding-link>
            <strong>{row.title}</strong>
          </Link>
        ) : (
          <strong>{row.title}</strong>
        )}
        <small>
          {mechanismWords(row.mechanism)}
        </small>
        <CategoryTags categories={row.categories} />
        {links.finding === null ? <small>Finding detail unavailable</small> : null}
      </td>
      <td>
        <strong className="impact" data-portfolio-value>
          {consequenceFirst(row, siteState)}
        </strong>
        <small>{episode}</small>
      </td>
      <td data-portfolio-placement={row.placement.group}>
        <strong>{PLACEMENT_GROUP_LABEL[row.placement.group]}</strong>
        <small data-portfolio-placement-reasons>{row.placement.reasons.map((r) => r.text).join(" · ")}</small>
      </td>
      <td data-portfolio-confidence={row.confidence ?? undefined}>
        <span className="badge badge--neutral">
          {row.confidence === null ? "Not assessed" : (PLACEMENT_CONFIDENCE_WORDS[row.confidence] ?? row.confidence)}
        </span>
        <small>{row.confidence === null ? "No reviewed confidence measure" : row.confidence_reasons.join(" · ")}</small>
      </td>
      <td>
        {row.action_id !== null && links.action !== null ? (
          <Link to={links.action} data-portfolio-action-link>
            <strong>{row.action_title}</strong>
          </Link>
        ) : threadState ? (
          // MOCK DEVIATION MD-FUEL-K4-1 (Architect combined pass 2026-11-08, K8 L1): v69 has no fuel row; a fuel Action has no Action page, so the column shows the fuel thread's state in bold.
          // MD-FUEL-K4-1, extended by R4.1 to Cold/EV rows: the Action column shows the row's thread state in bold when the Portfolio does not join the Site's Actions.
          <strong data-portfolio-workflow>{row.workflow_label}</strong>
        ) : (
          <strong>{row.action_id !== null ? row.action_title : "No action yet"}</strong>
        )}
        {threadState ? null : (
          <span className="workflow-text" data-portfolio-workflow>
            {row.workflow_label}
          </span>
        )}
        {row.action_id === null ? (
          links.finding !== null ? (
            <small>
              <Link to={links.finding}>Review finding</Link>
            </small>
          ) : (
            <small>Finding detail unavailable</small>
          )
        ) : null}
      </td>
    </tr>
  );
}

const TABLE_HEADS = ["Site", "Finding / operating mechanism", "Value / consequence", "Placement", "Confidence", "Action / next move"];

/** CC-R2: the loaded rows with one group heading before each group's first loaded row (once across pages). */
function placementRows(
  rows: EstatePortfolioRow[],
  counts: EstatePortfolioBody["summary"]["placement_counts"],
  siteState: Map<string, string>,
) {
  const out: ReactNode[] = [];
  let group: string | null = null;
  for (const row of rows) {
    if (row.placement.group !== group) {
      group = row.placement.group;
      const count = counts?.[row.placement.group] ?? null;
      out.push(
        <tr key={`group|${group}`} className="placement-group" data-placement-group={group}>
          <th colSpan={TABLE_HEADS.length} scope="colgroup">
            {PLACEMENT_GROUP_LABEL[row.placement.group]}
            {count === null ? "" : ` · ${count}`}
          </th>
        </tr>,
      );
    }
    out.push(<FindingRow key={`${row.finding_id}|${row.finding_revision_id}`} row={row} siteState={siteState.get(row.site_id)} />);
  }
  return out;
}

function PriorityPanel({
  body,
  rows,
  lens,
  pending,
  onLens,
  window,
  loadMore,
  warnings,
}: {
  body: EstatePortfolioBody;
  rows: EstatePortfolioRow[];
  lens: EstateLens;
  /** PL-1: the lens being read; the held rows belong to another lens and are not shown. */
  pending: EstateLens | null;
  onLens: (lens: EstateLens) => void;
  window: Window;
  loadMore: (() => void) | null;
  warnings: readonly OutcomeWarning[];
}) {
  const siteState = new Map(body.coverage.sites.map((s) => [s.site_id, s.state as string]));
  const incomplete = pending === null && (body.coverage.finding_state === "PARTIAL" || body.coverage.finding_state === "UNKNOWN");
  const count = pending !== null ? "Loading" : body.total_count === null ? "Unknown" : String(body.total_count);
  const pendingLabel = LENS_LABELS.find(([value]) => value === pending)?.[1] ?? "";
  return (
    <section
      className="panel priority-panel"
      aria-labelledby="portfolio-priority-heading"
      aria-busy={pending !== null ? "true" : undefined}
      data-portfolio-panel="priority"
    >
      <div className="panel-head">
        <div>
          <h2 id="portfolio-priority-heading">{PRIORITY_PANEL}</h2>
          <p>{PRIORITY_SUBTITLE}</p>
        </div>
        {/* PF-C (proposal §4 C6): one copy of the count, on the lens row; the coverage line states the days. */}
      </div>
      <div className="portfolio-lenses" role="group" aria-label="Finding lens">
        {LENS_LABELS.map(([value, label]) => (
          <button
            key={value}
            type="button"
            className="v69-chip chip"
            aria-pressed={lens === value}
            onClick={() => onLens(value)}
          >
            {label}
          </button>
        ))}
        <span data-portfolio-count>
          {count} findings{incomplete ? " · so far, some days incomplete" : ""}
        </span>
      </div>
      <div className="portfolio-findings" data-portfolio-scroll="findings">
        <DataTable>
          <thead>
            <tr>
              {TABLE_HEADS.map((h) => (
                <th key={h} scope="col">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pending !== null ? (
              <tr>
                <td colSpan={6} data-portfolio-loading-rows>
                  Loading the {pendingLabel} findings.
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={6} data-portfolio-empty>
                  {lens === "all" ? "No selected Findings for this window" : "No matching supported Findings"}
                </td>
              </tr>
            ) : (
              placementRows(rows, body.summary.placement_counts, siteState)
            )}
          </tbody>
        </DataTable>
      </div>
      <EarlyWarningList warnings={warnings} max={4} showSite />
      <details className="placement-policy" data-placement-policy>
        <summary>{PLACEMENT_POLICY_SUMMARY}</summary>
        <ul>
          {PLACEMENT_POLICY_LINES.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <p>{PLACEMENT_POLICY_FOOTER}</p>
      </details>
      {loadMore !== null ? (
        <p className="portfolio-more">
          <button type="button" className="v69-chip" onClick={loadMore}>
            Load more Findings
          </button>
        </p>
      ) : null}
      <div className="panel-bottom">
        <Link to={estateHref("/findings", window)}>Open all Findings →</Link>
        {pending === null && rows.length > 0 ? <span>{PRIORITY_BOTTOM_LINE}</span> : null}
      </div>
    </section>
  );
}

/**
 * OUT-B B6 (R521): the panel keeps its slot and shows the outcome matrix from `GET /api/estate/outcome-summary`
 * (mock `portfolio.js:50`, `outcomes.js:153-154`). The portfolio body's `objectives` wire stays but is not rendered.
 */
function ObjectivesPanel({ summary }: { summary: EstateResult<EstateOutcomeSummaryBody> | null }) {
  return (
    <section className="panel" aria-labelledby="portfolio-objectives-heading" data-portfolio-panel="objectives">
      <div className="panel-head">
        <div>
          <h2 id="portfolio-objectives-heading">{OUTCOME_MATRIX_LABEL}</h2>
          <p>{OUTCOME_MATRIX_NOTE}</p>
        </div>
      </div>
      <div className="portfolio-matrix-scroll" data-portfolio-scroll="objectives">
        <OutcomeMatrixBody read={summary} />
      </div>
    </section>
  );
}

function EvidenceAside({ body, window }: { body: EstatePortfolioBody; window: Window }) {
  const prompt = body.evidence_prompt;
  return (
    <div className="portfolio-evidence note" role="group" aria-labelledby="portfolio-evidence-heading" data-portfolio-prompt={prompt.state}>
      <div>
        <p className="portfolio-evidence__title" role="heading" aria-level={3} id="portfolio-evidence-heading">
          {EVIDENCE_ASIDE}
        </p>
      </div>
      <p>{prompt.text}</p>
      {prompt.state === "AVAILABLE" && prompt.site_code !== null ? (
        <p className="portfolio-evidence__site" data-portfolio-prompt-site={prompt.site_code}>
          Site {prompt.site_code}
        </p>
      ) : null}
      <Link to={estateHref(prompt.destination, window)}>Inspect the constraint →</Link>
    </div>
  );
}

/** CH-4: the opportunity panel's fixed words (mock `portfolio.js:53` literals; MD-CH4-4 for the right side). */
export const OPPORTUNITY_NONE = "No opportunity found in this period";
export const OPPORTUNITY_UNREAD = "Opportunities could not be read";
export const OPPORTUNITY_UNREAD_DETAIL = "Nothing can be said about opportunities until they can be read";
export const OPPORTUNITY_NONE_DETAIL = "Nothing seen on days with complete readings";
export const OPPORTUNITY_SIZE_UNKNOWN_PANEL = "Size not worked out yet";
export const OPPORTUNITY_NO_WHAT_IF = "No what-if yet";
export const OPPORTUNITY_NO_WHAT_IF_DETAIL = "No what-if value worked out yet";
export const OPPORTUNITY_FINDINGS_LINK = "Findings › Opportunities →";

function OpportunityPanel({ body, window }: { body: EstatePortfolioBody; window: Window }) {
  const opportunity = portfolioOpportunity(body);
  const unread = opportunity.state === "UNKNOWN";
  const first = opportunity.state === "FOUND" ? opportunity.items[0] : undefined;
  const more = opportunity.items.length - 1;
  const findingsHref = estateHref(opportunity.destination, window);
  const headroom = first?.study.headroom_kw ?? null;
  return (
    <section className="panel opportunity-panel" aria-labelledby="portfolio-opportunity-heading" data-portfolio-panel="opportunity" data-portfolio-opportunity-state={unread ? "UNKNOWN" : first === undefined ? "NONE" : "FOUND"}>
      <div className="panel-head">
        <div>
          <div className="eyebrow">GROW USEFUL DEMAND</div>
          <h2 id="portfolio-opportunity-heading">{OPPORTUNITY_PANEL}</h2>
        </div>
        <span className="badge badge--neutral">What-if</span>
      </div>
      <div className="opportunity-story">
        <div data-portfolio-opportunity-quantity>
          {first === undefined ? (
            <>
              <span className="opportunity-quantity">{unread ? OPPORTUNITY_UNREAD : OPPORTUNITY_NONE}</span>
              <p>{unread ? OPPORTUNITY_UNREAD_DETAIL : OPPORTUNITY_NONE_DETAIL}</p>
            </>
          ) : (
            <>
              <span className="opportunity-quantity">
                {headroom === null ? (
                  OPPORTUNITY_SIZE_UNKNOWN_PANEL
                ) : (
                  <>
                    {`${headroom.low}–${headroom.high}`} <small>{first.study.headroom_unit /* CH6b2-R Q7c: server copy (MOCK DEVIATION candidate, CH9-R3 Q2) */}</small>
                  </>
                )}
              </span>
              <p>{first.title}</p>
            </>
          )}
        </div>
        <span className="story-arrow">→</span>
        <div>
          <span className="opportunity-quantity">{OPPORTUNITY_NO_WHAT_IF}</span>
          <p>{OPPORTUNITY_NO_WHAT_IF_DETAIL}</p>
        </div>
      </div>
      <p className="chart-note" data-portfolio-opportunity-note>
        {first === undefined ? (unread ? "" : OPPORTUNITY_NOTE) : `${first.seen_line}${first.limit_line ? ` · ${first.limit_line}` : ""}`}
      </p>
      <div className="panel-bottom">
        {first === undefined ? (
          <Link to={findingsHref}>{OPPORTUNITY_FINDINGS_LINK}</Link>
        ) : (
          <>
            <Link to={first.links.opportunity}>Review opportunity Finding →</Link>
            <Link to={first.links.evidence}>Inspect physical headroom →</Link>
            {more > 0 ? <Link to={findingsHref}>{`${more} more under Findings › Opportunities →`}</Link> : null}
          </>
        )}
      </div>
    </section>
  );
}

function ProgressPanel({ body }: { body: EstatePortfolioBody }) {
  const p = body.progress;
  const pending = countText(p.pending_trial_count, "Unknown");
  const verified = countText(p.verified_resolution_count, "Unknown");
  return (
    <section className="panel progress-panel" aria-labelledby="portfolio-progress-heading" data-portfolio-panel="progress">
      <div className="panel-head">
        <div>
          <div className="eyebrow">CLOSE THE LOOP</div>
          <h2 id="portfolio-progress-heading">{PROGRESS_PANEL}</h2>
        </div>
        <Disclosure summary="Inspect basis ↗" name="portfolio-progress" variant="inline">
          <div className="portfolio-drawer" data-portfolio-drawer="progress">
            <h3>Change and verification basis</h3>
            <DataTable>
              <thead>
                <tr>
                  <th scope="col">Source object</th>
                  <th scope="col">Recorded fact</th>
                  <th scope="col">Outcome meaning</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Maintenance work</td>
                  <td>No completed-work source selected</td>
                  <td>Activity not known yet</td>
                </tr>
                <tr>
                  <td>Policy trial</td>
                  <td>{pending} selected verification windows</td>
                  <td>Outcome pending, not a verified result</td>
                </tr>
                <tr>
                  <td>Verification outcomes</td>
                  <td>{verified} verified outcomes kept in the last 30 days</td>
                  <td>Verified outcome is not recovered value</td>
                </tr>
              </tbody>
            </DataTable>
            {p.rows.length === 0 ? (
              <p data-portfolio-no-actions>No selected Actions in this window</p>
            ) : (
              <ul className="portfolio-progress-rows">
                {p.rows.map((r) => (
                  <li key={r.action_id} data-portfolio-progress-row={r.action_id}>
                    <span data-portfolio-progress-words>
                      Action {displayCode(r.action_code)} · {progressOutcomeWords(r.verification_outcome)}
                    </span>
                    {(r.origin_selected ?? r.origin_revision_selected) ? null : (
                      <small data-portfolio-origin-unselected> The version of the finding it came from is not the one selected</small>
                    )}
                    <TechnicalDetails name={`portfolio-progress-ids-${r.action_id}`}>
                      <span className="portfolio-scope-raw">
                        Action {r.action_id} · event {r.selected_action_event_id ?? "none"} · plan {r.verification_plan_id ?? "none"} ·
                        outcome {r.verification_outcome_id ?? "none"}
                        {r.verification_outcome ? ` (${r.verification_outcome})` : ""}
                      </span>
                    </TechnicalDetails>
                  </li>
                ))}
              </ul>
            )}
            <p className="portfolio-drawer__notice">{NO_SNAPSHOT_NOTICE}</p>
            <p>{PROGRESS_REFERENCE}</p>
            <p>{ACTION_WINDOW_NOTE}</p>
          </div>
        </Disclosure>
      </div>
      <div className="change-line">
        <span className="change-dot" />
        <strong>Completed activity · Not known yet</strong>
        <span>Outcome unverified</span>
      </div>
      <div className="change-line">
        <span className={`change-dot${(p.pending_trial_count ?? 0) > 0 ? " amber" : ""}`} />
        <strong>Trials waiting for a result · {pending}</strong>
        <span>Guardrails incomplete</span>
      </div>
      <div className="change-line">
        <span className={`change-dot${(p.verified_resolution_count ?? 0) > 0 ? " blue" : ""}`} />
        <strong>Fixes confirmed · {verified}</strong>
        <span>Recovered value not known yet</span>
      </div>
      <div className="outcome-note">{OUTCOME_NOTE}</div>
    </section>
  );
}

/** CH-5c Q9: the scope-ids load; one read for every Site, started when the first ids disclosure opens. */
type ScopeIds = { status: "loading" } | EstateResult<EstatePortfolioScopeIdsBody>;

/** Loading copy for the on-open ids read, built from the existing label (no new wording). */
export const ASSESSMENT_IDS_LOADING = `${ASSESSMENT_IDS}…`;

function unavailableIds(): EstateResult<EstatePortfolioScopeIdsBody> {
  return { status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: REFUSAL_COPY.ESTATE_STORE_UNAVAILABLE };
}

function ScopeIdsList({ ids, siteId }: { ids: ScopeIds | null; siteId: string }) {
  if (ids === null || ids.status === "loading") {
    return (
      <p role="status" data-portfolio-assessment-ids-loading>
        {ASSESSMENT_IDS_LOADING}
      </p>
    );
  }
  if (ids.status !== "loaded") {
    return (
      <p role="alert" data-portfolio-assessment-ids-error>
        {ids.copy}
      </p>
    );
  }
  const site = ids.value.sites.find((x) => x.site_id === siteId);
  return (
    <div className="portfolio-scope-ids" data-portfolio-assessment-ids>
      {(site?.selected_revision_ids ?? []).map((id) => (
        <div key={id}>{id}</div>
      ))}
    </div>
  );
}

function ScopeDisclosure({
  body,
  loadIds,
}: {
  body: EstatePortfolioBody;
  loadIds?: () => Promise<EstateResult<EstatePortfolioScopeIdsBody>>;
}) {
  const [ids, setIds] = useState<ScopeIds | null>(null);
  const open = () => {
    if (ids !== null) return; // one read per Portfolio read; a refusal stays shown until the page reloads
    setIds({ status: "loading" });
    const read = loadIds ? loadIds() : Promise.resolve(unavailableIds());
    void read.then(setIds, () => setIds(unavailableIds()));
  };
  return (
    <Disclosure summary="Assessment scope & periods ↗" name="portfolio-scope" variant="inline">
      <div className="portfolio-drawer" data-portfolio-drawer="scope">
        <h3>Portfolio scope & consequence ownership</h3>
        <DataTable>
          <thead>
            <tr>
              <th scope="col">Site / assessment</th>
              <th scope="col">Period</th>
              <th scope="col">Scope</th>
            </tr>
          </thead>
          <tbody>
            {body.scope_disclosure.sites.map((s) => (
              <tr key={s.site_id} data-portfolio-scope-site={s.site_code}>
                <td>
                  <span data-portfolio-scope-summary>
                    {s.site_name} · {selectedAssessmentWords(s.selected_revision_count)}
                  </span>
                  {s.selected_revision_count > 0 ? (
                    <Disclosure
                      summary={ASSESSMENT_IDS}
                      name={`portfolio-scope-ids-${s.site_id}`}
                      variant="inline"
                      technical
                      onOpen={open}
                    >
                      <ScopeIdsList ids={ids} siteId={s.site_id} />
                    </Disclosure>
                  ) : null}
                </td>
                <td>
                  {formatDayRange(s.window.from, s.window.to)}
                </td>
                <td data-portfolio-scope-coverage>
                  {DOMAIN_WORD[s.domain] ?? s.domain} · {coverageStateWords(s.coverage.state)}
                  {/* COV-PARTIAL MOCK DEVIATION R620: the incomplete days on their own line, every day with its
                      D-E5.46 reason (the deep tab never shortens to a count). */}
                  {s.coverage.state === "PARTIAL" && (s.coverage.days?.gaps.length ?? 0) > 0 ? (
                    <>
                      <br />
                      <small data-portfolio-scope-gaps>Incomplete days: {gapReasonClause(s.coverage.days, Infinity)}</small>
                    </>
                  ) : null}
                  {s.source_provenance === null ? <small> · No selected source basis</small> : null}
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <p>
          <strong>Assessment rule</strong> {SCOPE_RULE}
        </p>
        <p>
          <strong>Value ownership</strong> {VALUE_OWNERSHIP}
        </p>
        {body.scope_disclosure.exclusions.length > 0 ? (
          <ul>
            {body.scope_disclosure.exclusions.map((x) => (
              <li key={`${x.line_key}|${x.group_key ?? ""}`} data-portfolio-exclusion>
                <span data-portfolio-exclusion-words>
                  {exclusionLineLabel(x.line_key, body)} · {exclusionReasonWords(x)}
                </span>
                <Disclosure summary="Technical details" name={`portfolio-exclusion-${x.line_key}`} variant="inline" technical>
                  <span className="portfolio-scope-raw">
                    {x.line_key} · {x.group_key ?? "no group"} · {x.reason_codes.length > 0 ? x.reason_codes.join(", ") : "no reason code"}
                  </span>
                </Disclosure>
              </li>
            ))}
          </ul>
        ) : null}
        <p className="portfolio-drawer__notice">{SCOPE_NOTICE}</p>
      </div>
    </Disclosure>
  );
}

/** POLISH §3 ids: the plain outcome word of one progress row; the stored code stays in Technical details. */
export function progressOutcomeWords(outcome: string | null | undefined): string {
  if (outcome === null || outcome === undefined || outcome === "") return "no result yet";
  if (outcome === "VERIFIED") return "fix confirmed";
  if (outcome === "INEFFECTIVE") return "fix did not work";
  if (outcome === "INCONCLUSIVE") return "result not clear";
  return "result recorded";
}

function noneOr(values: string[] | undefined): string {
  return values && values.length > 0 ? values.join(", ") : "None selected";
}

function FooterSourceBlock({ block }: { block: EstateSourceBlock | null | undefined }) {
  if (!block || Object.keys(block).length === 0) return <p>No selected source basis</p>;
  return (
    <TechnicalDetails name="portfolio-footer-source">
    <dl data-portfolio-footer-source>
      <dt>Source basis</dt>
      <dd>
        <div>Classification: {block.classification ?? "None selected"}</div>
        <div>State: {block.state}</div>
        <div>Source IDs: {noneOr(block.source_ids)}</div>
        <div>Evidence IDs: {noneOr(block.evidence_ids)}</div>
        <div>Basis SHA-256: {block.basis_sha256 ?? "None selected"}</div>
        <div>
          Reasons:{" "}
          {block.reasons && block.reasons.length > 0
            ? block.reasons.map((r) => r.code).join(", ")
            : "None selected"}
        </div>
      </dd>
    </dl>
    </TechnicalDetails>
  );
}

function ContextFooter({ body }: { body: EstatePortfolioBody }) {
  const footer = body.footer;
  const line = footer === null ? undefined : body.selected_lines.find((x) => x.line_key === footer.line_key);
  const domains = new Map(body.scope_disclosure.sites.map((s) => [s.site_id, s.domain]));
  // r1b2 R12: the warning only from another applicable EV Site whose coverage is UNKNOWN/PENDING/STALE.
  const warn = body.coverage.sites.some(
    (s) => domains.get(s.site_id) === "EV_CHARGING" && s.site_id !== line?.site_id && EV_INCOMPLETE.has(s.state),
  );
  const quantity = line ? quantityText(line.quantity) : null;
  const amount = line ? moneyText(amountOf(line.amount), "even2") : null;
  return (
    <div className="portfolio-context-footer" data-portfolio-footer={footer === null ? "none" : footer.line_key}>
      {footer !== null && quantity !== null && amount !== null ? (
        <>
          <span>
            Business context: {footer.site_name} delivered <strong>{quantity}</strong> in selected records;{" "}
            <strong>{amount}</strong> at the recorded tariff, before costs (a what-if).
          </span>
          <Disclosure summary="Energy basis ↗" name="portfolio-energy-basis" variant="inline">
            <p>Selected window: {moneyWindowText(footer.window_start, footer.window_end) ?? "Window not recorded"}.</p>
            <FooterSourceBlock block={footer.source_provenance} />
          </Disclosure>
          <Link to={footer.destination}>Inspect energy basis →</Link>
        </>
      ) : (
        <>
          <span>{NO_ENERGY_TOTAL}</span>
          <span>{ENERGY_UNAVAILABLE}</span>
        </>
      )}
      <span data-portfolio-footer-coverage>{warn ? EV_COVERAGE_WARNING : CATEGORIES_SEPARATE}</span>
    </div>
  );
}

/**
 * PF-T: the section tab row. The Site tab family (`site-tabs` links with `aria-current`, not an ARIA tablist): each
 * tab is an address carrying the window and cutoff; `lens` only on Act first. A count that is unknown shows no badge.
 */
function PortfolioTabs({
  current,
  window,
  lens,
  counts,
}: {
  current: PortfolioTab;
  window: Window;
  lens: EstateLens;
  counts: Partial<Record<PortfolioTab, number | null | undefined>>;
}) {
  const rowRef = useCurrentTabInView<HTMLElement>();
  return (
    <nav className="site-tabs pf-tabs" aria-label={PORTFOLIO_TABS_LABEL} ref={rowRef} data-portfolio-tabs>
      <ol className="site-tabs__list">
        {PORTFOLIO_TABS.map(({ tab, label }) => {
          const n = counts[tab];
          return (
            <li key={tab} className={tab === "scope" ? "site-tabs__item pf-tabs__deep" : "site-tabs__item"}>
              <Link className="site-tabs__link" to={portfolioHref(window, lens, tab)} aria-current={tab === current ? "page" : undefined}>
                <span data-pf-tab-label>{label}</span>
                {typeof n === "number" ? (
                  <span className="pf-tabs__count" data-pf-tab-count>
                    {n}
                  </span>
                ) : null}
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

/** PF-T: the Overview keeps the first three ranked findings of "Where management should act first" (v71 `pf-top3`). */
function TopThree({ body, rows, pending, window }: { body: EstatePortfolioBody; rows: EstatePortfolioRow[]; pending: EstateLens | null; window: Window }) {
  const siteState = new Map(body.coverage.sites.map((s) => [s.site_id, s.state as string]));
  const top = rows.slice(0, 3);
  return (
    <section className="panel pf-top3" aria-labelledby="portfolio-top3-heading" data-portfolio-panel="top3">
      <div className="panel-head">
        <div>
          <h2 id="portfolio-top3-heading">{PRIORITY_PANEL}</h2>
          <p>{TOP3_SUBTITLE}</p>
        </div>
        <Link to={portfolioHref(window, "all", "act-first")}>{TOP3_SEE_ALL(pending !== null ? null : body.total_count)}</Link>
      </div>
      {pending !== null ? (
        <p data-portfolio-loading-rows>Loading the findings.</p>
      ) : top.length === 0 ? (
        <p data-portfolio-empty>No selected Findings for this window</p>
      ) : (
        <ol>
          {top.map((row, i) => {
            const finding = linkFor(row.link_refs?.finding);
            return (
              <li key={`${row.finding_id}|${row.finding_revision_id}`} data-portfolio-top3-row>
                <span className="rank" aria-hidden="true">
                  {i + 1}
                </span>
                <div>
                  {finding !== null ? (
                    <Link className="strong" to={finding} data-pf-top3-title>
                      {row.title}
                    </Link>
                  ) : (
                    <strong data-pf-top3-title>{row.title}</strong>
                  )}
                  <small>
                    {row.site_name} · {mechanismWords(row.mechanism)}
                  </small>
                </div>
                <div>
                  <strong className="impact">{consequenceFirst(row, siteState.get(row.site_id))}</strong>
                  <small>{episodeText(row)}</small>
                </div>
                <span className="badge badge--neutral">{PLACEMENT_GROUP_LABEL[row.placement.group]}</span>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

/** PF-T: on a tab change (not on first paint) focus moves to the shown panel's heading. */
function useFocusPanelHeading(tab: PortfolioTab) {
  const panelRef = useRef<HTMLDivElement>(null);
  const shown = useRef(tab);
  useEffect(() => {
    if (shown.current === tab) return;
    shown.current = tab;
    const heading = panelRef.current?.querySelector<HTMLElement>("h2");
    if (!heading) return;
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  }, [tab]);
  return panelRef;
}

function Loaded({
  tab,
  body,
  rows,
  lens,
  pending,
  onLens,
  window,
  loadMore,
  summary,
  loadIds,
}: {
  tab: PortfolioTab;
  loadIds?: () => Promise<EstateResult<EstatePortfolioScopeIdsBody>>;
  body: EstatePortfolioBody;
  rows: EstatePortfolioRow[];
  lens: EstateLens;
  pending: EstateLens | null;
  onLens: (lens: EstateLens) => void;
  window: Window;
  loadMore: (() => void) | null;
  summary: EstateResult<EstateOutcomeSummaryBody> | null;
}) {
  const ctx = contextWords(body.status, body.window.known_at);
  const s = body.summary;
  const checkedDays = (s.count_basis ?? null) === "CHECKED_DAYS";
  // OUT-C U5: the estate summary's early warnings; Unknown until the summary loads.
  const warnings = summary?.status === "loaded" ? summary.value.warnings : null;
  const warningCount = warnings === null ? null : warnings.length;
  const panelRef = useFocusPanelHeading(tab);
  return (
    <>
      <div className="portfolio-context" data-portfolio-context={body.status}>
        <div>
          <Badge tone="neutral" className={`portfolio-badge portfolio-badge--${ctx.tone}`}>
            {ctx.badge}
          </Badge>
          <span data-portfolio-sentence>{ctx.sentence}</span>
          <span data-portfolio-domains>{domainSummary(body)}</span>
        </div>
      </div>
      {/* PF-C1 (v71 `.pf-coverage`): coverage shown once, above the tabs; replaces R620's per-Site notes. */}
      <PortfolioCoverage
        line={summary?.status === "loaded" ? (summary.value.coverage_line ?? null) : null}
        partial={body.scope_disclosure.sites
          .filter((site) => site.coverage.state === "PARTIAL")
          .map((site) => ({ site_code: site.site_code, site_name: site.site_name, days: site.coverage.days }))}
        scopeHref={portfolioHref(window, lens, "scope")}
      />
      <PortfolioTabs
        current={tab}
        window={window}
        lens={lens}
        counts={{
          "act-first": pending !== null ? null : body.total_count,
          opportunity: s.opportunity_count,
          changes: s.accepted_action_count,
        }}
      />
      <div className="pf-panel" data-portfolio-tab-panel={tab} ref={panelRef}>
        {tab === "overview" ? (
          <>
            <h2 className="pf-sr">Overview</h2>
            {/* OUT-A A6: four outcome category cards replace the five value cards (mock pfCard). */}
            <CategoryCards body={body} window={window} summary={summary?.status === "loaded" ? summary.value : null} />
            {/* PF-T: each count links to the tab that holds it (v71 `pf-pulse`), so the Overview is also the contents. */}
            <div className="portfolio-pulse pf-pulse" data-portfolio-pulse>
              <span>
                <Link to={portfolioHref(window, "all", "act-first")}>
                  <strong>{countText(s.priority_site_count, "Not assessed")}</strong> {s.priority_site_count === 1 ? "priority site" : "priority sites"}
                </Link>
              </span>
              {/* CH-4: one count from the opportunity read, each item named by its short label (mock `portfolio.js:45`). */}
              <span data-portfolio-pulse-opportunity>
                <Link to={portfolioHref(window, "all", "opportunity")}>
                  <strong>{countText(s.opportunity_count ?? null, "Unknown")}</strong> {s.opportunity_count === 1 ? "opportunity" : "opportunities"}
                  {(s.opportunity_labels ?? []).length > 0 ? `: ${(s.opportunity_labels ?? []).join(" · ")}` : ""}
                </Link>
              </span>
              <PulseCount
                value={s.evidence_gap_site_count}
                missing="Unknown"
                label="site evidence gaps"
                checkedDays={checkedDays}
                to={portfolioHref(window, "all", "scope")}
              />
              <span>
                <Link to={portfolioHref(window, "all", "changes")}>
                  <strong>{countText(s.accepted_action_count, "Unknown")}</strong> accepted actions
                </Link>
              </span>
              <span data-portfolio-pulse-warnings>
                <Link to={portfolioHref(window, "all", "act-first")}>
                  <strong>{countText(warningCount, "Unknown")}</strong> {warningCount === 1 ? "warning" : "warnings"} not yet priced
                </Link>
              </span>
              <span className="pulse-note">{PULSE_NOTE}</span>
            </div>
            <TopThree body={body} rows={rows} pending={pending} window={window} />
          </>
        ) : tab === "act-first" ? (
          <div className="portfolio-main">
            <PriorityPanel
              body={body}
              rows={rows}
              lens={lens}
              pending={pending}
              onLens={onLens}
              window={window}
              loadMore={loadMore}
              warnings={warnings ?? []}
            />
            <aside className="portfolio-side" data-portfolio-side>
              <EvidenceAside body={body} window={window} />
            </aside>
          </div>
        ) : tab === "outcomes" ? (
          <ObjectivesPanel summary={summary} />
        ) : tab === "opportunity" ? (
          <OpportunityPanel body={body} window={window} />
        ) : tab === "changes" ? (
          <ProgressPanel body={body} />
        ) : (
          <section className="panel pf-scope" aria-labelledby="portfolio-scope-heading" data-portfolio-panel="scope">
            <div className="panel-head">
              <div>
                <h2 id="portfolio-scope-heading">Scope &amp; coverage</h2>
              </div>
            </div>
            <ScopeDisclosure key={`${body.window.from}|${body.window.to}|${body.window.known_at ?? ""}|${body.lens}`} body={body} loadIds={loadIds} />
            <ContextFooter body={body} />
          </section>
        )}
      </div>
    </>
  );
}

type Read = { key: string; windowKey: string; lens: EstateLens; first: EstateResult<EstatePortfolioBody>; more: EstatePortfolioRow[]; next: string | null };

/**
 * PF-T: the one mounted route `/portfolio/:tab?`. An unknown tab redirects to Overview; an old `/portfolio?lens=X`
 * address redirects to `/portfolio/act-first?lens=X`. Both keep the window and cutoff, and redirect before any read.
 */
export function EstatePortfolioPage({ client }: { client?: EstateClient }) {
  const { tab: segment } = useParams();
  const [params] = useSearchParams();
  const tab = portfolioTabFrom(segment);
  if (tab === null || (tab === "overview" && params.get("lens") !== null)) {
    const next = new URLSearchParams(params);
    if (tab === null) next.delete("lens");
    const path = tab === null ? portfolioTabPath("overview") : portfolioTabPath("act-first");
    const search = next.toString();
    return <Navigate replace to={search === "" ? path : `${path}?${search}`} />;
  }
  return <PortfolioTabsPage client={client} tab={tab} />;
}

function PortfolioTabsPage({ client, tab }: { client?: EstateClient; tab: PortfolioTab }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const base = queryFromParams(params);
  // PF-T: the lens belongs to Act first; every other tab reads (and keeps) the whole list.
  const lens = tab === "act-first" ? lensFrom(params) : "all";
  const window: Window = { from: base.from, to: base.to, known_at: base.known_at };
  const key = `${window.from}|${window.to}|${window.known_at ?? ""}|${lens}`;
  const [read, setRead] = useState<Read | null>(null);
  // PF-T (proposal §6): the whole-list read is kept by key, so moving from Act first?lens=cost to another tab, or back, shows it with no new read.
  const cache = useRef(new Map<string, Read>());
  useEffect(() => {
    if (read !== null && read.lens === "all") cache.current.set(read.key, read);
  }, [read]);
  const query: EstatePortfolioQuery = { ...window, lens, limit: PORTFOLIO_PAGE_SIZE, cursor: null };

  useEffect(() => {
    let live = true;
    const hit = lens === "all" ? cache.current.get(key) : undefined;
    if (hit !== undefined) {
      setRead(hit);
      return () => {
        live = false;
      };
    }
    void reads.portfolio(query).then((first) => {
      if (live) setRead({ key, windowKey: `${window.from}|${window.to}|${window.known_at ?? ""}`, lens, first, more: [], next: first.status === "loaded" ? first.value.next_cursor : null });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);

  // OUT-B B6: the outcome summary is read in parallel with the portfolio, for the same window.
  const windowKey = `${window.from}|${window.to}|${window.known_at ?? ""}`;
  const [summaryRead, setSummaryRead] = useState<{ key: string; result: EstateResult<EstateOutcomeSummaryBody> } | null>(null);
  useEffect(() => {
    let live = true;
    const pending =
      reads.getOutcomeSummary === undefined
        ? Promise.resolve<EstateResult<EstateOutcomeSummaryBody>>({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" })
        : reads.getOutcomeSummary(window, () => {
            // INFRA-1: while the summary waits to retry a 503 TEMPORARILY_UNAVAILABLE, the retrying state shows.
            if (live) setSummaryRead({ key: windowKey, result: SUMMARY_RETRYING });
          });
    void pending.then((result) => {
      if (live) setSummaryRead({ key: windowKey, result });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, windowKey]);
  const currentSummary = summaryRead?.key === windowKey ? summaryRead.result : null;

  const current = read?.key === key ? read : null;
  // PL-1 (D-E5.22): when only the lens changed, the held loaded read stays on screen whole until the new one replaces it.
  const held = current === null && read !== null && read.windowKey === windowKey && read.first.status === "loaded" ? read : null;
  const loadMore =
    current === null || current.next === null
      ? null
      : () => {
          const cursor = current.next;
          void reads.portfolio({ ...query, cursor }).then((page) => {
            setRead((prev) => {
              if (prev === null || prev.key !== key) return prev;
              // Any refusal replaces everything shown, so no stale privileged row survives (401, 409, 503).
              if (page.status !== "loaded") return { ...prev, first: page, more: [], next: null };
              return { ...prev, more: [...prev.more, ...page.value.rows], next: page.value.next_cursor };
            });
          });
        };

  const shown = current ?? held;
  const first = shown?.first ?? null;
  const body = first?.status === "loaded" ? first.value : null;
  return (
    <div className="estate-page estate-portfolio portfolio-v2" data-estate-root="portfolio">
      {/* PF-T (proposal §11, MOCK DEVIATION PF-T-1): the date range sits at the top, the same on every tab. */}
      <div className="pf-datebar" data-portfolio-datebar>
        <EstateDateBar
          key={`${window.from}|${window.to}|${window.known_at ?? ""}`}
          query={{ ...window, cursor: null }}
          body={barBody(body)}
          windowRefused={first?.status === "refused" && first.code === "INVALID_WINDOW"}
          onApply={(next) => navigate(portfolioHref(next, lens, tab))}
        />
      </div>
      <PageHeader title={PORTFOLIO_TITLE} subtitle={PORTFOLIO_SUBTITLE} />
      {first === null ? (
        <div className="portfolio-loading" data-estate-loading>
          <p>Loading the Portfolio across the estate.</p>
          <ul aria-label="Portfolio slots being read">
            {["Value cards", PRIORITY_PANEL, OUTCOME_MATRIX_LABEL, OPPORTUNITY_PANEL, PROGRESS_PANEL].map((slot) => (
              <li key={slot}>{slot}</li>
            ))}
          </ul>
        </div>
      ) : first.status === "refused" ? (
        <EstateRefusal code={first.code} copy={first.copy} window={window} firstPage={portfolioHref(window, lens, tab)} />
      ) : (
        <Loaded
          tab={tab}
          body={first.value}
          rows={[...first.value.rows, ...(shown?.more ?? [])]}
          lens={lens}
          pending={held !== null ? lens : null}
          onLens={(next) => navigate(portfolioHref(window, next, "act-first"))}
          window={window}
          loadMore={loadMore}
          summary={currentSummary}
          loadIds={reads.portfolioScopeIds ? () => reads.portfolioScopeIds!({ ...query, lens: shown?.lens ?? lens }) : undefined}
        />
      )}
    </div>
  );
}

