import { Link } from "react-router-dom";

import { Disclosure, Fact, FactList, Panel } from "../ui";
import type { ConsequenceHistoryBody, ConsequenceHistoryResult, ConsequenceHistoryRow } from "./financialsClient";
import { priceWords, quantityWords } from "./FindingConsequence";
import { formatInstant } from "./FoundationRevisionPanel";
import type { FinancialsLinks } from "./SiteFinancials";
import { SOURCE_WORDS, sourceState } from "./sourceProvenance";

/**
 * S4-08: Site > Financials > Assumptions "Interpretation history" (v69 `assumptions`, the history table). Every
 * fuel cost version this site had recorded at one moment, newest first, including earlier and unpriced versions,
 * each with its exact finding, the price version its stored link used, and its own source label.
 *
 * No current amount is ever shown here (`D-2026-10-16-s408` Q3). A recorded amount appears only where the server
 * returned one, labelled as historical, assumption-conditioned audit history beside its exact source label; the
 * finding's own Financials view is the only place a current amount may appear. Nothing is totalled.
 */

const AMOUNT_WORDS: Record<string, string> = {
  SOURCE_CLOSED: "Not shown: this site's source is closed, so no amount is shown for any version.",
  MIXED_OR_UNKNOWN_SOURCE: "Not shown: the source of the readings behind this version is not confirmed.",
  MINOR_UNIT_UNKNOWN: "Not shown: no rounding rule is known for this price's currency.",
  LINEAGE_INCONSISTENT: "Not shown: the price record this version names could not be matched.",
};

function amountWhy(row: ConsequenceHistoryRow): string {
  const d = row.recorded_amount.disposition;
  if (d === "UNPRICED") return `No amount. ${priceWords(row.price.reason)}`;
  if (d === "QUANTITY_UNAVAILABLE") return `No amount. ${quantityWords(row.quantity.reason)}`;
  return AMOUNT_WORDS[d] ?? "Not shown.";
}

function priceText(row: ConsequenceHistoryRow): string {
  switch (row.price.state) {
    case "LINKED":
      return `${row.price.value} ${row.price.currency} per litre`;
    case "NOT_EVALUATED":
      return "Not applied: no fuel amount was worked out";
    case "LINEAGE_INCONSISTENT":
      return "The price record could not be matched, so none is shown";
    default:
      return "No price applied";
  }
}

const CHANGE_WORDS: Record<string, string | null> = {
  PRICE_ONLY: "The price changed; the measured result did not.",
  MEASURED_RESULT_CHANGED: "The measured result changed from the version before.",
  FIRST_VERSION: "First fuel cost version of this finding version.",
  SAME_INPUTS: null,
  PRIOR_UNREADABLE: null,
};

function Ref({ label, value }: { label: string; value: string | null }) {
  if (value === null) return null;
  return (
    <p>
      {label}: <code data-vocabulary-exempt="source-reference">{value}</code>
    </p>
  );
}

function Row({ row, links }: { row: ConsequenceHistoryRow; links: FinancialsLinks }) {
  const current = row.at_cutoff === "CURRENT_AT_CUTOFF";
  const source = SOURCE_WORDS[sourceState(row.source_provenance)];
  const amount = row.recorded_amount.disposition === "SHOWN" ? row.recorded_amount.amount : null;
  const change = CHANGE_WORDS[row.change_from_prior] ?? null;
  return (
    <li
      className="consequence-history__row"
      data-history-row={row.consequence_revision_id}
      data-history-at-cutoff={row.at_cutoff}
      data-history-amount={row.recorded_amount.disposition}
      data-history-price={row.price.state}
    >
      <p>
        <strong>
          Finding for {formatInstant(row.window.from)} to {formatInstant(row.window.to)}
        </strong>
        {row.finding_revision_no !== null ? `, finding version ${row.finding_revision_no}` : ""}. Fuel cost version{" "}
        {row.revision_no}, recorded {formatInstant(row.recorded_at)}.
      </p>
      <p>
        <span className={current ? "badge badge--provenance" : "badge badge--neutral"} data-history-badge={current ? "latest" : "earlier"}>
          {current ? "Latest at this moment" : "Earlier version"}
        </span>{" "}
        {change}
      </p>
      <FactList>
        <Fact term="Diesel price">
          {priceText(row)}
          {row.price.price_revision_id !== null && row.price.state === "LINKED" ? (
            <>
              {" · "}
              <Link to={links.assumptions({ revisionId: row.price.price_revision_id })} data-history-price-link>
                The price version used
              </Link>
            </>
          ) : null}
        </Fact>
        <Fact term="Recorded amount">
          {amount ? (
            <span data-history-recorded-amount>
              <strong>
                {amount.low} to {amount.high} {amount.currency}
              </strong>
              . {row.recorded_amount.label}. Not a current cost.
            </span>
          ) : (
            amountWhy(row)
          )}
        </Fact>
        <Fact term="Source">
          <span data-history-source={sourceState(row.source_provenance)}>
            {source.label}. {source.statement}
          </span>
        </Fact>
      </FactList>
      <p>
        <Link to={links.consequence(row.finding_id, row.finding_revision_id, row.consequence_revision_id)} data-history-open>
          Open this fuel cost version
        </Link>
        {" · "}
        <Link to={links.finding(row.finding_id, row.finding_revision_id)} data-history-finding>
          Open the finding
        </Link>
      </p>
      <Disclosure summary="How this was worked out" name={`history-${row.consequence_revision_id}`}>
        <p>
          This version is kept exactly as it was recorded. Its price is the one its own record names, not today's
          price. {current
            ? "It is the latest version recorded for the latest version of its finding at this moment."
            : "A later version of the same finding, or of its fuel cost, had been recorded by this moment."}
        </p>
        <Ref label="Finding" value={row.finding_id} />
        <Ref label="Finding version" value={row.finding_revision_id} />
        <Ref label="Fuel cost version" value={row.consequence_revision_id} />
        <Ref label="Price version" value={row.price.price_revision_id} />
        <Ref label="Recorded at" value={row.recorded_at} />
      </Disclosure>
    </li>
  );
}

/** The panel for one loaded page; refusals and loading are the caller's. */
export function ConsequenceHistoryPanel({
  body,
  siteName,
  links,
  historyLimit = null,
}: {
  body: ConsequenceHistoryBody;
  siteName: string;
  links: FinancialsLinks;
  historyLimit?: number | null;
}) {
  const cutoff = body.cutoff.recorded_at;
  return (
    <Panel
      heading="Interpretation history"
      headingId="site-consequence-history-heading"
      description="Every fuel cost version this site had recorded at the moment below, newest first, with the price each one used. Earlier versions are kept for the record."
    >
      <div data-consequence-history="loaded" data-history-cutoff={cutoff} data-history-selected-by={body.cutoff.selected_by}>
        <p className="notice">
          {siteName}, as recorded at {formatInstant(cutoff)}. These are recorded amounts for the record only; no amount
          here is a current cost, and none is added up.
        </p>
        {!body.source_gate.open ? (
          <p className="notice" data-history-source-closed>
            This site's source is closed, so every version is listed without an amount.
          </p>
        ) : null}
        {body.rows.length === 0 ? (
          <p data-consequence-history-empty>
            {body.page.is_first
              ? "No fuel cost version had been recorded for this site at this moment."
              : "No further versions."}
          </p>
        ) : (
          <ol className="consequence-history">
            {body.rows.map((row) => (
              <Row key={row.consequence_revision_id} row={row} links={links} />
            ))}
          </ol>
        )}
        <p className="muted">
          {body.page.is_first ? null : (
            <>
              <Link to={links.assumptions({ recordedAt: cutoff, historyLimit })} data-history-first-page>
                Back to the newest versions
              </Link>
              {body.next_cursor !== null ? " · " : null}
            </>
          )}
          {body.next_cursor !== null ? (
            <Link to={links.assumptions({ recordedAt: cutoff, historyAfter: body.next_cursor, historyLimit })} data-history-next>
              Show earlier versions
            </Link>
          ) : null}
        </p>
      </div>
    </Panel>
  );
}

export function ConsequenceHistoryRefused({ read }: { read: Exclude<ConsequenceHistoryResult, { status: "loaded" }> }) {
  const words: Record<typeof read.status, string> = {
    not_found: "That list position is not one this list gave out. Nothing else is shown in its place.",
    unauthenticated: "Sign in to read this site's fuel cost versions.",
    forbidden: "Your account has no access to this site.",
    closed: "This site's source is not released.",
    unavailable: "The fuel cost versions could not be read, so nothing is known about them right now. This is not an empty history.",
    basis_changed: "The recorded versions changed while you were reading. The list is starting again from the newest.",
  };
  return (
    <Panel heading="Interpretation history" headingId="site-consequence-history-heading">
      <p data-consequence-history={read.status}>{words[read.status]}</p>
    </Panel>
  );
}
