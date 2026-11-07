import { useState, type CSSProperties, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { EvidenceTrace, WhyButton } from "../blocks/EvidenceTrace";
import { OutcomeCardValue } from "../blocks/OutcomeRow";
import { defaultChainClient, type ChainClient } from "../sites/chainClient";

import { OutcomeIcon, type OutcomeCategoryKey } from "../sites/outcomeCategories";
import { MissingClaim } from "../ui";
import type {
  EstateOutcomeSummaryBody,
  EstateOutcomeSummaryRow,
  EstatePortfolioBody,
  EstatePortfolioCard,
  EstateQuery,
  EstateResult,
} from "./estateClient";
import type { FinancialAmount } from "./estateEvidenceMoneyClient";
import { estateHref } from "./estateShared";

type Window = Pick<EstateQuery, "from" | "to" | "known_at">;

export const amountOf = (value: { low: unknown; high: unknown; currency: string | null } | null | undefined) =>
  (value ?? null) as FinancialAmount | null;

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

/** The card links (markup only); every card's words come from the server (CH-6b2). */
const CARD_DESTINATION: Record<OutcomeCategoryKey, string> = {
  GROW_REVENUE: "/findings/opportunities",
  OPTIMIZE_COST: "/financials",
  PROTECT_ASSET: "/findings/risks",
  ASSURE_PERFORMANCE: "/evidence",
};

interface CardContent {
  value: ReactNode;
  detail: string | null;
  note: string | null;
  days: string | null;
  basis: string;
  destination: string | null;
  tone: string;
  grow: EstatePortfolioCard["parts"] | null;
}

/** CH-6b2 (§B2, CH6b2-R Q1): a server card as markup: `{text} <small>{small}</small>`, the kept Grow gap. */
function serverValue(card: EstatePortfolioCard): ReactNode {
  if (card.missing) {
    return (
      <MissingClaim as="span" gapId="G-portfolio-grow-revenue" placement="portfolio.outcomes.grow-value">
        Not available yet
      </MissingClaim>
    );
  }
  return card.value.small ? (
    <>
      {card.value.text} <small>{card.value.small}</small>
    </>
  ) : (
    card.value.text
  );
}

function content(key: OutcomeCategoryKey, body: EstatePortfolioBody, summary: EstateOutcomeSummaryBody | null): CardContent {
  // CH5d1-R 2.3: Optimize is a server card too (each Site's chain cost claim); like Grow it carries no body note.
  const card = summary?.cards?.[key];
  const note = key === "GROW_REVENUE" || key === "OPTIMIZE_COST" ? null : (body.summary.card_notes?.[key] ?? null);
  if (card === undefined) {
    // The summary has not loaded (or is older): the card says so, never a browser-built value.
    return { value: "Not known yet", detail: null, note, days: null, basis: "", destination: CARD_DESTINATION[key], tone: "neutral", grow: null };
  }
  return {
    value: serverValue(card),
    detail: card.detail,
    note,
    days: card.days_line,
    basis: card.basis_text,
    destination: CARD_DESTINATION[key],
    tone: card.tone,
    grow: card.parts ?? null,
  };
}

/** CH-6b2 (mock v70 `pfGrowParts`, `index.html:421`): the Grow card's three parts, server text only. */
function PortfolioGrowParts({ parts }: { parts: NonNullable<EstatePortfolioCard["parts"]> }) {
  return (
    <dl className="oc-pfgrow" data-portfolio-grow-parts>
      <div>
        <dt>Target</dt>
        <dd data-portfolio-grow-part="target">{parts.target}</dd>
      </div>
      <div>
        <dt>Potential</dt>
        <dd data-portfolio-grow-part="potential">{parts.potential}</dd>
      </div>
      <div>
        <dt>Estimated income</dt>
        <dd data-portfolio-grow-part="income">{parts.income}</dd>
        {parts.income_note ? (
          <dd className="oc-pfnote" data-portfolio-grow-note>
            {parts.income_note}
          </dd>
        ) : null}
      </div>
    </dl>
  );
}

/**
 * WALK1-6 D4 (R697): a card dot is one outcome row, so a Site whose target sits under another outcome reads "No
 * target for this outcome" rather than "No objective declared". Card dots only; the board chips keep the server word.
 */
export const DOT_NO_OBJECTIVE = "No target for this outcome";
export function dotStateWord(row: Pick<EstateOutcomeSummaryRow, "state" | "state_label">): string {
  return row.state === "NO_OBJECTIVE" ? DOT_NO_OBJECTIVE : row.state_label;
}

/** OUT-B B6: one dot per Site in the category's outcome state (mock `pfCard` `.oc-sitedots`, `outcomes.js:151`). */
function SiteDots({ category, summary }: { category: OutcomeCategoryKey; summary: EstateOutcomeSummaryBody | null }) {
  return (
    <div className="oc-sitedots" data-portfolio-card-dots={category}>
      {(summary?.sites ?? []).map((site) => {
        const row = site.rows.find((r) => r.category === category);
        if (row === undefined) return null;
        const word = dotStateWord(row);
        return (
          <span
            key={site.site_id}
            className={`tone-${row.tone}`}
            title={`${site.site_name}: ${word}`}
            data-portfolio-dot={`${site.site_code}|${row.tone}`}
          >
            <i aria-hidden="true"></i>
            {site.site_name}
            <span className="oc-hidden">: {word}</span>
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
  why = defaultChainClient,
}: {
  body: EstatePortfolioBody;
  window: Window;
  summary?: EstateOutcomeSummaryBody | null;
  /** CH-5b3 (CH5b3-R Q2): the "Why?" chain client; the module default unless a test passes one. */
  why?: ChainClient;
}) {
  const [whyOpen, setWhyOpen] = useState<{ key: OutcomeCategoryKey; name: string; button: HTMLButtonElement } | null>(null);
  return (
    <>
      <div className="value-grid oc-pfgrid" data-portfolio-cards>
        {OUTCOME_CATEGORY_CARDS.map(({ key, name, definition }) => {
          const c = content(key, body, summary);
          const label = (
            <>
              <OutcomeIcon icon={key} label={name} />
              <span data-portfolio-card-name>{name}</span>
              <span className="icon" aria-hidden="true">
                →
              </span>
            </>
          );
          // CH-5b3 (CH5b3-R Q4, mock `pfCard`): a div card; the label is the link, stretched over the card by
          // `.oc-cardlink::after`, so the "Why?" button can sit above it (a button cannot be inside a link).
          return (
            <div key={key} className={`value-card ${c.tone} oc-pfcard`} data-portfolio-card={key}>
              {c.destination === null ? (
                <div className="value-label">{label}</div>
              ) : (
                <Link className="value-label oc-cardlink" to={estateHref(c.destination, window)} data-portfolio-card-link>
                  {label}
                </Link>
              )}
              <p className="oc-pfdef" data-portfolio-card-definition>
                {definition}
              </p>
              <OutcomeCardValue why={<WhyButton label={name} onOpen={(button) => setWhyOpen({ key, name, button })} />}>
                <div className="value-number" data-portfolio-card-value>
                  {c.value}
                </div>
              </OutcomeCardValue>
              {/* CH-6b2 (mock `oc-pfdays`): the server's days line; MD-CH5b-4 kept for Optimize only (CH6b2-R Q3). */}
              {c.days ? (
                <small className="ob-days oc-pfdays" data-portfolio-card-days>
                  {c.days}
                </small>
              ) : null}
              {c.grow ? <PortfolioGrowParts parts={c.grow} /> : null}
              {c.detail ? <p data-portfolio-card-detail>{c.detail}</p> : null}
              {/* CH6b2-R Q1: the Portfolio-body clause, one server line rendered on its own (never joined here). */}
              {c.note ? (
                <p className="oc-pfnote" data-portfolio-card-note>
                  {c.note}
                </p>
              ) : null}
              <SiteDots category={key} summary={summary} />
              <div className="value-basis" data-portfolio-card-basis>
                {c.basis}
              </div>
            </div>
          );
        })}
      </div>
      {whyOpen ? (
        <EvidenceTrace
          key={`${window.from}|${window.to}|${window.known_at ?? ""}|${whyOpen.key}`}
          label={whyOpen.name}
          load={() => why.getEstateWhy(whyOpen.key, { from: window.from, to: window.to, known_at: window.known_at })}
          opener={whyOpen.button}
          onClose={() => setWhyOpen(null)}
        />
      ) : null}
    </>
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
