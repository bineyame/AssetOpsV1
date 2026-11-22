/**
 * 5c unit 3 (spec §5): "The month", the one deep-dive screen, at `/portfolio/month?month=YYYY-MM`.
 *
 * The page renders the server's JSON (`deep-dive-month-1`) as given: it never formats, adds or compares a figure
 * (D-5C.2). The one piece of arithmetic is the tile bar's width, `actual / max(|actual|, |target|)` (spec §5.3); the
 * step bars and the scale marks are served positions, drawn as given (D-5C.27). A figure slot with no word is muted with
 * `dd-na` (D-5C.26). Every word chip shows the JSON's own word as text, never colour alone.
 *
 * Layout: IA-1b's hub shape (D-5C.14). `data-level` regions L1 (the lead and the four tiles), L2 (one queue block) and
 * L3 (three answer-titled sections): six blocks. Drawers stay inside their sections. MOCK DEVIATION rows MD1 to MD10
 * (`.agent/mock-departure-register.md`) record where vNEXT `#/portfolio` and this page differ.
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";

import type { EstateClient } from "./estateClient";
import { DecisionsRows } from "./homeLists";
import type { PeriodDays } from "./portfolioPeriodClient";

import { DataTable } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import {
  createDeepDiveMonthClient,
  type DeepDiveDriver,
  type DeepDiveMonthBody,
  type DeepDiveMonthClient,
  type DeepDiveResult,
  type DeepDiveStep,
  type DeepDiveStepBar,
  type DeepDiveTable,
} from "./deepDiveMonthClient";
import { PortfolioTabs } from "./PortfolioTabs";
import "./deepDiveMonth.css";

/**
 * The title of the section that lists the records still missing (spec §5.2, D-5C.11, D-5C.14). It names a section of
 * served rows, each naming its record; it is not a claim about a Site (missing-claim scan exemption).
 */
export const DD_NOT_AVAILABLE_TITLE = "What is not available yet";

/** Screen copy the page owns (spec §5.2); every figure and served sentence comes from the JSON. */
export const DD_COPY = {
  title: "Portfolio",
  loading: "Preparing the month…",
  signIn: "Sign in to see this operator's figures.",
  unreadable: "The month's figures cannot be read right now.",
  tryAgain: "Try again",
  bridge: "Where the gap comes from",
  byOutcome: "By outcome",
  notAvailable: DD_NOT_AVAILABLE_TITLE,
  showBySiteTable: "Show as table, by Site",
  showBySite: "Show by Site",
  close: "Close",
  monthNav: "Month",
  drawerSites: "By Site",
  drawerDrivers: "Drivers",
  showAll: (n: number) => `Show all ${n}`,
  partsOf: (label: string) => `Parts of ${label}`,
  more: (n: number) => `And ${n} more`,
} as const;

const SITE_CAP = 10;
const NOT_AVAILABLE_CAP = 8;
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

/** D-5C.26: a figure slot whose `word` is null holds no figure; its value is muted (`dd-na`). The shape, never a key. */
function mute(word: string | null, className: string): string {
  return word === null ? `${className} dd-na` : className;
}

/**
 * D-5C.27: the step's track (vNEXT `.ux-wf-track`) and, when served, its bar at the served `left` and `width` (strings,
 * used as given: no arithmetic). A null bar leaves the track empty. Decorative: the row's text carries the figure.
 */
function StepTrack({ bar }: { bar: DeepDiveStepBar | null }) {
  return (
    <span className="dd-wf__track" aria-hidden="true">
      {bar !== null ? <span className={`dd-wf__bar dd-wf__bar--${bar.tone}`} style={{ left: `${bar.left}%`, width: `${bar.width}%` }} /> : null}
    </span>
  );
}

/** D-5C.27: the target and actual marks above the step tracks, at the served `target_at` and `actual_at`. */
function Scale({ scale, totals }: { scale: { target_at: string; actual_at: string }; totals: NonNullable<DeepDiveMonthBody["bridge"]>["totals"] }) {
  return (
    <div className="dd-wf__scalerow" aria-hidden="true">
      <div className="dd-wf__scale">
        <span className="dd-wf__mark" style={{ left: `${scale.target_at}%` }}>
          {totals.target_label} {totals.target}
        </span>
        <span className="dd-wf__mark dd-wf__mark--end" style={{ left: `${scale.actual_at}%` }}>
          {totals.actual_label} {totals.actual}
        </span>
      </div>
    </div>
  );
}

/* ---------- drawers (vNEXT `uxOpen`/`uxClose`: dialog, focus to Close, Escape and scrim close, focus returns) ---------- */

export interface DrawerApi {
  openId: string | null;
  open: (id: string, opener: HTMLElement) => void;
  close: () => void;
}

export function useDrawers(): DrawerApi {
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
  const { close } = api;
  // Rev 4 (L1, L2; vNEXT `uxOpen`): while open, Escape and the Tab cycle are handled on `document`, so they hold
  // wherever focus is (also after "Show all" replaced the focused button), and `body` carries `dd-locked`.
  useEffect(() => {
    if (!shown) return undefined;
    closeButton.current?.focus();
    document.body.classList.add("dd-locked");
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key !== "Tab" || panel.current === null) return;
      const focusable = [...panel.current.querySelectorAll<HTMLElement>("button, a[href], summary, [tabindex='0']")];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const out = !focusable.includes(document.activeElement as HTMLElement);
      if (event.shiftKey && (out || document.activeElement === first)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (out || document.activeElement === last)) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.classList.remove("dd-locked");
    };
  }, [shown, close]);
  if (!shown) return null;
  const titleId = `${id}-title`;
  return (
    <div className="dd-drawer" data-dd-drawer={id}>
      <div className="dd-drawer__scrim" data-dd-scrim onClick={api.close} />
      <div className="dd-drawer__panel" role="dialog" aria-modal="true" aria-labelledby={titleId} ref={panel}>
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

export function Lines({ lines, className }: { lines: string[]; className?: string }) {
  if (lines.length === 0) return null;
  return (
    <ul className={className ?? "dd-lines"}>
      {lines.map((line, i) => (
        <li key={i}>{line}</li>
      ))}
    </ul>
  );
}

/**
 * A list capped at `cap` items, then "Show all {n}" (D-5C.12: scales to 300 Sites). The click moves focus to the first
 * newly shown row (rev 4, L1), which takes `tabIndex={-1}`, so focus stays where the reader was.
 */
function Capped<T>({ items, cap, className, render }: { items: T[]; cap: number; className: string; render: (item: T) => ReactNode }) {
  const [all, setAll] = useState(false);
  const firstNew = useRef<HTMLLIElement>(null);
  useEffect(() => {
    if (all) firstNew.current?.focus();
  }, [all]);
  const shown = all ? items : items.slice(0, cap);
  return (
    <>
      {shown.map((item, i) =>
        all && i === cap ? (
          <li key={i} className={className} ref={firstNew} tabIndex={-1}>
            {render(item)}
          </li>
        ) : (
          <li key={i} className={className}>
            {render(item)}
          </li>
        ),
      )}
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

/**
 * D-5C.21: one `<ul>` per level; a driver's parts sit in a nested `<ul>` inside its `<li>`, never beside it, so the
 * grouping on screen is the sum's grouping. No control: every level shows. The page adds nothing.
 */
function DriverList({ drivers, parent }: { drivers: DeepDiveDriver[]; parent?: string }) {
  return (
    <ul className={parent === undefined ? "dd-drivers" : "dd-drivers dd-drivers--parts"} aria-label={parent === undefined ? undefined : DD_COPY.partsOf(parent)}>
      {drivers.map((driver) => (
        <li key={driver.key} className="dd-driver" data-dd-driver>
          <span className="dd-driver__label">{driver.label}</span> <span className={mute(driver.word, "dd-num")}>{driver.value}</span> <Word word={driver.word} />
          <span className="dd-driver__meta">
            {driver.sites}
            {driver.detail !== null ? ` · ${driver.detail}` : ""}
          </span>
          {driver.children.length > 0 ? <DriverList drivers={driver.children} parent={driver.label} /> : null}
        </li>
      ))}
    </ul>
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
              className="dd-site"
              render={(s) => (
                <>
                  <span className="dd-site__name">{s.site}</span> <span className="dd-num">{s.value}</span>
                  {s.text !== null ? <p className="dd-site__stop">{s.text}</p> : null}
                </>
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
          <DriverList drivers={d.drivers} />
        </>
      ) : null}
    </Drawer>
  );
}

function MonthTable({ table, labelledBy }: { table: DeepDiveTable; labelledBy: string }) {
  const [all, setAll] = useState(false);
  const firstNewRow = useRef<HTMLTableRowElement>(null);
  useEffect(() => {
    if (all) firstNewRow.current?.focus();
  }, [all]);
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
            <tr key={r} {...(all && r === SITE_CAP ? { ref: firstNewRow, tabIndex: -1 } : {})}>
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

/** IA-P P3b: the four tiles (L1), shared by the month and the period body. */
export function DdTiles({ tiles }: { tiles: NonNullable<DeepDiveMonthBody["tiles"]> }) {
  return (
    <div className="dd-kpis">
      {tiles.map((tile) => (
        <div key={tile.key} className="dd-kpi" data-dd-tile={tile.key}>
          <span className="dd-kpi__label">{tile.label}</span>
          <span className={mute(tile.word, "dd-kpi__value")}>
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

/** IA-P P3b: the "Actions in hand" panel (L2), shared by the month and the period body. */
export function DdActions({ actions }: { actions: NonNullable<DeepDiveMonthBody["actions"]> }) {
  return (
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
  );
}

/**
 * IA-P P3b (spec §3 "Overview L2"): one queue block. 5c's Decisions panel is the Decisions list's rows for the range
 * (at most six, then "View all {n}"); "Actions in hand" stays beside them, from the body of the mode.
 */
export function DdQueue({ title, actions, estate }: { title: string; actions: NonNullable<DeepDiveMonthBody["actions"]> | null; estate?: EstateClient }) {
  return (
    <div className="dd-queue">
      <DecisionsRows client={estate} title={title} />
      {actions !== null ? <DdActions actions={actions} /> : null}
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
      {bridge.scale !== null ? <Scale scale={bridge.scale} totals={bridge.totals} /> : null}
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
                    <span className="dd-wf__label">{step.label}</span> <span className={mute(step.word, "dd-wf__value dd-num")}>{step.value}</span>{" "}
                    <span className="dd-wf__share">{step.share}</span> <Word word={step.word} />{" "}
                    <span className="dd-wf__sites">{step.sites}</span>
                    <StepTrack bar={step.bar} />
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

/** IA-P P3b: the outcome cards (L3), shared by the month and the period body; the period serves no not-available rows. */
export function DdOutcomes({
  cards,
  na,
  api,
}: {
  cards: NonNullable<DeepDiveMonthBody["outcomes"]>;
  na: DeepDiveMonthBody["not_available"] | null;
  api: DrawerApi;
}) {
  return (
    <section className="dd-section" aria-labelledby="dd-outcomes-h">
      <h2 id="dd-outcomes-h">{DD_COPY.byOutcome}</h2>
      <div className="dd-cards">
        {cards.map((card) => (
          <div key={card.key} className="dd-card" data-dd-outcome={card.key}>
            <span className="dd-card__label">{card.label}</span>
            {card.drawer !== null ? (
              <button type="button" className="dd-card__value dd-link" aria-haspopup="dialog" onClick={(e) => api.open(`dd-outcome-${card.key}`, e.currentTarget)}>
                {card.value}
              </button>
            ) : (
              // D-5C.26: a card with no drawer and no word holds no figure (Assure always has its drawer).
              <span className={mute(card.word, "dd-card__value")}>{card.value}</span>
            )}
            <Word word={card.word} />
            <span className="dd-card__line">{card.line}</span>
          </div>
        ))}
      </div>
      {na ? (
        <>
          <h3 id="dd-na-h">{DD_COPY.notAvailable}</h3>
          <ul className="dd-gaps" aria-labelledby="dd-na-h">
            <Capped
              items={na.rows}
              cap={NOT_AVAILABLE_CAP}
              className="dd-gaps__row"
              render={(row) => (
                <>
                  <span className="dd-gaps__needs">{row.needs}</span>
                  <span className="dd-gaps__fills">{row.fills}</span>
                  <span className="dd-gaps__sites">{row.sites}</span>
                </>
              )}
            />
          </ul>
          <p className="dd-meta">{na.not_built}</p>
        </>
      ) : null}
      {cards.map((card) =>
        card.drawer !== null ? (
          <Drawer key={card.key} id={`dd-outcome-${card.key}`} title={card.drawer.title} api={api}>
            <Lines lines={card.drawer.lines} />
          </Drawer>
        ) : null,
      )}
    </section>
  );
}

/** A month's range on the Overview: `from` and `to` replaced, every other parameter of the address kept (spec §3). */
export function monthRangeHref(days: { from: string; to: string }, params: URLSearchParams): string {
  const next = new URLSearchParams(params);
  next.set("from", days.from);
  next.set("to", days.to);
  return `/portfolio?${next.toString()}`;
}

/** IA-P P3b (I1): the ‹ › links are E2's `nav` (days from the server); with `next` null no next control is drawn. */
export type MonthNavDays = { previous: PeriodDays | null; next: PeriodDays | null };

function MonthNav({ current, nav }: { current: string; nav: MonthNavDays | null }) {
  const [params] = useSearchParams();
  return (
    <nav className="dd-nav" aria-label={DD_COPY.monthNav}>
      {nav?.previous ? (
        <Link className="dd-nav__link" to={monthRangeHref(nav.previous, params)}>
          ‹ {nav.previous.month_words}
        </Link>
      ) : null}
      <b className="dd-nav__current">{current}</b>
      {nav?.next ? (
        <Link className="dd-nav__link" to={monthRangeHref(nav.next, params)}>
          {nav.next.month_words} ›
        </Link>
      ) : null}
    </nav>
  );
}

/** IA-P P3b: E2's notes in the header (`<p class="dd-period" role="note">`). */
export function DdNotes({ notes }: { notes: readonly string[] }) {
  return (
    <>
      {notes.map((note) => (
        <p key={note} className="dd-period" role="note">
          {note}
        </p>
      ))}
    </>
  );
}

/** IA-P P3b: the hub header of every Overview mode: the title, the operator, the three tabs, then the mode's own lines. */
export function DdHead({ operator, children }: { operator: string | null; children?: ReactNode }) {
  return (
    <header className="dd-head">
      <div className="dd-head__title">
        <h1>{DD_COPY.title}</h1>
        {operator !== null ? <p className="dd-operator">{operator}</p> : null}
      </div>
      <PortfolioTabs current="overview" />
      {children}
    </header>
  );
}

type Read = { key: string; result: DeepDiveResult };

/**
 * 5c's month screen as the Overview's mode `month` (IA-P P3b, spec §3). It reads the month read for E2's month (never
 * for the range's `to`), and takes the header's links and notes from E2. L1 and L3 are 5c's, unchanged.
 */
export function DeepDiveMonthPage({
  client,
  estate,
  month,
  nav,
  notes,
}: {
  client?: DeepDiveMonthClient;
  estate?: EstateClient;
  month: string;
  nav: MonthNavDays | null;
  notes: readonly string[];
}) {
  const reads = useRef(client ?? createDeepDiveMonthClient()).current;
  const [attempt, setAttempt] = useState(0);
  const key = `${month}|${attempt}`;
  const [read, setRead] = useState<Read | null>(null);
  const api = useDrawers();
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
          <DdTiles tiles={body.tiles!} />
        </div>
        <div data-level="L2">
          <DdQueue title={body.decisions!.title} actions={body.actions!} estate={estate} />
        </div>
        <div data-level="L3">
          <Bridge body={body} api={api} />
          <Cash body={body} />
          <DdOutcomes cards={body.outcomes!} na={body.not_available!} api={api} />
        </div>
      </>
    );
  }

  return (
    <section data-shape="hub" className="dd-month">
      <DdHead operator={body !== null ? body.operator : null}>
        {body !== null ? <MonthNav current={body.month_words} nav={nav} /> : null}
        <DdNotes notes={notes} />
      </DdHead>
      {content}
    </section>
  );
}

/** The month screen in its own `<main>` (the Overview's frame is `PortfolioOverview.tsx`; tests mount this one). */
export function DeepDiveMonthFrame(props: Parameters<typeof DeepDiveMonthPage>[0]) {
  return (
    <main aria-label="Portfolio">
      <DeepDiveMonthPage {...props} />
    </main>
  );
}
