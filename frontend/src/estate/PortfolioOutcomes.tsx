import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";

import { OutcomeIcon, type OutcomeCategoryKey } from "../sites/outcomeCategories";
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
  return { value: card.display_value ?? CARD_VALUE[card.state] ?? "Not established", detail };
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

export const PROTECT_DETAIL = "Service disruptions recorded in Findings · loss not priced";
export const PROTECT_BASIS = "Measured events, counted separately · loss not priced";
export const ASSURE_BASIS = "Completed work does not establish savings";
export const OPTIMIZE_COST_MISSING = {
  value: "Not assessed",
  detail: "Operating cost is not assessed for this selection",
  basis: "No value line",
  destination: "/financials",
  tone: "neutral",
} as const;

/** Rulings A-Q9 / A-Q10: the evidence-gap clause of the Assure detail, from the summary and the scope. */
export function evidenceGapText(gaps: number | null, sites: number): string {
  if (gaps === null) return "evidence gaps not assessed";
  if (gaps === 0) return "no evidence gaps";
  if (gaps === 1) return "evidence gap at 1 site";
  if (gaps === sites) return `evidence gaps at all ${sites} sites`;
  if (gaps < sites) return `evidence gaps at ${gaps} of ${sites} sites`;
  return `evidence gaps at ${gaps} sites`;
}

/** Ruling A-Q10: the Protect value for n Sites with a primary Protect Finding (null: not assessed). */
function protectValue(n: number | null): ReactNode {
  if (n === null) return "Not assessed";
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

function content(key: OutcomeCategoryKey, body: EstatePortfolioBody, summary: EstateOutcomeSummaryBody | null): CardContent {
  const card = (k: EstateValueCard["key"]) => body.value_cards.find((c) => c.key === k);
  if (key === "GROW_REVENUE") {
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
    return { value, detail, basis: cost.basis_text, destination: cost.destination, tone: cost.tone };
  }
  if (key === "PROTECT_ASSET") {
    const n = body.summary.category_counts?.PROTECT_ASSET?.sites_with_primary_finding ?? null;
    return {
      value: protectValue(n),
      detail: PROTECT_DETAIL,
      basis: PROTECT_BASIS,
      destination: "/findings/risks",
      tone: n !== null && n >= 1 ? "red" : "neutral",
    };
  }
  const recovery = card("VERIFIED_RECOVERY");
  const gap = evidenceGapText(body.summary.evidence_gap_site_count, body.scope.authorized_site_count);
  return {
    value: recovery === undefined ? "Not established" : cardValue(recovery, body).value,
    detail: `No verified result yet · no targets declared · ${gap}`,
    basis: recovery?.basis_text || ASSURE_BASIS,
    destination: "/evidence",
    tone: "neutral",
  };
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
