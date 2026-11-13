import { useState, type CSSProperties, type ReactNode } from "react";
import { RangeLink as Link } from "../ui/RangeLink";
import { EvidenceTrace, WhyButton } from "../blocks/EvidenceTrace";
import { defaultChainClient, type ChainClient } from "../sites/chainClient";

import { OutcomeIcon, type OutcomeCategoryKey } from "../sites/outcomeCategories";
import { MissingClaim } from "../ui";
import { StatusPill } from "../ui/StatusPill";
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
import { TEMPORARILY_UNAVAILABLE } from "../sites/temporarilyUnavailable";

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
  values: { lines: string[]; note: string | null } | null;
  /** DIESEL-1-R3j (Protect only): one server line per unexplained-fuel Finding, never added; and its clause. */
  fuel?: { lines: string[]; note: string | null } | null;
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
    return { value: "Not known yet", detail: null, note, days: null, basis: "", destination: CARD_DESTINATION[key], tone: "neutral", grow: null, values: null };
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
    values: key === "ASSURE_PERFORMANCE" ? { lines: card.value_lines ?? [], note: card.value_note ?? null } : null,
    fuel: key === "PROTECT_ASSET" ? { lines: card.fuel_lines ?? [], note: card.fuel_note ?? null } : null,
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
/** PF-C2 (proposal §4): the label of a card's own days line, shown only when its days differ from the coverage line. */
export const DIFFERENT_DAYS = "Different days:";
export function dotStateWord(row: Pick<EstateOutcomeSummaryRow, "state" | "state_label">): string {
  return row.state === "NO_OBJECTIVE" ? DOT_NO_OBJECTIVE : row.state_label;
}

/**
 * OUT-B B6: one entry per Site in the category's outcome state (mock `pfCard` `.oc-sitedots`, `outcomes.js:151`).
 * UQ-FI-3: behind the card's "Why?"; the state is a `StatusPill` (the server word).
 */
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
            {site.site_name}
            <span className="oc-hidden">: </span>
            <StatusPill state={row.state} label={word} />
          </span>
        );
      })}
    </div>
  );
}

/**
 * UQ-FI-3 (rev 7, 7.2): everything on a card but its figure, sentence and basis line, moved behind its "Why?" in the
 * order the card showed it. Same server lines and data hooks as before; no new words.
 */
function CardQualifiers({ cardKey, definition, c, summary }: { cardKey: OutcomeCategoryKey; definition: string; c: CardContent; summary: EstateOutcomeSummaryBody | null }) {
  return (
    <div className="oc-pfwhy" data-portfolio-card-why={cardKey}>
      <p className="oc-pfdef" data-portfolio-card-definition>
        {definition}
      </p>
      {/* PF-C2 (v71 `.oc-pfexception`): the server sends a card's days line only when its days differ from the one
          coverage line above the tabs, so the line is labelled as the exception. */}
      {c.days ? (
        <small className="ob-days oc-pfdays oc-pfexception" data-portfolio-card-days>
          {DIFFERENT_DAYS} {c.days}
        </small>
      ) : null}
      {c.grow ? <PortfolioGrowParts parts={c.grow} /> : null}
      {/* MOCK DEVIATION MD-FUEL-K4-3 (DIESEL-1-R3j): v69 has no unexplained-fuel line on the Protect card; v69 `:131`
          and `:482` forbid a combined total, so each Finding is its own server line (as MD-FUEL-PV1-1). */}
      {c.fuel?.lines.map((line) => (
        <p key={line} className="oc-pfnote" data-portfolio-card-fuel-line>
          {line}
        </p>
      ))}
      {c.fuel?.note ? (
        <p className="oc-pfnote" data-portfolio-card-fuel-note>
          {c.fuel.note}
        </p>
      ) : null}
      {/* MOCK DEVIATION MD-FUEL-PV1-1: v69 `:129` is one "Verified value recovered" tile ("Not established") and v70
          `:492` puts the slot on the Assure card; we show one server line per verified result (its own basis) in that
          slot instead of one value, because v69 `:131` and `:482` forbid a combined total. */}
      {c.values?.lines.map((line) => (
        <p key={line} className="oc-pfnote" data-portfolio-card-value-line>
          {line}
        </p>
      ))}
      {c.values?.note ? (
        <p className="oc-pfnote" data-portfolio-card-value-note>
          {c.values.note}
        </p>
      ) : null}
      {/* CH6b2-R Q1: the Portfolio-body clause, one server line rendered on its own (never joined here). */}
      {c.note ? (
        <p className="oc-pfnote" data-portfolio-card-note>
          {c.note}
        </p>
      ) : null}
      <SiteDots category={cardKey} summary={summary} />
    </div>
  );
}

/**
 * OUT-A A6: the Portfolio's four outcome category cards (mock `pfCard`, `outcomes.js:144-151`), replacing the five
 * value cards. OUT-B B6 fills the per-Site dots and the Grow value from the outcome summary.
 * UQ-FI-3 (rev 7, 7.2; v7.2 sheet "Outcome card", portfolio-hifi `.kpi`): one figure (`--text-figure`, D-UQFI.7), one
 * sentence (the server `detail`), the basis line; the rest behind "Why?" (`CardQualifiers`).
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
  const [whyOpen, setWhyOpen] = useState<{ key: OutcomeCategoryKey; name: string; definition: string; button: HTMLButtonElement } | null>(null);
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
              <div className="oc-pftop">
                {c.destination === null ? (
                  <div className="value-label">{label}</div>
                ) : (
                  <Link className="value-label oc-cardlink" to={estateHref(c.destination, window)} data-portfolio-card-link>
                    {label}
                  </Link>
                )}
                <WhyButton label={name} onOpen={(button) => setWhyOpen({ key, name, definition, button })} />
              </div>
              <div className="value-number oc-pffig" data-portfolio-card-value>
                {c.value}
              </div>
              {c.detail ? (
                <p className="oc-pfsent" data-portfolio-card-detail>
                  {c.detail}
                </p>
              ) : null}
              <div className="value-basis" data-portfolio-card-basis>
                {c.basis}
              </div>
              {/* MOCK DEVIATION R740 (D-UQFI.12): portfolio-hifi's `.kpi` card foot state chip is left out. The server card
                  carries a tone, not a state code; an estate-level state needs an owner-ruled roll-up (BL-69). The per-Site
                  states stay behind "Why?". */}
              <p data-mock-deviation="R740">MOCK DEVIATION D1 (R740)</p>
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
          more={<CardQualifiers cardKey={whyOpen.key} definition={whyOpen.definition} c={content(whyOpen.key, body, summary)} summary={summary} />}
        />
      ) : null}
    </>
  );
}

/** The six states of the matrix colour key, in the mock order (`outcomes.js:154`). */
export const OUTCOME_KEY: readonly { state: string; label: string; tone: string }[] = [
  { state: "NEEDS_ATTENTION", label: "Needs attention", tone: "amber" },
  { state: "WATCH", label: "Watch", tone: "blue" },
  { state: "OPPORTUNITY", label: "Opportunity", tone: "green" },
  { state: "ON_TRACK", label: "On track", tone: "green" },
  { state: "UNKNOWN", label: "Unknown", tone: "gray" },
  { state: "NOT_MEASURED", label: "Not measured yet", tone: "none" },
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
                    <StatusPill state={row.state} label={row.state_label} />
                    {row.lead_outcome === null ? null : <small>{row.lead_outcome.label}</small>}
                  </Link>
                </span>
              );
            })}
          </div>
        ))}
      </div>
      <div className="oc-key" data-portfolio-outcome-key>
        {/* UQ-FI-3: the key shows each state's pill, the same look as the cells. */}
        {OUTCOME_KEY.map(({ state, label }) => (
          <StatusPill key={label} state={state} label={label} />
        ))}
      </div>
    </>
  );
}

/** The matrix panel body for one summary read: loading, unavailable, or the matrix. */
export function OutcomeMatrixBody({ read }: { read: EstateResult<EstateOutcomeSummaryBody> | null }) {
  if (read === null) return <p role="status">{OUTCOME_MATRIX_LOADING}</p>;
  if (read.status === "refused" && read.code === TEMPORARILY_UNAVAILABLE) {
    // INFRA-1 (D-E5.47): "Retrying…" while it waits, then "Still unavailable…"; never a data state.
    return (
      <p role="status" data-temporarily-unavailable>
        {read.copy}
      </p>
    );
  }
  if (read.status !== "loaded") return <p role="alert">{OUTCOME_MATRIX_UNAVAILABLE}</p>;
  return <OutcomeMatrix summary={read.value} />;
}
