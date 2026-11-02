import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";

import { OutcomeIcon, type OutcomeCategoryKey } from "../sites/outcomeCategories";
import { boardMoneyText } from "../sites/OutcomeBoard";
import { MissingClaim } from "../ui";
import type { EstateOutcomeSummaryBody, EstatePortfolioBody, EstateQuery, EstateResult, EstateValueCard } from "./estateClient";
import type { FinancialAmount } from "./estateEvidenceMoneyClient";
import { categoryLabel, moneyText, moneyWindowText, NOT_DISPLAYABLE } from "./estateFinancialsWords";
import { estateHref } from "./estateShared";
import { CARD_VALUE } from "./portfolioWords";

type Window = Pick<EstateQuery, "from" | "to" | "known_at">;

export const amountOf = (value: { low: unknown; high: unknown; currency: string | null } | null | undefined) =>
  (value ?? null) as FinancialAmount | null;

/** The value and detail of one server value card (W3-03 closure 1). Money formatting lives here only. */
export function cardValue(card: EstateValueCard, body: EstatePortfolioBody): { value: string; detail: string } {
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
  return { value: card.display_value ?? CARD_VALUE[card.state] ?? "Not known yet", detail };
}

/** OUT-A A6: the four outcome categories in canonical order, with the v7.0 mock's names and definitions. */
export const OUTCOME_CATEGORY_CARDS: readonly { key: OutcomeCategoryKey; name: string; definition: string }[] = [
  {
    key: "GROW_REVENUE",
    name: "Grow revenue",
    definition: "Capture more value from existing infrastructure and expand earning potential",
  },
  {
    key: "OPTIMIZE_COST",
    name: "Optimize cost and efficiency",
    definition: "Eliminate avoidable expenditure and get more output from operational resources",
  },
  {
    key: "PROTECT_ASSET",
    name: "Protect asset and capital",
    definition: "Preserve asset value, avoid premature replacement and reduce service disruption",
  },
  {
    key: "ASSURE_PERFORMANCE",
    name: "Assure performance and returns",
    definition: "Establish with defensible evidence whether the infrastructure is delivering expected results",
  },
];

export const PROTECT_DETAIL = "Service disruptions recorded as findings · loss not priced";
/** OUT-C U5: the Protect detail once the outcome summary is loaded; the early warnings are a separate clause. */
export function protectDetailText(summary: EstateOutcomeSummaryBody | null): string {
  const category = summary?.categories.find((c) => c.category === "PROTECT_ASSET");
  if (summary === null || category === undefined) return PROTECT_DETAIL;
  const w = category.warning_count;
  return `Service disruptions recorded as findings · ${w} early ${w === 1 ? "warning" : "warnings"}, counted separately · loss not priced`;
}
export const PROTECT_BASIS = "Measured events, counted separately · loss not priced";
export const ASSURE_BASIS = "Completed work does not establish savings";
export const OPTIMIZE_COST_MISSING = {
  value: "Not assessed",
  detail: "Operating cost is not assessed for this selection",
  basis: "No value line",
  destination: "/financials",
  tone: "neutral",
} as const;

/** WALK1-1 (WN-2, R670): how much of a partly checked estate was checked; null unless counts are on checked days. */
export function checkedDaysClause(body: EstatePortfolioBody): string | null {
  if ((body.summary.count_basis ?? null) !== "CHECKED_DAYS") return null;
  const days = body.summary.checked_days ?? [];
  if (days.length === 0) return null;
  if (days.length === 1) return `${days[0].checked} of ${days[0].requested} days checked at ${days[0].site_name}`;
  return `days not checked yet at ${days.length} sites`;
}

const withClause = (detail: string, clause: string | null) => (clause === null ? detail : `${detail} · ${clause}`);
const onCheckedDays = (body: EstatePortfolioBody) => (body.summary.count_basis ?? null) === "CHECKED_DAYS";

/** Rulings A-Q9 / A-Q10: the evidence-gap clause of the Assure detail, from the summary and the scope. */
export function evidenceGapText(gaps: number | null, sites: number, checkedDays = false): string {
  if (gaps === null) return "evidence gaps not assessed";
  if (gaps === 0) return checkedDays ? "no evidence gaps on the days checked" : "no evidence gaps";
  if (gaps === 1) return "evidence gap at 1 site";
  if (gaps === sites) return `evidence gaps at all ${sites} sites`;
  if (gaps < sites) return `evidence gaps at ${gaps} of ${sites} sites`;
  return `evidence gaps at ${gaps} sites`;
}

/** Ruling A-Q10: the Protect value for n Sites with a primary Protect Finding (null: not assessed). */
function protectValue(n: number | null, checkedDays: boolean): ReactNode {
  if (n === null) return "Not assessed";
  if (n === 0 && checkedDays) {
    return (
      <>
        None found <small>on the days checked</small>
      </>
    );
  }
  if (n === 0) return "No sites disrupted";
  return (
    <>
      {n} <small>{n === 1 ? "site disrupted" : "sites disrupted"}</small>
    </>
  );
}

interface CardContent {
  value: ReactNode;
  detail: string;
  basis: string;
  destination: string | null;
  tone: string;
}

/** B-Q27 (R549): the first Site's Grow `short_value`, when the outcome summary carries one. */
export function growShortValue(summary: EstateOutcomeSummaryBody | null): string | null {
  for (const site of summary?.sites ?? []) {
    const value = site.rows.find((r) => r.category === "GROW_REVENUE")?.short_value ?? null;
    if (value !== null && value !== "") return value;
  }
  return null;
}

/** WALK1-1 (WN-3, R672): each Site whose Grow row carries an amount (a declared price × measured kWh estimate). */
export function growEstimates(summary: EstateOutcomeSummaryBody | null): { site: string; money: string }[] {
  const out: { site: string; money: string }[] = [];
  for (const site of summary?.sites ?? []) {
    const row = site.rows.find((r) => r.category === "GROW_REVENUE");
    const money = boardMoneyText(row?.headline_money ?? null);
    if (money !== null) out.push({ site: site.site_name, money });
  }
  return out;
}
export const GROW_ESTIMATE_BASIS = "Declared price × measured kWh · not billed or collected";

function content(key: OutcomeCategoryKey, body: EstatePortfolioBody, summary: EstateOutcomeSummaryBody | null): CardContent {
  const card = (k: EstateValueCard["key"]) => body.value_cards.find((c) => c.key === k);
  const clause = checkedDaysClause(body);
  if (key === "GROW_REVENUE") {
    // D-W1-4: amounts from different Sites (different windows) are never added; each Site is named with its own.
    const estimates = growEstimates(summary);
    if (estimates.length > 0) {
      const k = estimates.length;
      return {
        value:
          k === 1 ? (
            <>
              {estimates[0].money} <small>estimated</small>
            </>
          ) : (
            <>
              {k} <small>sites with an estimate</small>
            </>
          ),
        detail: `${estimates.map((e) => `${e.site} ${e.money}`).join(" · ")} · latest day per site`,
        basis: GROW_ESTIMATE_BASIS,
        destination: "/findings/opportunities",
        tone: "green",
      };
    }
    const short = growShortValue(summary);
    if (short !== null) {
      return {
        value: short,
        detail: "Site income not recorded",
        basis: "Opportunities · revenue not measured yet",
        destination: "/findings/opportunities",
        tone: "green",
      };
    }
    return {
      value: (
        <MissingClaim as="span" gapId="G-portfolio-grow-revenue" placement="portfolio.outcomes.grow-value">
          Not available yet
        </MissingClaim>
      ),
      detail: "Site income not recorded",
      basis: "Opportunities · revenue not measured yet",
      destination: "/findings/opportunities",
      tone: "neutral",
    };
  }
  if (key === "OPTIMIZE_COST") {
    const cost = card("OPERATING_COST");
    // Addendum 2: the backend always sends OPERATING_COST, so its absence is a malformed body; keep the card in the
    // unknown wording (estate/portfolio.py DISPLAYED_VALUE["UNKNOWN"]).
    if (cost === undefined) return { ...OPTIMIZE_COST_MISSING };
    const { value, detail } = cardValue(cost, body);
    return { value, detail: withClause(detail, clause), basis: cost.basis_text, destination: cost.destination, tone: cost.tone };
  }
  if (key === "PROTECT_ASSET") {
    const n = body.summary.category_counts?.PROTECT_ASSET?.sites_with_primary_finding ?? null;
    return {
      value: protectValue(n, onCheckedDays(body)),
      detail: withClause(protectDetailText(summary), clause),
      basis: PROTECT_BASIS,
      destination: "/findings/risks",
      tone: n !== null && n >= 1 ? "red" : "neutral",
    };
  }
  const recovery = card("VERIFIED_RECOVERY");
  const gap = evidenceGapText(body.summary.evidence_gap_site_count, body.scope.authorized_site_count, onCheckedDays(body));
  return {
    // POLISH §3.1 (Assure card): the server's "Not established" reads "Not known yet" on this card.
    value:
      recovery === undefined || recovery.state === "NOT_ESTABLISHED" || recovery.state === "UNSUPPORTED"
        ? "Not known yet"
        : cardValue(recovery, body).value,
    detail: withClause(assureDetailText(summary, gap), clause),
    basis: recovery?.basis_text || ASSURE_BASIS,
    destination: "/evidence",
    tone: "neutral",
  };
}

const sites = (n: number) => `${n} ${n === 1 ? "site" : "sites"}`;

/**
 * OUT-D U5 (R586, review M2): the Assure detail names how many Sites declared targets. It says "no targets
 * declared" only when every Site was read, and names the Sites not checked when some were not.
 */
export function assureDetailText(summary: EstateOutcomeSummaryBody | null, gap: string): string {
  const lead = verifiedText(summary);
  const n = summary?.objective_site_count ?? null;
  const unread = summary?.objective_sites_unread ?? 0;
  if (n === null || (n === 0 && unread > 0)) return `${lead} · ${gap}`;
  if (n === 0) return `${lead} · no targets declared · ${gap}`;
  const unchecked = unread > 0 ? `, ${sites(unread)} not checked` : "";
  return `${lead} · targets declared at ${sites(n)}${unchecked} · ${gap}`;
}

/** WALK1-1 (WN-1, R671): the Assure lead clause from the boards' own verified count (same window as each Site row). */
export function verifiedText(summary: EstateOutcomeSummaryBody | null): string {
  const v = summary?.verified_result_count ?? null;
  const unread = summary?.verified_sites_unread ?? 0;
  const lead =
    v === null
      ? "Verified results not known yet"
      : v === 0
        ? "No verified result yet"
        : `${v} ${v === 1 ? "verified result" : "verified results"}`;
  return v !== null && unread > 0 ? `${lead}, ${sites(unread)} not checked` : lead;
}

/** OUT-B B6: one dot per Site in the category's outcome state (mock `pfCard` `.oc-sitedots`, `outcomes.js:151`). */
function SiteDots({ category, summary }: { category: OutcomeCategoryKey; summary: EstateOutcomeSummaryBody | null }) {
  return (
    <div className="oc-sitedots" data-portfolio-card-dots={category}>
      {(summary?.sites ?? []).map((site) => {
        const row = site.rows.find((r) => r.category === category);
        if (row === undefined) return null;
        return (
          <span
            key={site.site_id}
            className={`tone-${row.tone}`}
            title={`${site.site_name}: ${row.state_label}`}
            data-portfolio-dot={`${site.site_code}|${row.tone}`}
          >
            <i aria-hidden="true"></i>
            {site.site_name}
            <span className="oc-hidden">: {row.state_label}</span>
          </span>
        );
      })}
    </div>
  );
}

/**
 * OUT-A A6: the Portfolio's four outcome category cards (mock `pfCard`, `outcomes.js:144-151`), replacing the five
 * value cards. OUT-B B6 fills the per-Site dots and the Grow value from the outcome summary.
 */
export function CategoryCards({
  body,
  window,
  summary = null,
}: {
  body: EstatePortfolioBody;
  window: Window;
  summary?: EstateOutcomeSummaryBody | null;
}) {
  return (
    <div className="value-grid oc-pfgrid" data-portfolio-cards>
      {OUTCOME_CATEGORY_CARDS.map(({ key, name, definition }) => {
        const c = content(key, body, summary);
        const inner = (
          <>
            <div className="value-label">
              <OutcomeIcon icon={key} label={name} />
              <span data-portfolio-card-name>{name}</span>
              <span className="icon" aria-hidden="true">
                →
              </span>
            </div>
            <p className="oc-pfdef" data-portfolio-card-definition>
              {definition}
            </p>
            <div className="value-number" data-portfolio-card-value>
              {c.value}
            </div>
            <p data-portfolio-card-detail>{c.detail}</p>
            <SiteDots category={key} summary={summary} />
            <div className="value-basis" data-portfolio-card-basis>
              {c.basis}
            </div>
          </>
        );
        const props = { className: `value-card ${c.tone} oc-pfcard`, "data-portfolio-card": key };
        return c.destination === null ? (
          <div key={key} {...props}>
            {inner}
          </div>
        ) : (
          <Link key={key} {...props} to={estateHref(c.destination, window)}>
            {inner}
          </Link>
        );
      })}
    </div>
  );
}

/** The six states of the matrix colour key, in the mock order (`outcomes.js:154`). */
export const OUTCOME_KEY: readonly { label: string; tone: string }[] = [
  { label: "Needs attention", tone: "amber" },
  { label: "Watch", tone: "blue" },
  { label: "Opportunity", tone: "green" },
  { label: "On track", tone: "green" },
  { label: "Unknown", tone: "gray" },
  { label: "Not measured yet", tone: "none" },
];
export const OUTCOME_MATRIX_LABEL = "Outcomes across the estate";
export const OUTCOME_MATRIX_NOTE = "How each site is doing on what matters";
export const OUTCOME_MATRIX_LOADING = "Loading outcomes across the estate…";
export const OUTCOME_MATRIX_UNAVAILABLE = "Outcome status is not available right now";

/**
 * OUT-B B6: the Portfolio outcome matrix (mock `portfolioOutcomes`, `outcomes.js:153-154`): a header row of Site
 * links, one row per outcome category, and the colour key. Labels and state words come from the summary read.
 */
export function OutcomeMatrix({ summary }: { summary: EstateOutcomeSummaryBody }) {
  const columns = { "--oc-sites": String(Math.max(summary.sites.length, 1)) } as CSSProperties;
  return (
    <>
      <div className="oc-matrix" role="table" aria-label={OUTCOME_MATRIX_LABEL} style={columns} data-portfolio-outcome-matrix>
        <div className="oc-mrow oc-mhead" role="row">
          <span role="columnheader" className="oc-hidden">
            Outcome
          </span>
          {summary.sites.map((site) => (
            <span key={site.site_id} role="columnheader" data-portfolio-matrix-site={site.site_code}>
              <Link to={site.overview_href}>{site.site_name}</Link>
            </span>
          ))}
        </div>
        {summary.categories.map((category) => (
          <div key={category.category} className="oc-mrow" role="row" data-portfolio-outcome-row={category.category}>
            <span role="rowheader" className="oc-orow" title={category.definition}>
              <OutcomeIcon icon={category.category} label={category.label} />
              <span>{category.label}</span>
              <span className="oc-hidden">{category.definition}</span>
            </span>
            {summary.sites.map((site) => {
              const row = site.rows.find((r) => r.category === category.category);
              if (row === undefined) return <span key={site.site_id} role="cell" />;
              return (
                <span key={site.site_id} role="cell">
                  <Link
                    className={`oc-cell tone-${row.tone}`}
                    to={site.overview_href}
                    title={`${site.site_name} · ${category.label}: ${row.lead_outcome?.label ?? row.state_label}`}
                    data-portfolio-outcome-cell={`${site.site_code}|${category.category}|${row.tone}`}
                  >
                    <b>{row.state_label}</b>
                    {row.lead_outcome === null ? null : <small>{row.lead_outcome.label}</small>}
                  </Link>
                </span>
              );
            })}
          </div>
        ))}
      </div>
      <div className="oc-key" data-portfolio-outcome-key>
        {OUTCOME_KEY.map(({ label, tone }) => (
          <span key={label}>
            <i className={`tone-${tone}`} aria-hidden="true"></i>
            {label}
          </span>
        ))}
      </div>
    </>
  );
}

/** The matrix panel body for one summary read: loading, unavailable, or the matrix. */
export function OutcomeMatrixBody({ read }: { read: EstateResult<EstateOutcomeSummaryBody> | null }) {
  if (read === null) return <p role="status">{OUTCOME_MATRIX_LOADING}</p>;
  if (read.status !== "loaded") return <p role="alert">{OUTCOME_MATRIX_UNAVAILABLE}</p>;
  return <OutcomeMatrix summary={read.value} />;
}
