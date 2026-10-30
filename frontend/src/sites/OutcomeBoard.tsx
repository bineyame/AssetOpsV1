import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode, type RefObject } from "react";
import { Link } from "react-router-dom";

import { OutcomeGlyph, type OutcomeGlyphName } from "./componentIcons";
import { OutcomeIcon } from "./outcomeCategories";
import type {
  OutcomeBoardBody,
  OutcomeBoardClient,
  OutcomeBoardQuery,
  OutcomeBoardRead,
  OutcomeBoardRow,
  OutcomeLinkItem,
  OutcomeMoney,
} from "./outcomeBoardClient";
import "./outcomes.css";

/**
 * OUT-B B5: "How this site is doing", the four-row Site outcome board (v7.0 mock `outcomeBoard`,
 * `outcomes.js:116-124`). It replaces the old overview cards on the mini-grid, cold and EV overviews. Every text
 * on a row is backend data (§B.1, §B.4); the frontend adds only the column headings, the empty texts of the mock,
 * the issue-kind labels of §B.1 and the money of `headline_money` (ruling B-Q14). No outcome code is shown.
 */

export const BOARD_TITLE = "How this site is doing";
export const BOARD_LOADING = "Loading how this site is doing…";
export const BOARD_REFUSED = "This view is not available for this site";
export const BOARD_PARTIAL = "Some readings could not be loaded; those outcomes show Unknown";

/** Column headings and empty texts (`outcomes.js:121-122`). Earlier uses the row's `earlier_empty_text`. */
export const COLUMN = {
  drives: "What drives it",
  issues: "Issues",
  can: "What can be done",
  hand: "Already in hand",
  prev: "Earlier interventions",
} as const;
export const EMPTY = {
  issues: "None open",
  can: "Nothing proposed yet",
  hand: "No open action or work",
  /** Addendum 2: only when the field is absent on an older body. */
  prev: "None recorded",
} as const;

/** §B.1 issue kinds: label and the mock `.oc-kind` class (ruling B-Q29: `finding` and `gap` are neutral). */
const ISSUE_KIND: Record<string, [string, string]> = {
  FINDING: ["Finding", "finding"],
  EVIDENCE_GAP: ["Evidence gap", "gap"],
  RISK: ["Risk", "risk"],
  EARLY_WARNING: ["Early warning", "stress"],
  OPPORTUNITY: ["Opportunity", "opp"],
};

/** The explainer text, verbatim from the mock `explainBoard` (`outcomes.js:125`). */
const EXPLAIN = [
  "Each row is one of the four things the business is trying to achieve. It shows how it is doing, what is driving that, the problems and opportunities found, what could be done, what is already under way, and whether earlier work fixed anything. Every item opens the page that holds its detail.",
  "Money of different kinds is shown separately and never added together. Where a fix in one row could harm another, the row says what it must not harm.",
  "Confidence says how complete and consistent the readings are. “Not measured yet” means the records needed to judge it are not connected.",
] as const;

/**
 * Ruling B-Q14: the backend sends the amount unformatted. This is the mini overview money slot's own text
 * (`SiteWindowOverview.tsx` `Money`: "{low} to {high} {currency}"); one amount when both bounds are equal (EV Grow).
 */
export function boardMoneyText(money: OutcomeMoney | null): string | null {
  if (money === null || money.amount_low === null || money.amount_high === null) return null;
  const low = String(money.amount_low);
  const high = String(money.amount_high);
  const amount = low === high ? low : `${low} to ${high}`;
  return money.currency ? `${amount} ${money.currency}` : amount;
}

export function countsText(issues: number, inHand: number): string {
  const head = issues === 0 ? "No open issues" : `${issues} issue${issues === 1 ? "" : "s"}`;
  return inHand > 0 ? `${head} · ${inHand} in hand` : head;
}

function To({ href, children }: { href: string | null; children: ReactNode }) {
  return href ? <Link to={href}>{children}</Link> : <>{children}</>;
}

function ColHead({ icon, children }: { icon: OutcomeGlyphName; children: ReactNode }) {
  return (
    <h4>
      <OutcomeGlyph name={icon} className="oc-colic" size={12} />
      {children}
    </h4>
  );
}

function Name({ row }: { row: OutcomeBoardRow }) {
  return (
    <>
      <OutcomeIcon icon={row.category} label={row.label} />
      <span className="ob-name">
        {row.label}
        <small>{row.definition}</small>
      </span>
    </>
  );
}

function ItemList({
  items,
  empty,
}: {
  items: (OutcomeLinkItem & { note?: string | null })[];
  empty: string;
}) {
  if (items.length === 0) return <p className="ob-none">{empty}</p>;
  return (
    <ul className="ob-list">
      {items.map((item, i) => (
        <li key={i}>
          <To href={item.href}>{item.text}</To>
          {item.note ? <> <span className="oc-state">{item.note}</span></> : null}
        </li>
      ))}
    </ul>
  );
}

function Row({ row }: { row: OutcomeBoardRow }) {
  const data = { "data-outcome-row": row.category, "data-outcome-state": row.state };
  if (row.state === "NOT_MEASURED") {
    return (
      <div className="ob ob-later" {...data}>
        <div className="ob-sum">
          <Name row={row} />
          <span className="oc-chip tone-none">{row.state_label}</span>
          <span className="ob-head muted">{row.not_measured_text}</span>
        </div>
      </div>
    );
  }
  const money = boardMoneyText(row.headline_money);
  const headline = money !== null && row.headline ? `${money} ${row.headline}` : (row.headline ?? money);
  const earlierEmpty = "earlier_empty_text" in row ? (row.earlier_empty_text ?? "") : EMPTY.prev;
  return (
    <details className={`ob tone-${row.tone}`} open={row.state === "NEEDS_ATTENTION"} {...data}>
      <summary className="ob-sum">
        <Name row={row} />
        <span className={`oc-chip tone-${row.tone}`}>{row.state_label}</span>
        <span className="ob-head">{headline}</span>
        <span className="ob-counts" data-outcome-counts>
          {countsText(row.counts.issues, row.counts.in_hand)}
        </span>
      </summary>
      <div className="ob-body">
        {row.subline ? <p className="ob-sub">{row.subline}</p> : null}
        {row.must_not_harm ? (
          <p className="ob-guard" data-outcome-guard>
            <OutcomeGlyph name="guard" className="oc-colic" size={14} />
            <span>
              <b>Must not harm</b> <To href={row.must_not_harm.href}>{row.must_not_harm.text}</To>
            </span>
          </p>
        ) : null}
        <div className="ob-grid">
          <div className="ob-col" data-outcome-col="drives">
            <ColHead icon="drives">{COLUMN.drives}</ColHead>
            <ul className="ob-list ob-contrib">
              {row.contributors.map((c, i) => (
                <li key={`${c.key}-${i}`}>
                  <div>
                    <b>
                      <To href={c.href}>{c.label}</To>
                    </b>
                    <small>{c.text}</small>
                  </div>
                  {c.confidence ? <span className={`oc-conf tone-${c.confidence.tone}`}>{c.confidence.label}</span> : null}
                </li>
              ))}
            </ul>
          </div>
          <div className="ob-col" data-outcome-col="issues">
            <ColHead icon="issues">{COLUMN.issues}</ColHead>
            {row.issues.length === 0 ? (
              <p className="ob-none">{EMPTY.issues}</p>
            ) : (
              <ul className="ob-list">
                {row.issues.map((issue, i) => {
                  const [label, cls] = ISSUE_KIND[issue.kind] ?? ISSUE_KIND.FINDING;
                  return (
                    <li key={i}>
                      <span className={`oc-kind ${cls}`}>{label}</span> <To href={issue.href}>{issue.text}</To>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
          <div className="ob-col" data-outcome-col="can">
            <ColHead icon="can">{COLUMN.can}</ColHead>
            <ItemList items={row.options} empty={EMPTY.can} />
          </div>
          <div className="ob-col" data-outcome-col="hand">
            <ColHead icon="hand">{COLUMN.hand}</ColHead>
            <ItemList items={row.in_hand.map((x) => ({ ...x, note: x.state_label }))} empty={EMPTY.hand} />
          </div>
          <div className="ob-col" data-outcome-col="prev">
            <ColHead icon="prev">{COLUMN.prev}</ColHead>
            <ItemList items={row.earlier.map((x) => ({ ...x, note: x.result_label }))} empty={earlierEmpty} />
          </div>
        </div>
        {row.evidence_link ? (
          <div className="ob-foot">
            <To href={row.evidence_link.href}>{`${row.evidence_link.label} →`}</To>
          </div>
        ) : null}
      </div>
    </details>
  );
}

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** The board explainer: a native `<dialog>`, modal when supported; Escape closes and focus returns to the opener. */
function Explainer({ rows, onClose, opener }: { rows: OutcomeBoardRow[]; onClose: () => void; opener: HTMLButtonElement | null }) {
  const ref = useRef<HTMLDialogElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (dialog !== null && typeof dialog.showModal === "function" && !dialog.open) {
      try {
        dialog.showModal();
      } catch {
        dialog.setAttribute("open", "");
      }
    } else if (dialog !== null && !dialog.open) {
      dialog.setAttribute("open", "");
    }
    closeRef.current?.focus();
    return () => opener?.focus();
  }, [opener]);
  const onKeyDown = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab" || ref.current === null) return;
    const items = Array.from(ref.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (items.length === 0) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };
  return (
    <dialog
      ref={ref}
      className="ob-dialog"
      aria-labelledby="ob-dialog-title"
      onKeyDown={onKeyDown}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      data-outcome-explainer
    >
      <div className="ob-dialog-head">
        <h2 id="ob-dialog-title">{BOARD_TITLE}</h2>
        <button type="button" ref={closeRef} className="ob-dialog-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      <p className="prose">{EXPLAIN[0]}</p>
      <table className="ob-dialog-table">
        <thead>
          <tr>
            <th scope="col">Outcome</th>
            <th scope="col">What it means</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.category}>
              <td>
                <span className="oc-dname">
                  <OutcomeIcon icon={row.category} label={row.label} />
                  {row.label}
                </span>
              </td>
              <td>{row.definition}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="prose">{EXPLAIN[1]}</p>
      <p className="prose">{EXPLAIN[2]}</p>
    </dialog>
  );
}

function OutcomeBoardView({ body }: { body: OutcomeBoardBody }) {
  return (
    <>
      {body.read_state === "PARTIAL" ? (
        <p className="v69-notice" data-outcome-partial>
          {BOARD_PARTIAL}
        </p>
      ) : null}
      {body.rows.map((row) => (
        <Row key={row.category} row={row} />
      ))}
    </>
  );
}

function InfoButton({
  opener,
  onOpen,
  hidden,
}: {
  opener: RefObject<HTMLButtonElement>;
  onOpen: () => void;
  hidden?: boolean;
}) {
  if (hidden) return null;
  return (
    <button type="button" ref={opener} className="oc-info" aria-label="About this view" onClick={onOpen}>
      i
    </button>
  );
}

export function OutcomeBoard({
  client,
  siteCode,
  query,
}: {
  client: OutcomeBoardClient;
  siteCode: string;
  query: OutcomeBoardQuery;
}) {
  const key = `${siteCode}|${query.date ?? ""}|${query.from ?? ""}|${query.to ?? ""}|${query.known_at ?? ""}|${
    query.finding_id ?? ""
  }|${query.finding_revision_id ?? ""}`;
  const [read, setRead] = useState<{ key: string; read: OutcomeBoardRead } | null>(null);
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    let live = true;
    void client.getOutcomeBoard(siteCode, query).then((r) => {
      if (live) setRead({ key, read: r });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, key]);
  const current = read?.key === key ? read.read : null;
  const body = current?.status === "loaded" ? current.value : null;
  return (
    <section className="ob-board" aria-label="Outcomes at this site" data-outcome-board={current?.status ?? "loading"}>
      <div className="ob-board-head">
        <h2>{BOARD_TITLE}</h2>
        <InfoButton opener={opener} onOpen={() => setOpen(true)} hidden={body === null} />
      </div>
      {current === null ? (
        <p role="status">{BOARD_LOADING}</p>
      ) : body === null ? (
        <p role="alert" className="v69-notice">
          {BOARD_REFUSED}
        </p>
      ) : (
        <>
          <OutcomeBoardView body={body} />
          {open ? <Explainer rows={body.rows} opener={opener.current} onClose={() => setOpen(false)} /> : null}
        </>
      )}
    </section>
  );
}
