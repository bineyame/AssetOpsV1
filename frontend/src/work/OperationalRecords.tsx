/**
 * W6-01e E2: the global Operational records root (v6.9 `oprecords`, `index.html:973-987` `opRecordsScreen`), read
 * from `GET /api/work/operational-records` (`global-work-index-1`). Mock order: breadcrumb, h1 and subtitle (no tabs),
 * the date bar, the four cards, the five record-type chips, the `Operational records` panel, then the pair
 * `Record a manual reading` / `How records are used`. Copy follows `.agent/W6-01-build-spec.md` section 2, section 3.1
 * (A2Q1, A2Q4-A2Q7, A2Q10, X1-X8, CL3-1, CL3-6) and the "E1-E2 pre-flight rulings" P-E2-1..8, which supersede them.
 *
 * MOCK DEVIATIONS (register `.agent/mock-departure-register.md`):
 * - D4 (R29): cards 2-4 keep their headings, the amber fourth tone and the first note, but state that no publication
 *   link, review workflow or request list is established, instead of the mock's example counts and REC codes.
 * - R12 (D1, the inert form) is closed by OWN-G3b: `Record a manual reading` saves through the server's entry route
 *   (build sheet OWN-GAPS §3.3, R2-G3b). The mock's `Fills REC-307 when submitted` sub-line is still not rendered.
 * - MD-OWN-G3-1: the "Fuel delivery" Reading option, its Ticket reference row, and the per-reading unit suffix and
 *   placeholder are additions to the mock form.
 * - MD-OWN-G3-2: `Taken at` is a native date-time input labelled "(Site local time)", not the mock's filled text field.
 * - MD-OWN-G3-3: the result line under the footer and the replaced panel description line.
 * - MD-OWN-G3-4: the "Entered by site admin" By label and the added third `How records are used` paragraph.
 * - D4 (R31): `How records are used` keeps its two paragraphs and bold `Operator record`, bounded to what is stored.
 * - D4 (R30): table rows are the persisted Submitted heads with stored actor IDs, not the mock's example rows/roles.
 * A refusal, a read failure or a changed list is stated, never zero.
 */
import { useId, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import { displayCode } from "../ui/displayCode";
import { useNavigate } from "react-router-dom";
import { Breadcrumbs, DataTable, MetricCard, MetricCards, PageHeader, Panel } from "../ui";
import { CellDisclosure } from "./CellDisclosure";
import {
  GLOBAL_OPERATIONAL_KINDS,
  createGlobalWorkClient,
  globalWorkHref,
  globalWorkUtc,
  operationalEntryKey,
  type GlobalOperationalBody,
  type GlobalOperationalKind,
  type GlobalOperationalRow,
  type GlobalWorkClient,
  type OperationalEntryKind,
  type OperationalEntryResult,
} from "./globalWorkClient";
import {
  CHANGE_WINDOW,
  Clamp,
  GlobalWorkBar,
  GlobalWorkSlot,
  LinkOrText,
  MockDeviation,
  Pager,
  SCROLL_TABLE,
  WorkSourceLine,
  useGlobalWorkPage,
  type GlobalWorkPageRead,
} from "./globalWorkParts";
import { recKindLabel } from "./WorkRequestRecord";
import "./globalWork.css";

/** The page path; the route constant `OPERATIONAL_RECORDS_PATH` in `shell/operatorSiteRoutes.ts` has the same value. */
const PAGE_PATH = "/operational-records";
export const OPERATIONAL_RECORDS_HEADING_ID = "operational-records-heading";
const TABLE_HEADING_ID = "operational-records-table-heading";
const FORM_HEADING_ID = "operational-records-form-heading";
const USED_HEADING_ID = "operational-records-used-heading";

export const OPERATIONAL_RECORDS_SUBTITLE = "Operator logs, manual readings, shift notes and site visits";
export const OPERATIONAL_RECORDS_LOADING = "Loading the operational records across the estate.";
/** P-E2-4: the mock panel sub-line, verbatim, as the Panel description (A2Q7). */
export const OPERATIONAL_RECORDS_DESCRIPTION = "What people on site recorded, and the evidence each one feeds";
/** §3.3 (MD-OWN-G3-3): the form panel's description line. */
export const MANUAL_READING_DESCRIPTION = "Saved records are listed above as Submitted.";
/** Post-W6 W6 Q7: the stored time that places a record in the window. */
export const OPERATIONAL_RECORDS_MEMBERSHIP = "Listed by the time each record's event happened.";
export const NO_OPERATIONAL_RECORDS = "No operational records in this window.";
/** CL3-6: the kind-filtered zero sentences. */
export const KIND_ZERO: Readonly<Record<GlobalOperationalKind, string>> = {
  OPERATOR_LOG: "No operator log records in this window.",
  MANUAL_READING: "No manual reading records in this window.",
  SHIFT_NOTE: "No shift note records in this window.",
  SITE_VISIT: "No site visit records in this window.",
};
/** P-E2-6: the two `How records are used` paragraphs (the first carries the bold `Operator record`). */
export const RECORDS_USED_FIRST_BEFORE = "Authored records are kept apart from measured readings. This page shows them as ";
export const RECORDS_USED_FIRST_AFTER = "; none is accepted equipment evidence.";
export const RECORDS_USED_SECOND =
  "A reading that has not been taken remains a visible gap; this page has no request list to count it.";
/** §3.3 / R2-G3b 9 (MD-OWN-G3-4): the added third paragraph. */
export const RECORDS_USED_THIRD =
  "Fuel tank dips and fuel deliveries are read by the nightly fuel check. Stock and meter readings are stored and listed; no check reads them yet.";

/** §3.1 Rev 1 (MD-OWN-G3-4): the server entry service's id and its By label; other ids show as stored. */
export const OPERATOR_ENTRY_ACTOR = "service:operator-entry";
export const OPERATOR_ENTRY_LABEL = "Entered by site admin";
export const actorLabel = (actorId: string): string => (actorId === OPERATOR_ENTRY_ACTOR ? OPERATOR_ENTRY_LABEL : actorId);

/** §3.3: the Reading options, in order, with each one's unit suffix and Value placeholder (MD-OWN-G3-1). */
export const READING_OPTIONS: readonly { entry: OperationalEntryKind; label: string; unit: string; placeholder: string }[] = [
  { entry: "TANK_DIP", label: "Fuel tank dip", unit: "L", placeholder: "e.g. 192 L" },
  { entry: "FUEL_DELIVERY", label: "Fuel delivery", unit: "L", placeholder: "e.g. 300 L" },
  { entry: "STOCK_IN_CHAMBER", label: "Stock in chamber", unit: "kg", placeholder: "e.g. 40 kg" },
  { entry: "METER_READING", label: "Meter reading", unit: "kWh", placeholder: "e.g. 1520 kWh" },
];

/** §3.3 client validation literals (R2-G3b 10 adds the ticket-pattern message). */
export const ENTRY_ERRORS = {
  site: "Choose a Site.",
  value: "Enter a number of 0 or more, with at most 3 decimals.",
  delivery: "Enter the delivered litres (more than 0).",
  time: "Enter the time the reading was taken.",
  ticket: "Enter the delivery ticket reference.",
  ticketPattern: "Use letters, digits, spaces and / . _ - only, up to 40 characters, starting with a letter or digit.",
} as const;

/** §3.3 outcome literals (R2-G3b 2 changes the success line). */
export const ENTRY_OUTCOMES = {
  fuelRecheck:
    "If this Site's tank level is measured, the night it falls in is checked again at the next background refresh.",
  forbidden: "Saving records is not switched on for this installation.",
  noTank: "This Site has no single fuel tank to record against.",
  future: "The time taken is in the future.",
  tooOld: "The time taken is more than 30 days ago.",
  duplicate: "This entry was already saved with different values. Reload the page and enter it again.",
  other: "Check the values and try again.",
  unconfirmed: "The record could not be confirmed. Try again; it will not be saved twice.",
} as const;
export const savedLine = (publicCode: string): string => `Saved as ${displayCode(publicCode)}, status Submitted.`;

/** §3.2's server patterns, checked before sending. */
const VALUE_PATTERN = /^\d{1,6}(\.\d{1,3})?$/;
const TIME_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
const TICKET_PATTERN = /^[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}$/;
const isFuel = (entry: OperationalEntryKind) => entry === "TANK_DIP" || entry === "FUEL_DELIVERY";

/** §3.3 outcome table / R2-G3b 14: the result lines for one answer. */
export function entryOutcome(result: OperationalEntryResult, entry: OperationalEntryKind): string[] {
  if (result.status === "saved") return isFuel(entry) ? [savedLine(result.publicCode), ENTRY_OUTCOMES.fuelRecheck] : [savedLine(result.publicCode)];
  if (result.status === "unconfirmed") return [ENTRY_OUTCOMES.unconfirmed];
  const { httpStatus, code } = result;
  if (code === "WORK_EVENT_DUPLICATE_KEY") return [ENTRY_OUTCOMES.duplicate];
  if (httpStatus >= 500) return [ENTRY_OUTCOMES.unconfirmed];
  if (httpStatus === 403 && code === "WORK_WRITE_FORBIDDEN") return [ENTRY_OUTCOMES.forbidden];
  if (httpStatus === 422 && code === "OPREC_ENTRY_NO_TANK") return [ENTRY_OUTCOMES.noTank];
  if (httpStatus === 422 && code === "WORK_OCCURRED_AT_FUTURE") return [ENTRY_OUTCOMES.future];
  if (httpStatus === 422 && code === "WORK_OCCURRED_AT_TOO_OLD") return [ENTRY_OUTCOMES.tooOld];
  return [ENTRY_OUTCOMES.other];
}

/** The mock chips, in order; `All` maps to no `kind` in the URL (P-E2-2). */
export const KIND_CHIPS: readonly [string, GlobalOperationalKind | null][] = [
  ["All", null],
  ["Operator log", "OPERATOR_LOG"],
  ["Manual reading", "MANUAL_READING"],
  ["Shift note", "SHIFT_NOTE"],
  ["Site visit", "SITE_VISIT"],
];

/** P-E2-1: `kind` absent or `all` is all (null); one stored kind is itself; anything else or repeated is invalid. */
export function operationalKindOf(values: string[]): GlobalOperationalKind | null | undefined {
  if (values.length === 0) return null;
  if (values.length > 1) return undefined;
  if (values[0] === "all") return null;
  return (GLOBAL_OPERATIONAL_KINDS as readonly string[]).includes(values[0]) ? (values[0] as GlobalOperationalKind) : undefined;
}

/**
 * P-E2-8 / KD3 ruling: `Reading: {quantity}[ {unit}]` for a manual reading with a quantity, only when the body does
 * not already contain that formatted value (then the body shows it once and no reading line renders).
 */
export function readingLine(row: Pick<GlobalOperationalRow, "kind" | "quantity" | "unit" | "body">): string | null {
  if (row.kind !== "MANUAL_READING" || row.quantity === null) return null;
  const value = `${row.quantity}${row.unit === null ? "" : ` ${row.unit}`}`;
  return row.body.includes(value) ? null : `Reading: ${value}`;
}

function RecordRow({ row }: { row: GlobalOperationalRow }) {
  const reading = readingLine(row);
  return (
    <tr data-global-work-row={row.root_id} data-global-work-head={row.head_id}>
      <td>
        <CellDisclosure column="Record" row={row.code} data={{ "data-global-work-code": "" }}>
          {displayCode(row.code)}
        </CellDisclosure>
        {row.correction_reason !== null ? (
          <>
            <CellDisclosure column="Record correction" row={row.code} data={{ "data-global-work-correction": "" }}>
              {`Correction: ${row.correction_reason}`}
            </CellDisclosure>
            {row.supersedes_record_id !== null ? (
              <details className="global-work-details" data-global-work-supersedes>
                <summary>Earlier record version</summary>
                {row.supersedes_record_id}
              </details>
            ) : null}
          </>
        ) : null}
        <WorkSourceLine provenance={row.source_provenance} />
      </td>
      <td>
        <CellDisclosure column="Type" row={row.code} data={{ "data-global-work-kind": row.kind }}>
          {recKindLabel(row.kind)}
        </CellDisclosure>
      </td>
      <td>
        <CellDisclosure column="Site" row={row.code}>
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </CellDisclosure>
      </td>
      <td>
        <Clamp data={{ "data-global-work-when": "" }}>{globalWorkUtc(row.occurred_at)}</Clamp>
        {row.period_end !== null ? (
          <Clamp data={{ "data-global-work-period-end": "" }}>{`Until ${globalWorkUtc(row.period_end)}`}</Clamp>
        ) : null}
      </td>
      <td>
        <CellDisclosure column="By" row={row.code} data={{ "data-global-work-actor": "" }}>
          {actorLabel(row.actor_id)}
        </CellDisclosure>
      </td>
      <td>
        <Clamp data={{ "data-global-work-body": "" }}>{row.body}</Clamp>
        {reading !== null ? <Clamp data={{ "data-global-work-reading": "" }}>{reading}</Clamp> : null}
        <details className="global-work-details" data-global-work-full-body>
          <summary>Full record text</summary>
          {row.body}
        </details>
      </td>
      <td>
        <CellDisclosure
          column="Feeds"
          row={row.code}
          data={{ "data-global-work-feeds": row.links.case === null ? "none" : "case" }}
        >
          {row.links.case === null ? (
            "None linked"
          ) : (
            <>
              <LinkOrText link={row.links.case} data={{ "data-global-work-case": row.case_kind ?? "" }} />
              {" →"}
            </>
          )}
        </CellDisclosure>
      </td>
      <td>
        <span className="w1f4-action-badge w1f4-action-badge--blue" data-global-work-state={row.state} data-global-work-tone="blue">
          Submitted
        </span>
      </td>
    </tr>
  );
}

const COLUMNS = ["Record", "Type", "Site", "When", "By", "What it says", "Feeds", "State"];
/**
 * Post-W6 W6 Q16 (R356, superseding P-E2-8's 1150 px minimum): fixed column widths (px, total 1085 after the
 * caps ruling 3 Feeds retune 140 -> 125) that fit the
 * 1105 px table client width at 1440, with wrapping cells; below 761 px the table keeps its inner horizontal scroll.
 */
const MIN_WIDTHS = [90, 110, 150, 130, 120, 270, 125, 90];

function RecordTable({ body }: { body: GlobalOperationalBody }) {
  return (
    <DataTable labelledBy={TABLE_HEADING_ID}>
      <colgroup>
        {MIN_WIDTHS.map((width, index) => (
          <col key={index} style={{ width: `${width}px` }} />
        ))}
      </colgroup>
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
        {body.rows.map((row) => (
          <RecordRow key={`${row.site_id}/${row.root_id}`} row={row} />
        ))}
      </tbody>
    </DataTable>
  );
}

/** P-E2-3: the mock's four card headings and first note; cards 2-4 state their gaps (MOCK DEVIATION D4, R29). */
function Cards({ body }: { body: GlobalOperationalBody }) {
  return (
    <MetricCards label="Operational records summary" data={{ "data-global-work-cards": "" }}>
      <MetricCard
        label="Records in window"
        value={String(body.total_count)}
        note="Logs, readings, notes and visits"
        data={{ "data-global-work-card": "records_in_window" }}
      />
      <MetricCard
        label="Feeding evidence"
        value="Not established"
        word
        note="No accepted-evidence publication link"
        data={{ "data-global-work-card": "feeding_evidence" }}
      />
      <MetricCard
        label="In review"
        value="No review workflow"
        word
        note="All stored records are Submitted"
        data={{ "data-global-work-card": "in_review" }}
      />
      <MetricCard
        label="Requested, not yet done"
        value="Not recorded"
        assessment
        tone="amber"
        note="No request list recorded"
        data={{ "data-global-work-card": "requested" }}
      />
    </MetricCards>
  );
}

/**
 * P-E2-2: the mock's five chip buttons, outside the first panel. Each sets a validated kind in the URL (All removes
 * it), drops `cursor`, clears `globalWorkTrail` and keeps a valid window and explicit cutoff.
 */
function KindChips({ page }: { page: GlobalWorkPageRead<GlobalOperationalBody> }) {
  const navigate = useNavigate();
  const base = page.query ?? page.windowQuery;
  const active = page.parsed.status === "valid" ? (page.query?.kind ?? null) : undefined;
  const choose = (kind: GlobalOperationalKind | null) => {
    const href =
      base === null
        ? kind === null
          ? PAGE_PATH
          : `${PAGE_PATH}?kind=${encodeURIComponent(kind)}`
        : globalWorkHref(PAGE_PATH, { from: base.from, to: base.to, known_at: base.known_at, ...(kind ? { kind } : {}) });
    navigate(href, { state: { globalWorkTrail: [] } });
  };
  return (
    <div className="v69-chips global-work-chips" role="group" aria-label="Record type" data-global-work-chips>
      {KIND_CHIPS.map(([label, kind]) => (
        <button
          key={label}
          type="button"
          className="v69-chip"
          aria-pressed={active === kind}
          data-rec-type={label}
          onClick={() => choose(kind)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

/**
 * Post-W6 W6 Q17 (R362): the Site options are the response's own authorized Sites (`coverage.sites` codes, named by
 * a returned row's stored Site name where one is on this page), or one empty placeholder before or without a read.
 * No mock Site is offered.
 */
export function manualReadingSites(body: GlobalOperationalBody | null): { code: string; label: string }[] {
  if (body === null) return [];
  const names = new Map(body.rows.map((row) => [row.site_code, row.site_name] as const));
  return body.coverage.sites.map(({ site_code: code }) => {
    const name = names.get(code);
    return { code, label: name ? `${name} · ${code}` : code };
  });
}

type EntryErrors = Partial<Record<"site" | "value" | "time" | "ticket", string>>;

function entryErrors(site: string | null, entry: OperationalEntryKind, value: string, takenAt: string, ticket: string): EntryErrors {
  const errors: EntryErrors = {};
  if (site === null) errors.site = ENTRY_ERRORS.site;
  if (!VALUE_PATTERN.test(value)) errors.value = ENTRY_ERRORS.value;
  else if (entry === "FUEL_DELIVERY" && !(Number(value) > 0)) errors.value = ENTRY_ERRORS.delivery;
  if (!TIME_PATTERN.test(takenAt)) errors.time = ENTRY_ERRORS.time;
  if (entry === "FUEL_DELIVERY") {
    if (ticket === "") errors.ticket = ENTRY_ERRORS.ticket;
    else if (!TICKET_PATTERN.test(ticket)) errors.ticket = ENTRY_ERRORS.ticketPattern;
  }
  return errors;
}

/** One field cell: the label, its control, and its message under the control once a Submit was attempted. */
function EntryField({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return (
    <div className="field" data-global-work-field={label}>
      <label htmlFor={id}>{label}</label>
      {children}
      {error !== undefined ? (
        <span className="field-error global-work-field-error" id={`${id}-error`} data-global-work-field-error>
          {error}
        </span>
      ) : null}
    </div>
  );
}

/**
 * OWN-G3b (build sheet OWN-GAPS §3.3, R2-G3b): the live entry form. Sites are the response's own authorized Sites
 * (R362; the visible D4 label stays). The browser sends the closed §3.2 body; the server supplies the actor. The
 * idempotency key is made at the first valid submit, kept after a refusal or a failed confirmation, and replaced
 * after any field edit or a success (R2-G3b 11). Fields stay enabled while a save is in flight (R2-G3b 12).
 */
function ManualReadingPanel({
  body,
  client,
  onSaved,
}: {
  body: GlobalOperationalBody | null;
  client: GlobalWorkClient;
  onSaved: () => void;
}) {
  const sites = manualReadingSites(body);
  const [siteChoice, setSiteChoice] = useState<string | null>(null);
  const [entry, setEntry] = useState<OperationalEntryKind>("TANK_DIP");
  const [value, setValue] = useState("");
  const [takenAt, setTakenAt] = useState("");
  const [ticket, setTicket] = useState("");
  const [attempted, setAttempted] = useState(false);
  const [inFlight, setInFlight] = useState(false);
  const [result, setResult] = useState<string[]>([]);
  const key = useRef<string | null>(null);
  const ids = useId();
  const id = (name: string) => `${ids}-${name}`;

  // R2-G3b 4: the kept Site is re-selected when the options return; otherwise the first option.
  const site = sites.find((s) => s.code === siteChoice)?.code ?? sites[0]?.code ?? null;
  const reading = READING_OPTIONS.find((option) => option.entry === entry) ?? READING_OPTIONS[0];
  const errors = entryErrors(site, entry, value.trim(), takenAt, ticket.trim());
  const shownErrors: EntryErrors = attempted ? errors : {};
  const edit =
    <T,>(set: (next: T) => void) =>
    (next: T) => {
      key.current = null;
      set(next);
    };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setAttempted(true);
    if (inFlight) return;
    // Polish L2: a refused Submit moves focus to the first invalid field, in form order, so its message is announced.
    const firstInvalid = (["site", "value", "time", "ticket"] as const).find((name) => errors[name] !== undefined);
    if (firstInvalid !== undefined) {
      document.getElementById(id(firstInvalid))?.focus();
      return;
    }
    if (site === null) return;
    key.current ??= operationalEntryKey();
    setResult([]); // Polish L1: a repeated identical outcome is then a DOM change, so the live region re-announces it
    const sent = entry;
    setInFlight(true);
    let answer: OperationalEntryResult;
    if (client.submitOperationalEntry === undefined) {
      answer = { status: "refused", httpStatus: 403, code: "WORK_WRITE_FORBIDDEN" };
    } else {
      try {
        answer = await client.submitOperationalEntry(site, {
          entry: sent,
          value: value.trim(),
          taken_at_local: takenAt,
          ticket_reference: sent === "FUEL_DELIVERY" ? ticket.trim() : null,
          idempotency_key: key.current,
        });
      } catch {
        answer = { status: "unconfirmed" };
      }
    }
    setInFlight(false);
    setResult(entryOutcome(answer, sent));
    if (answer.status === "saved") {
      key.current = null;
      setValue("");
      setTicket("");
      setTakenAt("");
      setAttempted(false);
      onSaved();
    }
  };

  const describe = (name: keyof EntryErrors, extra?: string) =>
    [shownErrors[name] !== undefined ? `${id(name)}-error` : null, extra].filter(Boolean).join(" ") || undefined;

  return (
    <Panel heading="Record a manual reading" headingId={FORM_HEADING_ID} description={MANUAL_READING_DESCRIPTION}>
      <form className="global-work-form" data-global-work-manual-form noValidate onSubmit={(e) => void submit(e)}>
        <MockDeviation category="D4" id="R362" />
        <div className="input-row">
          <EntryField id={id("site")} label="Site" error={shownErrors.site}>
            <select
              id={id("site")}
              value={site ?? ""}
              onChange={(e) => edit(setSiteChoice)(e.target.value)}
              aria-invalid={shownErrors.site !== undefined || undefined}
              aria-describedby={describe("site")}
              data-global-work-form-site
            >
              {sites.length === 0 ? (
                <option value="">No Site selected</option>
              ) : (
                sites.map((s) => (
                  <option key={s.code} value={s.code}>
                    {s.label}
                  </option>
                ))
              )}
            </select>
          </EntryField>
          <EntryField id={id("reading")} label="Reading">
            <select
              id={id("reading")}
              value={entry}
              onChange={(e) => edit(setEntry)(e.target.value as OperationalEntryKind)}
              data-global-work-form-reading
            >
              {READING_OPTIONS.map((option) => (
                <option key={option.entry} value={option.entry}>
                  {option.label}
                </option>
              ))}
            </select>
          </EntryField>
        </div>
        <div className="input-row">
          <EntryField id={id("value")} label="Value" error={shownErrors.value}>
            <span className="global-work-value">
              <input
                id={id("value")}
                inputMode="decimal"
                value={value}
                placeholder={reading.placeholder}
                onChange={(e) => edit(setValue)(e.target.value)}
                aria-invalid={shownErrors.value !== undefined || undefined}
                aria-describedby={describe("value", id("unit"))}
                data-global-work-form-value
              />
              <span className="global-work-unit" id={id("unit")} data-global-work-form-unit>
                {reading.unit}
              </span>
            </span>
          </EntryField>
          <EntryField id={id("time")} label="Taken at (Site local time)" error={shownErrors.time}>
            <input
              id={id("time")}
              type="datetime-local"
              step={60}
              value={takenAt}
              onChange={(e) => edit(setTakenAt)(e.target.value)}
              aria-invalid={shownErrors.time !== undefined || undefined}
              aria-describedby={describe("time")}
              data-global-work-form-time
            />
          </EntryField>
        </div>
        {entry === "FUEL_DELIVERY" ? (
          <div className="input-row" data-global-work-ticket-row>
            <EntryField id={id("ticket")} label="Ticket reference" error={shownErrors.ticket}>
              <input
                id={id("ticket")}
                value={ticket}
                placeholder="e.g. KIS-DT-0002"
                onChange={(e) => edit(setTicket)(e.target.value)}
                aria-invalid={shownErrors.ticket !== undefined || undefined}
                aria-describedby={describe("ticket")}
                data-global-work-form-ticket
              />
            </EntryField>
          </div>
        ) : null}
        <div className="form-footer">
          <button className="button primary" type="submit" disabled={inFlight || site === null} data-rec-submit>
            Submit for review
          </button>
        </div>
        <div className="global-work-form-result" role="status" aria-live="polite" data-global-work-form-result>
          {result.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      </form>
    </Panel>
  );
}

/** P-E2-6: the mock's two paragraphs, bounded copy (MOCK DEVIATION D4, R31). */
function RecordsUsedPanel() {
  return (
    <Panel heading="How records are used" headingId={USED_HEADING_ID}>
      <div className="prose" data-global-work-records-used>
        <p>
          {RECORDS_USED_FIRST_BEFORE}
          <strong>Operator record</strong>
          {RECORDS_USED_FIRST_AFTER}
        </p>
        <p>{RECORDS_USED_SECOND}</p>
        <p>{RECORDS_USED_THIRD}</p>
      </div>
    </Panel>
  );
}

export function OperationalRecordsPage({ client }: { client?: GlobalWorkClient }) {
  const page = useGlobalWorkPage<GlobalOperationalBody>(
    PAGE_PATH,
    client,
    (reads, query) => (reads.operationalRecords ? reads.operationalRecords(query) : null),
    operationalKindOf,
  );
  const { body, shown, query, trail } = page;
  const kind = query?.kind ?? null;
  const writes = useMemo(() => client ?? createGlobalWorkClient(), [client]);

  return (
    <div className="global-work global-work--oprecords" data-global-work-root="operational-records">
      <Breadcrumbs trail={[{ label: "Operational records" }]} />
      <PageHeader title="Operational records" headingId={OPERATIONAL_RECORDS_HEADING_ID} subtitle={OPERATIONAL_RECORDS_SUBTITLE} />
      <GlobalWorkBar page={page} label="Operational records window" membership={OPERATIONAL_RECORDS_MEMBERSHIP} />
      <GlobalWorkSlot page={page} loading={OPERATIONAL_RECORDS_LOADING} cards={(value) => <Cards body={value} />} />
      <KindChips page={page} />
      <Panel heading="Operational records" headingId={TABLE_HEADING_ID} description={OPERATIONAL_RECORDS_DESCRIPTION}>
        {shown && body !== null ? (
          body.total_count === 0 ? (
            <div className="global-work-empty" data-global-work-zero={kind ?? "all"}>
              <p>{kind === null ? NO_OPERATIONAL_RECORDS : KIND_ZERO[kind]}</p>
              <p>{CHANGE_WINDOW}</p>
            </div>
          ) : (
            <>
              <p className="global-work-scroll-hint" data-global-work-scroll-hint>
                {SCROLL_TABLE}
              </p>
              <RecordTable body={body} />
              <Pager
                label="Operational records pages"
                body={body}
                trail={trail}
                cursor={query?.cursor ?? null}
                onPage={(cursor, nextTrail) => query && page.go(query, cursor, nextTrail)}
              />
            </>
          )
        ) : null}
      </Panel>
      <div className="panel-pair global-work-pair">
        <ManualReadingPanel body={shown ? body : null} client={writes} onSaved={page.reload} />
        <RecordsUsedPanel />
      </div>
    </div>
  );
}

/** The routed frame: the page in its `<main>` landmark, named by the page heading. */
export function OperationalRecordsFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <main aria-labelledby={OPERATIONAL_RECORDS_HEADING_ID}>
      <OperationalRecordsPage client={client} />
    </main>
  );
}
