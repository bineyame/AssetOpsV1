/**
 * SR-11 (sequence doc rev 10b.1 / 10b.3; D-SR.51, D-SR.58, D-SR.60, D-SR.70-72): the mini-grid Backup tab over the
 * date range, from `backup-range` (stored `mini_depth.backup_day` rows). One row per Site-local day: "n backup starts:
 * p passed, f failed, i incomplete", the slowest recovery against its target, and the state words. A day that is not
 * stored, still being prepared or has no readings spans the row in words; its figures are unknown, never zero
 * (D-SR.51.3, D-SR.70). Rows are worded "backup start sequences", never outages (q3 ruling 8). Start successes are the
 * hour-card sum (D-SR.60). Window totals count a sequence that crosses local midnight once (D-SR.51.4, server-side).
 * The range view declares nothing to the date-range bar (D-SR.57).
 *
 * MOCK DEVIATION R728: v69 `backup` (screen 8.24) is one selected hour's event chains; over a range the tab is a day
 * table plus the range's sequences, with the hour page as the drill-in.
 */
import type { ReactNode } from "react";

import { RangeLink as Link } from "../ui/RangeLink";
import { Badge, DataTable, Panel, StatusBar } from "../ui";
import { localDateOf, localTimeOf } from "./miniDepthClient";
import {
  DEFAULT_SITE_RANGE_CLIENT,
  type BackupRangeBody,
  type BackupRangeDay,
  type BackupRangeSequence,
  type RangeWindowQuery,
  type SequenceCounts,
  type SiteRangeClient,
} from "./siteRangeClient";
import { OPEN_NOON_HOUR, RangeNotLoaded, dayWords, gapDaysText, useRangeRead, useWholeRangeState } from "./SiteRangeParts";

export const BACKUP_RANGE_NOT_APPLICABLE = "Backup starts over a range are read for mini-grid sites only.";
export const BACKUP_NO_READINGS_DAY = "No readings this day";
export const BACKUP_STILL_PREPARED = "Still being prepared";

/** Full words per day state (10b.1; D-SR.70 "No readings this day"; D-SR.51.3 "Still being prepared"). */
export const BACKUP_DAY_WORDS: Record<string, string> = {
  SEQUENCES_PASSED: "Every backup start sequence passed",
  SEQUENCE_FAILED: "A backup start sequence failed",
  SEQUENCE_INCOMPLETE: "A backup start sequence is incomplete",
  NO_SEQUENCE: "No backup start recorded",
  NO_ASSESSMENT: "No hour of this day could be assessed",
  NO_DATA: BACKUP_NO_READINGS_DAY,
  STILL_PROCESSING: BACKUP_STILL_PREPARED,
  NOT_EXPECTED: "Before this Site's readings began",
};

const SHORT_REASON: Record<string, string> = {
  NO_ASSESSMENT: "no hour assessed",
  NO_DATA: "no readings",
  STILL_PROCESSING: "still being prepared",
  NOT_EXPECTED: "before readings began",
};

const COUNTED = new Set(["SEQUENCES_PASSED", "SEQUENCE_FAILED", "SEQUENCE_INCOMPLETE", "NO_SEQUENCE"]);
const RESULT_WORD: Record<string, string> = { PASS: "Pass", FAIL: "Fail", INCOMPLETE: "Incomplete" };
const OUTCOME_WORD: Record<string, string> = { RECOVERED: "Recovered", MISSED_TARGET: "Missed recovery target", UNKNOWN: "Unknown" };

const NUMBER = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const minutes = (seconds: number | null | undefined): string => (seconds === null || seconds === undefined ? "–" : `${NUMBER.format(seconds / 60)} min`);

/** "n backup starts: p passed, f failed, i incomplete" (10b.3). */
export function startsText(counts: SequenceCounts): string {
  const n = counts.PASS + counts.FAIL + counts.INCOMPLETE;
  return `${n} backup start${n === 1 ? "" : "s"}: ${counts.PASS} passed, ${counts.FAIL} failed, ${counts.INCOMPLETE} incomplete`;
}

function slowestText(day: BackupRangeDay): string {
  const slow = day.slowest_recovery;
  if (slow === null) return "No timed recovery";
  const target = slow.target_seconds === null ? "" : ` (target ${minutes(slow.target_seconds)})`;
  return `Slowest recovery ${minutes(slow.seconds)}${target}`;
}

function BackupRangeStatus({ body }: { body: BackupRangeBody }) {
  const { totals } = body;
  const gaps = body.days
    .filter((d) => !COUNTED.has(d.state))
    .map((d) => ({ day: d.local_day, reason: SHORT_REASON[d.state] ?? "no usable result" }));
  const lead =
    totals.days_counted === 0
      ? "No day in this range has assessed backup starts"
      : `${startsText(totals.sequence_counts)}, for ${totals.days_counted} of ${totals.days_requested} days analysed`;
  return (
    <StatusBar label="Backup starts over the range" items data={{ "data-backup-range-status": "" }}>
      <span className="status-strip__item" data-backup-range-summary>
        {`${lead}${gapDaysText(gaps)}`}
      </span>
      {totals.days_counted > 0 ? (
        <span className="status-strip__item" data-backup-range-starts>
          {totals.start_success_count === null
            ? "No witnessed start request and result"
            : `Start successes: ${totals.start_success_count}`}
        </span>
      ) : null}
    </StatusBar>
  );
}

function stateWords(day: BackupRangeDay): ReactNode {
  const words = BACKUP_DAY_WORDS[day.state] ?? "No usable result for this day";
  if (!day.partial || day.hours_assessed === null || day.hours_expected === null) return words;
  return (
    <>
      {words}
      <span className="mini-cited" data-backup-day-partial>{` · Partial day: ${day.hours_assessed} of ${day.hours_expected} hours assessed`}</span>
    </>
  );
}

function BackupDayTable({ body }: { body: BackupRangeBody }) {
  const wholeRange = useWholeRangeState();
  return (
    <Panel
      heading="Backup starts by day"
      headingId="mini-backup-range-days-heading"
      description="Backup start sequences on each Site-local day of the date range."
      flush
    >
      <DataTable labelledBy="mini-backup-range-days-heading">
        <thead>
          <tr>
            <th scope="col">Day</th>
            <th scope="col">Backup starts</th>
            <th scope="col">Recovery</th>
            <th scope="col">State</th>
            <th scope="col">Hour detail</th>
          </tr>
        </thead>
        <tbody>
          {body.days.map((day) => (
            <tr key={day.local_day} data-backup-range-day={day.local_day} data-backup-day-state={day.state}>
              <th scope="row">{dayWords(day.local_day)}</th>
              {COUNTED.has(day.state) && day.sequence_counts !== null ? (
                <>
                  <td>{startsText(day.sequence_counts)}</td>
                  <td>{slowestText(day)}</td>
                  <td>{stateWords(day)}</td>
                </>
              ) : (
                <td colSpan={3} data-panel-gap="backup-range-day">
                  <span className="not-available-yet">{stateWords(day)}</span>
                </td>
              )}
              <td>
                <Link to={day.hour_link} state={wholeRange}>
                  {OPEN_NOON_HOUR}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

/** The counted days' sequences, once each by `chain_id` (the latest day wins, as the totals count them; D-SR.51.4). */
export function rangeSequences(body: BackupRangeBody): BackupRangeSequence[] {
  const chains = new Map<string, BackupRangeSequence>();
  for (const day of [...body.days].sort((a, b) => a.local_day.localeCompare(b.local_day))) {
    if (!COUNTED.has(day.state)) continue;
    for (const seq of day.sequences ?? []) chains.set(String(seq.chain_id), seq);
  }
  return [...chains.values()].sort((a, b) =>
    (a.outage_start ?? "") === (b.outage_start ?? "")
      ? String(a.chain_id).localeCompare(String(b.chain_id))
      : (a.outage_start ?? "").localeCompare(b.outage_start ?? ""),
  );
}

/**
 * "Sequences in this range" (10b.3). The stored day rows carry each sequence's start, result, outcome for service and
 * recovery, not its step records, so the hour page's step columns are not repeated here; each hour page shows them.
 */
function BackupSequencesPanel({ body, timeZone }: { body: BackupRangeBody; timeZone: string }) {
  const sequences = rangeSequences(body);
  return (
    <Panel
      heading="Sequences in this range"
      headingId="mini-backup-range-sequences-heading"
      description="Grid → start → generator → power → load → service, one row per backup start sequence. The steps of each are on its hour."
      flush
    >
      <DataTable labelledBy="mini-backup-range-sequences-heading">
        <thead>
          <tr>
            <th scope="col">When</th>
            <th scope="col">Outcome for service</th>
            <th scope="col">Recovery</th>
            <th scope="col">Result</th>
          </tr>
        </thead>
        <tbody>
          {sequences.length === 0 ? (
            <tr data-backup-range-sequence="none">
              <td colSpan={4} data-panel-gap="backup-range-sequences">
                <span className="not-available-yet">No backup start sequence was assessed in this range</span>
              </td>
            </tr>
          ) : (
            sequences.map((seq) => {
              const start = seq.outage_start === null ? Number.NaN : Date.parse(seq.outage_start);
              const recovery = seq.critical_recovery;
              return (
                <tr key={seq.chain_id} data-backup-range-sequence={(seq.result ?? "unknown").toLowerCase()}>
                  <td>{Number.isNaN(start) ? "–" : `${dayWords(localDateOf(timeZone, start))} ${localTimeOf(timeZone, start)}`}</td>
                  <td>{OUTCOME_WORD[seq.service_outcome ?? "UNKNOWN"] ?? "Unknown"}</td>
                  <td>
                    {recovery === null || recovery.seconds === null
                      ? "–"
                      : `${minutes(recovery.seconds)}${recovery.target_seconds === null ? "" : ` (target ${minutes(recovery.target_seconds)})`}`}
                  </td>
                  <td>
                    <Badge tone="neutral" className={`mini-decision--${(seq.result ?? "unknown").toLowerCase()}`}>
                      {RESULT_WORD[seq.result ?? ""] ?? "Unknown"}
                    </Badge>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </DataTable>
    </Panel>
  );
}

export function MiniBackupRangePage({ body }: { body: BackupRangeBody }) {
  const timeZone = body.site.timezone ?? "UTC";
  return (
    <>
      <BackupRangeStatus body={body} />
      <BackupDayTable body={body} />
      <BackupSequencesPanel body={body} timeZone={timeZone} />
    </>
  );
}

/** The Backup tab over the range: one `backup-range` read for the address range. */
export function MiniBackupRange({
  siteCode,
  window,
  client = DEFAULT_SITE_RANGE_CLIENT,
}: {
  siteCode: string;
  window: RangeWindowQuery;
  client?: SiteRangeClient;
}): ReactNode {
  const key = `${siteCode}|${window.from}|${window.to}|${window.known_at ?? ""}`;
  const { read, retrying } = useRangeRead((onRetrying) => client.getBackupRange(siteCode, window, onRetrying), key);
  return (
    <div className="mini-range" data-mini-range="backup">
      {read !== null && read.status === "loaded" ? (
        <MiniBackupRangePage body={read.value} />
      ) : (
        <RangeNotLoaded read={read} retrying={retrying} notApplicable={BACKUP_RANGE_NOT_APPLICABLE} name="backup-range" />
      )}
    </div>
  );
}
