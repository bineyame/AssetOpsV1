import { useEffect, useMemo, useState, type ReactNode } from "react";
import { displayCode } from "../ui/displayCode";
import { formatDayRange, formatDayTime } from "../ui/time";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { linkFor } from "../shell/operatorSiteRoutes";
import { Badge, DataTable, Disclosure, PageHeader } from "../ui";
import { TechnicalDetails } from "../ui/TechnicalDetails";
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
  gapDayList,
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
  PORTFOLIO_PATH,
  PORTFOLIO_SUBTITLE,
  PORTFOLIO_TITLE,
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

/** A Portfolio URL: the accepted window and explicit cutoff, a non-default lens, never a cursor. */
export function portfolioHref(window: Window, lens: EstateLens): string {
  const href = estateHref(PORTFOLIO_PATH, window);
  return lens === "all" ? href : `${href}&lens=${lens}`;
}

/** The shared date bar reads only `status` and `window`; its HISTORICAL line keys off the same status word. */
function barBody(body: EstatePortfolioBody | null): EstateEnvelope | null {
  return body === null ? null : (body as unknown as EstateEnvelope);
}

const countText = (value: number | null, missing: string) => (value === null ? missing : String(value));
/** WALK1-1 (WN-2, R670): on a partly checked estate a zero count is a claim on the checked days only. */
export const NONE_ON_CHECKED_DAYS = "None found on the days assessed";
function PulseCount({ value, missing, label, checkedDays, data }: { value: number | null; missing: string; label: string; checkedDays: boolean; data?: string }) {
  const attrs = data === undefined ? {} : { [data]: "" };
  if (value === 0 && checkedDays) {
    // MOCK DEVIATION (R670): the label leads so the qualified "none" reads as a sentence; v70 shows "{n} {label}".
    return (
      <span {...attrs}>
        {label[0].toUpperCase() + label.slice(1)}: <strong>{NONE_ON_CHECKED_DAYS}</strong>
      </span>
    );
  }
  return (
    <span {...attrs}>
      <strong>{countText(value, missing)}</strong> {label}
    </span>
  );
}

/** COV-PARTIAL: a partly checked Site's row never shows an amount (the backend sends none). */
export function partialConsequence(c: { state: string; source_revision_id: string | null }): string {
  return `Partly checked · ${c.source_revision_id === null ? "No consequence recorded" : c.state === "UNPRICED" ? "Unpriced" : "value shown once every day is checked"}`;
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

function FindingRow({ row, siteState }: { row: EstatePortfolioRow; siteState: string | undefined }) {
  // PB-3 review M1: an open episode shows its recorded start; "No time recorded yet" only when neither end is held.
  const episode =
    moneyWindowText(row.episode_start, row.episode_end) ??
    (row.episode_start !== null ? `From ${formatDayTime(row.episode_start)} · no end time yet` : "No time recorded yet");
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
  onLens,
  window,
  loadMore,
  warnings,
}: {
  body: EstatePortfolioBody;
  rows: EstatePortfolioRow[];
  lens: EstateLens;
  onLens: (lens: EstateLens) => void;
  window: Window;
  loadMore: (() => void) | null;
  warnings: readonly OutcomeWarning[];
}) {
  const siteState = new Map(body.coverage.sites.map((s) => [s.site_id, s.state as string]));
  const incomplete = body.coverage.finding_state === "PARTIAL" || body.coverage.finding_state === "UNKNOWN";
  const count = body.total_count === null ? "Unknown" : String(body.total_count);
  return (
    <section className="panel priority-panel" aria-labelledby="portfolio-priority-heading" data-portfolio-panel="priority">
      <div className="panel-head">
        <div>
          <h2 id="portfolio-priority-heading">{PRIORITY_PANEL}</h2>
          <p>{PRIORITY_SUBTITLE}</p>
        </div>
        <span className="eyebrow">
          {count} findings{incomplete ? " · some days not checked" : ""}
        </span>
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
          {count} findings{incomplete ? " · some days not checked" : ""}
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
            {rows.length === 0 ? (
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
        {rows.length > 0 ? <span>{PRIORITY_BOTTOM_LINE}</span> : null}
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
export const OPPORTUNITY_NONE_DETAIL = "Nothing seen on the days checked";
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
                  {/* COV-PARTIAL MOCK DEVIATION R620: the unchecked days on their own line; v70 has no day gaps. */}
                  {s.coverage.state === "PARTIAL" && (s.coverage.days?.gaps.length ?? 0) > 0 ? (
                    <>
                      <br />
                      <small data-portfolio-scope-gaps>Days not checked yet: {gapDayList(s.coverage.days)}</small>
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

function Loaded({
  body,
  rows,
  lens,
  onLens,
  window,
  loadMore,
  summary,
  loadIds,
}: {
  loadIds?: () => Promise<EstateResult<EstatePortfolioScopeIdsBody>>;
  body: EstatePortfolioBody;
  rows: EstatePortfolioRow[];
  lens: EstateLens;
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
  return (
    <>
      <div className="portfolio-context" data-portfolio-context={body.status}>
        <div>
          <Badge tone="neutral" className={`portfolio-badge portfolio-badge--${ctx.tone}`}>
            {ctx.badge}
          </Badge>
          <span data-portfolio-sentence>{ctx.sentence}</span>
          <span data-portfolio-domains>{domainSummary(body)}</span>
          {/* COV-PARTIAL MOCK DEVIATION R620: one note per partly checked Site; v70 shows the badge and counts only. */}
          {body.scope_disclosure.sites
            .filter((site) => site.coverage.state === "PARTIAL" && site.coverage.days?.text)
            .map((site) => (
              <span key={site.site_id} className="portfolio-partial" data-portfolio-partial={site.site_code}>
                {site.site_name}: {site.coverage.days?.text}
                {(site.coverage.days?.gaps.length ?? 0) <= 7
                  ? ` · not assessed: ${gapDayList(site.coverage.days)}`
                  : " · the days are listed under Assessment scope & periods"}
              </span>
            ))}
        </div>
        <ScopeDisclosure key={`${body.window.from}|${body.window.to}|${body.window.known_at ?? ""}|${body.lens}`} body={body} loadIds={loadIds} />
      </div>
      {/* OUT-A A6: four outcome category cards replace the five value cards (mock pfCard). */}
      <CategoryCards body={body} window={window} summary={summary?.status === "loaded" ? summary.value : null} />
      <div className="portfolio-pulse" data-portfolio-pulse>
        <span>
          <strong>{countText(s.priority_site_count, "Not assessed")}</strong> {s.priority_site_count === 1 ? "priority site" : "priority sites"}
        </span>
        {/* CH-4: one count from the opportunity read, each item named by its short label (mock `portfolio.js:45`). */}
        <span data-portfolio-pulse-opportunity>
          <strong>{countText(s.opportunity_count ?? null, "Unknown")}</strong> {s.opportunity_count === 1 ? "opportunity" : "opportunities"}
          {(s.opportunity_labels ?? []).length > 0 ? `: ${(s.opportunity_labels ?? []).join(" · ")}` : ""}
        </span>
        <PulseCount value={s.evidence_gap_site_count} missing="Unknown" label="site evidence gaps" checkedDays={checkedDays} />
        <span>
          <strong>{countText(s.accepted_action_count, "Unknown")}</strong> accepted actions
        </span>
        <span data-portfolio-pulse-warnings>
          <strong>{countText(warningCount, "Unknown")}</strong> {warningCount === 1 ? "warning" : "warnings"} not yet priced
        </span>
        <span className="pulse-note">{PULSE_NOTE}</span>
      </div>
      <div className="portfolio-main">
        <PriorityPanel
          body={body}
          rows={rows}
          lens={lens}
          onLens={onLens}
          window={window}
          loadMore={loadMore}
          warnings={warnings ?? []}
        />
        <aside className="portfolio-side" data-portfolio-side>
          <ObjectivesPanel summary={summary} />
          <EvidenceAside body={body} window={window} />
        </aside>
      </div>
      <div className="portfolio-bottom">
        <OpportunityPanel body={body} window={window} />
        <ProgressPanel body={body} />
      </div>
      <ContextFooter body={body} />
    </>
  );
}

type Read = { key: string; first: EstateResult<EstatePortfolioBody>; more: EstatePortfolioRow[]; next: string | null };

export function EstatePortfolioPage({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const base = queryFromParams(params);
  const lens = lensFrom(params);
  const window: Window = { from: base.from, to: base.to, known_at: base.known_at };
  const key = `${window.from}|${window.to}|${window.known_at ?? ""}|${lens}`;
  const [read, setRead] = useState<Read | null>(null);
  const query: EstatePortfolioQuery = { ...window, lens, limit: PORTFOLIO_PAGE_SIZE, cursor: null };

  useEffect(() => {
    let live = true;
    void reads.portfolio(query).then((first) => {
      if (live) setRead({ key, first, more: [], next: first.status === "loaded" ? first.value.next_cursor : null });
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
        : reads.getOutcomeSummary(window);
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
  const loadMore =
    current === null || current.next === null
      ? null
      : () => {
          const cursor = current.next;
          void reads.portfolio({ ...query, cursor }).then((page) => {
            setRead((prev) => {
              if (prev === null || prev.key !== key) return prev;
              // Any refusal replaces everything shown, so no stale privileged row survives (401, 409, 503).
              if (page.status !== "loaded") return { key, first: page, more: [], next: null };
              return { ...prev, more: [...prev.more, ...page.value.rows], next: page.value.next_cursor };
            });
          });
        };

  const first = current?.first ?? null;
  const body = first?.status === "loaded" ? first.value : null;
  return (
    <div className="estate-page estate-portfolio portfolio-v2" data-estate-root="portfolio">
      <PageHeader title={PORTFOLIO_TITLE} subtitle={PORTFOLIO_SUBTITLE} />
      <EstateDateBar
        key={`${window.from}|${window.to}|${window.known_at ?? ""}`}
        query={{ ...window, cursor: null }}
        body={barBody(body)}
        windowRefused={first?.status === "refused" && first.code === "INVALID_WINDOW"}
        onApply={(next) => navigate(portfolioHref(next, lens))}
      />
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
        <EstateRefusal code={first.code} copy={first.copy} window={window} firstPage={portfolioHref(window, lens)} />
      ) : (
        <Loaded
          body={first.value}
          rows={[...first.value.rows, ...(current?.more ?? [])]}
          lens={lens}
          onLens={(next) => navigate(portfolioHref(window, next))}
          window={window}
          loadMore={loadMore}
          summary={currentSummary}
          loadIds={reads.portfolioScopeIds ? () => reads.portfolioScopeIds!(query) : undefined}
        />
      )}
    </div>
  );
}

