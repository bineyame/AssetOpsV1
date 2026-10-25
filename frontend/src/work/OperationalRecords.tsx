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
 * - D1 (R12): `Record a manual reading` keeps its form, fields and `Submit for review` button, inert; the false
 *   `Fills REC-307 when submitted` sub-line and the other tenant's Site option are not rendered.
 * - D4 (R31): `How records are used` keeps its two paragraphs and bold `Operator record`, bounded to what is stored.
 * - D4 (R30): table rows are the persisted Submitted heads with stored actor IDs, not the mock's example rows/roles.
 * A refusal, a read failure or a changed list is stated, never zero.
 */
import { useNavigate } from "react-router-dom";
import { Breadcrumbs, DataTable, MetricCard, MetricCards, PageHeader, Panel } from "../ui";
import { UnavailableInline } from "../ui/UnavailableEntry";
import {
  GLOBAL_OPERATIONAL_KINDS,
  globalWorkHref,
  globalWorkUtc,
  type GlobalOperationalBody,
  type GlobalOperationalKind,
  type GlobalOperationalRow,
  type GlobalWorkClient,
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
export const MANUAL_READING_DESCRIPTION = "Manual readings cannot be submitted from this page.";
export const MANUAL_READING_REASON = "Recording requires an authorized work service.";
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
        <Clamp data={{ "data-global-work-code": "" }}>{row.code}</Clamp>
        {row.correction_reason !== null ? (
          <>
            <Clamp data={{ "data-global-work-correction": "" }}>{`Correction: ${row.correction_reason}`}</Clamp>
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
        <Clamp data={{ "data-global-work-kind": row.kind }}>{recKindLabel(row.kind)}</Clamp>
      </td>
      <td>
        <Clamp>
          <LinkOrText link={row.links.site} data={{ "data-global-work-site": row.site_code }} />
        </Clamp>
      </td>
      <td>
        <Clamp data={{ "data-global-work-when": "" }}>{globalWorkUtc(row.occurred_at)}</Clamp>
        {row.period_end !== null ? (
          <Clamp data={{ "data-global-work-period-end": "" }}>{`Until ${globalWorkUtc(row.period_end)}`}</Clamp>
        ) : null}
      </td>
      <td>
        <Clamp data={{ "data-global-work-actor": "" }}>{row.actor_id}</Clamp>
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
        <Clamp data={{ "data-global-work-feeds": row.links.case === null ? "none" : "case" }}>
          {row.links.case === null ? (
            "None linked"
          ) : (
            <>
              <LinkOrText link={row.links.case} data={{ "data-global-work-case": row.case_kind ?? "" }} />
              {" →"}
            </>
          )}
        </Clamp>
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
 * Post-W6 W6 Q16 (R356, superseding P-E2-8's 1150 px minimum): fixed column widths (px, total 1100) that fit the
 * 1105 px table client width at 1440, with wrapping cells; below 761 px the table keeps its inner horizontal scroll.
 */
const MIN_WIDTHS = [90, 110, 150, 130, 120, 270, 140, 90];

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

/**
 * P-E2-5: the mock form, inert (MOCK DEVIATION D1, R12): no POST, no state change, no REC allocated. Post-W6 W6 Q17
 * (R362, D4): selected Sites or an empty placeholder, an empty `Event time` input, and the D4 label beside the form.
 */
function ManualReadingPanel({ body }: { body: GlobalOperationalBody | null }) {
  const sites = manualReadingSites(body);
  return (
    <Panel heading="Record a manual reading" headingId={FORM_HEADING_ID} description={MANUAL_READING_DESCRIPTION}>
      <div className="global-work-form" data-global-work-manual-form>
        <MockDeviation category="D4" id="R362" />
        <div className="input-row">
          <label className="field">
            Site
            <select disabled aria-disabled="true" data-global-work-form-site>
              {sites.length === 0 ? (
                <option value="">No Site selected</option>
              ) : (
                sites.map((site) => (
                  <option key={site.code} value={site.code}>
                    {site.label}
                  </option>
                ))
              )}
            </select>
          </label>
          <label className="field">
            Reading
            <select disabled aria-disabled="true">
              <option>Fuel tank dip</option>
              <option>Stock in chamber</option>
              <option>Meter reading</option>
            </select>
          </label>
        </div>
        <div className="input-row">
          <label className="field">
            Value
            <input disabled aria-disabled="true" defaultValue="" placeholder="e.g. 192 L" />
          </label>
          <label className="field">
            Taken at
            <input disabled aria-disabled="true" defaultValue="" placeholder="Event time" data-global-work-form-time />
          </label>
        </div>
        <div className="form-footer">
          <button className="button primary" type="button" disabled aria-disabled="true" data-rec-submit>
            <UnavailableInline label="Submit for review" />
          </button>
          <span className="global-work-form-reason" data-global-work-form-reason>
            {MANUAL_READING_REASON}
          </span>
        </div>
      </div>
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
        <ManualReadingPanel body={shown ? body : null} />
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
