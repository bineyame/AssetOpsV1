import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, ExactReferences, Panel, ProductStatus, readResultWords, type ProductWords } from "../ui";
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

/**
 * W1-UX-02: the state line of the Interpretation history. Every version here is a recorded one, shown as it
 * was; the line never says or implies a current amount (`D-2026-10-16-s408` Q3).
 */
const RECORDED_WORDS: ProductWords = {
  label: "Recorded versions, kept for the record",
  sentence: "Every amount here is shown as it was recorded. None of them is a current cost, and none is added up.",
  tone: "neutral",
  code: "HISTORICAL",
  unrecognised: false,
};

function Row({ row, links, pinnedCutoff }: { row: ConsequenceHistoryRow; links: FinancialsLinks; pinnedCutoff?: string }) {
  const current = row.at_cutoff === "CURRENT_AT_CUTOFF";
  const source = SOURCE_WORDS[sourceState(row.source_provenance)];
  const amount = row.recorded_amount.disposition === "SHOWN" ? row.recorded_amount.amount : null;
  const change = CHANGE_WORDS[row.change_from_prior] ?? null;
  // W1-F3 phase D: one table row per version, as the mock's Interpretation history table.
  return (
    <tr
      className="consequence-history__row"
      data-history-row={row.consequence_revision_id}
      data-history-at-cutoff={row.at_cutoff}
      data-history-amount={row.recorded_amount.disposition}
      data-history-price={row.price.state}
    >
      <td>
        <strong>
          Finding for {formatInstant(row.window.from)} to {formatInstant(row.window.to)}
        </strong>
        {row.finding_revision_no !== null ? `, finding version ${row.finding_revision_no}` : ""}.
        <small className="consequence-history__line">
          Fuel cost version {row.revision_no}, recorded {formatInstant(row.recorded_at)}.
        </small>
        <small className="consequence-history__line">
          <Link to={links.consequence(row.finding_id, row.finding_revision_id, row.consequence_revision_id)} data-history-open>
            Open this fuel cost version
          </Link>
          {" · "}
          <Link to={links.finding(row.finding_id, row.finding_revision_id)} data-history-finding>
            Open the finding
          </Link>
        </small>
        <ExactReferences
          name={`history-${row.consequence_revision_id}`}
          references={[
            { label: "Finding reference", value: row.finding_id },
            { label: "Finding version reference", value: row.finding_revision_id },
            { label: "Fuel cost version reference", value: row.consequence_revision_id },
            ...(row.price.price_revision_id !== null ? [{ label: "Price version reference", value: row.price.price_revision_id }] : []),
            { label: "Recorded at", value: row.recorded_at },
          ]}
        />
      </td>
      <td>
        {priceText(row)}
        {row.price.price_revision_id !== null && row.price.state === "LINKED" ? (
          <>
            {" · "}
            <Link to={links.assumptions({ revisionId: row.price.price_revision_id, recordedAt: pinnedCutoff })} data-history-price-link>
              The price version used
            </Link>
          </>
        ) : null}
      </td>
      <td>
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
      </td>
      <td>
        <span data-history-source={sourceState(row.source_provenance)}>
          {source.label}. {source.statement}
        </span>
      </td>
      <td>
        <span className={current ? "badge badge--provenance" : "badge badge--neutral"} data-history-badge={current ? "latest" : "earlier"}>
          {current ? "Latest at this moment" : "Earlier version"}
        </span>
        {change ? <small className="consequence-history__line">{change}</small> : null}
      </td>
    </tr>
  );
}

/** The panel for one loaded page; refusals and loading are the caller's. */
export function ConsequenceHistoryPanel({
  body,
  siteName,
  links,
  historyLimit = null,
  children,
}: {
  body: ConsequenceHistoryBody;
  siteName: string;
  links: FinancialsLinks;
  historyLimit?: number | null;
  /** W1-F3: the price versions recorded at the same moment, inside this panel. */
  children?: ReactNode;
}) {
  const cutoff = body.cutoff.recorded_at;
  return (
    <Panel
      heading="Interpretation history"
      headingId="site-consequence-history-heading"
      description="Every fuel cost version this site had recorded at the moment below, newest first, with the price each one used. Earlier versions are kept for the record."
    >
      <div data-consequence-history="loaded" data-history-cutoff={cutoff} data-history-selected-by={body.cutoff.selected_by}>
        <div className="v69-state-line" data-history-state="recorded">
          <ProductStatus
            inline
            words={RECORDED_WORDS}
            scope={`${siteName}, every fuel cost version recorded by this moment`}
            asOf={cutoff}
          />
        </div>
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
        ) : null}
        {body.rows.length === 0 && body.page.is_first && children ? (
          <p className="v69-gap-line" data-consequence-history-prices-only>
            The price versions below are prices only; no fuel cost was worked out from them by this moment.
          </p>
        ) : null}
        {body.rows.length === 0 ? (
          null
        ) : (
          <DataTable>
            <thead>
              <tr>
                <th scope="col">Version</th>
                <th scope="col">Diesel price</th>
                <th scope="col">Recorded amount</th>
                <th scope="col">Source</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
            {body.rows.map((row) => (
              <Row
                key={row.consequence_revision_id}
                row={row}
                links={links}
                // S4-08 review L1: an explicitly selected moment carries into the price link; the default view stays default.
                pinnedCutoff={body.cutoff.selected_by === "RECORDED_CUTOFF" ? cutoff : undefined}
              />
            ))}
            </tbody>
          </DataTable>
        )}
        {body.rows.length === 0 ? null : (
          <p className="v69-chart-note" data-history-kept-note>
            Each version is kept exactly as it was recorded. Its price is the one its own record names, not today&apos;s
            price. &quot;Latest at this moment&quot;: it is the latest version recorded for the latest version of its finding
            at this moment. &quot;Earlier version&quot;: a later version of the same finding, or of its fuel cost, had been
            recorded by this moment.
          </p>
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
      {children}
    </Panel>
  );
}

export function ConsequenceHistoryRefused({
  read,
  children,
}: {
  read: Exclude<ConsequenceHistoryResult, { status: "loaded" }>;
  children?: ReactNode;
}) {
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
      <div data-history-state={read.status}>
        <ProductStatus words={refusedWords(read.status)} scope="This site's fuel cost versions" asOf={null}>
          <p data-consequence-history={read.status}>{words[read.status]}</p>
        </ProductStatus>
      </div>
      {children}
    </Panel>
  );
}

/** W1-UX-02: how a refused history read ended, in the shared words; a changed list is its own waiting state. */
function refusedWords(status: Exclude<ConsequenceHistoryResult, { status: "loaded" }>["status"]): ProductWords {
  switch (status) {
    case "not_found":
      return readResultWords("not-found");
    case "unavailable":
      return readResultWords("unavailable");
    case "basis_changed":
      return {
        label: "The list changed while you were reading",
        sentence: "New versions were recorded, so the list starts again from the newest. Nothing is lost.",
        tone: "waiting",
        code: status,
        unrecognised: false,
      };
    default:
      return readResultWords("refused");
  }
}
