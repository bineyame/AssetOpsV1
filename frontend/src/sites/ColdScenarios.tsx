/**
 * W5-01b C5: the cold Site Financials > Scenarios body (v6.9 `cold-scenarios`), from the authored C4 list
 * (`.agent/W5-01-build-spec.md` C5 card, readiness pass 3, closure 2 and the C5 mock and UI closure P-C5-1..22).
 *
 * The mock panel is `Financial scenarios` (`Placeholder · to be designed with the owner`) with its evidence-icon
 * empty block, then the blue closing notice. Authored definitions are labelled what-ifs: no observed outcome, no
 * measured comparison and no create control. The frame owns the Site-name heading, tabs and Financials row.
 */
import { useEffect, useState } from "react";
import { Badge, DataTable, Panel, RailIcon } from "../ui";
import { Notice } from "../ui/V69Layout";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import { classificationWord } from "./coldAssessmentWords";
import type { ColdScenarioItem, ColdScenarioQuery, ColdScenariosClient, ColdScenariosRead, ColdScenariosState } from "./coldScenariosClient";
import { RequestedWindowBar, SelectedWindowBar } from "./coldSiteViews";
import "./coldScenarios.css";

export const SCENARIOS_LOADING = "Loading the site's cold scenarios.";
export const SCENARIOS_UNREACHABLE = "The cold scenarios read could not be reached.";
export const SCENARIOS_MALFORMED = "The cold scenarios read answered in an unexpected shape.";
export const SCENARIOS_REFUSAL_HEADING = "Cold scenarios unavailable";
export const SCENARIOS_PANEL = "Financial scenarios";
export const SCENARIOS_PANEL_SUBTITLE = "Placeholder · to be designed with the owner";
export const SCENARIOS_EMPTY_TITLE = "No scenario defined yet";
export const SCENARIOS_EMPTY_BODY =
  "A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.";
export const SCENARIOS_CLOSING_NOTICE =
  "Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.";
/** C5 closure 2 "Currentness": the amber notice above the panel by `selection.state`; `CURRENT` has none. */
export const SCENARIOS_STATE_NOTICE: Record<Exclude<ColdScenariosState, "CURRENT">, string> = {
  PENDING_RECOMPUTE: "Underlying evidence is being reassessed; the authored scenario remains separate.",
  HISTORICAL: "Read at an earlier evidence cutoff; newer evidence exists.",
  STALE_SOURCE: "The selected source is stale for this window.",
  UNKNOWN: "No selected cold assessment covers this window yet.",
};
export const SCENARIO_STATE_PILL: Record<ColdScenarioItem["scenario_state"], string> = {
  DEFINED: "Defined",
  HISTORICAL: "Historical",
};
export const SCENARIO_KIND_WORDS: Record<ColdScenarioItem["kind"], string> = { STOCK_VALUE_CONTEXT: "Stock value context" };
const ASSUMPTION_WORDS: [keyof ColdScenarioItem["assumptions"], string][] = [
  ["stock_quantity", "Stock quantity"],
  ["stock_unit", "Stock unit"],
  ["unit_value", "Unit value"],
  ["currency", "Currency"],
];
const PANEL_HEADING_ID = "cold-scenarios-heading";

const pad = (n: number) => String(n).padStart(2, "0");
/** `YYYY-MM-DD HH:MM UTC`; a null clock is never formatted as a date. */
export function utcMinute(value: string | null): string {
  if (value === null) return "None";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}

export const assumptionsLine = (a: ColdScenarioItem["assumptions"]) =>
  `${a.stock_quantity} ${a.stock_unit} at ${a.unit_value} ${a.currency} per ${a.stock_unit}`;
export const recordsCount = (n: number) => (n === 1 ? "1 record" : `${n} records`);

type Settled = { key: string; value: ColdRead<ColdScenariosRead> };

function useScenarioPage(client: ColdScenariosClient, siteCode: string, query: ColdScenarioQuery, cursor: string | null, attempt: number) {
  const key = `${siteCode}|${query.from ?? ""}|${query.to ?? ""}|${query.known_at ?? ""}|${query.scenario_at ?? ""}|${cursor ?? ""}|${attempt}`;
  const [state, setState] = useState<Settled | null>(null);
  useEffect(() => {
    let active = true;
    void client.list(siteCode, query, cursor).then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // The key names exactly what is read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state !== null && state.key === key ? state.value : null;
}

function ScenariosRefusal({ read, onRetry }: { read: Exclude<ColdRead<ColdScenariosRead>, { status: "loaded" }>; onRetry: () => void }) {
  return (
    <div className="page-refusal" role="status" data-page-refusal="cold-scenarios">
      <p className="page-refusal__title">
        <strong>{SCENARIOS_REFUSAL_HEADING}</strong>
      </p>
      {read.status === "refused" ? (
        <p data-cold-scenarios-error>
          <code data-vocabulary-exempt="source-reference">{read.code}</code>
          {read.message === null ? null : <> {read.message}</>}
        </p>
      ) : (
        <p data-cold-scenarios-error>{read.message === null ? SCENARIOS_UNREACHABLE : SCENARIOS_MALFORMED}</p>
      )}
      <button type="button" className="button" data-cold-retry onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

/** One exact source reference: its own exempt span, character-broken, one per line. */
function Ref({ value }: { value: string | null }) {
  if (value === null) return <span className="cold-scenarios-ref">None</span>;
  return (
    <span className="cold-scenarios-ref" data-vocabulary-exempt="source-reference">
      {value}
    </span>
  );
}

function RefList({ values }: { values: string[] }) {
  if (values.length === 0) return <span className="cold-scenarios-ref">None</span>;
  return (
    <>
      {values.map((value) => (
        <Ref key={value} value={value} />
      ))}
    </>
  );
}

/** C5 closure 2 `Review assumptions →` expansion: the exact authored basis, in order. */
function Basis({ item }: { item: ColdScenarioItem }) {
  const basis = item.authored_basis;
  return (
    <div className="cold-scenarios-basis" data-scenario-basis={item.id} role="region" aria-label="Authored scenario basis" tabIndex={0}>
      <dl>
        <dt>Kind</dt>
        <dd>{SCENARIO_KIND_WORDS[item.kind]}</dd>
        <dt>Assumptions</dt>
        <dd>
          {ASSUMPTION_WORDS.map(([key, word]) => (
            <span key={key} className="cold-scenarios-line" data-scenario-assumption={key}>
              {word}: {item.assumptions[key]}
            </span>
          ))}
        </dd>
        <dt>Window</dt>
        <dd>
          <span className="cold-scenarios-line">
            {basis.from} – {basis.to}
          </span>
        </dd>
        <dt>Evidence cutoff</dt>
        <dd>
          <span className="cold-scenarios-line">{basis.cutoff ?? "None"}</span>
        </dd>
        <dt>Assessment revisions</dt>
        <dd>
          <RefList values={basis.assessment_revision_ids} />
        </dd>
        <dt>Accepted evidence</dt>
        <dd>
          <span className="cold-scenarios-line" data-scenario-evidence-count>
            {recordsCount(basis.accepted_evidence_ids.length)}
          </span>
          {basis.accepted_evidence_ids.map((id) => (
            <Ref key={id} value={id} />
          ))}
        </dd>
        <dt>Foundation revision</dt>
        <dd>
          <Ref value={basis.foundation_revision_id} />
        </dd>
        <dt>Source classification</dt>
        <dd>{classificationWord(basis.source_provenance.classification)}</dd>
        <dt>Revision</dt>
        <dd>
          <Ref value={item.revision_id} />
        </dd>
      </dl>
    </div>
  );
}

function ScenarioRows({ items }: { items: ColdScenarioItem[] }) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const toggle = (id: string) =>
    setOpen((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  return (
    <DataTable labelledBy={PANEL_HEADING_ID}>
      <thead>
        <tr>
          <th scope="col">Authored scenario</th>
          <th scope="col">Assumptions</th>
          <th scope="col">Basis</th>
          <th scope="col">Defined at</th>
          <th scope="col">State</th>
        </tr>
      </thead>
      <tbody>
        {items.flatMap((item) => {
          const expanded = open.has(item.revision_id);
          const rows = [
            <tr key={item.revision_id} data-scenario-row={item.id}>
              <th scope="row">
                <span className="cold-scenarios-line" data-vocabulary-exempt="user-owned">
                  {item.name}
                </span>
                <span className="cold-scenarios-line cold-scenarios-code">
                  <span data-vocabulary-exempt="source-reference">{item.code}</span> revision {item.revision_no}
                </span>
              </th>
              <td>{assumptionsLine(item.assumptions)}</td>
              <td>
                <span className="cold-scenarios-line">Selected evidence through {utcMinute(item.authored_basis.cutoff)}</span>
                <button
                  type="button"
                  className="link-button"
                  aria-expanded={expanded}
                  data-scenario-review={item.id}
                  onClick={() => toggle(item.revision_id)}
                >
                  Review assumptions →
                </button>
              </td>
              <td>{utcMinute(item.recorded_at)}</td>
              <td>
                <Badge tone="neutral">{SCENARIO_STATE_PILL[item.scenario_state]}</Badge>
              </td>
            </tr>,
          ];
          if (expanded) {
            rows.push(
              <tr key={`${item.revision_id}-basis`} className="cold-scenarios-expansion" data-scenario-expansion={item.id}>
                <td colSpan={5}>
                  <Basis item={item} />
                </td>
              </tr>,
            );
          }
          return rows;
        })}
      </tbody>
    </DataTable>
  );
}

/** The mock's evidence-icon empty block, verbatim. */
function EmptyBlock() {
  return (
    <div className="cold-scenarios-empty" data-scenarios-empty>
      <span className="cold-scenarios-empty__icon" aria-hidden="true">
        <RailIcon name="evidence" />
      </span>
      <h3>{SCENARIOS_EMPTY_TITLE}</h3>
      <p>{SCENARIOS_EMPTY_BODY}</p>
    </div>
  );
}

/**
 * P-C5-12/19/20/22 pager. `Next` follows `next_cursor` (disabled without one); `First page` clears the cursor.
 * W5-01b Q-C5b-2: the `{page} of {total pages}` counter follows `Next`; the total is the C4 `total_pages`.
 */
function Pager({
  hasNext,
  onFirst,
  onNext,
  first,
  page,
  totalPages,
}: {
  hasNext: boolean;
  onFirst: () => void;
  onNext: () => void;
  first: boolean;
  page: number;
  totalPages: number;
}) {
  return (
    <nav aria-label="Scenario pages" className="cold-scenarios-pages" data-scenarios-pages>
      <button type="button" className="link-button" data-scenarios-first disabled={first} onClick={onFirst}>
        First page
      </button>
      <button type="button" className="link-button" data-scenarios-next disabled={!hasNext} onClick={onNext}>
        Next
      </button>
      <span data-scenarios-page-count>{page} of {totalPages}</span>
    </nav>
  );
}

function ScenariosBody({
  read,
  cursors,
  onFirst,
  onNext,
}: {
  read: ColdScenariosRead;
  cursors: string[];
  onFirst: () => void;
  onNext: (cursor: string) => void;
}) {
  const state = read.selection.state;
  const empty = read.items.length === 0 && cursors.length === 0;
  return (
    <>
      <SelectedWindowBar read={read} />
      <p className="cold-scenarios-through" data-scenarios-through>
        Scenarios created through <time dateTime={read.scenario_at}>{utcMinute(read.scenario_at)}</time>
      </p>
      {/* MOCK DEVIATION — currentness notice (P-C5-1..5): the mock has only its blue closing notice; a pending, stale,
          historical or unknown selection adds this amber notice above the panel so an old basis stays visible. */}
      {state === "CURRENT" ? null : <Notice data={{ "data-scenarios-state-notice": state }}>{SCENARIOS_STATE_NOTICE[state]}</Notice>}
      <Panel heading={SCENARIOS_PANEL} headingId={PANEL_HEADING_ID} description={SCENARIOS_PANEL_SUBTITLE} className="cold-scenarios-panel">
        {empty ? (
          <EmptyBlock />
        ) : (
          <>
            {/* MOCK DEVIATION — authored rows (P-C5-1..5): the mock panel has only an empty block; real C4 definitions
                replace it with this table, its disclosure and pager inside the same titled and subtitled panel. */}
            <ScenarioRows key={cursors.join("|")} items={read.items} />
            <Pager
              hasNext={read.next_cursor !== null}
              first={cursors.length === 0}
              onFirst={onFirst}
              onNext={() => read.next_cursor !== null && onNext(read.next_cursor)}
              page={cursors.length + 1}
              totalPages={read.total_pages}
            />
          </>
        )}
      </Panel>
      <Notice tone="blue" data={{ "data-scenarios-closing-notice": "" }}>
        {/* Q-C5b-6 info icon held: tools/checks/shell-overflow.ps1 rule 5 refuses an svg element in this page module (open question Q-C5c-1). */}
        {SCENARIOS_CLOSING_NOTICE}
      </Notice>
    </>
  );
}

export interface ColdScenariosProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  window: ColdWindowQuery;
  /** The authored clock, from the address; null reads at the current authored time. */
  scenarioAt: string | null;
  client: ColdScenariosClient;
}

/** The cold Scenarios panel, its currentness notice and the closing notice (the frame adds heading and tabs). */
export function ColdScenarios({ siteCode, window, scenarioAt, client }: ColdScenariosProps) {
  const [attempt, setAttempt] = useState(0);
  /** The cursors followed from the first page; the last one is the current page's. */
  const [cursors, setCursors] = useState<string[]>([]);
  const query: ColdScenarioQuery = { ...window, scenario_at: scenarioAt };
  const cursor = cursors.length === 0 ? null : cursors[cursors.length - 1];
  const read = useScenarioPage(client, siteCode, query, cursor, attempt);
  if (read === null) return <p className="prose">{SCENARIOS_LOADING}</p>;
  if (read.status !== "loaded") {
    return (
      <>
        <RequestedWindowBar
          window={window}
          refusal={{ sentence: SCENARIOS_REFUSAL_HEADING, retry: true, key: read.status === "refused" && read.httpStatus === 422 ? "invalid-window" : "unavailable" }}
        />
        <ScenariosRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />
      </>
    );
  }
  return (
    <ScenariosBody
      read={read.value}
      cursors={cursors}
      onFirst={() => setCursors([])}
      onNext={(next) => setCursors((current) => [...current, next])}
    />
  );
}
