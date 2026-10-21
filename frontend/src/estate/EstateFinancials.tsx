/**
 * W3-02 commit 4: the estate Financials root (v6.9 `globalfinancials`, `I-estate-money-root`) read from
 * `GET /api/estate/financials` (`estate-financials-1`). Copy and layout follow `.agent/W3-02-build-spec.md`: the mock
 * ledger, "Refusals and UI states", closure 1 "Money row and comparison contract" (display) and "Mock copy,
 * navigation and measured layout", closure 2 Q19, closure 3 Q19/C1, closure 4 wire/links, closure 5 S13 (the two
 * panel titles) and the commit-3 review carries L3 (differing-value category copy), L4 (`PARTITION_INELIGIBLE` in
 * plain words) and L5 (the prior mini-grid amount is unavailable in a pending/stale selection). Every value is a
 * server field: the page groups, sums and scores nothing, builds no Site route and shows no estate total.
 */
import { Fragment, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { DataTable, Disclosure, Notice, PageHeader, Panel, StatusBar } from "../ui";
import type { EstateEnvelope } from "./estateClient";
import {
  createEstateFinancialsClient,
  type EstateFinancialsBody,
  type EstateFinancialsClient,
  type EvidenceResult,
  type FinancialGroup,
  type FinancialRow,
} from "./estateEvidenceMoneyClient";
import {
  ELIGIBILITY_WORDS,
  GROUP_STATE_WORDS,
  NOT_DISPLAYABLE,
  categoryLabel,
  diagnosticText,
  moneyText,
  moneyWindowText,
  quantityText,
  reasonText,
} from "./estateFinancialsWords";
import { EstateDateBar, EstateRefusal, Pager, estateHref, queryFromParams, utcInstant } from "./estateShared";
import "./estateEvidence.css";
import "./estateFinancials.css";

export const ESTATE_FINANCIALS_PATH = "/financials";

export const FINANCIALS_TITLE = "Portfolio financials";
export const FINANCIALS_EYEBROW = "Financials";
export const FINANCIALS_SUBTITLE = "Estate consequences with source-site ownership and bounded interpretation";
export const STATUS_CHIP = "Site-owned consequences";
export const STATUS_TEXT = "Values grouped by basis and period; no financial assessment";
export const REGISTER_PANEL = "Consequence register";
export const AGGREGATION_PANEL = "Aggregation rule";
export const REGISTER_SUBTITLE = "No independent repricing or technical re-derivation";
export const FINANCIALS_NOTICE =
  "These values are not an additive profit or savings total. Categories, time periods, uncertainty and overlapping technical bases differ.";
/** The mock's exact `Aggregation rule` prose (`frontend/mockups/v69/screens.js` `globalfinancials`). */
export const AGGREGATION_PROSE =
  "Aggregate distinct eligible consequence-line IDs by category, currency and compatible window. Reuse the exact site consequence revision; preserve exclusions and assumption references.";

export const REGISTER_COLUMNS = ["Site", "Category", "Window / quantity", "Value", "Basis / limit", "Source"] as const;

export const NO_ACCESSIBLE_SITES = "No accessible Sites";
export const NO_CONSEQUENCE_LINES = "No consequence lines for this window";
export const STILL_ASSESSED = "Some Sites are still being assessed";
export const BASIS_UNRESOLVED = "Source or basis is unresolved";
export const NO_COMPARABLE_TOTAL = "Comparable total unavailable for this selection";
/** Commit-3 L5: a pending/stale mini-grid selection has no selected prior head; this never says none exists. */
export const PRIOR_MINI_GRID_UNAVAILABLE = "The prior mini-grid amount is unavailable in this selection";
export const WINDOW_QUANTITY_UNKNOWN = "Window or quantity not established";
export const QUANTITY_UNKNOWN = "Quantity not established";
export const LIMIT_NOT_RECORDED = "Limit not recorded";
export const SOURCE_UNAVAILABLE = "Source detail unavailable";

export function historicalAsOf(instant: string): string {
  return `Historical as of ${utcInstant(instant)}`;
}

function Chip({ tone, text, data }: { tone: string; text: string; data: Record<string, string> }) {
  return (
    <span className={`estate-chip estate-tone--${tone}`} {...data}>
      {text}
    </span>
  );
}

/** The stored line value for display: W1 outward to its minor unit, EV half even (its Site page rule). */
function lineMoney(row: FinancialRow, amount: FinancialRow["amount"] | undefined): string | null {
  return moneyText(amount, row.domain === "ev_charging" ? "even2" : "outward");
}

function siteLabel(row: Pick<FinancialRow, "site_name" | "site_code">): string {
  return row.site_name.trim() !== "" ? row.site_name : row.site_code;
}

function ValueCell({ row, asOf }: { row: FinancialRow; asOf: string }) {
  if (row.eligibility === "ELIGIBLE") {
    const text = lineMoney(row, row.amount);
    return <span data-estate-money-value={text === null ? "not-displayable" : "eligible"}>{text ?? NOT_DISPLAYABLE}</span>;
  }
  const word = ELIGIBILITY_WORDS[row.eligibility] ?? ELIGIBILITY_WORDS.UNKNOWN;
  const text = row.eligibility === "HISTORICAL" ? historicalAsOf(asOf) : word.text;
  return <Chip tone={word.tone} text={text} data={{ "data-estate-eligibility": row.eligibility }} />;
}

function ids(values: string[]): string {
  return values.length > 0 ? values.join(", ") : "None recorded";
}

function BasisDetails({ row }: { row: FinancialRow }) {
  const pinned = row.eligibility === "ELIGIBLE" ? null : lineMoney(row, row.disclosure.pinned_amount);
  return (
    <Disclosure summary="Basis details" name="estate-financials-row" variant="inline">
      <dl className="estate-evidence-facts">
        <dt>Site</dt>
        <dd>{row.site_name.trim() !== "" ? `${row.site_name} · ${row.site_code}` : row.site_code}</dd>
        <dt>Assumption references</dt>
        <dd>{ids(row.assumption_revision_ids)}</dd>
        <dt>Assumption fingerprint</dt>
        <dd>{row.assumption_fingerprint ?? "Not comparable"}</dd>
        <dt>Consequence reference</dt>
        <dd>{row.consequence_revision_id}</dd>
        <dt>Line reference</dt>
        <dd>{row.line_key}</dd>
        <dt>Technical inputs</dt>
        <dd>{ids(row.technical_interval_ids)}</dd>
        <dt>Evidence references</dt>
        <dd>{ids(row.basis_evidence_ids)}</dd>
        <dt>Overlap group</dt>
        <dd>{row.overlap_group ?? "None recorded"}</dd>
        {row.reason_codes.length > 0 ? (
          <>
            <dt>Reasons</dt>
            <dd>{reasonText(row.reason_codes)}</dd>
          </>
        ) : null}
        {pinned !== null ? (
          <>
            <dt>Stored value, not current</dt>
            <dd>{pinned}</dd>
          </>
        ) : null}
      </dl>
    </Disclosure>
  );
}

/** The ledger's Source cell: cold rows open Site evidence (the mock's temperature link), others the Site bridge. */
function SourceCell({ row }: { row: FinancialRow }) {
  const evidenceFirst = row.domain === "cold_chain";
  const [href, label] =
    evidenceFirst && row.links.evidence !== null
      ? [row.links.evidence, "Site evidence →"]
      : row.links.bridge !== null
        ? [row.links.bridge, "Site bridge →"]
        : row.links.evidence !== null
          ? [row.links.evidence, "Site evidence →"]
          : [null, SOURCE_UNAVAILABLE];
  if (href === null) return <span data-estate-source="unavailable">{label}</span>;
  return (
    <>
      <Link className="estate-cell__primary" to={href} data-estate-source-link>
        {label}
      </Link>
      {row.links.current_view_label !== null ? (
        <span className="estate-cell__secondary" data-estate-current-view>
          {row.links.current_view_label}
        </span>
      ) : null}
    </>
  );
}

function RegisterRow({ row, asOf }: { row: FinancialRow; asOf: string }) {
  const window = moneyWindowText(row.window_start, row.window_end);
  const quantity = quantityText(row.quantity);
  return (
    <tr data-estate-money-row={row.line_key}>
      <td>
        <Link className="estate-cell__primary" to={row.links.site} data-estate-site-link>
          {siteLabel(row)}
        </Link>
      </td>
      <td>{categoryLabel(row.category)}</td>
      <td data-estate-money-window>
        {window === null && quantity === null ? (
          WINDOW_QUANTITY_UNKNOWN
        ) : (
          <>
            {window !== null ? <span className="estate-cell__primary">{window}</span> : null}
            <span className={window === null ? "estate-cell__primary" : "estate-cell__secondary"}>{quantity ?? QUANTITY_UNKNOWN}</span>
          </>
        )}
      </td>
      <td>
        <ValueCell row={row} asOf={asOf} />
      </td>
      <td>
        <span className="estate-cell__primary">{row.limit ?? LIMIT_NOT_RECORDED}</span>
        <BasisDetails row={row} />
      </td>
      <td>
        <SourceCell row={row} />
      </td>
    </tr>
  );
}

function RegisterTable({ body }: { body: EstateFinancialsBody }) {
  const asOf = body.summary.as_of ?? body.window.known_at;
  return (
    <div className="estate-evidence-table estate-financials-table">
      <DataTable labelledBy="estate-financials-register-heading">
        <colgroup>
          {[11, 21, 20, 10, 24, 14].map((width, index) => (
            <col key={index} style={{ width: `${width}%` }} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {REGISTER_COLUMNS.map((h) => (
              <th key={h} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.rows.map((row) => (
            <RegisterRow key={row.line_key} row={row} asOf={asOf} />
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

/** The state table's register notes (outside the table, headers kept). */
function RegisterNotes({ body }: { body: EstateFinancialsBody }) {
  const notes: [string, string][] = [];
  if (body.status === "EMPTY_SCOPE") notes.push(["empty-scope", NO_ACCESSIBLE_SITES]);
  else if (body.total_count === 0) notes.push(["no-selection", NO_CONSEQUENCE_LINES]);
  if (body.status !== "EMPTY_SCOPE" && body.coverage.state !== "COMPLETE") notes.push(["partial", STILL_ASSESSED]);
  if (body.groups.some((g) => g.category === "CANDIDATE_OPERATING_COST_EXPOSURE" && g.state === "UNKNOWN_COVERAGE")) {
    notes.push(["prior-mini-grid", PRIOR_MINI_GRID_UNAVAILABLE]);
  }
  if (body.rows.some((r) => r.eligibility === "CONFLICT")) notes.push(["conflict", BASIS_UNRESOLVED]);
  if (body.status === "HISTORICAL") notes.push(["historical", historicalAsOf(body.summary.as_of ?? body.window.known_at)]);
  if (notes.length === 0) return null;
  return (
    <p className="estate-evidence-note">
      {notes.map(([key, text], index) => (
        <Fragment key={key}>
          {index > 0 ? " · " : null}
          <span data-estate-note={key}>{text}</span>
        </Fragment>
      ))}
    </p>
  );
}

function groupLines(n: number): string {
  return n === 1 ? "1 line" : `${n} lines`;
}

function GroupResult({ group, body }: { group: FinancialGroup; body: EstateFinancialsBody }) {
  const state = GROUP_STATE_WORDS[group.state] ?? GROUP_STATE_WORDS.INELIGIBLE;
  const amount = group.state === "COMPARABLE" ? moneyText(group.amount, "outward") : null;
  const excluded = group.group_key === null ? [] : body.exclusions.filter((e) => e.group_key === group.group_key);
  const byKey = new Map(body.rows.map((r) => [r.line_key, r]));
  const parts = [categoryLabel(group.category)];
  if (group.state === "COMPARABLE") parts.push(amount ?? NOT_DISPLAYABLE);
  if (group.line_keys.length > 0) parts.push(groupLines(group.line_keys.length));
  return (
    <li className="estate-financials-result" data-estate-group={group.group_key ?? `${group.category}|${group.state}`}>
      <Chip tone={state.tone} text={state.text} data={{ "data-estate-group-state": group.state }} />
      <span className="estate-financials-result__text">{parts.join(" · ")}</span>
      {group.reason_codes.length > 0 ? (
        <span className="estate-financials-result__reasons" data-estate-group-reasons>
          {reasonText(group.reason_codes)}
        </span>
      ) : null}
      {excluded.length > 0 ? (
        <Disclosure summary={`Excluded: ${groupLines(excluded.length)}`} name="estate-financials-exclusions" variant="inline">
          <ul className="estate-financials-exclusions">
            {excluded.map((e) => {
              const row = byKey.get(e.line_key);
              return (
                <li key={e.line_key} data-estate-exclusion={e.line_key}>
                  {row === undefined ? e.line_key : `${siteLabel(row)} · ${categoryLabel(row.category)}`}
                  {": "}
                  {reasonText(e.reason_codes)}
                </li>
              );
            })}
          </ul>
        </Disclosure>
      ) : null}
    </li>
  );
}

/**
 * Commit-4 ruling c4: the panel keeps the mock's title and prose; every grouping result sits behind one closed
 * summary row (`Results (N) · No comparable total`), so the default panel stays within its measured cap. Opened, it
 * shows all groups and diagnostics in wire order, unclipped, plus the no-comparable message when it applies.
 */
export function aggregationSummary(body: EstateFinancialsBody): { visible: string; spoken: string } {
  const count = body.groups.length + body.diagnostics.length;
  const comparable = body.groups.filter((g) => g.state === "COMPARABLE").length;
  const totals = comparable === 0 ? "No comparable total" : comparable === 1 ? "1 comparable total" : `${comparable} comparable totals`;
  const spokenTotals = comparable === 0 ? `${NO_COMPARABLE_TOTAL}.` : `${totals} by basis; no estate total.`;
  const results = count === 1 ? "1 grouping result" : `${count} grouping results`;
  return { visible: `Results (${count}) · ${totals}`, spoken: `${results}. ${spokenTotals}` };
}

function AggregationResults({ body }: { body: EstateFinancialsBody }) {
  const comparable = body.groups.some((g) => g.state === "COMPARABLE");
  const summary = aggregationSummary(body);
  return (
    <div className="estate-financials-summary" data-estate-aggregation-summary>
      <Disclosure
        summary={
          <>
            <span data-estate-summary-text>
              {summary.visible}
            </span>
            <span className="visually-hidden"> {summary.spoken}</span>
          </>
        }
        name="estate-financials-results"
        variant="tech"
      >
        {body.groups.length > 0 || body.diagnostics.length > 0 ? (
          <ul className="estate-financials-results" aria-label="Grouping results" data-estate-results>
            {body.groups.map((group, index) => (
              <GroupResult key={group.group_key ?? `${group.category}|${index}`} group={group} body={body} />
            ))}
            {body.diagnostics.map((d) => (
              <li key={`${d.category}|${d.code}`} className="estate-financials-result" data-estate-diagnostic={d.code}>
                <Chip tone="gray" text="Different values" data={{ "data-estate-diagnostic-chip": d.code }} />
                <span className="estate-financials-result__text">{diagnosticText(d.category, d.code, d.line_keys.length)}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {comparable ? null : (
          <p className="estate-evidence-note estate-financials-no-total" data-estate-note="no-comparable">
            {NO_COMPARABLE_TOTAL}
          </p>
        )}
      </Disclosure>
    </div>
  );
}

/** The shared date bar reads only `status` and `window`; the new roots add `EMPTY_SCOPE`, which it ignores. */
function barBody(body: EstateFinancialsBody | null): EstateEnvelope | null {
  return body === null ? null : (body as unknown as EstateEnvelope);
}

export function EstateFinancialsPage({ client }: { client?: EstateFinancialsClient }) {
  const reads = useMemo(() => client ?? createEstateFinancialsClient(), [client]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = queryFromParams(params);
  const key = params.toString();
  const [result, setResult] = useState<{ key: string; read: EvidenceResult<EstateFinancialsBody> } | null>(null);

  useEffect(() => {
    let live = true;
    void reads.financials(query).then((read) => {
      if (live) setResult({ key, read });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);

  const firstPage = estateHref(ESTATE_FINANCIALS_PATH, query);
  const read = result?.key === key ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  const next =
    body === null || body.next_cursor === null ? null : estateHref(ESTATE_FINANCIALS_PATH, query, { cursor: body.next_cursor });

  return (
    <div className="estate-page estate-evidence estate-financials" data-estate-root="financials">
      <PageHeader eyebrow={FINANCIALS_EYEBROW} title={FINANCIALS_TITLE} subtitle={FINANCIALS_SUBTITLE} />
      <EstateDateBar
        key={`${query.from}|${query.to}|${query.known_at ?? ""}`}
        query={query}
        body={barBody(body)}
        onApply={(nextQuery) => navigate(estateHref(ESTATE_FINANCIALS_PATH, nextQuery))}
      />
      {read === null ? (
        <p className="estate-loading" data-estate-loading>
          Loading financials across the estate.
        </p>
      ) : read.status === "refused" ? (
        <EstateRefusal code={read.code} copy={read.copy} firstPage={firstPage} />
      ) : (
        <>
          <StatusBar label="Financial status" data={{ "data-estate-status": "" }}>
            <Chip tone="blue" text={STATUS_CHIP} data={{ "data-estate-status-chip": "" }} /> {STATUS_TEXT}
          </StatusBar>
          <Panel heading={REGISTER_PANEL} headingId="estate-financials-register-heading" description={REGISTER_SUBTITLE}>
            <RegisterTable body={read.value} />
            <RegisterNotes body={read.value} />
            <Pager next={next} first={firstPage} paged={query.cursor !== null} />
          </Panel>
          <Notice tone="amber" data={{ "data-estate-notice": "" }}>
            {FINANCIALS_NOTICE}
          </Notice>
          <Panel heading={AGGREGATION_PANEL} headingId="estate-financials-aggregation-heading" className="estate-financials__aggregation">
            <p className="prose estate-financials-prose estate-financials__aggregation-prose">{AGGREGATION_PROSE}</p>
            <AggregationResults body={read.value} />
          </Panel>
        </>
      )}
    </div>
  );
}
