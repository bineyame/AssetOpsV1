import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Badge, DataTable, Disclosure, MissingClaim, PageHeader } from "../ui";
import {
  createEstateClient,
  type EstateClient,
  type EstateEnvelope,
  type EstateLens,
  type EstatePortfolioBody,
  type EstatePortfolioQuery,
  type EstatePortfolioRow,
  type EstateQuery,
  type EstateResult,
  type EstateSourceBlock,
  type EstateValueCard,
} from "./estateClient";
import { EstateDateBar, EstateRefusal, estateHref, queryFromParams } from "./estateShared";
import { categoryLabel, moneyText, moneyWindowText, NOT_DISPLAYABLE, quantityText } from "./estateFinancialsWords";
import type { FinancialAmount } from "./estateEvidenceMoneyClient";
import {
  ACTION_WINDOW_NOTE,
  CARD_LABEL,
  CARD_VALUE,
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
  OBJECTIVES_FOOTNOTE,
  OBJECTIVES_PANEL,
  OBJECTIVES_SUBTITLE,
  OPPORTUNITY_NOTE,
  OPPORTUNITY_PANEL,
  OUTCOME_NOTE,
  PORTFOLIO_PAGE_SIZE,
  PORTFOLIO_PATH,
  PORTFOLIO_SUBTITLE,
  PORTFOLIO_TITLE,
  PRIORITY_PANEL,
  PRIORITY_SUBTITLE,
  PROGRESS_PANEL,
  PROGRESS_REFERENCE,
  PULSE_NOTE,
  SCOPE_NOTICE,
  SCOPE_RULE,
  VALUE_OWNERSHIP,
} from "./portfolioWords";
import "./estatePortfolio.css";

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

const amountOf = (value: { low: unknown; high: unknown; currency: string | null } | null | undefined) =>
  (value ?? null) as FinancialAmount | null;

function cardValue(card: EstateValueCard, body: EstatePortfolioBody): { value: string; detail: string } {
  const detail = card.detail ?? "";
  if (card.state === "COMPARABLE_GROUP") {
    const group = body.money.groups.find((g) => g.group_key === card.group_key);
    const window = group ? moneyWindowText(group.window_start, group.window_end) : null;
    return {
      value: (group && moneyText(amountOf(group.amount), "outward")) ?? NOT_DISPLAYABLE,
      detail: card.detail ?? `${categoryLabel(group?.category ?? "")} · ${window ?? "Window not recorded"} · ${card.line_keys.length} Site lines`,
    };
  }
  if (card.state === "SITE_OWNED") {
    const line = body.selected_lines.find((x) => x.line_key === card.line_keys[0]);
    const rounding = line?.domain === "ev_charging" ? "even2" : "outward";
    const window = line ? moneyWindowText(line.window_start, line.window_end) : null;
    return {
      value: (line && moneyText(amountOf(line.amount), rounding)) ?? NOT_DISPLAYABLE,
      detail: card.detail ?? `${line?.site_name ?? ""} · ${categoryLabel(line?.category ?? "")} · ${window ?? "Window not recorded"}`,
    };
  }
  return { value: card.display_value ?? CARD_VALUE[card.state] ?? "Not established", detail };
}

function ValueCard({ card, body, window }: { card: EstateValueCard; body: EstatePortfolioBody; window: Window }) {
  const { value, detail } = cardValue(card, body);
  const inner = (
    <>
      <div className="value-label">
        <span>{CARD_LABEL[card.key]}</span>
      </div>
      <div className="value-number" data-portfolio-card-value>
        {value}
      </div>
      <p>{detail}</p>
      <div className="value-basis">{card.basis_text}</div>
    </>
  );
  const props = { className: `value-card ${card.tone}`, "data-portfolio-card": card.key, "data-portfolio-card-state": card.state };
  if (card.key === "VERIFIED_RECOVERY") {
    // Closure 1: the recovery card is not a claim; its financial basis is a separate text link.
    return (
      <div {...props}>
        {inner}
        {card.destination !== null ? (
          <Link className="value-card__link" to={estateHref(card.destination, window)}>
            Inspect financial basis
          </Link>
        ) : null}
      </div>
    );
  }
  return card.destination === null ? (
    <div {...props}>{inner}</div>
  ) : (
    <Link {...props} to={estateHref(card.destination, window)}>
      {inner}
    </Link>
  );
}

const countText = (value: number | null, missing: string) => (value === null ? missing : String(value));

function consequenceFirst(row: EstatePortfolioRow, siteState: string | undefined): string {
  const c = row.consequence;
  const base =
    c.source_revision_id === null && c.state !== "PRICED"
      ? "No consequence recorded"
      : c.state === "PRICED"
        ? moneyText({ low: c.amount_low ?? c.amount, high: c.amount_high ?? c.amount, currency: c.currency }, "outward") ?? NOT_DISPLAYABLE
        : c.state === "UNPRICED"
          ? "Unpriced"
          : "Source unverified";
  // Closure 1: a pending or historical Site prefixes the first line only and never shows a current amount.
  if (siteState === "PENDING_RECOMPUTE") return `Updating · ${c.state === "PRICED" ? "Value withheld" : base}`;
  if (siteState === "HISTORICAL") return `Historical · ${c.state === "PRICED" ? "Value withheld" : base}`;
  return base;
}

function FindingRow({ row, siteState }: { row: EstatePortfolioRow; siteState: string | undefined }) {
  const episode = moneyWindowText(row.episode_start, row.episode_end) ?? "Episode window not recorded";
  return (
    <tr data-portfolio-row={`${row.finding_id}|${row.finding_revision_id}`}>
      <td>
        {row.links.site !== null ? (
          <Link to={row.links.site} data-portfolio-site-link>
            <strong>{row.site_name}</strong>
          </Link>
        ) : (
          <strong>Site detail unavailable</strong>
        )}
        <small>{DOMAIN_WORD[row.domain] ?? row.domain}</small>
        {row.links.site !== null ? <small data-portfolio-current-view>{CURRENT_SITE_VIEW}</small> : null}
      </td>
      <td>
        {row.links.finding !== null ? (
          <Link to={row.links.finding} data-portfolio-finding-link>
            <strong>{row.title}</strong>
          </Link>
        ) : (
          <strong>{row.title}</strong>
        )}
        <small>
          Finding {row.site_code} · {row.finding_id} · {row.mechanism ?? "Mechanism not recorded"}
        </small>
        {row.links.finding === null ? <small>Finding detail unavailable</small> : null}
      </td>
      <td>
        <strong className="impact" data-portfolio-value>
          {consequenceFirst(row, siteState)}
        </strong>
        <small>Basis not recorded</small>
        <small>{episode}</small>
      </td>
      <td>
        <span className="badge badge--neutral">{row.priority ?? "Not assessed"}</span>
      </td>
      <td>
        <span className="badge badge--neutral">{row.confidence ?? "Not assessed"}</span>
        <small>{row.confidence === null ? "No reviewed confidence measure" : row.confidence_reasons.join(", ")}</small>
      </td>
      <td>
        {row.action_id !== null && row.links.action !== null ? (
          <Link to={row.links.action} data-portfolio-action-link>
            <strong>{row.action_title}</strong>
          </Link>
        ) : (
          <strong>{row.action_id !== null ? row.action_title : "No accepted Action"}</strong>
        )}
        <small>Next move not recorded</small>
        <span className="workflow-text" data-portfolio-workflow>
          {row.workflow_label}
        </span>
        {row.action_id === null ? (
          row.links.finding !== null ? (
            <small>
              <Link to={row.links.finding}>Review Finding</Link>
            </small>
          ) : (
            <small>Finding detail unavailable</small>
          )
        ) : null}
      </td>
    </tr>
  );
}

const TABLE_HEADS = ["Site", "Finding / operating mechanism", "Value / consequence", "Priority", "Confidence", "Action / next move"];

function PriorityPanel({
  body,
  rows,
  lens,
  onLens,
  window,
  loadMore,
}: {
  body: EstatePortfolioBody;
  rows: EstatePortfolioRow[];
  lens: EstateLens;
  onLens: (lens: EstateLens) => void;
  window: Window;
  loadMore: (() => void) | null;
}) {
  const siteState = new Map(body.coverage.sites.map((s) => [s.site_id, s.state as string]));
  const incomplete = body.coverage.finding_state === "PARTIAL" || body.coverage.finding_state === "UNKNOWN";
  const count = body.total_count === null ? "Unknown" : String(body.total_count);
  const both = rows.length > 0 && rows.every((r) => r.priority !== null && r.confidence !== null);
  return (
    <section className="panel priority-panel" aria-labelledby="portfolio-priority-heading" data-portfolio-panel="priority">
      <div className="panel-head">
        <div>
          <h2 id="portfolio-priority-heading">{PRIORITY_PANEL}</h2>
          <p>{PRIORITY_SUBTITLE}</p>
        </div>
        <span className="eyebrow">
          {count} selected Findings{incomplete ? " · Coverage incomplete" : ""}
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
          {count} selected Findings{incomplete ? " · coverage incomplete" : ""}
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
              rows.map((row) => (
                <FindingRow key={`${row.finding_id}|${row.finding_revision_id}`} row={row} siteState={siteState.get(row.site_id)} />
              ))
            )}
          </tbody>
        </DataTable>
      </div>
      {loadMore !== null ? (
        <p className="portfolio-more">
          <button type="button" className="v69-chip" onClick={loadMore}>
            Load more Findings
          </button>
        </p>
      ) : null}
      <div className="panel-bottom">
        <Link to={estateHref("/findings", window)}>Open all Findings →</Link>
        <span>
          {both ? "Priority and confidence answer different questions." : "Priority and confidence are not assessed for these records."}
        </span>
      </div>
    </section>
  );
}

function ObjectivesPanel({ body }: { body: EstatePortfolioBody }) {
  const keys = ["SERVICE_PRODUCT", "BACKUP", "ASSET_CONDITION", "COST_CONTROL", "EVIDENCE"] as const;
  const labels = ["Service / product", "Backup", "Asset condition", "Cost control", "Evidence"];
  const columns = { gridTemplateColumns: `1.2fr repeat(${Math.max(body.objectives.length, 1)}, minmax(64px, 1fr))` };
  return (
    <section className="panel" aria-labelledby="portfolio-objectives-heading" data-portfolio-panel="objectives">
      <div className="panel-head">
        <div>
          <h2 id="portfolio-objectives-heading">{OBJECTIVES_PANEL}</h2>
          <p>{OBJECTIVES_SUBTITLE}</p>
        </div>
      </div>
      <div className="portfolio-matrix-scroll" data-portfolio-scroll="objectives">
        <div className="objective-matrix" role="table" aria-label={OBJECTIVES_PANEL}>
          <div className="matrix-head" role="row" style={columns}>
            <span role="columnheader">Objective</span>
            {body.objectives.map((site) => (
              <span key={site.site_id} role="columnheader" className="matrix-site" data-portfolio-matrix-site={site.site_code}>
                {site.site_name}
                <small>{site.site_code}</small>
              </span>
            ))}
          </div>
          {keys.map((key, i) => (
            <div key={key} className="matrix-row" role="row" style={columns} data-portfolio-objective={key}>
              <span role="rowheader">{labels[i]}</span>
              {body.objectives.map((site) => {
                const cell = site.cells.find((c) => c.key === key);
                if (cell === undefined) return <span key={site.site_id} role="cell" />;
                const tone = cell.state === "REVIEW" || cell.state === "LIMITED" ? "attention" : cell.state === "NOT_APPLICABLE" ? "na" : "unknown";
                return (
                  <span
                    key={site.site_id}
                    role="cell"
                    className={`objective-cell ${tone}`}
                    title={cell.reason}
                    aria-description={cell.reason}
                    data-portfolio-cell={`${site.site_code}|${key}|${cell.state}`}
                  >
                    {cell.label}
                    {cell.destination === null ? <small>Site detail unavailable</small> : null}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <p className="chart-note">{OBJECTIVES_FOOTNOTE}</p>
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

function OpportunityPanel() {
  return (
    <section className="panel opportunity-panel" aria-labelledby="portfolio-opportunity-heading" data-portfolio-panel="opportunity">
      <div className="panel-head">
        <div>
          <div className="eyebrow">GROW USEFUL DEMAND</div>
          <h2 id="portfolio-opportunity-heading">{OPPORTUNITY_PANEL}</h2>
        </div>
        <span className="badge badge--neutral">Scenario</span>
      </div>
      <div className="opportunity-story">
        <div>
          <span className="opportunity-quantity">No reviewed scenario</span>
          <p>Eligible productive demand not established</p>
        </div>
        <span className="story-arrow">→</span>
        <div>
          <span className="opportunity-quantity">No eligible headroom or demand basis</span>
          <p>Gross scenario value unavailable</p>
        </div>
      </div>
      <p className="chart-note">{OPPORTUNITY_NOTE}</p>
      <div className="panel-bottom">
        <MissingClaim as="span" className="portfolio-inert" gapId="G-portfolio-opportunity" placement="portfolio.opportunity.review-finding">
          <span aria-label="Review opportunity Finding, Not available yet">Review opportunity Finding · Not available yet</span>
        </MissingClaim>
        <MissingClaim as="span" className="portfolio-inert" gapId="G-portfolio-opportunity" placement="portfolio.opportunity.inspect-headroom">
          <span aria-label="Inspect physical headroom, Not available yet">Inspect physical headroom · Not available yet</span>
        </MissingClaim>
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
                  <td>Activity not established</td>
                </tr>
                <tr>
                  <td>Policy trial</td>
                  <td>{pending} selected verification windows</td>
                  <td>Outcome pending, not a verified result</td>
                </tr>
                <tr>
                  <td>Verification outcomes</td>
                  <td>{verified} surviving VERIFIED outcomes in 30 days</td>
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
                    Action {r.action_code} · {r.action_id} · event {r.selected_action_event_id ?? "none"} · plan{" "}
                    {r.verification_plan_id ?? "none"} · outcome {r.verification_outcome_id ?? "none"}
                    {r.verification_outcome ? ` (${r.verification_outcome})` : ""}
                    {r.origin_revision_selected ? null : <small data-portfolio-origin-unselected> Origin Finding revision not selected</small>}
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
        <strong>Completed activity · Not established</strong>
        <span>Outcome unverified</span>
      </div>
      <div className="change-line">
        <span className={`change-dot${(p.pending_trial_count ?? 0) > 0 ? " amber" : ""}`} />
        <strong>Policy trial awaiting outcome · {pending}</strong>
        <span>Guardrails incomplete</span>
      </div>
      <div className="change-line">
        <span className={`change-dot${(p.verified_resolution_count ?? 0) > 0 ? " blue" : ""}`} />
        <strong>Verified resolutions · {verified}</strong>
        <span>Recovered value not established</span>
      </div>
      <div className="outcome-note">{OUTCOME_NOTE}</div>
    </section>
  );
}

function ScopeDisclosure({ body }: { body: EstatePortfolioBody }) {
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
              <tr key={s.site_id}>
                <td>
                  {s.site_name} · {s.selected_revision_ids.length > 0 ? s.selected_revision_ids.join(", ") : "No selected assessment"}
                </td>
                <td>
                  {s.window.from.slice(0, 10)}–{s.window.to.slice(0, 10)} UTC
                </td>
                <td>
                  {DOMAIN_WORD[s.domain] ?? s.domain} · {s.coverage.state}
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
              <li key={`${x.line_key}|${x.group_key ?? ""}`}>
                {x.line_key} · {x.group_key ?? "no group"} · {x.reason_codes.join(", ")}
              </li>
            ))}
          </ul>
        ) : null}
        <p className="portfolio-drawer__notice">{SCOPE_NOTICE}</p>
      </div>
    </Disclosure>
  );
}

function noneOr(values: string[] | undefined): string {
  return values && values.length > 0 ? values.join(", ") : "None selected";
}

function FooterSourceBlock({ block }: { block: EstateSourceBlock | null | undefined }) {
  if (!block || Object.keys(block).length === 0) return <p>No selected source basis</p>;
  return (
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
            <strong>{amount}</strong> gross tariff scenario.
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
}: {
  body: EstatePortfolioBody;
  rows: EstatePortfolioRow[];
  lens: EstateLens;
  onLens: (lens: EstateLens) => void;
  window: Window;
  loadMore: (() => void) | null;
}) {
  const ctx = contextWords(body.status, body.window.known_at);
  const s = body.summary;
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
        <ScopeDisclosure body={body} />
      </div>
      <div className="value-grid" data-portfolio-cards>
        {body.value_cards.map((card) => (
          <ValueCard key={card.key} card={card} body={body} window={window} />
        ))}
      </div>
      <div className="portfolio-pulse" data-portfolio-pulse>
        <span>
          <strong>{countText(s.priority_site_count, "Not assessed")}</strong> priority sites
        </span>
        <span>
          <strong>{countText(s.opportunity_count, "Unknown")}</strong> opportunity
        </span>
        <span>
          <strong>{countText(s.evidence_gap_site_count, "Unknown")}</strong> site evidence gaps
        </span>
        <span>
          <strong>{countText(s.accepted_action_count, "Unknown")}</strong> accepted actions
        </span>
        <span className="pulse-note">{PULSE_NOTE}</span>
      </div>
      <div className="portfolio-main">
        <PriorityPanel body={body} rows={rows} lens={lens} onLens={onLens} window={window} loadMore={loadMore} />
        <aside className="portfolio-side" data-portfolio-side>
          <ObjectivesPanel body={body} />
          <EvidenceAside body={body} window={window} />
        </aside>
      </div>
      <div className="portfolio-bottom">
        <OpportunityPanel />
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
        onApply={(next) => navigate(portfolioHref(next, lens))}
      />
      {first === null ? (
        <div className="portfolio-loading" data-estate-loading>
          <p>Loading the Portfolio across the estate.</p>
          <ul aria-label="Portfolio slots being read">
            {["Value cards", PRIORITY_PANEL, OBJECTIVES_PANEL, OPPORTUNITY_PANEL, PROGRESS_PANEL].map((slot) => (
              <li key={slot}>{slot}</li>
            ))}
          </ul>
        </div>
      ) : first.status === "refused" ? (
        <EstateRefusal code={first.code} copy={first.copy} firstPage={portfolioHref(window, lens)} />
      ) : (
        <Loaded
          body={first.value}
          rows={[...first.value.rows, ...(current?.more ?? [])]}
          lens={lens}
          onLens={(next) => navigate(portfolioHref(window, next))}
          window={window}
          loadMore={loadMore}
        />
      )}
    </div>
  );
}

