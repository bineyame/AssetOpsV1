/**
 * W5-03b E6: the EV Site Financials > Scenarios body (v6.9 `ev-scenarios`, `index.html:859-862`), from the authored
 * E5 list (`.agent/W5-03-build-spec.md` E6 card, page literals, E6 consolidated correction and
 * `.agent/W5-03b-ui-preflight-rulings.md` points 11-13 and 16).
 *
 * The mock panel is `Financial scenarios` (`Placeholder · to be designed with the owner`) with its empty block, then
 * the blue closing notice. Authored definitions are labelled what-ifs: no observed outcome, no measured comparison
 * and no create control. The frame owns the Site-name heading, tabs and Financials row.
 *
 * MOCK DEVIATION (D2) R27: persisted authored rows replace only the empty block, inside the same panel.
 * MOCK DEVIATION (D2) R15: a non-CURRENT selection adds the amber currentness (or E6 pending) notice above the panel.
 * MOCK DEVIATION (D1) R98: only the first page is read; a further page is disclosed below the table, never paged.
 */
import { useEffect, useState } from "react";
import { Badge, DataTable, Panel, RailIcon } from "../ui";
import { Notice } from "../ui/V69Layout";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import { depthStateNotice } from "./evDepthClient";
import {
  EV_SCENARIOS_MALFORMED,
  EV_SCENARIOS_UNREACHABLE,
  type EvScenarioItem,
  type EvScenarioQuery,
  type EvScenariosClient,
  type EvScenariosRead,
  type EvScenariosState,
} from "./evScenariosClient";
import "./coldScenarios.css";
import "./evScenarios.css";

export const EV_SCENARIOS_LOADING = "Loading the site's EV scenarios.";
export const EV_SCENARIOS_REFUSAL_HEADING = "EV scenarios unavailable";
export const EV_SCENARIOS_PANEL = "Financial scenarios";
export const EV_SCENARIOS_PANEL_SUBTITLE = "Placeholder · to be designed with the owner";
export const EV_SCENARIOS_EMPTY_TITLE = "No scenario defined yet";
export const EV_SCENARIOS_EMPTY_BODY =
  "A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.";
export const EV_SCENARIOS_CLOSING_NOTICE =
  "Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.";
export const EV_SCENARIOS_PENDING = "Underlying evidence is being reassessed; the authored scenario remains separate.";
export const EV_SCENARIO_STATE_BADGE: Record<EvScenarioItem["scenario_state"], string> = { DEFINED: "Defined", HISTORICAL: "Historical" };
const PANEL_HEADING_ID = "ev-scenarios-heading";

/** The E6 currentness sentence: the EV ledger sentence, except PENDING_RECOMPUTE keeps the E6 pending notice. */
export function scenariosStateNotice(state: EvScenariosState): string | null {
  return state === "PENDING_RECOMPUTE" ? EV_SCENARIOS_PENDING : depthStateNotice(state);
}

/** Ruling 12 (R98): the in-panel first-page disclosure. */
export const firstPageLine = (n: number) =>
  `Showing first ${n} authored scenarios. More exist; later pages are not available in this view.`;

const pad = (n: number) => String(n).padStart(2, "0");
/** `YYYY-MM-DD HH:MM UTC` of a wire instant (microsecond fractions truncated). */
export function utcMinute(value: string): string {
  const d = new Date(value.replace(/(\.\d{3})\d+/, "$1"));
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}

export const assumptionsLine = (a: EvScenarioItem["assumptions"]) => `${a.tariff_per_kwh} ${a.currency}/kWh gross tariff`;

function useScenarioList(client: EvScenariosClient, siteCode: string, query: EvScenarioQuery, attempt: number) {
  const key = `${siteCode}|${query.from ?? ""}|${query.to ?? ""}|${query.known_at ?? ""}|${query.scenario_at ?? ""}|${attempt}`;
  const [state, setState] = useState<{ key: string; value: ColdRead<EvScenariosRead> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.list(siteCode, query).then((value) => {
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

function ScenariosRefusal({ read, onRetry }: { read: Exclude<ColdRead<EvScenariosRead>, { status: "loaded" }>; onRetry: () => void }) {
  return (
    <div className="page-refusal" role="status" data-page-refusal="ev-scenarios">
      <p className="page-refusal__title">
        <strong>{EV_SCENARIOS_REFUSAL_HEADING}</strong>
      </p>
      {read.status === "refused" ? (
        <p data-ev-scenarios-error="">
          <code data-vocabulary-exempt="source-reference">{read.code}</code>
          {read.message === null ? null : <> {read.message}</>}
        </p>
      ) : (
        <p data-ev-scenarios-error="">{read.message ?? EV_SCENARIOS_UNREACHABLE}</p>
      )}
      <button type="button" className="button" data-ev-scenarios-retry="" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

/** One exact source reference: its own exempt span, character-broken, one per line; null prints `None`. */
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

/** E6 closure 2 `Review assumptions →` expansion: the exact stored basis, in order. */
function Basis({ item }: { item: EvScenarioItem }) {
  const basis = item.authored_basis;
  return (
    <div className="cold-scenarios-basis ev-scenarios-basis" data-ev-scenario-basis={item.id} role="region" aria-label="Authored scenario basis" tabIndex={0}>
      <dl>
        <dt>Kind</dt>
        <dd>
          <Ref value={item.kind} />
        </dd>
        <dt>Assumptions</dt>
        <dd>
          {(["tariff_per_kwh", "currency"] as const).map((key) => (
            <span key={key} className="cold-scenarios-line" data-vocabulary-exempt="source-reference" data-ev-scenario-assumption={key}>
              {`${key}: ${item.assumptions[key]}`}
            </span>
          ))}
        </dd>
        <dt>Window</dt>
        <dd>
          <span className="cold-scenarios-ref" data-vocabulary-exempt="source-reference">{`${basis.from} – ${basis.to}`}</span>
        </dd>
        <dt>Evidence cutoff</dt>
        <dd>
          <Ref value={basis.cutoff} />
        </dd>
        <dt>Assessment revision</dt>
        <dd>
          <Ref value={basis.assessment_revision_id} />
        </dd>
        <dt>Session revisions</dt>
        <dd>
          <RefList values={basis.session_revision_ids} />
        </dd>
        <dt>Accepted evidence</dt>
        <dd>
          <span className="cold-scenarios-line" data-ev-scenario-evidence-count="">{`${basis.accepted_evidence_ids.length} records`}</span>
          {basis.accepted_evidence_ids.map((id) => (
            <Ref key={id} value={id} />
          ))}
        </dd>
        <dt>Foundation revision</dt>
        <dd>
          <Ref value={basis.foundation_revision_id} />
        </dd>
        <dt>Consequence revision</dt>
        <dd>
          <Ref value={basis.consequence_revision_id} />
        </dd>
        <dt>Tariff revision</dt>
        <dd>
          <Ref value={basis.tariff_revision_id} />
        </dd>
        <dt>Source classification</dt>
        <dd>
          <Ref value={basis.source_provenance.classification} />
        </dd>
        <dt>Revision</dt>
        <dd>
          <Ref value={item.revision_id} />
        </dd>
      </dl>
    </div>
  );
}

function ScenarioRows({ items }: { items: EvScenarioItem[] }) {
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
            <tr key={item.revision_id} data-ev-scenario-row={item.id}>
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
                  data-ev-scenario-review={item.id}
                  onClick={() => toggle(item.revision_id)}
                >
                  Review assumptions →
                </button>
              </td>
              <td>{utcMinute(item.recorded_at)}</td>
              <td>
                <Badge tone="neutral">{EV_SCENARIO_STATE_BADGE[item.scenario_state]}</Badge>
              </td>
            </tr>,
          ];
          if (expanded) {
            rows.push(
              <tr key={`${item.revision_id}-basis`} className="cold-scenarios-expansion" data-ev-scenario-expansion={item.id}>
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
    <div className="cold-scenarios-empty" data-ev-scenarios-empty="">
      <span className="cold-scenarios-empty__icon" aria-hidden="true">
        <RailIcon name="evidence" />
      </span>
      <h3>{EV_SCENARIOS_EMPTY_TITLE}</h3>
      <p>{EV_SCENARIOS_EMPTY_BODY}</p>
    </div>
  );
}

function ScenariosBody({ read }: { read: EvScenariosRead }) {
  const state = read.selection.state;
  const notice = scenariosStateNotice(state);
  return (
    <>
      {notice === null ? null : <Notice data={{ "data-ev-scenarios-state-notice": state }}>{notice}</Notice>}
      <Panel heading={EV_SCENARIOS_PANEL} headingId={PANEL_HEADING_ID} description={EV_SCENARIOS_PANEL_SUBTITLE} className="cold-scenarios-panel">
        {read.items.length === 0 ? (
          <EmptyBlock />
        ) : (
          <>
            <ScenarioRows items={read.items} />
            {read.next_cursor === null ? null : (
              <p className="muted" data-ev-scenarios-first-page="">
                {firstPageLine(read.items.length)}
              </p>
            )}
          </>
        )}
      </Panel>
      <Notice tone="blue" data={{ "data-ev-scenarios-closing-notice": "" }}>
        <RailIcon name="info" />
        <p>{EV_SCENARIOS_CLOSING_NOTICE}</p>
      </Notice>
    </>
  );
}

export interface EvScenariosProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  window: ColdWindowQuery;
  /** The authored clock, from the address; null reads at the current authored time. */
  scenarioAt: string | null;
  client: EvScenariosClient;
}

/** The EV Scenarios panel, its currentness notice and the closing notice (the frame adds heading and tabs). */
export function EvScenarios({ siteCode, window, scenarioAt, client }: EvScenariosProps) {
  const [attempt, setAttempt] = useState(0);
  const read = useScenarioList(client, siteCode, { ...window, scenario_at: scenarioAt }, attempt);
  if (read === null) return <p className="prose">{EV_SCENARIOS_LOADING}</p>;
  if (read.status !== "loaded") return <ScenariosRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />;
  return <ScenariosBody read={read.value} />;
}

export { EV_SCENARIOS_MALFORMED, EV_SCENARIOS_UNREACHABLE };
