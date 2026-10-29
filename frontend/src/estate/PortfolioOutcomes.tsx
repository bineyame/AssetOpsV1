import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { OutcomeIcon, type OutcomeCategoryKey } from "../sites/outcomeCategories";
import type { EstatePortfolioBody, EstateQuery, EstateValueCard } from "./estateClient";
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

export const NOT_AVAILABLE_YET = "Not available yet";
export const PROTECT_DETAIL = "Service disruptions recorded in Findings · loss not priced";
export const PROTECT_BASIS = "Measured events, counted separately · loss not priced";
export const ASSURE_BASIS = "Completed work does not establish savings";

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

function content(key: OutcomeCategoryKey, body: EstatePortfolioBody): CardContent {
  const card = (k: EstateValueCard["key"]) => body.value_cards.find((c) => c.key === k);
  if (key === "GROW_REVENUE") {
    return {
      value: NOT_AVAILABLE_YET,
      detail: "Site income not recorded",
      basis: "Opportunities · revenue not measured yet",
      destination: "/findings/opportunities",
      tone: "neutral",
    };
  }
  if (key === "OPTIMIZE_COST") {
    const cost = card("OPERATING_COST");
    if (cost === undefined) return { value: NOT_AVAILABLE_YET, detail: "", basis: "", destination: null, tone: "neutral" };
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

/**
 * OUT-A A6: the Portfolio's four outcome category cards (mock `pfCard`, `outcomes.js:144-151`), replacing the five
 * value cards. Only existing fields feed them; the per-Site dots stay empty until B6 fills them.
 */
export function CategoryCards({ body, window }: { body: EstatePortfolioBody; window: Window }) {
  return (
    <div className="value-grid oc-pfgrid" data-portfolio-cards>
      {OUTCOME_CATEGORY_CARDS.map(({ key, name, definition }) => {
        const c = content(key, body);
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
            <div className="oc-sitedots" />
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
