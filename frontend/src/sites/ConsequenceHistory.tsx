import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable, Disclosure, ExactReferences, Panel, ProductStatus, readResultWords, type ProductWords } from "../ui";
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

/** W1-F3 review M7: an empty first page says so in its one state line, never "every amount here". */
function emptyWords(pricesOnly: boolean): ProductWords {
  return {
    label: "No fuel cost version recorded",
    sentence: pricesOnly
      ? "No fuel cost version recorded by this moment; the price versions below are prices only."
      : "No fuel cost version had been recorded for this site at this moment.",
    tone: "neutral",
    code: "HISTORICAL",
    unrecognised: false,
  };
}

/**
 * post-W6 W1-b Q23 cap fallback (pre-flight ruling 7: "improve wrap, paging or internal scroll"): the version table
 * sits in one labelled, keyboard-focusable vertical scroll region so the closed Interpretation history stays inside
 * 800 px at 1440 and 1400 px at 390 even when stored price and amount words are long. Nothing is hidden or truncated;
 * the cue shows only when the rows overflow the region. Same pattern as the Finding Revision history (caps2 ruling 3).
 */
function VersionsScroll({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [overflows, setOverflows] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (el === null) return;
    const measure = () => setOverflows(el.scrollHeight > el.clientHeight + 1);
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    for (const child of Array.from(el.children)) observer.observe(child);
    el.addEventListener("toggle", measure, true);
    return () => {
      observer.disconnect();
      el.removeEventListener("toggle", measure, true);
    };
  }, []);
  return (
    <>
      <p className="consequence-history__scroll-cue" data-consequence-history-scroll-cue hidden={!overflows}>
        Scroll versions to see every row
      </p>
      <div
        ref={ref}
        className="consequence-history__versions"
        role="region"
        aria-label="Fuel cost versions"
        tabIndex={0}
        data-consequence-history-scroll
      >
        {children}
      </div>
    </>
  );
}

function Row({ row, links, pinnedCutoff }: { row: ConsequenceHistoryRow; links: FinancialsLinks; pinnedCutoff?: string }) {
  const current = row.at_cutoff === "CURRENT_AT_CUTOFF";
  const source = SOURCE_WORDS[sourceState(row.source_provenance)];
  const amount = row.recorded_amount.disposition === "SHOWN" ? row.recorded_amount.amount : null;
  const change = CHANGE_WORDS[row.change_from_prior] ?? null;
  // W1-F3 phase D: one table row per version, as the mock's Interpretation history table. post-W6 W1-b Q23 / R200:
  // the row is compact (Version, Fuel price, Recorded amount, Status); the source and the full version sit in the
  // row's closed "Show this version" disclosure, still in the document and keyboard reachable.
  return (
    <tr
      className="consequence-history__row"
      data-history-row={row.consequence_revision_id}
      data-history-at-cutoff={row.at_cutoff}
      data-history-amount={row.recorded_amount.disposition}
      data-history-price={row.price.state}
    >
      <td>
        <strong>Fuel cost version {row.revision_no}</strong>
        {row.finding_revision_no !== null ? (
          <small className="consequence-history__line">Finding version {row.finding_revision_no}</small>
        ) : null}
        <Disclosure name={`history-version-${row.consequence_revision_id}`} summary="Show this version">
          <p data-history-version-detail>
            Finding for {formatInstant(row.window.from)} to {formatInstant(row.window.to)}
            {row.finding_revision_no !== null ? `, finding version ${row.finding_revision_no}` : ""}. Fuel cost version{" "}
            {row.revision_no}, recorded {formatInstant(row.recorded_at)}.
          </p>
          <p>
            <span data-history-source={sourceState(row.source_provenance)}>
              {source.label}. {source.statement}
            </span>
          </p>
          <p>
            <Link to={links.consequence(row.finding_id, row.finding_revision_id, row.consequence_revision_id)} data-history-open>
              Open this fuel cost version
            </Link>
            {" · "}
            <Link to={links.finding(row.finding_id, row.finding_revision_id)} data-history-finding>
              Open the finding
            </Link>
            {row.price.price_revision_id !== null && row.price.state === "LINKED" ? (
              <>
                {" · "}
                <Link to={links.assumptions({ revisionId: row.price.price_revision_id, recordedAt: pinnedCutoff })} data-history-price-link>
                  The price version used
                </Link>
              </>
            ) : null}
          </p>
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
        </Disclosure>
      </td>
      <td>{priceText(row)}</td>
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
        <span className={current ? "badge badge--provenance" : "badge badge--neutral"} data-history-badge={current ? "latest" : "earlier"}>
          {current ? "Latest at this moment" : "Earlier version"}
        </span>
        {change ? <small className="consequence-history__line">{change}</small> : null}
      </td>
    </tr>
  );
}

/**
 * post-W6 W1-b Q23 (pre-flight ruling 7): the URL-safe prior-cursor stack, one repeated `history_back` value per
 * newer page, oldest first; `0` is the first page and may only sit at the bottom. A malformed or out-of-range stack
 * is rejected (null), never repaired into a guessed cursor; the caller then offers only "Back to newest".
 */
export const HISTORY_BACK_MAX = 100;
const CURSOR_TOKEN = /^[A-Za-z0-9_-]{1,4096}$/;
export function parseHistoryBack(values: string[], currentAfter: string | null): string[] | null {
  if (values.length === 0) return [];
  if (currentAfter === null || values.length > HISTORY_BACK_MAX) return null;
  const ok = values.every((v, i) => (v === "0" ? i === 0 : CURSOR_TOKEN.test(v)));
  return ok ? values : null;
}

/** The panel for one loaded page; refusals and loading are the caller's. */
export function ConsequenceHistoryPanel({
  body,
  siteName,
  links,
  historyLimit = null,
  historyAfter = null,
  historyBack = [],
  children,
}: {
  body: ConsequenceHistoryBody;
  siteName: string;
  links: FinancialsLinks;
  historyLimit?: number | null;
  /** post-W6 W1-b Q23: the current page's cursor (null on the first page). */
  historyAfter?: string | null;
  /** post-W6 W1-b Q23: the parsed prior-cursor stack; null when the address's stack was rejected. */
  historyBack?: string[] | null;
  /** W1-F3: the price versions recorded at the same moment, inside this panel. */
  children?: ReactNode;
}) {
  const cutoff = body.cutoff.recorded_at;
  const empty = body.rows.length === 0 && body.page.is_first;
  const pricesOnly = empty && Boolean(children);
  return (
    <Panel
      heading="Interpretation history"
      headingId="site-consequence-history-heading"
      description="Every fuel cost version this site had recorded at the moment below, newest first, with the price each one used. Earlier versions are kept for the record."
    >
      <div data-consequence-history="loaded" data-history-cutoff={cutoff} data-history-selected-by={body.cutoff.selected_by}>
        <div
          className="v69-state-line"
          data-history-state={empty ? "empty" : "recorded"}
          data-consequence-history-empty={empty ? "" : undefined}
          data-consequence-history-prices-only={pricesOnly ? "" : undefined}
        >
          <ProductStatus
            inline
            words={empty ? emptyWords(pricesOnly) : RECORDED_WORDS}
            scope={`${siteName}, every fuel cost version recorded by this moment`}
            asOf={cutoff}
          />
        </div>
        {!body.source_gate.open ? (
          <p className="notice" data-history-source-closed>
            This site's source is closed, so every version is listed without an amount.
          </p>
        ) : null}
        {body.rows.length === 0 && !body.page.is_first ? (
          <p className="v69-gap-line" data-consequence-history-empty>
            No further versions.
          </p>
        ) : null}
        {body.rows.length === 0 ? (
          null
        ) : (
          <VersionsScroll>
          <DataTable>
            <thead>
              <tr>
                <th scope="col">Version</th>
                <th scope="col">Fuel price</th>
                <th scope="col">Recorded amount</th>
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
          </VersionsScroll>
        )}
        {body.rows.length === 0 ? null : (
          <p className="v69-chart-note" data-history-kept-note>
            Each version is kept exactly as it was recorded. Its price is the one its own record names, not today&apos;s
            price. &quot;Latest at this moment&quot;: it is the latest version recorded for the latest version of its finding
            at this moment. &quot;Earlier version&quot;: a later version of the same finding, or of its fuel cost, had been
            recorded by this moment.
          </p>
        )}
        <HistoryPager body={body} links={links} historyLimit={historyLimit} historyAfter={historyAfter} historyBack={historyBack} />
      </div>
      {children}
    </Panel>
  );
}

/**
 * post-W6 W1-b Q23 / R200: "Previous versions" (older) follows the server cursor and pushes the current one onto the
 * stack; "Next versions" (newer) pops one prior cursor. A page reached without a usable stack offers "Back to
 * newest", which clears cursor and stack. Every link keeps the exact cutoff and page size.
 */
function HistoryPager({
  body,
  links,
  historyLimit,
  historyAfter,
  historyBack,
}: {
  body: ConsequenceHistoryBody;
  links: FinancialsLinks;
  historyLimit: number | null;
  historyAfter: string | null;
  historyBack: string[] | null;
}) {
  const cutoff = body.cutoff.recorded_at;
  const stack = historyBack ?? [];
  const older =
    body.next_cursor === null
      ? null
      : links.assumptions({
          recordedAt: cutoff,
          historyAfter: body.next_cursor,
          historyLimit,
          historyBack: [...stack, historyAfter ?? "0"],
        });
  let newer: { href: string; label: string; attr: string } | null = null;
  if (historyBack !== null && stack.length > 0) {
    const prior = stack[stack.length - 1];
    newer = {
      href: links.assumptions({
        recordedAt: cutoff,
        historyAfter: prior === "0" ? null : prior,
        historyLimit,
        historyBack: stack.slice(0, -1),
      }),
      label: "Next versions",
      attr: "next",
    };
  } else if (!body.page.is_first || historyAfter !== null) {
    newer = { href: links.assumptions({ recordedAt: cutoff, historyLimit }), label: "Back to newest", attr: "newest" };
  }
  if (older === null && newer === null) return null;
  return (
    <nav className="muted consequence-history__pager" aria-label="Interpretation history pages" data-history-pager>
      {newer === null ? null : (
        <Link to={newer.href} data-history-newer={newer.attr} data-history-first-page={newer.attr === "newest" ? "" : undefined}>
          {newer.label}
        </Link>
      )}
      {newer !== null && older !== null ? " · " : null}
      {older === null ? null : (
        <Link to={older} data-history-next>
          Previous versions
        </Link>
      )}
    </nav>
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
