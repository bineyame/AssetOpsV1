/**
 * W4-03 unit 6a: mini Site > Financials > Scenarios (`/sites/:siteId/financials/scenarios`, v69 `scenarios`).
 *
 * Read-only (closure 1): the persisted authored what-ifs of this Site from `mini-scenarios-1`. The first request
 * omits both bounds; the page then shows `Scenarios created through {read time}` (the returned effective `window.to`
 * minus one microsecond) and carries the returned `from`/`to`/`known_at` in its address for every cursor page and
 * reload (closure 4 S15). A row's `url:null` is the noninteractive `Scenario detail unavailable`; creation is the
 * noninteractive `Scenario creation unavailable`. The notice is always shown.
 */
import { useEffect, useRef, useState, type FormEvent } from "react";
import { DataTable, Panel, RailIcon } from "../ui";
import { Notice } from "../ui/V69Layout";
import {
  decisionRefusal,
  microsecondBefore,
  type DecisionRead,
  type MiniDecisionsClient,
  type ScenarioAssumption,
  type ScenarioListBody,
  type ScenarioRow,
  type ScenarioScope,
} from "./miniDecisionsClient";
import { ClaimLabel } from "./ClaimLabel";
import { siteLocalDate,siteLocalEndUtc, siteLocalLastDay, siteLocalMidnightUtc, siteZoneDisplayLabel } from "./siteTime";
import "../ui/mock-deviation.css";
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

/** uF 8 (final review L8): plain-language names for the closed authored keys; the API field stays the key. */
const ASSUMPTION_LABELS: Record<string, string> = {
  stop_soc: "Stop at battery charge",
  proposed_kw: "Proposed load",
  duration_hours: "Duration",
  tariff_per_kwh: "Tariff",
};

/** One typed assumption as authored: its plain name, decimal (or declared text) and unit. */
function declared(a: ScenarioAssumption): string {
  return `${ASSUMPTION_LABELS[a.key] ?? a.key} ${a.value ?? ""}${a.unit ? ` ${a.unit}` : ""}`.trim();
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** uF 8 (L8): the exact six-digit UTC token read as a plain UTC date and second; never local time. */
export function plainUtc(token: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2}:\d{2})(?:\.\d+)?Z$/.exec(token);
  return m === null ? token : `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}, ${m[4]} UTC`;
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
              <td data-scenario-result>
                {illustrative(row)}
                {/* CC-R1 / R500: the claim level and beneficiary under the gross scenario figure. */}
                {row.calculation_state === "GROSS_SCENARIO" && row.gross_sales !== null ? (
                  <ClaimLabel level="MODELLED_OPPORTUNITY" beneficiary="MINI_OPERATOR" />
                ) : null}
              </td>
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
          Scenarios created through <time dateTime={through}>{plainUtc(through)}</time>
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

/**
 * post-W6 W4 R325 (Q14), MOCK DEVIATION D2 (R450): a compact page-local Window in Site-local calendar days, after the
 * subtabs (the DomainWorkWindow pattern). The address keeps UTC bounds; Apply keeps the cutoff and reads page one.
 * Invalid input stays on the page with its reason and makes no new read.
 */
export function ScenariosWindow({
  scope,
  timeZone,
  onApply,
}: {
  scope: ScenarioScope;
  timeZone: string | null;
  onApply: (next: ScenarioScope) => void;
}) {
  const [first, setFirst] = useState(siteLocalDate(scope.from, timeZone));
  const [last, setLast] = useState(siteLocalLastDay(scope.to, timeZone));
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setFirst(siteLocalDate(scope.from, timeZone));
    setLast(siteLocalLastDay(scope.to, timeZone));
    setError(null);
  }, [scope.from, scope.to, timeZone]);
  const zone = siteZoneDisplayLabel(timeZone, scope.from);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const from = first ? siteLocalMidnightUtc(first, timeZone) : "";
    // build ruling 7: the chosen end day is included; the half-open URL bound is the next Site-local midnight.
    const to = last ? siteLocalEndUtc(last, timeZone) : "";
    if (from === "" || to === "") {
      setError("Choose both dates.");
      return;
    }
    if (Date.parse(to) <= Date.parse(from)) {
      setError("The end must be after the start.");
      return;
    }
    setError(null);
    onApply({ from, to, known_at: scope.known_at, cursor: null });
  };
  return (
    <div className="mini-scenarios-window-row">
      <form className="site-date-bar mini-scenarios-window" onSubmit={submit} aria-label="Window" data-scenarios-window>
        <span className="mini-scenarios-window__lead">Window</span>
        <label className="mini-scenarios-window__field">
          {`From (${zone}) `}
          <input className="v69-chip-control" type="date" value={first} onChange={(e) => setFirst(e.target.value)} data-scenarios-window-from />
        </label>
        <label className="mini-scenarios-window__field">
          {`To (${zone}, included) `}
          <input className="v69-chip-control" type="date" value={last} onChange={(e) => setLast(e.target.value)} data-scenarios-window-to />
        </label>
        <button className="button" type="submit" data-scenarios-window-apply>
          Apply
        </button>
        {error === null ? null : (
          <span className="mini-scenarios-window__error" role="alert" data-scenarios-window-error>
            {error}
          </span>
        )}
      </form>
      <p className="mock-deviation-line" data-mock-deviation="R450">
        MOCK DEVIATION D2 (R450)
      </p>
    </div>
  );
}

/** post-W6 W4 Q5: the shared decision refusal table (copy and offered action); never a raw code or server message. */
function Refused({ result, onFirstPage }: { result: Exclude<DecisionRead<unknown>, { status: "loaded" }>; onFirstPage: () => void }) {
  const refusal = decisionRefusal(result);
  return (
    <p className="mini-scenarios-refused" data-scenarios-refused={result.status === "refused" ? result.code : "unavailable"}>
      {refusal.copy}
      {refusal.action === "first-page" ? (
        <>
          {" "}
          <button type="button" className="link-button" data-scenarios-restart onClick={onFirstPage}>
            First page
          </button>
        </>
      ) : null}
    </p>
  );
}

export function MiniScenarios({
  siteCode,
  client,
  scope,
  timeZone = null,
  onScope,
}: {
  siteCode: string;
  client: MiniDecisionsClient;
  scope: ScenarioScope;
  /** The Site's stored timezone for the Window control; null says UTC. */
  timeZone?: string | null;
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
      <ScenariosWindow scope={scope} timeZone={timeZone} onApply={(next) => onScope(next, false)} />
      <Panel heading="Financial scenarios" headingId={SCENARIOS_HEADING_ID} description={SCENARIOS_PANEL_DESCRIPTION}>
        {result === null ? (
          <p data-scenarios-loading>Loading the site&apos;s scenarios.</p>
        ) : result.status === "loaded" ? (
          <Loaded body={result.value} scope={scope} onScope={(next) => onScope(next, false)} />
        ) : (
          <Refused result={result} onFirstPage={() => onScope({ from, to, known_at, cursor: null }, false)} />
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
