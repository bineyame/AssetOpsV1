/*
 * PF-T (2026-11-11): Portfolio section tabs, layout `frontend/mockups/v71/portfolio-tabs.html`; proposal
 * `archive/agent-history/architect-proposal-portfolio-layout-2026-11-10.md` §6, §11.
 * PF-T-1 (closed by SR-1): the Portfolio date bar is gone; the range is the shell's shared top-bar range
 *   (`shell/SharedRangeBar.tsx`, v71 Change 0b). The page keeps only the read's cutoff line under the title.
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
import { useEffect, useMemo, useRef, useState } from "react";
import { displayCode } from "../ui/displayCode";
import { formatDayRange } from "../ui/time";
import { Navigate, useParams, useSearchParams } from "react-router-dom";
import { RangeLink as Link } from "../ui/RangeLink";
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
  type EstateCoverageSite,
  type EstateResult,
  type EstateSourceBlock,
} from "./estateClient";
import { EstateCutoffLine, EstateRefusal, estateHref, queryFromParams } from "./estateShared";
import { moneyText, moneyWindowText, NOT_DISPLAYABLE, quantityText } from "./estateFinancialsWords";
import {
  ACTION_WINDOW_NOTE,
  ASSESSMENT_IDS,
  coverageStateWords,
  analysedDaysMoney,
  gapReasonClause,
  exclusionLineLabel,
  exclusionReasonWords,
  selectedAssessmentWords,
  CATEGORIES_SEPARATE,
  contextWords,
  DOMAIN_WORD,
  domainSummary,
  ENERGY_UNAVAILABLE,
  EV_COVERAGE_WARNING,
  NO_ENERGY_TOTAL,
  NO_SNAPSHOT_NOTICE,
  OPPORTUNITY_NOTE,
  OPPORTUNITY_PANEL,
  OUTCOME_NOTE,
  PORTFOLIO_PAGE_SIZE,
  PORTFOLIO_HUB_TITLE,
  portfolioTabFrom,
  portfolioTabPath,
  type PortfolioTab,
  PRIORITY_PANEL,
  PROGRESS_PANEL,
  PROGRESS_REFERENCE,
  SCOPE_NOTICE,
  SCOPE_RULE,
  VALUE_OWNERSHIP,
} from "./portfolioWords";
import "./estatePortfolio.css";
import { amountOf, CategoryCards, OUTCOME_MATRIX_LABEL, OUTCOME_MATRIX_NOTE, OutcomeMatrixBody } from "./PortfolioOutcomes";
import { PortfolioTabs, portfolioHref } from "./PortfolioTabs";
import { PortfolioCoverage } from "./PortfolioCoverage";
import type { PortfolioSitesClient } from "./portfolioSitesClient";
import { OutcomesSites } from "./sitesList";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import { RangePartNote } from "../ui/RangePartNote";
import { readSharedRange, type DayRange } from "../ui/sharedRange";
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
export { portfolioHref };
const countText = (value: number | null, missing: string) => (value === null ? missing : String(value));

export const NONE_ON_CHECKED_DAYS = "None found on the days assessed";
const EV_INCOMPLETE = new Set(["UNKNOWN", "PENDING_RECOMPUTE", "STALE_SOURCE"]);


/** The shared date bar reads only `status` and `window`; its HISTORICAL line keys off the same status word. */
export function barBody(body: EstatePortfolioBody | null): EstateEnvelope | null {
  return body === null ? null : (body as unknown as EstateEnvelope);
}


/**
 * COV-PARTIAL: a Finding on a gap day of a Site with incomplete days shows no amount (the backend sends none; PARTIAL-
 * MONEY D-E5.45 shows an analysed day's amount with `analysedDaysMoney`). PF-C (proposal
 * §4 C7) shortens the words to the reason alone; PF-W (D-E5.46) says "incomplete days", never "checked".
 */
export const VALUE_WITHHELD = "Value not shown while this site has incomplete days";
export function partialConsequence(c: { state: string; source_revision_id: string | null }): string {
  return c.source_revision_id === null ? "No consequence recorded" : c.state === "UNPRICED" ? "Unpriced" : VALUE_WITHHELD;
}

export function consequenceFirst(row: EstatePortfolioRow, site: EstateCoverageSite | undefined): string {
  const c = row.consequence;
  const siteState = site?.state;
  if (siteState === "PARTIAL" && !(c.state === "PRICED" && (c.amount_low ?? c.amount) != null)) return partialConsequence(c);
  // PARTIAL-MONEY (D-E5.45): a head on an analysed day carries its amount, named as the analysed days' only.
  if (siteState === "PARTIAL" && site?.days) {
    const amount = moneyText({ low: c.amount_low ?? c.amount, high: c.amount_high ?? c.amount, currency: c.currency }, "outward");
    return amount === null ? NOT_DISPLAYABLE : analysedDaysMoney(amount, site.days);
  }
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

export function ProgressPanel({ body }: { body: EstatePortfolioBody }) {
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

export function ScopeDisclosure({
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

export function ContextFooter({ body }: { body: EstatePortfolioBody }) {
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

type HubTab = Exclude<PortfolioTab, "overview">;

function Loaded({
  tab,
  body,
  window,
  summary,
  sites,
  range,
  directory,
}: {
  tab: HubTab;
  body: EstatePortfolioBody;
  window: Window;
  summary: EstateResult<EstateOutcomeSummaryBody> | null;
  sites?: PortfolioSitesClient;
  range: DayRange | null;
  directory?: SiteDirectoryClient;
}) {
  const ctx = contextWords(body.status, body.window.known_at);
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
      {/* IA-P P3b (spec §3): the coverage line and the scope disclosure moved to Evidence & records › Coverage. */}
      <PortfolioTabs current={tab} />
      <div className="pf-panel" data-portfolio-tab-panel={tab} ref={panelRef}>
        {tab === "outcomes" ? (
          <>
            {/* IA-P P4b (spec §6 P4b): L1 E1's headline, L2 the Sites rows (the Sites list's def). */}
            <OutcomesSites sites={sites} waitingBySite={body.summary.waiting_by_site} directory={directory} />
            {/* L3 (MD-IAP-7, Q8): the range category cards, then each Site's objectives in a disclosure; the estate read's
                31-day window is said when it is not the range (P0, pre-flight Q7). */}
            <div data-level="L3">
              <RangePartNote range={range} />
              <CategoryCards body={body} window={window} summary={summary?.status === "loaded" ? summary.value : null} />
              <Disclosure summary="Each Site's objectives" name="portfolio-objectives" variant="inline">
                <ObjectivesPanel summary={summary} />
              </Disclosure>
            </div>
          </>
        ) : (
          // IA-P P3b (MD-IAP-3): Demand & capacity holds the opportunity panel; the mock's L1 chain has no live read.
          <OpportunityPanel body={body} window={window} />
        )}
      </div>
    </>
  );
}

type Read = { key: string; windowKey: string; lens: EstateLens; first: EstateResult<EstatePortfolioBody>; more: EstatePortfolioRow[]; next: string | null };

/**
 * IA-P P3b (spec §2.2, §2.4): the mounted route `/portfolio/:tab` for Outcomes and Demand & capacity. A segment that
 * names no tab (or names the Overview) goes to `/portfolio`, keeping the range, before any read.
 */
export function EstatePortfolioPage({ client, sites, directory }: { client?: EstateClient; sites?: PortfolioSitesClient; directory?: SiteDirectoryClient }) {
  const { tab: segment } = useParams();
  const [params] = useSearchParams();
  const tab = portfolioTabFrom(segment);
  if (tab === null || tab === "overview") {
    const search = params.toString();
    const path = portfolioTabPath("overview");
    return <Navigate replace to={search === "" ? path : `${path}?${search}`} />;
  }
  return <PortfolioTabsPage client={client} sites={sites} tab={tab} directory={directory} />;
}

function PortfolioTabsPage({ client, sites, tab, directory }: { client?: EstateClient; sites?: PortfolioSitesClient; tab: HubTab; directory?: SiteDirectoryClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const sharedRange = readSharedRange(params);
  const base = queryFromParams(params);
  // PF-T: the lens belongs to Act first; every other tab reads (and keeps) the whole list.
  const lens: EstateLens = "all";
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
            return live; // false after unmount: the client stops retrying
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
  const shown = current ?? held;
  const first = shown?.first ?? null;
  const body = first?.status === "loaded" ? first.value : null;
  return (
    <div className="estate-page estate-portfolio portfolio-v2" data-estate-root="portfolio">
      <PageHeader title={PORTFOLIO_HUB_TITLE} />
      {/* SR-1: the range is set in the shell's shared top bar (every page, every tab); this line keeps the read's cutoff. */}
      <div className="pf-cutoff" data-portfolio-cutoff>
        <EstateCutoffLine
          query={{ known_at: window.known_at, cursor: null }}
          body={barBody(body)}
          windowRefused={first?.status === "refused" && first.code === "INVALID_WINDOW"}
        />
      </div>
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
        <EstateRefusal code={first.code} copy={first.copy} window={window} firstPage={portfolioHref(window, tab)} />
      ) : (
        <Loaded tab={tab} body={first.value} window={window} summary={currentSummary} sites={sites} range={sharedRange.status === "set" ? sharedRange : null} directory={directory} />
      )}
    </div>
  );
}


/** IA-P P3b (spec §2.4 `/portfolio/scope`): the second section of Evidence & records › Coverage. */
export const SCOPE_SECTION_TITLE = "Scope & coverage";

/**
 * IA-P P3b (spec §3 "The old Overview's content"): the coverage line and the scope disclosure (with its context
 * footer), moved verbatim from the Portfolio's Scope & coverage tab to Evidence & records › Coverage. It reads the
 * estate portfolio's page 1 and the outcome summary for the window, as the tab did.
 */
export function PortfolioScopeSection({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const base = queryFromParams(params);
  const window: Window = { from: base.from, to: base.to, known_at: base.known_at };
  const key = `${window.from}|${window.to}|${window.known_at ?? ""}`;
  const query: EstatePortfolioQuery = { ...window, lens: "all", limit: PORTFOLIO_PAGE_SIZE, cursor: null };
  const [read, setRead] = useState<{ key: string; first: EstateResult<EstatePortfolioBody>; summary: EstateResult<EstateOutcomeSummaryBody> | null } | null>(null);
  useEffect(() => {
    let live = true;
    const summary = reads.getOutcomeSummary === undefined ? Promise.resolve(null) : reads.getOutcomeSummary(window, () => live);
    void Promise.all([reads.portfolio(query), summary]).then(([first, s]) => {
      if (live) setRead({ key, first, summary: s });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);
  const current = read?.key === key ? read : null;
  const body = current?.first.status === "loaded" ? current.first.value : null;
  const summary = current?.summary?.status === "loaded" ? current.summary.value : null;
  return (
    <section className="panel pf-scope" aria-labelledby="portfolio-scope-heading" data-portfolio-panel="scope">
      <div className="panel-head">
        <div>
          <h2 id="portfolio-scope-heading">{SCOPE_SECTION_TITLE}</h2>
        </div>
      </div>
      {current === null ? (
        <p className="estate-loading">Loading the Portfolio across the estate.</p>
      ) : current.first.status === "refused" ? (
        <EstateRefusal code={current.first.code} copy={current.first.copy} window={window} firstPage={estateHref("/evidence", window)} />
      ) : body !== null ? (
        <>
          <PortfolioCoverage
            line={summary?.coverage_line ?? null}
            partial={body.scope_disclosure.sites
              .filter((site) => site.coverage.state === "PARTIAL")
              .map((site) => ({ site_code: site.site_code, site_name: site.site_name, days: site.coverage.days }))}
            scopeHref={estateHref("/evidence", window)}
          />
          <ScopeDisclosure
            key={`${body.window.from}|${body.window.to}|${body.window.known_at ?? ""}|${body.lens}`}
            body={body}
            loadIds={reads.portfolioScopeIds ? () => reads.portfolioScopeIds!(query) : undefined}
          />
          <ContextFooter body={body} />
        </>
      ) : null}
    </section>
  );
}
