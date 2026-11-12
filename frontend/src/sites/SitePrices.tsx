import { Fragment, type ReactNode } from "react";
import { DataTable, Panel } from "../ui";
import type { NeedBlock, PricePage, PriceRowBody } from "./pricePageClient";
import "./sitePrices.css";

/**
 * PR-2a (BL-68): the read-only Site price page body (v7.1 `price-it.html` Part B, Part C). Every word is the server's
 * (`financials/price_page.py`); this file lays them out and never decides which key can be priced.
 *
 * Seam for PR-3: `renderBelow(row)` is rendered in a full-width row directly under that price's row, before its
 * History. PR-3 passes its inline price form there (stored keys only, when `entry.enabled`). PR-2a passes nothing,
 * so the page has no form, no input and no Save.
 */
export const SITE_PRICES_TABLE_HEADING_ID = "site-prices-table-heading";
const COLUMNS = ["Price", "Current value", "Basis", "Applies from", "Set by", "Used by"] as const;

export interface SitePricesBodyProps {
  page: PricePage;
  /** The `?key=` the reader arrived with: that row is highlighted (mock `tr.focused`). */
  focusKey?: string | null;
  /** PR-3 seam: content opened inline under one price row (its form); nothing in PR-2a. */
  renderBelow?: (row: PriceRowBody) => ReactNode;
}

/**
 * The sign-in line: plain words, no error colour, no disabled Save (mock `.signin`).
 * MOCK DEVIATION (PR-2a D4): no lock icon; an inline svg outside the diagram modules is refused by the shell-overflow
 * guard, so the note carries its words only.
 */
export function PricesSignIn({ text }: { text: string }) {
  return (
    <div className="site-prices__signin" role="note" data-prices-sign-in>
      <p>
        <b>{text}</b>
      </p>
    </div>
  );
}

/** Part C: a model, data or integration item; the words are the server's, with no "Tell your contact" (default 5). */
export function PriceNeedBlock({ need }: { need: NeedBlock }) {
  return (
    <section className="site-prices__need" aria-labelledby="site-prices-need-heading" data-price-need={need.need_key}>
      <h2 id="site-prices-need-heading">{need.title}</h2>
      <p>{need.text}</p>
      <p className="site-prices__meanwhile">{need.meanwhile}</p>
    </section>
  );
}

function Small({ children }: { children: ReactNode }) {
  return <small className="site-prices__sub">{children}</small>;
}

/** One price's rows: the price row, the PR-3 slot, then its History disclosure. */
export function PriceRowGroup({ row, focused, below }: { row: PriceRowBody; focused: boolean; below?: ReactNode }) {
  const c = row.current;
  return (
    <>
      <tr
        className={focused ? "site-prices__row site-prices__row--focused" : "site-prices__row"}
        data-price-row={row.key}
        data-price-focused={focused ? "" : undefined}
        aria-current={focused ? "true" : undefined}
      >
        <th scope="row">
          <strong>{row.label}</strong>
          <Small>{row.detail}</Small>
        </th>
        <td data-price-cell="value">
          {c === null ? (
            <>
              <span className="site-prices__notset">{row.not_set_text}</span>
              {row.note === null ? null : <Small>{row.note}</Small>}
            </>
          ) : (
            <>
              <span className="site-prices__value">{c.amount_text}</span> {c.per_text}
            </>
          )}
        </td>
        <td>
          {c === null ? "—" : (
            <>
              {c.basis_text}
              {c.source_reference === null ? null : <Small>{c.source_reference}</Small>}
            </>
          )}
        </td>
        <td>
          {c === null ? "—" : (
            <>
              {c.applies_from_text}
              {c.applies_until_text === null ? null : <Small>{c.applies_until_text}</Small>}
            </>
          )}
        </td>
        <td>
          {c === null ? "—" : (
            <>
              {c.set_by_label}
              <Small>{c.recorded_text}</Small>
            </>
          )}
        </td>
        <td>
          {row.used_by.text}
          <Small>{row.used_by.detail}</Small>
        </td>
      </tr>
      {below === undefined || below === null ? null : (
        <tr className="site-prices__slot" data-price-slot={row.key}>
          <td colSpan={COLUMNS.length}>{below}</td>
        </tr>
      )}
      {row.history.length === 0 || row.history_title === null ? null : (
        <tr className="site-prices__history-row" data-price-history={row.key}>
          <td colSpan={COLUMNS.length}>
            <details className="site-prices__history">
              <summary>{row.history_title}</summary>
              <ol>
                {row.history.map((h) => (
                  <li key={h.revision_id} data-price-revision={h.revision_no}>
                    <b>{h.headline}</b>
                    {h.until_text === null ? "" : ` ${h.until_text}`}: {h.value_text}, {h.basis_text}
                    {h.reason === null ? "" : `. Reason: "${h.reason}"`}{" "}
                    <small>
                      · {h.set_by_label} · {h.recorded_text}
                      {h.replaced_text === null ? "" : ` · ${h.replaced_text}`}
                    </small>
                  </li>
                ))}
              </ol>
            </details>
          </td>
        </tr>
      )}
    </>
  );
}

export function SitePricesBody({ page, focusKey = null, renderBelow }: SitePricesBodyProps) {
  return (
    <>
      {page.cutoff.text === null ? null : (
        <p className="site-prices__cutoff" data-prices-cutoff>
          {page.cutoff.text}
        </p>
      )}
      <PricesSignIn text={page.sign_in_text} />
      {page.need === null ? null : <PriceNeedBlock need={page.need} />}
      <Panel
        heading={page.table_title}
        headingId={SITE_PRICES_TABLE_HEADING_ID}
        description={page.table_note}
        actions={<span className="badge site-prices__count">{page.count_text}</span>}
      >
        <div className="site-prices__table">
          <DataTable labelledBy={SITE_PRICES_TABLE_HEADING_ID}>
            <thead>
              <tr>
                {COLUMNS.map((h) => (
                  <th key={h} scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {page.prices.map((row) => (
                <Fragment key={row.key}>
                  <PriceRowGroup row={row} focused={row.key === focusKey} below={renderBelow?.(row)} />
                </Fragment>
              ))}
            </tbody>
          </DataTable>
        </div>
      </Panel>
    </>
  );
}
