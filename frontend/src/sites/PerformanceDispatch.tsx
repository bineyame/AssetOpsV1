/**
 * Imported-Site Performance > Dispatch over the durable dispatch assessment
 * (S3-01 phase 3b; mock `dispatch:1-3` and the S3-supported portions of
 * `analysis:1,3`).
 *
 * One selected UTC day (`?day=`) is read only when the Performance cutover is
 * open; while it is closed the reason and the comparison summary are shown and
 * nothing else. The selected interval revision (`?revision=`) and block
 * (`?block=`) stay in the address, so a reload reopens the exact stored
 * revision, including an earlier one that is no longer selected. Status is
 * shown as read (UNASSESSED, PENDING, CURRENT, STALE_PROJECTION, FAILED) and a
 * stale or failed day keeps its earlier result visibly marked. Fuel, money,
 * alternatives and Finding comparison are shown as not yet available.
 * Demonstration-data notes sit apart from the accepted-record provenance.
 */
import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import {
  clock,
  constraintWords,
  coverageWords,
  durationText,
  groupLimitations,
  isDay,
  limitationWords,
  minutes,
  reasonWords,
  roleWords,
  shiftDay,
  STATUS_WORDS,
} from "./dispatchWords";
import { ClaimBadge, LocalViews, localView, localViewSearch, OUTCOME_WORDS } from "./findingPresentation";
import type { EvidenceRead } from "./siteEvidenceClient";
import type {
  AcceptedEvidenceItem,
  AssessmentRevision,
  ComparisonSummary,
  CutoverState,
  DemoAnnotation,
  DispatchSegment,
  DispatchWindow,
  PerformanceDispatchClient,
  RevisionDetail,
} from "./performanceDispatchClient";

export const DURABLE_DISPATCH_VIEWS_LABEL = "Dispatch views";

const CLASS_FILL: Record<string, string> = {
  NECESSARY: "needed",
  CANDIDATE_AVOIDABLE: "avoidable",
  INDETERMINATE: "unknown",
};

function todayUtc(): string {
  return new Date().toISOString().slice(0, 10);
}

function outcome(level: string): string {
  return OUTCOME_WORDS[level] ?? level;
}

export function PerformanceDispatch({
  siteId,
  client,
}: {
  siteId: string;
  client: PerformanceDispatchClient;
}) {
  const [params, setParams] = useSearchParams();
  const day = isDay(params.get("day")) ? (params.get("day") as string) : todayUtc();
  const revisionId = params.get("revision");
  const view = localView(params);
  const [cutover, setCutover] = useState<EvidenceRead<CutoverState> | null>(null);
  const [windowRead, setWindowRead] = useState<EvidenceRead<DispatchWindow> | null>(null);

  useEffect(() => {
    let active = true;
    setCutover(null);
    void client.getCutover(siteId).then((loaded) => {
      if (active) {
        setCutover(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId]);

  const open = cutover?.status === "loaded" && cutover.value.permitted;

  useEffect(() => {
    if (!open) {
      return;
    }
    let active = true;
    setWindowRead(null);
    void client.getWindow(siteId, day).then((loaded) => {
      if (active) {
        setWindowRead(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId, day, open]);

  const choose = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(patch)) {
      if (value === null) {
        next.delete(key);
      } else {
        next.set(key, value);
      }
    }
    setParams(next);
  };

  if (cutover === null) {
    return <p>Loading the site&apos;s assessments.</p>;
  }

  return (
    <section aria-labelledby="site-dispatch-heading" className="dispatch-view durable-dispatch">
      <h2 id="site-dispatch-heading" className="identity-heading">
        Was the generator needed?
      </h2>
      <LocalViews label={DURABLE_DISPATCH_VIEWS_LABEL} current={view} params={params} />
      <DayPicker day={day} onDay={(next) => choose({ day: next, revision: null, block: null })} />
      {cutover.status !== "loaded" ? (
        <Panel heading="Dispatch unavailable" headingId="durable-dispatch-unavailable-heading">
          <p data-dispatch-cutover="unreadable">
            {cutover.status === "unavailable" && cutover.message !== null
              ? cutover.message
              : "Whether the stored dispatch assessment may be shown could not be checked."}
          </p>
        </Panel>
      ) : !cutover.value.permitted ? (
        <ClosedCutover state={cutover.value} />
      ) : windowRead === null ? (
        <p>Loading the site&apos;s assessments.</p>
      ) : windowRead.status !== "loaded" ? (
        <Panel heading="Dispatch unavailable" headingId="durable-dispatch-window-unavailable-heading">
          <p data-dispatch-window="unreadable">
            {windowRead.status === "not_found"
              ? "This site has no dispatch assessment record."
              : (windowRead.message ?? "The selected day could not be read.")}
          </p>
        </Panel>
      ) : (
        <WindowView
          siteId={siteId}
          client={client}
          read={windowRead.value}
          comparison={cutover.value.comparison}
          view={view}
          revisionId={revisionId}
          block={params.get("block")}
          choose={choose}
          params={params}
        />
      )}
    </section>
  );
}

function DayPicker({ day, onDay }: { day: string; onDay: (day: string) => void }) {
  const [draft, setDraft] = useState(day);
  useEffect(() => setDraft(day), [day]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (isDay(draft)) {
      onDay(draft);
    }
  };
  return (
    <form className="dispatch-day" onSubmit={submit} aria-label="Assessed day">
      <button type="button" className="dispatch-day__button" onClick={() => onDay(shiftDay(day, -1))}>
        Previous day
      </button>
      <label>
        Day (UTC){" "}
        <input type="date" value={draft} onChange={(event) => setDraft(event.target.value)} data-dispatch-day={day} />
      </label>
      <button type="submit" className="dispatch-day__button">
        Show
      </button>
      <button type="button" className="dispatch-day__button" onClick={() => onDay(shiftDay(day, 1))}>
        Next day
      </button>
    </form>
  );
}

function ClosedCutover({ state }: { state: CutoverState }) {
  return (
    <>
      <Panel heading="Dispatch results are not shown yet" headingId="durable-dispatch-closed-heading">
        <p data-dispatch-cutover="closed">
          The stored dispatch assessment for this site is not shown until it has been checked against the
          earlier results and its records are complete. Nothing is shown in its place.
        </p>
        <p className="chart-note" data-dispatch-cutover-reason>
          {state.unavailable ? "The check could not be read: " : "Why: "}
          {state.reason}
        </p>
      </Panel>
      {state.comparison ? <ComparisonPanel summary={state.comparison} /> : null}
    </>
  );
}

function WindowView({
  siteId,
  client,
  read,
  comparison,
  view,
  revisionId,
  block,
  choose,
  params,
}: {
  siteId: string;
  client: PerformanceDispatchClient;
  read: DispatchWindow;
  comparison: ComparisonSummary | null;
  view: "overview" | "analysis";
  revisionId: string | null;
  block: string | null;
  choose: (patch: Record<string, string | null>) => void;
  params: URLSearchParams;
}) {
  const [detail, setDetail] = useState<EvidenceRead<RevisionDetail> | null>(null);

  useEffect(() => {
    if (revisionId === null) {
      setDetail(null);
      return;
    }
    let active = true;
    setDetail(null);
    void client.getRevision(siteId, revisionId).then((loaded) => {
      if (active) {
        setDetail(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId, revisionId]);

  const inWindow = read.intervals.find((item) => item.id === revisionId) ?? null;
  const loaded = detail?.status === "loaded" ? detail.value : null;
  const selected: AssessmentRevision | null = inWindow ?? loaded;
  const blockIndex = block === null ? null : Number(block);
  const segment =
    selected !== null && blockIndex !== null && Number.isInteger(blockIndex)
      ? (selected.result.segments[blockIndex] ?? null)
      : null;

  return (
    <div className="durable-dispatch__body" data-dispatch-status={read.status}>
      <StatusLine read={read} />
      {view === "analysis" ? (
        <AnalysisView read={read} selected={selected} segment={segment} comparison={comparison} detail={loaded} />
      ) : (
        <>
          <p className="overview-note" data-dispatch-question>
            For each period the generator ran, this asks whether the available solar power and the battery could
            have met the site demand instead. A period, or a 15-minute block of one, is Needed (a recorded
            reason required the generator), Possibly avoidable (the reported available solar power and battery
            output limit were above the demand; a bounded estimate, not proof of wasted fuel) or Cannot determine
            (records needed are missing or conflicting). Times are UTC.
          </p>
          <DayTotals read={read} />
          <div className="durable-dispatch__pair">
            <Panel heading="Generator periods and 15-minute blocks" headingId="durable-dispatch-blocks-heading">
              <PeriodsAndBlocks
                read={read}
                selected={selected}
                blockIndex={segment === null ? null : blockIndex}
                onPeriod={(id) => choose({ revision: id, block: null })}
                onBlock={(id, index) => choose({ revision: id, block: String(index) })}
              />
            </Panel>
            <Panel heading="Selected period" headingId="durable-dispatch-selected-heading">
              <SelectedPeriod
                read={read}
                revisionId={revisionId}
                inWindow={inWindow}
                detail={detail}
                segment={segment}
                analysisSearch={localViewSearch(params, "analysis")}
              />
            </Panel>
          </div>
          <LimitationsPanel read={read} />
          <CoveragePanel read={read} />
          {comparison ? <ComparisonLine summary={comparison} /> : null}
        </>
      )}
      {loaded !== null && view === "overview" ? (
        <EvidencePanel detail={loaded} segment={segment} windowNote={read.demo_annotations} />
      ) : null}
    </div>
  );
}

function StatusLine({ read }: { read: DispatchWindow }) {
  const words = STATUS_WORDS[read.status] ?? { label: read.status, sentence: "" };
  return (
    <div className={`dispatch-status dispatch-status--${read.status.toLowerCase()}`} role="status">
      <p>
        <strong data-dispatch-status-label={read.status}>{words.label}.</strong> {words.sentence}
      </p>
      {read.status_reasons.length > 0 ? (
        <ul className="dispatch-status__reasons">
          {read.status_reasons.map((reason) => (
            <li key={reason} data-status-reason={reason.split(":")[0]}>
              {reasonWords(reason)}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="chart-note">
        {read.window.start.slice(0, 10)} · assessment rules {read.model_version}
        {read.selection ? ` · result made with ${read.selection.model_version}` : ""}
      </p>
    </div>
  );
}

function portion(read: DispatchWindow, key: string): number {
  return read.intervals.reduce((sum, item) => sum + (minutes(item.result.portions_minutes?.[key]) ?? 0), 0);
}

function DayTotals({ read }: { read: DispatchWindow }) {
  if (read.intervals.length === 0) {
    return null;
  }
  const low = read.intervals.reduce((sum, item) => sum + (minutes(item.result.interval.lower_minutes) ?? 0), 0);
  const open = read.intervals.some((item) => minutes(item.result.interval.upper_minutes) === null);
  const high = read.intervals.reduce(
    (sum, item) => sum + (minutes(item.result.interval.upper_minutes) ?? minutes(item.result.interval.lower_minutes) ?? 0),
    0,
  );
  const cards: [string, string, string, string][] = [
    [
      "Generator operation",
      open ? `at least ${durationText(low)}` : low === high ? durationText(low) : `${durationText(low)} to ${durationText(high)}`,
      "From reported on/off states; start and stop are bounded, not exact",
      "operation",
    ],
    ["Needed", durationText(portion(read, "necessary")), "A recorded reason required the generator", "needed"],
    [
      "Possibly avoidable",
      durationText(portion(read, "candidate")),
      "Only the blocks that qualify; never the whole period",
      "avoidable",
    ],
    ["Cannot determine", durationText(portion(read, "indeterminate")), "Records missing or conflicting", "unknown"],
  ];
  return (
    <ul className="dispatch-cards" aria-label="Day totals">
      {cards.map(([label, value, note, key]) => (
        <li key={key} className="dispatch-card" data-total={key}>
          <span className="dispatch-card__label">{label}</span>
          <span className="dispatch-card__value">{value}</span>
          <span className="dispatch-card__note">{note}</span>
        </li>
      ))}
    </ul>
  );
}

function PeriodsAndBlocks({
  read,
  selected,
  blockIndex,
  onPeriod,
  onBlock,
}: {
  read: DispatchWindow;
  selected: AssessmentRevision | null;
  blockIndex: number | null;
  onPeriod: (id: string) => void;
  onBlock: (id: string, index: number) => void;
}) {
  if (read.intervals.length === 0) {
    return (
      <p data-dispatch-empty>
        {read.selection === null
          ? "No result exists for this day."
          : "No generator period was assessed for this day. The limitations below say why, where one applies."}
      </p>
    );
  }
  const dayStart = Date.parse(read.window.start);
  const span = Date.parse(read.window.end) - dayStart;
  const at = (instant: string) => ((Date.parse(instant) - dayStart) / span) * 100;
  const current = selected !== null && read.intervals.some((item) => item.id === selected.id) ? selected : null;
  return (
    <>
      <ol className="dispatch-periods">
        {read.intervals.map((item) => {
          const iv = item.result.interval;
          return (
            <li key={item.id}>
              <button
                type="button"
                className="dispatch-period"
                aria-pressed={current?.id === item.id}
                data-revision-id={item.id}
                onClick={() => onPeriod(item.id)}
              >
                <ClaimBadge level={item.claim_level} label={outcome(item.claim_level)} />{" "}
                {clock(iv.first_on)} to {iv.last_on ? clock(iv.last_on) : "open"} UTC
              </button>
            </li>
          );
        })}
      </ol>
      <div className="dispatch-track" aria-hidden="true">
        {read.intervals.flatMap((item) =>
          item.result.segments.map((seg, index) => (
            <span
              key={`${item.id}-${index}`}
              className={`dispatch-track__block dispatch-fill--${CLASS_FILL[seg.classification] ?? "unknown"}`}
              style={{ left: `${at(seg.start)}%`, width: `${Math.max(at(seg.end) - at(seg.start), 0.4)}%` }}
            />
          )),
        )}
      </div>
      <p className="chart-note dispatch-track__axis" aria-hidden="true">
        <span>00:00</span>
        <span>06:00</span>
        <span>12:00</span>
        <span>18:00</span>
        <span>24:00</span>
      </p>
      {current === null ? (
        <p className="chart-note">Select a period to see its 15-minute blocks.</p>
      ) : (
        <>
          <ol className="dispatch-blocks" aria-label="15-minute blocks of the selected period">
            {current.result.segments.map((seg, index) => (
              <li key={seg.start} style={{ flexGrow: Math.max(minutes(seg.minutes) ?? 15, 1) }}>
                <button
                  type="button"
                  className={`dispatch-block dispatch-fill--${CLASS_FILL[seg.classification] ?? "unknown"}`}
                  aria-pressed={blockIndex === index}
                  aria-label={`${clock(seg.start)} to ${clock(seg.end)}: ${outcome(seg.classification)}`}
                  title={`${clock(seg.start)}–${clock(seg.end)} ${outcome(seg.classification)}`}
                  data-block={index}
                  onClick={() => onBlock(current.id, index)}
                />
              </li>
            ))}
          </ol>
          <p className="chart-note">
            Select a block to see what the readings show and open its records. Blocks are coloured Needed, Possibly
            avoidable or Cannot determine; gaps between reports are not filled in.
          </p>
        </>
      )}
      <ul className="graphic-legend dispatch-legend" aria-label="Legend">
        <li>
          <span className="dispatch-swatch dispatch-fill--needed" /> Needed
        </li>
        <li>
          <span className="dispatch-swatch dispatch-fill--avoidable" /> Possibly avoidable
        </li>
        <li>
          <span className="dispatch-swatch dispatch-fill--unknown" /> Cannot determine
        </li>
      </ul>
    </>
  );
}

function SelectedPeriod({
  read,
  revisionId,
  inWindow,
  detail,
  segment,
  analysisSearch,
}: {
  read: DispatchWindow;
  revisionId: string | null;
  inWindow: AssessmentRevision | null;
  detail: EvidenceRead<RevisionDetail> | null;
  segment: DispatchSegment | null;
  analysisSearch: string;
}) {
  if (revisionId === null) {
    return <p className="chart-note">No period selected.</p>;
  }
  if (inWindow === null && detail === null) {
    return <p>Loading the assessment.</p>;
  }
  if (inWindow === null && detail !== null && detail.status !== "loaded") {
    return (
      <p data-dispatch-selected-missing>
        {detail.status === "not_found"
          ? "The selected assessment revision does not exist for this site. No other result has been put in its place."
          : (detail.message ?? "The selected assessment revision could not be read.")}
      </p>
    );
  }
  const revision = (inWindow ?? (detail?.status === "loaded" ? detail.value : null)) as AssessmentRevision;
  const full = detail?.status === "loaded" ? detail.value : null;
  const iv = revision.result.interval;
  const pinned = inWindow === null;
  const olderRule = full?.model_note ?? null;
  return (
    <div data-selected-revision={revision.id}>
      {pinned ? (
        <p className="dispatch-pinned" data-dispatch-pinned>
          This is a stored result that is not the current one for {read.window.start.slice(0, 10)}. It is shown
          exactly as it was recorded, for reference.
        </p>
      ) : null}
      {olderRule !== null ? (
        <p className="dispatch-pinned" data-older-rule>
          Older rule result: made with {revision.model_version}; the current rules are {read.model_version}.
        </p>
      ) : null}
      {read.stale && !pinned ? (
        <p className="dispatch-pinned" data-dispatch-stale-selection>
          {STATUS_WORDS[read.status]?.label ?? read.status}: this result is kept for reference and is not current.
        </p>
      ) : null}
      <FactList>
        <Fact term="Outcome">
          <ClaimBadge level={revision.claim_level} label={outcome(revision.claim_level)} />
        </Fact>
        <Fact term="Generator ran">
          {clock(iv.first_on)} to {iv.last_on ? clock(iv.last_on) : "open"} UTC
          {iv.off_before || iv.off_after
            ? ` (last seen off ${clock(iv.off_before)}, next seen off ${clock(iv.off_after)})`
            : ""}
        </Fact>
        <Fact term="Needed / possibly avoidable / cannot determine">
          {["necessary", "candidate", "indeterminate"]
            .map((key) => durationText(minutes(revision.result.portions_minutes?.[key]) ?? 0))
            .join(" / ")}
        </Fact>
        {revision.result.binding_constraints?.length ? (
          <Fact term="What held the generator on">
            {revision.result.binding_constraints.map(constraintWords).join("; ")}
          </Fact>
        ) : null}
        {revision.result.limitations?.length ? (
          <Fact term="Limits on this period">
            {groupLimitations(revision.result.limitations)
              .map((group) => limitationWords(group.code))
              .join("; ")}
          </Fact>
        ) : null}
        <Fact term="Stored result">
          Revision {revision.revision_no} · <code>{revision.id}</code>
        </Fact>
      </FactList>
      {segment !== null ? (
        <div className="dispatch-block-detail" data-selected-block={segment.start}>
          <h3>
            Block {clock(segment.start)} to {clock(segment.end)} UTC: {outcome(segment.classification)}
          </h3>
          <ul>
            {segment.load_kw ? <li>Site demand {segment.load_kw} kW.</li> : null}
            {segment.binding_constraint ? <li>{constraintWords(segment.binding_constraint)}.</li> : null}
            {(segment.missing ?? []).map((item) => (
              <li key={item}>Missing: {item}</li>
            ))}
            {segment.observed === false ? <li>No report falls inside this block; it is bounded by its neighbours.</li> : null}
          </ul>
        </div>
      ) : null}
      <p className="chart-note">
        <Link to={{ search: analysisSearch }}>See how the readings lead to this outcome</Link>
      </p>
    </div>
  );
}

function LimitationsPanel({ read }: { read: DispatchWindow }) {
  const groups = groupLimitations(read.limitations);
  return (
    <Panel heading="What limits this day's result" headingId="durable-dispatch-limits-heading">
      {groups.length === 0 ? (
        <p data-dispatch-limitations="none">No limitation is recorded for this day&apos;s result.</p>
      ) : (
        <ul className="dispatch-limits">
          {groups.map((group) => (
            <li key={group.code} data-limitation={group.code}>
              {limitationWords(group.code)}
              {group.items.length > 1 ? ` (${group.items.length} places)` : ""}.
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function CoveragePanel({ read }: { read: DispatchWindow }) {
  const rows = Object.entries(read.coverage ?? {});
  return (
    <Panel heading="Accepted sample coverage" headingId="durable-dispatch-coverage-heading">
      {rows.length === 0 ? (
        <p>No record coverage exists for this day.</p>
      ) : (
        <DataTable labelledBy="durable-dispatch-coverage-heading">
          <thead>
            <tr>
              <th scope="col">Input</th>
              <th scope="col">Set up</th>
              <th scope="col">Accepted readings</th>
              <th scope="col">Not good quality</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([role, item]) => (
              <tr key={role} data-coverage-role={role}>
                <th scope="row">{roleWords(role)}</th>
                <td>{coverageWords(item.status)}</td>
                <td>{item.readings}</td>
                <td>{item.not_good}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      <p className="chart-note">
        {read.evidence_count} accepted records behind this day&apos;s result. A reading counted here is a report the
        site sent and AssetOps accepted; gaps between reports are not filled in.
      </p>
    </Panel>
  );
}

function ComparisonLine({ summary }: { summary: ComparisonSummary }) {
  return (
    <p className="chart-note" data-comparison-outcome={summary.outcome} data-comparison-empty={summary.empty_set}>
      {summary.empty_set
        ? "Checked against the earlier file-based results: there were none for this site, so nothing could be compared. This is not a match."
        : `Checked against the earlier file-based results: ${summary.counts.MATCH ?? 0} agree, ${
            summary.counts.INTENTIONAL_DELTA ?? 0
          } differ because of a documented rule change, ${summary.counts.MISSING_SOURCE ?? 0} cite records that were never accepted, ${
            summary.counts.UNPROVEN ?? 0
          } are not proven.`}
    </p>
  );
}

function EvidencePanel({
  detail,
  segment,
  windowNote,
}: {
  detail: RevisionDetail;
  segment: DispatchSegment | null;
  windowNote: DemoAnnotation[];
}) {
  const wanted = segment?.evidence_ids ? new Set(segment.evidence_ids) : null;
  const rows = wanted === null ? detail.evidence : detail.evidence.filter((item) => wanted.has(item.evidence_id));
  const shown = rows.slice(0, 60);
  const notes = detail.demo_annotations.length > 0 ? detail.demo_annotations : windowNote;
  return (
    <Panel heading="Accepted records behind the selected result" headingId="durable-dispatch-evidence-heading">
      <p className="chart-note" data-evidence-scope={segment === null ? "period" : "block"}>
        {segment === null
          ? `All ${detail.evidence.length} accepted records of this stored result.`
          : `${rows.length} accepted records for the block ${clock(segment.start)} to ${clock(segment.end)} UTC.`}
        {shown.length < rows.length ? ` The first ${shown.length} are listed.` : ""}
      </p>
      <DataTable labelledBy="durable-dispatch-evidence-heading">
        <thead>
          <tr>
            <th scope="col">Taken at (UTC)</th>
            <th scope="col">Input</th>
            <th scope="col">Value</th>
            <th scope="col">Quality</th>
            <th scope="col">Record</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((item) => (
            <tr key={item.evidence_id} data-evidence-id={item.evidence_id}>
              <td>{item.source_time ?? `${item.interval_start ?? "?"} to ${item.interval_end ?? "?"}`}</td>
              <td>{roleWords(item.role)}</td>
              <td>
                {item.value ?? "none"} {item.unit ?? ""}
              </td>
              <td>{item.quality}</td>
              <td>
                <RecordProvenance item={item} />
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      <ConfigurationNote detail={detail} />
      {notes.length > 0 ? <DemoNotes notes={notes} /> : null}
    </Panel>
  );
}

function RecordProvenance({ item }: { item: AcceptedEvidenceItem }) {
  return (
    <Disclosure name={`record-${item.evidence_id}`} summary={<code>{item.evidence_id.slice(0, 8)}</code>}>
      <FactList>
        <Fact term="Accepted record">
          <code>{item.evidence_id}</code>
        </Fact>
        <Fact term="Gateway">
          <code>{item.gateway_id}</code>
        </Fact>
        <Fact term="Source">
          <code>{item.source_id}</code> · series {item.sequence_epoch} · number {item.sequence}
        </Fact>
        <Fact term="Batch">
          <code>{item.batch_id}</code>
        </Fact>
        <Fact term="Message">
          <code>{item.message_id}</code>
        </Fact>
        <Fact term="Accepted at">{item.accepted_at}</Fact>
        {item.selection_note ? <Fact term="Note">{item.selection_note}</Fact> : null}
      </FactList>
    </Disclosure>
  );
}

function ConfigurationNote({ detail }: { detail: RevisionDetail }) {
  const accepted = new Set(
    detail.evidence
      .map((item) => (item.as_accepted as { foundation_revision_id?: string } | undefined)?.foundation_revision_id)
      .filter((id): id is string => typeof id === "string"),
  );
  const selected = detail.selected_configuration.foundation_revision_ids;
  const same = [...accepted].every((id) => selected.includes(id));
  return (
    <p className="chart-note" data-configuration-note={same ? "same" : "differs"}>
      {same
        ? "The records were accepted under the same site configuration the assessment used."
        : `Some records were accepted under an earlier site configuration (${[...accepted].join(", ")}); the assessment used the configuration in force for the day (${selected.join(", ")}).`}
    </p>
  );
}

function DemoNotes({ notes }: { notes: DemoAnnotation[] }) {
  return (
    <aside className="dispatch-demo-notes" data-demo-annotations={notes.length} aria-label="Demonstration data notes">
      <h3>Note supplied with the demonstration data</h3>
      <p>
        These notes come from the demonstration data&apos;s own description. They are not records AssetOps
        accepted and they do not change the result above.
      </p>
      <ul>
        {notes.map((note, index) => (
          <li key={index}>
            {String(note.case_label ?? note.label ?? "labelled case")}
            {Array.isArray(note.matched_evidence_ids) ? ` (${note.matched_evidence_ids.length} records)` : ""}
          </li>
        ))}
      </ul>
    </aside>
  );
}

function ComparisonPanel({ summary }: { summary: ComparisonSummary }) {
  return (
    <Panel heading="Comparison with earlier file-based results" headingId="durable-dispatch-comparison-heading">
      <p data-comparison-outcome={summary.outcome} data-comparison-empty={summary.empty_set}>
        <strong>{summary.outcome}.</strong> {summary.statement}
      </p>
      <FactList>
        {Object.entries(summary.counts).map(([key, value]) => (
          <Fact key={key} term={key}>
            {value}
          </Fact>
        ))}
        <Fact term="Rules compared">{summary.model_version ?? "not recorded"}</Fact>
        <Fact term="Compared at">{summary.compared_at}</Fact>
        <Fact term="Report">
          <code>{summary.report_id}</code>
        </Fact>
      </FactList>
      {Object.keys(summary.lineage_breaks ?? {}).length > 0 ? (
        <p data-lineage-breaks>Record lineage breaks: {JSON.stringify(summary.lineage_breaks)}</p>
      ) : null}
      {summary.claims.length > 0 ? (
        <ul className="dispatch-comparison-claims">
          {summary.claims.map((claim, index) => (
            <li key={claim.legacy_assessment_id ?? index} data-comparison-class={claim.class}>
              <strong>{claim.class}</strong> · {claim.legacy_assessment_id} ({claim.legacy_claim ?? "?"} to{" "}
              {claim.postgres_claim ?? "none"}). {claim.reason ?? ""}
              {claim.class === "MISSING_SOURCE" ? (
                <span data-missing-message-ids>
                  {" "}
                  Missing records: {(claim.missing_message_ids ?? []).join(", ") || "none cited"}. This needs
                  remediation or a separate migration decision; it is not a match.
                </span>
              ) : null}
              {claim.class === "INTENTIONAL_DELTA" && claim.rule_change ? (
                <span data-delta-rule={claim.rule}>
                  {" "}
                  Rule {claim.rule} ({claim.rule_change.from} to {claim.rule_change.to}, table rows{" "}
                  {claim.rule_change.table_rows}): {claim.rule_change.explanation}. Interval limitations:{" "}
                  {(claim.interval_limitations ?? []).join("; ")}. Compared records:{" "}
                  {(claim.compared_evidence_ids ?? []).join(", ")}.
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}

function AnalysisView({
  read,
  selected,
  segment,
  comparison,
  detail,
}: {
  read: DispatchWindow;
  selected: AssessmentRevision | null;
  segment: DispatchSegment | null;
  comparison: ComparisonSummary | null;
  detail: RevisionDetail | null;
}) {
  const result = selected?.result ?? null;
  return (
    <>
      <div className="durable-dispatch__pair">
        <Panel heading="Constraint comparison" headingId="durable-dispatch-constraints-heading">
          {selected === null ? (
            <p className="chart-note">Select a period on the Overview to compare its readings with its limits.</p>
          ) : (
            <DataTable labelledBy="durable-dispatch-constraints-heading">
              <thead>
                <tr>
                  <th scope="col">Block (UTC)</th>
                  <th scope="col">Outcome</th>
                  <th scope="col">Demand</th>
                  <th scope="col">Spare capacity</th>
                  <th scope="col">Recorded reason or missing input</th>
                </tr>
              </thead>
              <tbody>
                {(segment === null ? selected.result.segments : [segment]).map((seg) => (
                  <tr key={seg.start} data-constraint-block={seg.start}>
                    <td>
                      {clock(seg.start)}–{clock(seg.end)}
                    </td>
                    <td>{outcome(seg.classification)}</td>
                    <td>{seg.load_kw ? `${seg.load_kw} kW` : "not reported"}</td>
                    <td>{seg.margin_kw ? `${seg.margin_kw} kW` : "not shown"}</td>
                    <td>{[...(seg.reasons ?? []), ...(seg.missing ?? []).map((m) => `missing: ${m}`)].join("; ")}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
        </Panel>
        <Panel heading="Coverage, confidence and alternatives" headingId="durable-dispatch-confidence-heading">
          <FactList>
            <Fact term="Confidence">
              {result?.confidence
                ? `${result.confidence.level.toLowerCase()}: ${result.confidence.basis.join("; ")}`
                : "no period selected"}
            </Fact>
            <Fact term="Record series used">
              {read.selection
                ? `${read.selection.cohort_status}${read.selection.cohort.reason ? `: ${read.selection.cohort.reason}` : ""}`
                : "none"}
            </Fact>
            {Object.entries(read.unavailable).map(([key, value]) => (
              <Fact key={key} term={key.replace(/_/g, " ")}>
                <span data-unavailable={key}>Not yet available. {value.replace(/^UNAVAILABLE:\s*/, "")}</span>
              </Fact>
            ))}
            {result?.alternatives
              ? Object.entries(result.alternatives).map(([key, value]) => (
                  <Fact key={`alt-${key}`} term={`Alternative: ${key.replace(/_/g, " ")}`}>
                    {value}
                  </Fact>
                ))
              : null}
            {result?.candidate_bound ? <Fact term="Possibly avoidable bound">{result.candidate_bound}</Fact> : null}
          </FactList>
        </Panel>
      </div>
      <Panel heading="Fuel, money and Finding comparison" headingId="durable-dispatch-gated-heading">
        <p data-dispatch-gated>
          Not yet available. This assessment makes no fuel quantity, saving or money claim, and an interval result
          is not a Finding. Those need later, separately reviewed work.
        </p>
      </Panel>
      <Panel heading="Stored assessment record" headingId="durable-dispatch-record-heading">
        <FactList>
          <Fact term="Status">
            <code>{read.status}</code>
          </Fact>
          {read.status_reasons.map((reason) => (
            <Fact key={reason} term="Status reason">
              <code>{reason}</code>
            </Fact>
          ))}
          <Fact term="Window">
            {read.window.start} to {read.window.end} ({read.window.calendar})
          </Fact>
          {read.selection ? (
            <>
              <Fact term="Selected run">
                <code>{read.selection.run_id}</code> · {read.selection.model_version}
              </Fact>
              <Fact term="Input digest">
                <code>{read.selection.input_sha256}</code>
              </Fact>
              <Fact term="Configuration digest">
                <code>{read.selection.configuration_sha256}</code>
              </Fact>
              <Fact term="Foundation revisions">{read.selection.foundation_revision_ids.join(", ")}</Fact>
              <Fact term="Knowledge cutoff">
                {read.selection.knowledge_cutoff} ({read.selection.knowledge_cutoff_label})
              </Fact>
              <Fact term="Built at">{read.selection.built_at}</Fact>
            </>
          ) : null}
          {Object.entries(read.watermarks ?? {}).map(([key, value]) => (
            <Fact key={key} term={`Watermark ${key.replace(/_/g, " ")}`}>
              {value ?? "none"}
            </Fact>
          ))}
          {read.jobs.map((job) => (
            <Fact key={job.id} term="Recompute job">
              <code>{job.id}</code> {job.status} · attempts {job.attempts}
              {job.last_error ? ` · ${job.last_error}` : ""}
            </Fact>
          ))}
          {selected ? (
            <Fact term="Selected revision">
              <code>{selected.id}</code> · {selected.assessment_key} · revision {selected.revision_no} ·{" "}
              {selected.model_version}
            </Fact>
          ) : null}
          {detail?.model_note ? <Fact term="Model note">{detail.model_note}</Fact> : null}
        </FactList>
        {detail !== null && detail.history.length > 0 ? (
          <>
            <h3>Revisions of this period</h3>
            <ol className="dispatch-history">
              {detail.history.map((item) => (
                <li key={item.id} data-history-revision={item.id}>
                  <Link to={{ search: `?day=${item.window_start.slice(0, 10)}&revision=${item.id}&view=analysis` }}>
                    Revision {item.revision_no} · {item.model_version} · {outcome(item.claim_level)}
                  </Link>
                  {item.id === detail.id ? " (shown)" : ""}
                </li>
              ))}
            </ol>
          </>
        ) : null}
        {read.limitations.length > 0 ? (
          <Disclosure name="window-limitations" summary={`All ${read.limitations.length} recorded limitations`}>
            <ul className="dispatch-limits dispatch-limits--raw">
              {read.limitations.map((item, index) => (
                <li key={index}>
                  <code>{item}</code>
                </li>
              ))}
            </ul>
          </Disclosure>
        ) : null}
      </Panel>
      {comparison ? <ComparisonPanel summary={comparison} /> : null}
    </>
  );
}
