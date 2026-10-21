/**
 * W4-03 unit 6a: mini Site > Financials > Scenarios (`/sites/:siteId/financials/scenarios`, v69 `scenarios`).
 *
 * Read-only (closure 1): the persisted authored what-ifs of this Site from `mini-scenarios-1`. The first request
 * omits both bounds; the page then shows `Scenarios created through {read time}` (the returned effective `window.to`
 * minus one microsecond) and carries the returned `from`/`to`/`known_at` in its address for every cursor page and
 * reload (closure 4 S15). A row's `url:null` is the noninteractive `Scenario detail unavailable`; creation is the
 * noninteractive `Scenario creation unavailable`. The notice is always shown.
 */
import { useEffect, useRef, useState } from "react";
import { DataTable, Panel, RailIcon } from "../ui";
import { Notice } from "../ui/V69Layout";
import {
  microsecondBefore,
  type DecisionRead,
  type MiniDecisionsClient,
  type ScenarioAssumption,
  type ScenarioListBody,
  type ScenarioRow,
  type ScenarioScope,
} from "./miniDecisionsClient";
import "./w4-mini-decisions.css";

export const SCENARIOS_HEADING_ID = "mini-scenarios-heading";
export const SCENARIOS_NOTICE =
  "Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.";
export const SCENARIOS_PANEL_DESCRIPTION = "Declared scenarios are separate from measured results.";
export const SCENARIOS_EMPTY = {
  heading: "No scenario defined yet",
  body: "A scenario compares a declared what-if with the measured case. None has been defined for this site.",
} as const;

/** PR-12.1: the Physical basis cell states the pinned count; the exact IDs are in the disclosure below the table. */
export function pinnedCount(n: number): string {
  return `${n} pinned renewable revision${n === 1 ? "" : "s"}`;
}
export const PINNED_DISCLOSURE_ID = "mini-scenarios-pinned";

const KIND_WORDS: Record<string, string> = {
  STOP_SOC: "Stop setting",
  PRODUCTIVE_LOAD: "Productive load",
  TARIFF_ONLY: "Tariff only",
  OTHER: "Other",
};

const CALCULATION_WORDS: Record<string, string> = {
  NO_CALCULATION: "No calculation",
  ENERGY_ONLY: "Energy only",
  GROSS_SCENARIO: "Gross scenario",
  WITHHELD: "Withheld",
};

/** Closure 1: exact decimal money, half-even to two minor units; USD as `$`, any other code before the amount. */
export function scenarioMoney(amount: string, currency: string): string {
  const m = /^(-?)(\d+)(?:\.(\d+))?$/.exec(amount);
  if (m === null) return `${currency} ${amount}`;
  const [, sign, whole, frac = ""] = m;
  let cents = BigInt(whole) * 100n + BigInt((frac + "00").slice(0, 2));
  const rest = frac.slice(2);
  if (rest !== "" && /[1-9]/.test(rest)) {
    const half = rest[0] > "5" || (rest[0] === "5" && /[1-9]/.test(rest.slice(1)));
    const tie = rest[0] === "5" && !/[1-9]/.test(rest.slice(1));
    if (half || (tie && cents % 2n === 1n)) cents += 1n;
  }
  const text = `${cents / 100n}.${String(cents % 100n).padStart(2, "0")}`;
  const signed = sign === "-" && cents !== 0n ? "-" : "";
  return currency === "USD" ? `${signed}$${text}` : `${signed}${currency} ${text}`;
}

/** One typed assumption as authored: key, decimal (or declared text) and unit. */
function declared(a: ScenarioAssumption): string {
  return `${a.key} ${a.value ?? ""}${a.unit ? ` ${a.unit}` : ""}`.trim();
}

function illustrative(row: ScenarioRow): string {
  if (row.calculation_state === "GROSS_SCENARIO" && row.gross_sales !== null) {
    return `${scenarioMoney(row.gross_sales.amount, row.gross_sales.currency)} gross sales scenario per eligible window, before costs`;
  }
  if (row.calculation_state === "ENERGY_ONLY" && row.energy_kwh !== null) {
    return `${row.energy_kwh} kWh energy scenario per eligible window; gross sales unknown`;
  }
  return "Cannot calculate from the selected evidence";
}

function Rows({ rows }: { rows: ScenarioRow[] }) {
  // PR-12.1: one disclosure outside the row layout; closed it is `hidden` and adds no height to any row.
  const [inspected, setInspected] = useState<string | null>(null);
  const open = rows.find((r) => r.id === inspected && r.pinned_mini_revision_ids.length > 0) ?? null;
  return (
    <div className="mini-scenarios-table" data-scenarios-table>
      <DataTable labelledBy={SCENARIOS_HEADING_ID}>
        <colgroup>
          <col style={{ width: "20%" }} />
          <col style={{ width: "24%" }} />
          <col style={{ width: "20%" }} />
          <col style={{ width: "22%" }} />
          <col style={{ width: "14%" }} />
        </colgroup>
        <thead>
          <tr>
            <th scope="col">Scenario</th>
            <th scope="col">Declared change</th>
            <th scope="col">Physical basis</th>
            <th scope="col">Illustrative result</th>
            <th scope="col">State</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} data-scenario-row={row.id} data-scenario-revision={row.revision_id}>
              <th scope="row">
                <span data-scenario-name>{row.name}</span>
                <small>
                  {" "}
                  · {KIND_WORDS[row.kind] ?? row.kind} · {row.code}
                </small>
                {row.url === null ? (
                  <span className="mini-scenarios-gap" data-scenario-detail-unavailable>
                    Scenario detail unavailable
                  </span>
                ) : null}
              </th>
              <td data-scenario-declared>{row.assumptions.map(declared).join("; ")}</td>
              <td data-scenario-basis>
                {row.pinned_mini_revision_ids.length === 0 ? (
                  "No measured basis pinned"
                ) : (
                  <>
                    <span data-scenario-pinned-count>{pinnedCount(row.pinned_mini_revision_ids.length)}</span>{" "}
                    <button
                      type="button"
                      className="link-button mini-scenarios-inspect"
                      aria-expanded={open?.id === row.id}
                      aria-controls={PINNED_DISCLOSURE_ID}
                      data-scenario-inspect={row.id}
                      onClick={() => setInspected(open?.id === row.id ? null : row.id)}
                    >
                      Inspect pinned revisions
                    </button>
                  </>
                )}
              </td>
              <td data-scenario-result>{illustrative(row)}</td>
              <td data-scenario-state>
                {row.scenario_state === "HISTORICAL" ? "Historical basis" : "Defined"} ·{" "}
                {CALCULATION_WORDS[row.calculation_state] ?? row.calculation_state}
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      <div
        id={PINNED_DISCLOSURE_ID}
        className="mini-scenarios-pinned"
        role="region"
        aria-label={open === null ? "Pinned revisions" : `Pinned revisions of ${open.name}`}
        tabIndex={open === null ? undefined : 0}
        hidden={open === null}
        data-scenario-pinned={open?.id ?? ""}
      >
        {open === null ? null : (
          <ul className="mini-scenarios-pins">
            {open.pinned_mini_revision_ids.map((pin) => (
              <li key={pin}>
                <code>{pin}</code>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Loaded({
  body,
  scope,
  onScope,
}: {
  body: ScenarioListBody;
  scope: ScenarioScope;
  onScope: (next: ScenarioScope) => void;
}) {
  const through = body.window.to === null ? null : microsecondBefore(body.window.to);
  const bound = { from: body.window.from, to: body.window.to, known_at: body.window.known_at };
  return (
    <div data-scenarios-loaded>
      {through === null ? null : (
        <p className="mini-scenarios-through" data-scenarios-through>
          Scenarios created through {through}
        </p>
      )}
      {body.rows.length === 0 ? (
        <>
          <div className="mini-scenarios-empty" data-scenarios-empty>
            <span className="mini-scenarios-empty__icon" aria-hidden="true">
              <RailIcon name="evidence" />
            </span>
            <h3>{SCENARIOS_EMPTY.heading}</h3>
            <p>{SCENARIOS_EMPTY.body}</p>
          </div>
        </>
      ) : (
        <>
          <Rows rows={body.rows} />
          <nav aria-label="Scenario pages" className="mini-scenarios-pages" data-scenarios-pages>
            <span data-scenarios-count>
              {body.rows.length} of {body.total_count}
            </span>
            {scope.cursor !== null ? (
              <button type="button" className="link-button" data-scenarios-first onClick={() => onScope({ ...bound, cursor: null })}>
                First page
              </button>
            ) : null}
            {body.next_cursor !== null ? (
              <button
                type="button"
                className="link-button"
                data-scenarios-next
                onClick={() => onScope({ ...bound, cursor: body.next_cursor })}
              >
                Next
              </button>
            ) : null}
          </nav>
        </>
      )}
    </div>
  );
}

export function MiniScenarios({
  siteCode,
  client,
  scope,
  onScope,
}: {
  siteCode: string;
  client: MiniDecisionsClient;
  scope: ScenarioScope;
  /** Called with the server's effective bounds after the first read, and on a page change. */
  onScope: (next: ScenarioScope, replace: boolean) => void;
}) {
  const [result, setResult] = useState<DecisionRead<ScenarioListBody> | null>(null);
  const { from, to, known_at, cursor } = scope;
  // The address the first read adopted: reaching it is not a new read (the first answer stays on screen).
  const adopted = useRef<string | null>(null);
  useEffect(() => {
    const key = JSON.stringify([from, to, known_at, cursor]);
    if (adopted.current === key) {
      adopted.current = null;
      return;
    }
    let active = true;
    setResult(null);
    void client.getScenarios(siteCode, { from, to, known_at, cursor }).then((loaded) => {
      if (!active) return;
      setResult(loaded);
      // S15: the first read's effective bounds and cutoff go into the address, so reload reads the same set.
      if (loaded.status === "loaded" && from === null && to === null && known_at === null) {
        const w = loaded.value.window;
        adopted.current = JSON.stringify([w.from, w.to, w.known_at, cursor]);
        onScope({ from: w.from, to: w.to, known_at: w.known_at, cursor }, true);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteCode, from, to, known_at, cursor, onScope]);
  return (
    <div className="mini-scenarios" data-mini-scenarios>
      <Panel heading="Financial scenarios" headingId={SCENARIOS_HEADING_ID} description={SCENARIOS_PANEL_DESCRIPTION}>
        {result === null ? (
          <p data-scenarios-loading>Loading the site&apos;s scenarios.</p>
        ) : result.status === "loaded" ? (
          <Loaded body={result.value} scope={scope} onScope={(next) => onScope(next, false)} />
        ) : (
          <p className="mini-scenarios-refused" data-scenarios-refused={result.status === "refused" ? result.code : "unavailable"}>
            {result.status === "refused" && result.message !== null
              ? result.message
              : "The scenario read is unavailable; no scenario is shown."}
          </p>
        )}
        <p className="mini-scenarios-gap" data-scenario-creation-unavailable>
          Scenario creation unavailable
        </p>
      </Panel>
      <Notice tone="blue" data={{ "data-scenarios-notice": "" }}>
        {SCENARIOS_NOTICE}
      </Notice>
    </div>
  );
}
