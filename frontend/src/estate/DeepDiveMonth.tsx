/**
 * 5c unit 3 (spec §5): "The month", the one deep-dive screen, at `/portfolio/month?month=YYYY-MM`.
 *
 * The page renders the server's JSON (`deep-dive-month-1`) as given: it never formats, adds or compares a figure
 * (D-5C.2). The one piece of arithmetic is the bar's width, `actual / max(|actual|, |target|)` (spec §5.3). Every word
 * chip shows the JSON's own word as text, never colour alone.
 *
 * Layout: IA-1b's hub shape (D-5C.14). `data-level` regions L1 (the lead and the four tiles), L2 (one queue block) and
 * L3 (three answer-titled sections): six blocks. Drawers stay inside their sections. MOCK DEVIATION rows MD1 to MD10
 * (`.agent/mock-departure-register.md`) record where vNEXT `#/portfolio` and this page differ.
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";

import { DataTable } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import {
  createDeepDiveMonthClient,
  type DeepDiveMonthBody,
  type DeepDiveMonthClient,
  type DeepDiveResult,
  type DeepDiveStep,
  type DeepDiveTable,
} from "./deepDiveMonthClient";
import { queryFromParams } from "./estateShared";
import { PortfolioTabs } from "./PortfolioTabs";
import "./deepDiveMonth.css";

/** Screen copy the page owns (spec §5.2); every figure and served sentence comes from the JSON. */
export const DD_COPY = {
  title: "Portfolio",
  loading: "Preparing the month…",
  signIn: "Sign in to see this operator's figures.",
  unreadable: "The month's figures cannot be read right now.",
  tryAgain: "Try again",
  bridge: "Where the gap comes from",
  byOutcome: "By outcome",
  notAvailable: "What is not available yet",
  showBySiteTable: "Show as table, by Site",
  showBySite: "Show by Site",
  close: "Close",
  monthNav: "Month",
  drawerSites: "By Site",
  drawerDrivers: "Drivers",
  needs: "Needs",
  fills: "Fills",
  sites: "Sites",
  showAll: (n: number) => `Show all ${n}`,
  more: (n: number) => `And ${n} more`,
} as const;

const SITE_CAP = 10;
const NOT_AVAILABLE_CAP = 8;
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

/** A `YYYY-MM` code as words ("September 2026"): a label for the month links, not a figure. */
function monthWords(code: string): string {
  const [y, m] = code.split("-");
  return `${MONTHS[parseInt(m, 10) - 1] ?? m} ${y}`;
}

/** The month after `code`, for the disabled "next" label only. */
function monthAfter(code: string): string {
  const [y, m] = code.split("-").map((p) => parseInt(p, 10));
  return m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, "0")}`;
}

const monthHref = (code: string) => `/portfolio/month?month=${code}`;

/** The bar's widths (spec §5.3: the page's one ratio), as percentages of the larger magnitude. */
function barWidths(bar: { actual: string; target: string }): { actual: number; target: number } {
  const a = Number(bar.actual);
  const t = Number(bar.target);
  const top = Math.max(Math.abs(a), Math.abs(t));
  if (!Number.isFinite(top) || top === 0) return { actual: 0, target: 0 };
  return { actual: (Math.max(a, 0) / top) * 100, target: (Math.max(t, 0) / top) * 100 };
}

function Word({ word }: { word: string | null | undefined }) {
  if (word === null || word === undefined) return null;
  return (
    <span className="dd-chip" data-dd-word>
      {word}
    </span>
  );
}

function Bar({ bar, label }: { bar: { actual: string; target: string }; label: string }) {
  const w = barWidths(bar);
  return (
    <div className="dd-bar" role="img" aria-label={label}>
      <span className="dd-bar__actual" style={{ width: `${w.actual}%` }} />
      <span className="dd-bar__target" style={{ left: `${w.target}%` }} />
    </div>
  );
}

/* ---------- drawers (vNEXT `uxOpen`/`uxClose`: dialog, focus to Close, Escape and scrim close, focus returns) ---------- */

interface DrawerApi {
  openId: string | null;
  open: (id: string, opener: HTMLElement) => void;
  close: () => void;
}

function useDrawers(): DrawerApi {
  const [openId, setOpenId] = useState<string | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const restore = useRef(false);
  useEffect(() => {
    if (openId === null && restore.current) {
      restore.current = false;
      opener.current?.focus();
    }
  }, [openId]);
  const open = useCallback((id: string, el: HTMLElement) => {
    opener.current = el;
    setOpenId(id);
  }, []);
  const close = useCallback(() => {
    restore.current = true;
    setOpenId(null);
  }, []);
  return { openId, open, close };
}

function Drawer({ id, title, api, children }: { id: string; title: string; api: DrawerApi; children: ReactNode }) {
  const panel = useRef<HTMLDivElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const shown = api.openId === id;
  useEffect(() => {
    if (shown) closeButton.current?.focus();
  }, [shown]);
  if (!shown) return null;
  const titleId = `${id}-title`;
  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Escape") {
      event.preventDefault();
      api.close();
      return;
    }
    if (event.key !== "Tab" || panel.current === null) return;
    const focusable = [...panel.current.querySelectorAll<HTMLElement>("button, a[href], summary, [tabindex='0']")];
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };
  return (
    <div className="dd-drawer" data-dd-drawer={id}>
      <div className="dd-drawer__scrim" data-dd-scrim onClick={api.close} />
      <div className="dd-drawer__panel" role="dialog" aria-modal="true" aria-labelledby={titleId} ref={panel} onKeyDown={onKeyDown}>
        <div className="dd-drawer__head">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="dd-button" ref={closeButton} onClick={api.close}>
            {DD_COPY.close}
          </button>
        </div>
        <div className="dd-drawer__body">{children}</div>
      </div>
    </div>
  );
}

function Lines({ lines, className }: { lines: string[]; className?: string }) {
  if (lines.length === 0) return null;
  return (
    <ul className={className ?? "dd-lines"}>
      {lines.map((line, i) => (
        <li key={i}>{line}</li>
      ))}
    </ul>
  );
}

/** A list capped at `cap` items, then "Show all {n}" (D-5C.12: scales to 300 Sites). */
function Capped<T>({ items, cap, render }: { items: T[]; cap: number; render: (item: T, i: number) => ReactNode }) {
  const [all, setAll] = useState(false);
  const shown = all ? items : items.slice(0, cap);
  return (
    <>
      {shown.map(render)}
      {!all && items.length > cap ? (
        <li className="dd-showall">
          <button type="button" className="dd-link" onClick={() => setAll(true)}>
            {DD_COPY.showAll(items.length)}
          </button>
        </li>
      ) : null}
    </>
  );
}

function StepDrawer({ step, api }: { step: DeepDiveStep; api: DrawerApi }) {
  const d = step.drawer;
  return (
    <Drawer id={`dd-step-${step.key}`} title={d.title} api={api}>
      <Lines lines={d.lines} />
      <p className="dd-drawer__word">
        <Word word={step.word} />
      </p>
      {d.sites.length > 0 ? (
        <>
          <h3>{DD_COPY.drawerSites}</h3>
          <ul className="dd-sites">
            <Capped
              items={d.sites}
              cap={SITE_CAP}
              render={(s, i) => (
                <li key={i} className="dd-site">
                  <span className="dd-site__name">{s.site}</span> <span className="dd-num">{s.value}</span>
                  {s.text !== null ? <p className="dd-site__stop">{s.text}</p> : null}
                </li>
              )}
            />
          </ul>
        </>
      ) : null}
      <Lines lines={d.carried} className="dd-lines dd-lines--note" />
      <Lines lines={d.out} className="dd-lines dd-lines--note" />
      <Lines lines={d.lines_org} className="dd-lines dd-lines--note" />
      {d.drivers.length > 0 ? (
        <>
          <h3>{DD_COPY.drawerDrivers}</h3>
          <ul className="dd-drivers">
            {d.drivers.map((driver, i) => (
              <li key={i} className="dd-driver" data-dd-driver>
                <span className="dd-driver__label">{driver.label}</span> <span className="dd-num">{driver.value}</span>{" "}
                <Word word={driver.word} />
                <span className="dd-driver__meta">
                  {driver.sites}
                  {driver.detail !== null ? ` · ${driver.detail}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </Drawer>
  );
}

function MonthTable({ table, labelledBy }: { table: DeepDiveTable; labelledBy: string }) {
  const [all, setAll] = useState(false);
  const rows = all ? table.rows : table.rows.slice(0, SITE_CAP);
  return (
    <>
      <DataTable labelledBy={labelledBy} stickyFirstColumn>
        <thead>
          <tr>
            {table.columns.map((c, i) => (
              <th key={i} scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, r) => (
            <tr key={r}>
              {row.map((cell, i) => (i === 0 ? <th key={i} scope="row">{cell}</th> : <td key={i}>{cell}</td>))}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            {table.total.map((cell, i) => (i === 0 ? <th key={i} scope="row">{cell}</th> : <td key={i}>{cell}</td>))}
          </tr>
        </tfoot>
      </DataTable>
      {!all && table.rows.length > SITE_CAP ? (
        <button type="button" className="dd-link" onClick={() => setAll(true)}>
          {DD_COPY.showAll(table.rows.length)}
        </button>
      ) : null}
    </>
  );
}

/* ---------- the hub ---------- */

function Lead({ body }: { body: DeepDiveMonthBody }) {
  return (
    <div className="dd-lead">
      <p className="dd-headline">
        {body.headline!.text}{" "}
        {body.headline!.evidence.map((e, i) => (
          <span key={i} className="dd-chip dd-chip--headline" data-dd-word>
            {e}
          </span>
        ))}
      </p>
      <p role="status" className="dd-status">
        {body.status_line}
      </p>
      {body.fresh?.text ? <p className="dd-fresh">{body.fresh.text}</p> : null}
    </div>
  );
}

function Tiles({ body }: { body: DeepDiveMonthBody }) {
  return (
    <div className="dd-kpis">
      {body.tiles!.map((tile) => (
        <div key={tile.key} className="dd-kpi" data-dd-tile={tile.key}>
          <span className="dd-kpi__label">{tile.label}</span>
          <span className={tile.word === null && tile.bar === null && tile.key.startsWith("plan") ? "dd-kpi__value dd-kpi__value--na" : "dd-kpi__value"}>
            {tile.value}
          </span>
          <Word word={tile.word} />
          {tile.bar !== null ? <Bar bar={tile.bar} label={`${tile.label} ${tile.value}; ${tile.lines[0] ?? ""}`} /> : null}
          <Lines lines={tile.lines} className="dd-kpi__lines" />
        </div>
      ))}
    </div>
  );
}

function Queue({ body }: { body: DeepDiveMonthBody }) {
  const actions = body.actions!;
  return (
    <div className="dd-queue">
      <section className="dd-panel" aria-labelledby="dd-decisions-h">
        <h2 id="dd-decisions-h">{body.decisions!.title}</h2>
        <p>{body.decisions!.text}</p>
      </section>
      <section className="dd-panel" aria-labelledby="dd-actions-h">
        <h2 id="dd-actions-h">{actions.title}</h2>
        {actions.text !== null ? <p>{actions.text}</p> : null}
        {actions.rows.length > 0 ? (
          <ul className="dd-actions">
            {actions.rows.map((row, i) => (
              <li key={i} className="dd-action">
                <span className="dd-action__title">{row.title}</span>
                <span className="dd-chip">{row.state}</span>
                <span className="dd-action__meta">{row.owner}</span>
                <span className="dd-action__meta">{row.agreed}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {actions.more > 0 ? <p className="dd-more">{DD_COPY.more(actions.more)}</p> : null}
      </section>
    </div>
  );
}

function Bridge({ body, api }: { body: DeepDiveMonthBody; api: DrawerApi }) {
  const bridge = body.bridge!;
  const bar = body.tiles![0]?.bar ?? null;
  return (
    <section className="dd-section" aria-labelledby="dd-bridge-h">
      <h2 id="dd-bridge-h">{DD_COPY.bridge}</h2>
      <p className="dd-section__title">{bridge.title}</p>
      {body.notices!.map((notice, i) => (
        <p key={i} role="note" className="dd-notice">
          {notice}
        </p>
      ))}
      <div className="dd-totals">
        {bar !== null ? <Bar bar={bar} label={`${bridge.totals.actual_label} ${bridge.totals.actual}; ${bridge.totals.target_label} ${bridge.totals.target}`} /> : null}
        <div className="dd-totals__line">
          <span>
            {bridge.totals.actual_label} <b className="dd-num">{bridge.totals.actual}</b>
          </span>
          <span>
            {bridge.totals.target_label} <b className="dd-num">{bridge.totals.target}</b>
          </span>
        </div>
      </div>
      <ol className="dd-wf">
        {bridge.groups.map((group) => (
          <li key={group.key} className="dd-wf__group">
            <div className="dd-wf__grouprow">
              <span className="dd-wf__glabel">{group.label}</span> <span className="dd-num">{group.value}</span>
            </div>
            <ol className="dd-wf__steps">
              {group.steps.map((step) => (
                <li key={step.key}>
                  <button
                    type="button"
                    className="dd-wf__step"
                    aria-haspopup="dialog"
                    data-dd-step={step.key}
                    onClick={(e) => api.open(`dd-step-${step.key}`, e.currentTarget)}
                  >
                    <span className="dd-wf__label">{step.label}</span> <span className="dd-wf__value dd-num">{step.value}</span>{" "}
                    <span className="dd-wf__share">{step.share}</span> <Word word={step.word} />{" "}
                    <span className="dd-wf__sites">{step.sites}</span>
                  </button>
                </li>
              ))}
            </ol>
          </li>
        ))}
      </ol>
      <details className="dd-details">
        <summary id="dd-bysite-h">{DD_COPY.showBySiteTable}</summary>
        <MonthTable table={bridge.by_site} labelledBy="dd-bysite-h" />
      </details>
      {bridge.groups.flatMap((g) => g.steps).map((step) => (
        <StepDrawer key={step.key} step={step} api={api} />
      ))}
    </section>
  );
}

function Cash({ body }: { body: DeepDiveMonthBody }) {
  const cash = body.cash!;
  return (
    <section className="dd-section" aria-labelledby="dd-cash-h">
      <h2 id="dd-cash-h">{cash.title}</h2>
      <p>{cash.text}</p>
      <p className="dd-meta">
        <Word word={cash.word} /> <span>{cash.sites}</span>
      </p>
      <details className="dd-details">
        <summary id="dd-cash-table-h">{DD_COPY.showBySite}</summary>
        <MonthTable table={cash.table} labelledBy="dd-cash-table-h" />
      </details>
    </section>
  );
}

function Outcomes({ body, api }: { body: DeepDiveMonthBody; api: DrawerApi }) {
  const na = body.not_available!;
  return (
    <section className="dd-section" aria-labelledby="dd-outcomes-h">
      <h2 id="dd-outcomes-h">{DD_COPY.byOutcome}</h2>
      <div className="dd-cards">
        {body.outcomes!.map((card) => (
          <div key={card.key} className="dd-card" data-dd-outcome={card.key}>
            <span className="dd-card__label">{card.label}</span>
            {card.drawer !== null ? (
              <button type="button" className="dd-card__value dd-link" aria-haspopup="dialog" onClick={(e) => api.open(`dd-outcome-${card.key}`, e.currentTarget)}>
                {card.value}
              </button>
            ) : (
              <span className="dd-card__value">{card.value}</span>
            )}
            <Word word={card.word} />
            <span className="dd-card__line">{card.line}</span>
          </div>
        ))}
      </div>
      <h3 id="dd-na-h">{DD_COPY.notAvailable}</h3>
      <ul className="dd-na" aria-labelledby="dd-na-h">
        <Capped
          items={na.rows}
          cap={NOT_AVAILABLE_CAP}
          render={(row, i) => (
            <li key={i} className="dd-na__row">
              <span className="dd-na__needs">{row.needs}</span>
              <span className="dd-na__fills">{row.fills}</span>
              <span className="dd-na__sites">{row.sites}</span>
            </li>
          )}
        />
      </ul>
      <p className="dd-meta">{na.not_built}</p>
      {body.outcomes!.map((card) =>
        card.drawer !== null ? (
          <Drawer key={card.key} id={`dd-outcome-${card.key}`} title={card.drawer.title} api={api}>
            <Lines lines={card.drawer.lines} />
          </Drawer>
        ) : null,
      )}
    </section>
  );
}

function MonthNav({ body }: { body: DeepDiveMonthBody }) {
  const next = body.nav.next;
  return (
    <nav className="dd-nav" aria-label={DD_COPY.monthNav}>
      <Link className="dd-nav__link" to={monthHref(body.nav.previous)}>
        ‹ {monthWords(body.nav.previous)}
      </Link>
      <b className="dd-nav__current">{body.month_words}</b>
      {next !== null ? (
        <Link className="dd-nav__link" to={monthHref(next)}>
          {monthWords(next)} ›
        </Link>
      ) : (
        <button type="button" className="dd-nav__link" disabled>
          {monthWords(monthAfter(body.month))} ›
        </button>
      )}
    </nav>
  );
}

type Read = { key: string; result: DeepDiveResult };

export function DeepDiveMonthPage({ client }: { client?: DeepDiveMonthClient }) {
  const reads = useRef(client ?? createDeepDiveMonthClient()).current;
  const [params] = useSearchParams();
  const month = params.get("month") ?? undefined;
  const [attempt, setAttempt] = useState(0);
  const key = `${month ?? ""}|${attempt}`;
  const [read, setRead] = useState<Read | null>(null);
  const api = useDrawers();
  // spec §5.1: the month page's tabs carry the Portfolio's default window and lens.
  const window = queryFromParams(new URLSearchParams());

  useEffect(() => {
    let live = true;
    void reads.fetchDeepDiveMonth(month).then((result) => {
      if (live) setRead({ key, result });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);

  const current = read !== null && read.key === key ? read.result : null;
  const body = current?.status === "loaded" ? current.body : null;
  const served = body !== null && body.state === "SERVED";

  let content: ReactNode;
  if (current === null) {
    content = <p className="dd-state">{DD_COPY.loading}</p>;
  } else if (current.status === "refused") {
    content =
      current.httpStatus === 401 ? (
        <p className="dd-state">{DD_COPY.signIn}</p>
      ) : (
        <div className="dd-state">
          <p>{current.text ?? DD_COPY.unreadable}</p>
          {current.httpStatus !== 422 ? (
            <button type="button" className="dd-button" onClick={() => setAttempt((n) => n + 1)}>
              {DD_COPY.tryAgain}
            </button>
          ) : null}
        </div>
      );
  } else if (!served) {
    content = <p className="dd-state">{current.body.state_text}</p>;
  } else {
    content = (
      <>
        <div data-level="L1">
          <Lead body={body} />
          <Tiles body={body} />
        </div>
        <div data-level="L2">
          <Queue body={body} />
        </div>
        <div data-level="L3">
          <Bridge body={body} api={api} />
          <Cash body={body} />
          <Outcomes body={body} api={api} />
        </div>
      </>
    );
  }

  return (
    <section data-shape="hub" className="dd-month">
      <header className="dd-head">
        <div className="dd-head__title">
          <h1>{DD_COPY.title}</h1>
          {body !== null ? <p className="dd-operator">{body.operator}</p> : null}
        </div>
        <PortfolioTabs current="month" window={window} lens="all" />
        {body !== null ? <MonthNav body={body} /> : null}
      </header>
      {content}
    </section>
  );
}

export function DeepDiveMonthFrame({ client }: { client?: DeepDiveMonthClient }) {
  return (
    <main aria-label="Portfolio">
      <DeepDiveMonthPage client={client} />
    </main>
  );
}
