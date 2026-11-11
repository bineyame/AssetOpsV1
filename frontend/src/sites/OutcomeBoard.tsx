import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { Link } from "react-router-dom";

import { ExplainerDialog } from "../blocks/Dialog";
import { EvidenceTrace, WhyButton } from "../blocks/EvidenceTrace";
import { OutcomeRowHead } from "../blocks/OutcomeRow";
import { defaultChainClient, type ChainClient } from "./chainClient";

import { OutcomeGlyph, type OutcomeGlyphName } from "./componentIcons";
import { DataTable } from "../ui";
import { OutcomeIcon } from "./outcomeCategories";
import { money2 } from "../ui/money";
import type {
  OutcomeBoardBody,
  OutcomeBoardClient,
  OutcomeBoardQuery,
  OutcomeBoardRead,
  OutcomeBoardRow,
  OutcomeLinkItem,
  OutcomeMoney,
} from "./outcomeBoardClient";
import { useLinkFor, type Ref } from "./chainRef";
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
/** WALK1-1 (WN-2, R673): when the board names days without assessed readings, "none" is a claim on checked days only. */
export const EMPTY_ISSUES_CHECKED = "None found on days with complete readings";
/** WALK1-1 fix round (M1): Findings next to the unchecked days were left out, so "none" cannot be claimed. */
export const EMPTY_ISSUES_WITHHELD = "None shown yet";

/** §B.1 issue kinds: label and the mock `.oc-kind` class (ruling B-Q29: `finding` and `gap` are neutral). */
export const ISSUE_KIND: Record<string, [string, string]> = {
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
  // MOCK DEVIATION (OUT-D review L1, R580): the mock has no declared objectives, so it has no such paragraph.
  "A declared objective is a target set for this demonstration so the status can be shown. It is not the customer's target.",
] as const;

/**
 * Ruling B-Q14: the backend sends the amount unformatted. This is the mini overview money slot's own text
 * (`SiteWindowOverview.tsx` `Money`: "{low} to {high} {currency}"); one amount when both bounds are equal (EV Grow).
 */
export function boardMoneyText(money: OutcomeMoney | null): string | null {
  if (money === null || money.amount_low === null || money.amount_high === null) return null;
  // WALK1-6 D3 (R696): every board money amount shows two decimals by the shared money2 rule.
  const low = money2(String(money.amount_low));
  const high = money2(String(money.amount_high));
  const amount = low === high ? low : `${low} to ${high}`;
  return money.currency ? `${amount} ${money.currency}` : amount;
}

export function countsText(issues: number, inHand: number, checkedDaysOnly: boolean | "withheld" = false): string {
  const none =
    checkedDaysOnly === "withheld"
      ? "No open issues shown yet"
      : checkedDaysOnly
        ? "No open issues on days with complete readings"
        : "No open issues";
  const head = issues === 0 ? none : `${issues} issue${issues === 1 ? "" : "s"}`;
  return inHand > 0 ? `${head} · ${inHand} in hand` : head;
}

/** CH5a2-R4(c): a link renders only from its `link_ref`; a body without one renders no link. */
function To({ link, children }: { link: Ref | null | undefined; children: ReactNode }) {
  const href = useLinkFor()(link);
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

const GROW_PARTS = [["kpi", "Target"], ["potential", "Potential"], ["earnings", "Estimated income"]] as const;

/**
 * CH-6a3 R2b (H4): `div.ob-grow > div.ob-part` x3, each `span.ob-plabel + b (per line) + small.ob-days`, from the
 * server's per-part `days_line`; a part never shows a neighbour's line. All three parts always show (the server fills
 * an absent one). MOCK DEVIATION: MD-CH6-1 (R11 basis), MD-CH6-2 (the section A4 lines differ from the v70 mock
 * examples), MD-CH6-3 (`target_note` in the subline), MD-CH6-7 (no Potential days line when the study has no day
 * grades); register: mock-departure-register.md, mock: v70/index.html:213-215, 238, 420.
 */
function GrowParts({ row }: { row: OutcomeBoardRow }) {
  const nodes = row.nodes;
  if (!nodes || GROW_PARTS.every(([k]) => !nodes[k])) return null;
  return (
    <div className="ob-grow" data-outcome-grow aria-label="Grow revenue in three parts">
      {GROW_PARTS.map(([k, label]) => {
        const c = nodes[k];
        const lines = (c?.text ?? "").split("\n");
        return (
          // CH6b2-R Q6: the removed Grow "Opportunity" chip's words move onto the Potential part.
          <div
            key={k}
            className="ob-part"
            data-outcome-part={k}
            title={k === "potential" ? (row.potential?.text ?? undefined) : undefined}
          >
            <span className="ob-plabel">{label}</span>
            {lines.map((l, i) => (
              <b key={i}>{l}</b>
            ))}
            {c?.days_line ? <small className="ob-days" data-outcome-days>{c.days_line}</small> : null}
          </div>
        );
      })}
    </div>
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
  items: (OutcomeLinkItem & { note?: string | null; detail?: string | null })[];
  empty: string;
}) {
  if (items.length === 0) return <p className="ob-none">{empty}</p>;
  return (
    <ul className="ob-list">
      {items.map((item, i) => (
        <li key={i}>
          <To link={item.link_ref}>{item.text}</To>
          {item.note ? <> <span className="oc-state">{item.note}</span></> : null}
          {item.detail ? <> <small>{item.detail}</small></> : null}
        </li>
      ))}
    </ul>
  );
}

type OnWhy = (row: OutcomeBoardRow, button: HTMLButtonElement) => void;

function Row({ row, gaps = false, onWhy }: { row: OutcomeBoardRow; gaps?: boolean | "withheld"; onWhy?: OnWhy }) {
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
  const text = money !== null && row.headline ? `${money} ${row.headline}` : (row.headline ?? money);
  // CH-6b2 (§B3, CH6b2-R Q6, mock v70 `outcomeRow`): the Grow `ob-val` is the server's `grow_headline`; the three
  // parts sit in `ob-body`, and the Grow row has no separate "Opportunity" chip (its words are the Potential part).
  const grow = row.category === "GROW_REVENUE" && !!row.nodes;
  const headline = grow ? (row.grow_headline ?? text) : text;
  const earlierEmpty = "earlier_empty_text" in row ? (row.earlier_empty_text ?? "") : EMPTY.prev;
  return (
    <details className={`ob tone-${row.tone}`} open={row.state === "NEEDS_ATTENTION"} {...data}>
      <summary className="ob-sum">
        <Name row={row} />
        <span className={`oc-chip tone-${row.tone}`}>{row.state_label}</span>
        {row.potential && !grow ? (
          // WALK1-3b (R690): the opportunity beside the KPI state, never folded into it.
          <span className="oc-chip tone-green" data-outcome-potential title={row.potential.text ?? undefined}>
            {row.potential.label}
          </span>
        ) : null}
        {/* CH-5b3: the value and "Why?" (every row but NOT_MEASURED, CH5b3-R Q6); MD-CH5b-2/4 in OutcomeRow. */}
        <OutcomeRowHead
          headline={headline}
          why={onWhy ? <WhyButton label={row.label} onOpen={(button) => onWhy(row, button)} /> : null}
        />
        <span className="ob-counts" data-outcome-counts>
          {countsText(row.counts.issues, row.counts.in_hand, gaps)}
        </span>
      </summary>
      <div className="ob-body">
        {grow ? <GrowParts row={row} /> : null}
        {row.subline ? <p className="ob-sub">{row.subline}</p> : null}
        {row.target_note ? <p className="ob-sub" data-outcome-target-note>{row.target_note}</p> : null}
        {row.must_not_harm ? (
          <p className="ob-guard" data-outcome-guard>
            <OutcomeGlyph name="guard" className="oc-colic" size={14} />
            <span>
              <b>Must not harm</b> <To link={row.must_not_harm.link_ref}>{row.must_not_harm.text}</To>
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
                      <To link={c.link_ref}>{c.label}</To>
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
              <p className="ob-none">{gaps === "withheld" ? EMPTY_ISSUES_WITHHELD : gaps ? EMPTY_ISSUES_CHECKED : EMPTY.issues}</p>
            ) : (
              <ul className="ob-list">
                {row.issues.map((issue, i) => {
                  const [label, cls] = ISSUE_KIND[issue.kind] ?? ISSUE_KIND.FINDING;
                  return (
                    <li key={i}>
                      <span className={`oc-kind ${cls}`}>{label}</span> <To link={issue.link_ref}>{issue.text}</To>
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
            <To link={row.evidence_link.link_ref}>{`${row.evidence_link.label} →`}</To>
          </div>
        ) : null}
      </div>
    </details>
  );
}

/** The board explainer (mock `explainBoard`). */
function Explainer({ rows, onClose, opener }: { rows: OutcomeBoardRow[]; onClose: () => void; opener: HTMLButtonElement | null }) {
  return (
    <ExplainerDialog title={BOARD_TITLE} titleId="ob-dialog-title" onClose={onClose} opener={opener} marker="data-outcome-explainer">
      <p className="prose">{EXPLAIN[0]}</p>
      <div className="ob-dialog-table">
        <DataTable>
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
        </DataTable>
      </div>
      <p className="prose">{EXPLAIN[1]}</p>
      <p className="prose">{EXPLAIN[2]}</p>
      <p className="prose">{EXPLAIN[3]}</p>
    </ExplainerDialog>
  );
}

function OutcomeBoardView({ body, onWhy }: { body: OutcomeBoardBody; onWhy?: OnWhy }) {
  return (
    <>
      {body.read_state === "PARTIAL" ? (
        <p className="v69-notice" data-outcome-partial>
          {BOARD_PARTIAL}
        </p>
      ) : null}
      {body.rows.map((row) => (
        <Row
          key={row.category}
          row={row}
          gaps={body.finding_gaps ? (body.finding_gaps.withheld === true ? "withheld" : true) : false}
          onWhy={onWhy}
        />
      ))}
      {/* IDX-GAPS (R610): the backend's note naming the days without assessed readings; never counted as none. */}
      {body.finding_gaps ? (
        <p className="v69-chart-note" data-outcome-finding-gaps>
          {body.finding_gaps.text}
        </p>
      ) : null}
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
  onRead,
  why = defaultChainClient,
}: {
  client: OutcomeBoardClient;
  siteCode: string;
  query: OutcomeBoardQuery;
  /** POLISH P-10 (Addendum 12 Q1): told the read once it resolves for the current key; no extra fetch. */
  onRead?: (read: OutcomeBoardRead) => void;
  /** CH-5b3 (CH5b3-R Q2): the "Why?" chain client; the module default unless a test passes one. */
  why?: ChainClient;
}) {
  const key = `${siteCode}|${query.date ?? ""}|${query.from ?? ""}|${query.to ?? ""}|${query.known_at ?? ""}|${
    query.finding_id ?? ""
  }|${query.finding_revision_id ?? ""}`;
  const [read, setRead] = useState<{ key: string; read: OutcomeBoardRead } | null>(null);
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement>(null);
  const [whyOpen, setWhyOpen] = useState<{ row: OutcomeBoardRow; button: HTMLButtonElement } | null>(null);
  useEffect(() => {
    let live = true;
    void client.getOutcomeBoard(siteCode, query).then((r) => {
      if (!live) return;
      setRead({ key, read: r });
      onRead?.(r);
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
          <OutcomeBoardView body={body} onWhy={(row, button) => setWhyOpen({ row, button })} />
          {open ? <Explainer rows={body.rows} opener={opener.current} onClose={() => setOpen(false)} /> : null}
          {whyOpen ? (
            <EvidenceTrace
              key={`${key}|${whyOpen.row.category}`}
              label={whyOpen.row.label}
              load={() => why.getSiteWhy(siteCode, whyOpen.row.category, query)}
              opener={whyOpen.button}
              onClose={() => setWhyOpen(null)}
            />
          ) : null}
        </>
      )}
    </section>
  );
}
