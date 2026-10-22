/**
 * W6-01c C3: the work request Maintenance record (v6.9 `wr-record`, `index.html:969`), read from
 * `GET /api/work/requests/{case_id}?site_id={site_code}[&known_at=]` (`global-work-detail-1`). Mock order: breadcrumb,
 * heading with `Open site`, the `Context tabs` row, the date bar, the `wrHeader` mheader, the
 * `Maintenance record · activity` panel, then the Operational records notice. Copy follows `.agent/W6-01-build-spec.md`
 * "C1-C3 pre-flight rulings" P-C3-1..5 and P-X-1..3, which supersede the section 2 record rows and F5 `wr-record`.
 *
 * The table keeps the mock's four columns `Item, Detail, Status, Basis` and its six item labels for every selected
 * record head (grouped `Record {n} · {occurred_at UTC}`, ordered `(occurred_at, id)`); rows without a stored field
 * state the gap (`Not recorded` / `Not established` / `No stored field`). The footer is the Panel description (A2Q7).
 *
 * MOCK DEVIATION (P-C3-4): the mock's notice links `Operational records` immediately, but `/operational-records` is
 * not mounted until W6-01e (E2). Until then the linked REC codes are PLAIN TEXT and the notice adds
 * `The Operational records page is being prepared.`; no `/operational-records` anchor renders. E2 promotes the codes
 * to CL3-3 window anchors in this file.
 */
import type { ReactNode } from "react";
import { DataTable, Notice, Panel } from "../ui";
import {
  globalWorkUtc,
  type GlobalWorkClient,
  type GlobalWorkDetailBody,
  type GlobalWorkDetailOperationalRecord,
  type WorkCaseDetailRecord,
} from "./globalWorkClient";
import { Clamp, SCROLL_TABLE } from "./globalWorkParts";
import { WorkRequestFrame } from "./workRequestShared";

export const RECORD_PANEL_HEADING = "Maintenance record · activity";
export const RECORD_TABLE_HEADING_ID = "work-request-record-heading";
export const RECORD_FOOTER = "What was recorded on site; no outcome verification follows from this entry.";
export const NO_MAINTENANCE_ACTIVITY = "No maintenance activity recorded";
export const NO_OUTCOME_NOTE = "No outcome note recorded";
export const NO_LINKED_REC = "No linked Operational record.";
export const REC_PAGE_PREPARED = "The Operational records page is being prepared.";
export const RECORD_COLUMNS = ["Item", "Detail", "Status", "Basis"] as const;
export const RECORD_ITEMS = [
  "Technician notes",
  "Parts",
  "Time on site",
  "Return-to-service reading",
  "Configuration readback",
  "Witnessed automatic start",
] as const;
/** P-B2-7 pattern: column minimum widths (px); the table scrolls inside its panel below their sum. */
const MIN_WIDTHS = [190, 420, 150, 200];

/** Section 2 oprecords chip labels for the stored `kind`; an unknown kind shows its stored value. */
const REC_KIND_LABEL: Readonly<Record<string, string>> = {
  OPERATOR_LOG: "Operator log",
  MANUAL_READING: "Manual reading",
  SHIFT_NOTE: "Shift note",
  SITE_VISIT: "Site visit",
};

export function recKindLabel(kind: string): string {
  return REC_KIND_LABEL[kind] ?? kind;
}

function byOccurred(a: WorkCaseDetailRecord, b: WorkCaseDetailRecord): number {
  if (a.occurred_at !== b.occurred_at) return a.occurred_at < b.occurred_at ? -1 : 1;
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

/** One selected head with its earlier versions (newest first, following `supersedes_record_id`). */
export interface RecordGroup {
  head: WorkCaseDetailRecord;
  earlier: WorkCaseDetailRecord[];
}

/** P-C3-1/2: the selected correction heads (nothing supersedes them), ordered `(occurred_at, id)`, with their chains. */
export function recordGroups(records: WorkCaseDetailRecord[]): RecordGroup[] {
  const byId = new Map(records.map((r) => [r.id, r]));
  const superseded = new Set(records.map((r) => r.supersedes_record_id).filter((id): id is string => id !== null));
  return records
    .filter((r) => !superseded.has(r.id))
    .sort(byOccurred)
    .map((head) => {
      const earlier: WorkCaseDetailRecord[] = [];
      const seen = new Set([head.id]);
      let next = head.supersedes_record_id === null ? undefined : byId.get(head.supersedes_record_id);
      while (next !== undefined && !seen.has(next.id)) {
        earlier.push(next);
        seen.add(next.id);
        next = next.supersedes_record_id === null ? undefined : byId.get(next.supersedes_record_id);
      }
      return { head, earlier };
    });
}

/** Section 2: a three-line preview and the complete escaped value in a named disclosure. */
function LongText({ text, hook }: { text: string; hook: string }) {
  return (
    <>
      <Clamp data={{ "data-work-record-clamp": hook }}>{text}</Clamp>
      <details className="global-work-details" data-work-record-full={hook}>
        <summary>Full activity text</summary>
        {text}
      </details>
    </>
  );
}

function Badge({ tone, children }: { tone: "neutral" | "amber"; children: string }) {
  return (
    <span className={`work-record-badge work-record-badge--${tone}`} data-work-record-status={children}>
      {children}
    </span>
  );
}

function TechnicianNotes({ group }: { group: RecordGroup }) {
  const { head, earlier } = group;
  return (
    <>
      <LongText text={head.activity} hook="activity" />
      <p className="work-record-outcome" data-work-record-outcome={head.outcome_note === null ? "none" : "recorded"}>
        {head.outcome_note === null ? (
          `Outcome note: ${NO_OUTCOME_NOTE}`
        ) : (
          <>
            <Clamp data={{ "data-work-record-clamp": "outcome" }}>{`Outcome note: ${head.outcome_note}`}</Clamp>
            <span className="work-record-outcome__basis" data-work-record-outcome-basis>
              Unverified · Authored note
            </span>
          </>
        )}
      </p>
      {earlier.length > 0 ? (
        <details className="global-work-details work-record-earlier" data-work-record-earlier>
          <summary>Earlier record versions</summary>
          <ol className="work-record-earlier__list">
            {earlier.map((version) => (
              <li key={version.id} data-work-record-version={version.id}>
                <span className="work-record-earlier__when">{`Recorded ${globalWorkUtc(version.recorded_at)}`}</span>
                <div className="work-record-earlier__text">{version.activity}</div>
                {version.outcome_note !== null ? (
                  <div className="work-record-earlier__text">{`Outcome note: ${version.outcome_note}`}</div>
                ) : null}
              </li>
            ))}
          </ol>
        </details>
      ) : null}
    </>
  );
}

type Row = [item: (typeof RECORD_ITEMS)[number], detail: ReactNode, status: ReactNode, basis: string];

function groupRows(group: RecordGroup): Row[] {
  const gap = (item: (typeof RECORD_ITEMS)[number]): Row => [item, "Not recorded", <Badge tone="amber">Not established</Badge>, "No stored field"];
  return [
    ["Technician notes", <TechnicianNotes group={group} />, <Badge tone="neutral">Recorded</Badge>, "Authored maintenance record"],
    gap("Parts"),
    ["Time on site", globalWorkUtc(group.head.occurred_at), <Badge tone="neutral">Recorded</Badge>, "Authored time"],
    gap("Return-to-service reading"),
    gap("Configuration readback"),
    gap("Witnessed automatic start"),
  ];
}

function RecordTable({ groups }: { groups: RecordGroup[] }) {
  return (
    <DataTable labelledBy={RECORD_TABLE_HEADING_ID}>
      <colgroup>
        {MIN_WIDTHS.map((width, index) => (
          <col key={index} style={{ width: `${width}px` }} />
        ))}
      </colgroup>
      <thead>
        <tr>
          {RECORD_COLUMNS.map((h) => (
            <th key={h} scope="col">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      {groups.map((group, index) => (
        <tbody key={group.head.id} data-work-record-group={group.head.id}>
          <tr className="work-record-group">
            <th colSpan={4} scope="rowgroup" data-work-record-group-heading>
              {`Record ${index + 1} · ${globalWorkUtc(group.head.occurred_at)}`}
            </th>
          </tr>
          {groupRows(group).map(([item, detail, status, basis]) => (
            <tr key={item} data-work-record-item={item}>
              <th scope="row" className="work-record-item">
                {item}
              </th>
              <td>{detail}</td>
              <td>{status}</td>
              <td>{basis}</td>
            </tr>
          ))}
        </tbody>
      ))}
    </DataTable>
  );
}

/** P-C3-3: the exact root REC codes with their kind labels, in the C1 array order. */
export function recNoticeSentence(records: GlobalWorkDetailOperationalRecord[]): string {
  const listed = records.map((r) => `${r.code} (${recKindLabel(r.kind)})`).join(", ");
  return `This record is also listed in Operational records as ${listed}.`;
}

/** The mock notice under the table; codes are plain text until E2 mounts `/operational-records` (MOCK DEVIATION). */
function RecordNotice({ body }: { body: GlobalWorkDetailBody }) {
  const recs = body.history.operational_records;
  return (
    <Notice tone="blue" data={{ "data-work-record-notice": recs.length === 0 ? "none" : "linked" }}>
      {recs.length === 0 ? (
        <p>{NO_LINKED_REC}</p>
      ) : (
        <p>
          {recNoticeSentence(recs)} {REC_PAGE_PREPARED}
        </p>
      )}
    </Notice>
  );
}

function RecordPanel({ body }: { body: GlobalWorkDetailBody | null }) {
  const groups = body === null ? [] : recordGroups(body.work_detail.records);
  return (
    <Panel heading={RECORD_PANEL_HEADING} headingId={RECORD_TABLE_HEADING_ID} description={RECORD_FOOTER}>
      {body === null ? null : groups.length === 0 ? (
        <div className="global-work-empty" data-work-record-empty>
          <p>{NO_MAINTENANCE_ACTIVITY}</p>
        </div>
      ) : (
        <>
          <p className="global-work-scroll-hint" data-global-work-scroll-hint>
            {SCROLL_TABLE}
          </p>
          <RecordTable groups={groups} />
        </>
      )}
    </Panel>
  );
}

/** The routed frame (`WORK_REQUEST_RECORD_ROUTE_PATH`): the shared request frame with the Maintenance record tab. */
export function WorkRequestRecordFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <WorkRequestFrame client={client} rootClass="work-request--record" tab="record">
      {(body) => (
        <>
          <RecordPanel body={body} />
          {body !== null ? <RecordNotice body={body} /> : null}
        </>
      )}
    </WorkRequestFrame>
  );
}
