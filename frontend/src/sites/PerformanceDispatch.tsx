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

import { currentnessWords, DataTable, Disclosure, ExactReferences, Fact, FactList, HeadlineVisualCard, Panel, ProductStatus, type ProductWords } from "../ui";
import {
  clock,
  constraintWords,
  coverageWords,
  durationText,
  groupLimitations,
  isDay,
  limitationWords,
  minutes,
  missingWords,
  qualityWords,
  reasonWords,
  roleWords,
  shiftDay,
  stamp,
  STATUS_SENTENCES,
} from "./dispatchWords";
import { PeriodStrip, type StripTone } from "./periodStrip";
import { ClaimBadge, LocalViews, localView, localViewSearch, OUTCOME_WORDS } from "./findingPresentation";
import type { EvidenceRead } from "./siteEvidenceClient";
import type { FindingClient, FindingReadResult, FindingWindowBody } from "./findingClient";
import { LIFECYCLE_WORDS, WINDOW_STATE_WORDS } from "./findingWords";
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

/** One labelled exact value in a technical disclosure (the single-value vocabulary exemption). */
const REF = { "data-vocabulary-exempt": "source-reference" } as const;

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
  findings,
  findingHref,
}: {
  siteId: string;
  client: PerformanceDispatchClient;
  /** S4-01: the day's Findings, linked when both are given. */
  findings?: FindingClient;
  findingHref?: (findingId: string) => string;
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
        <ClosedCutover state={cutover.value} view={view} />
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
          findings={findings && findingHref ? { client: findings, href: findingHref } : null}
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

function ClosedCutover({ state, view }: { state: CutoverState; view: "overview" | "analysis" }) {
  const technical = view === "analysis";
  return (
    <>
      <Panel heading="Dispatch results are not shown yet" headingId="durable-dispatch-closed-heading">
        <div data-closed-plain>
          <p data-dispatch-cutover="closed">
            The stored dispatch assessment for this site is not shown until it has been checked against the
            earlier results and its records are complete. Nothing is shown in its place.
          </p>
          {technical ? (
            <p className="chart-note" data-dispatch-cutover-reason>
              {state.unavailable ? "The check could not be read: " : "Why: "}
              {state.reason}
            </p>
          ) : (
            <p className="chart-note" data-dispatch-cutover-plain>
              {state.unavailable
                ? "The check could not be read, so nothing can be shown yet."
                : state.comparison
                  ? "The check against the earlier results found differences that still need to be resolved."
                  : "The check against the earlier results has not been completed."}{" "}
              The Analysis view has the full detail.
            </p>
          )}
        </div>
      </Panel>
      {state.comparison ? technical ? <ComparisonPanel summary={state.comparison} /> : <ComparisonLine summary={state.comparison} /> : null}
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
  findings,
}: {
  siteId: string;
  client: PerformanceDispatchClient;
  findings: { client: FindingClient; href: (findingId: string) => string } | null;
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
      {view === "analysis" ? <StatusLine read={read} storedNotCurrent={selected !== null && inWindow === null} /> : null}
      {read.demo_annotations.length > 0 ? <DemoNotes notes={read.demo_annotations} /> : null}
      {view === "analysis" ? (
        <AnalysisView
          read={read}
          selected={selected}
          selectedIsCurrent={inWindow !== null}
          segment={segment}
          comparison={comparison}
          detail={loaded}
        />
      ) : (
        <>
          <HeadlineVisualCard
            dataName="dispatch-story"
            headingId="durable-dispatch-story-heading"
            title="Why the generator operated"
            description="Classifications describe the readings, not equipment condition"
            question="Why did the generator operate, and what can the readings support?"
            headline={<span data-dispatch-headline>{dayHeadline(read)}</span>}
            status={<StatusLine read={read} />}
            visual={
              <>
                <DayBlockStrip read={read} selected={selected} blockIndex={segment === null ? null : blockIndex} params={params} />
                <DayTotals read={read} />
              </>
            }
            meaning={
              <>
                <p data-dispatch-question>
                  For each period the generator operated, this asks whether the available solar power and the battery
                  could have met the site demand instead. A period, or a 15-minute block of one, is Needed (a recorded
                  reason required the generator), Possibly avoidable (the reported available solar power and battery
                  output limit were above the demand; a bounded estimate, not proof of wasted fuel) or Cannot
                  determine (records needed are missing or conflicting). Times are UTC.
                </p>
                <LimitationSummary read={read} />
              </>
            }
            destination={
              <Link to={{ search: localViewSearch(params, "analysis") }} data-dispatch-analysis-link>
                Open Dispatch › Analysis for how the readings lead to each outcome
              </Link>
            }
            references={<DispatchReferences read={read} />}
          />
          {findings ? <DayFindings siteId={siteId} day={read.window.start.slice(0, 10)} findings={findings} /> : null}
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

/** S4-01: the Findings recorded over this day, or why there is no settled answer. */
function DayFindings({
  siteId,
  day,
  findings,
}: {
  siteId: string;
  day: string;
  findings: { client: FindingClient; href: (findingId: string) => string };
}) {
  const [state, setState] = useState<FindingReadResult<FindingWindowBody> | null>(null);
  useEffect(() => {
    let active = true;
    setState(null);
    void findings.client.getFindingWindow(siteId, day).then((loaded) => {
      if (active) {
        setState(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [findings.client, siteId, day]);
  if (state === null) {
    return null;
  }
  if (state.status !== "loaded") {
    return (
      <p className="overview-note" data-day-findings="unavailable">
        Findings for this day could not be read.
      </p>
    );
  }
  const shown = state.value.findings.filter((f) => f.lifecycle !== "MERGED");
  return (
    <div className="overview-note" data-day-findings={state.value.state}>
      <p>
        <strong>Findings: </strong>
        {WINDOW_STATE_WORDS[state.value.state] ?? "The Finding state of this day is not known."}
      </p>
      {shown.length > 0 ? (
        <ul className="site-finding__inline">
          {shown.map((f) => {
            const id = String(f.finding_id ?? f.id ?? "");
            return (
              <li key={id}>
                <Link to={findings.href(id)} data-dispatch-finding={id}>
                  {LIFECYCLE_WORDS[f.lifecycle]?.label ?? "Finding"}: {clock(f.episode_start)}–{clock(f.episode_end)}{" "}
                  UTC →
                </Link>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

/**
 * W1-UX-03: the day's state words. The shared map owns the label and tone
 * (only CURRENT is positive; an unknown code is never positive and never
 * shown); the dispatch read keeps its own sentence.
 */
function statusWords(status: string): ProductWords {
  const shared = currentnessWords(status);
  const own = (STATUS_SENTENCES as Record<string, { sentence: string } | undefined>)[status];
  return own === undefined || shared.unrecognised ? shared : { ...shared, sentence: own.sentence };
}

function dayScope(read: DispatchWindow): string {
  return `Generator operation on ${read.window.start.slice(0, 10)} (UTC day)`;
}

/**
 * W1-UX-03 fix round 1 (F1): a stored version that is not in the day's
 * current set is never framed by the day's state. Its state line is the
 * shared non-current "earlier version" words, never the current tone.
 */
function storedVersionWords(read: DispatchWindow): ProductWords {
  return {
    ...currentnessWords("HISTORICAL"),
    sentence: `This is a stored version for ${read.window.start.slice(0, 10)}. It is shown as it was recorded, and it is not the current result.`,
  };
}

function StatusLine({ read, storedNotCurrent = false }: { read: DispatchWindow; storedNotCurrent?: boolean }) {
  const words = storedNotCurrent ? storedVersionWords(read) : statusWords(read.status);
  return (
    <div
      className={`dispatch-status dispatch-status--${storedNotCurrent ? "historical" : read.status.toLowerCase()}`}
      role="status"
      data-dispatch-status-label={read.status}
      data-dispatch-shown={storedNotCurrent ? "stored-not-current" : "day"}
    >
      <ProductStatus words={words} scope={dayScope(read)} asOf={read.current_basis?.read_at ?? null}>
        {read.status_reasons.length > 0 ? (
          <ul className="dispatch-status__reasons">
            {read.status_reasons.map((reason) => (
              <li key={reason} data-status-reason={reason.split(":")[0]}>
                {reasonWords(reason)}
              </li>
            ))}
          </ul>
        ) : null}
      </ProductStatus>
    </div>
  );
}

/** The few exact references behind the day's result: rule versions only, labelled. */
function DispatchReferences({ read }: { read: DispatchWindow }) {
  return (
    <ExactReferences
      name="dispatch-references"
      references={[
        { label: "Assessment rules in force", value: read.model_version },
        { label: "Rules the shown result was made with", value: read.selection?.model_version ?? null },
        { label: "Day state", value: read.status },
      ]}
    />
  );
}

/** A day's portion total; null (not known) when any period did not state it - never counted as zero. */
function portion(read: DispatchWindow, key: string): number | null {
  let total = 0;
  for (const item of read.intervals) {
    const value = minutes(item.result.portions_minutes?.[key]);
    if (value === null) return null;
    total += value;
  }
  return total;
}

function portionText(value: number | null): string {
  return value === null ? "not known" : durationText(value);
}

function operationText(read: DispatchWindow): string {
  const low = read.intervals.reduce((sum, item) => sum + (minutes(item.result.interval.lower_minutes) ?? 0), 0);
  const open = read.intervals.some((item) => minutes(item.result.interval.upper_minutes) === null);
  const high = read.intervals.reduce(
    (sum, item) => sum + (minutes(item.result.interval.upper_minutes) ?? minutes(item.result.interval.lower_minutes) ?? 0),
    0,
  );
  return open ? `at least ${durationText(low)}` : low === high ? durationText(low) : `${durationText(low)} to ${durationText(high)}`;
}

/** The lead answer, only as strong as the day's read. */
function dayHeadline(read: DispatchWindow): string {
  if (read.intervals.length === 0) {
    return read.selection === null
      ? "No result exists for this day, so nothing is concluded about the generator."
      : "No generator period was assessed on this day.";
  }
  const sentence = `The generator operated for ${operationText(read)}: ${portionText(portion(read, "candidate"))} possibly avoidable, ${portionText(portion(read, "necessary"))} needed and ${portionText(portion(read, "indeterminate"))} that cannot be determined.`;
  return read.status === "CURRENT" && !read.stale ? sentence : `From an earlier result that is not current: ${sentence}`;
}

const STRIP_TONE: Record<string, StripTone> = {
  NECESSARY: "necessary",
  CANDIDATE_AVOIDABLE: "avoidable",
  INDETERMINATE: "undetermined",
};

/**
 * Every assessed 15-minute block of the day on one strip, by outcome; each
 * block is an exact selection link (revision and block in the address).
 * Hours with no assessed block are left blank, never drawn as an outcome.
 */
function DayBlockStrip({
  read,
  selected,
  blockIndex,
  params,
}: {
  read: DispatchWindow;
  selected: AssessmentRevision | null;
  blockIndex: number | null;
  params: URLSearchParams;
}) {
  if (read.intervals.length === 0) return null;
  const href = (revision: string, index: number) => {
    const next = new URLSearchParams(params);
    next.set("revision", revision);
    next.set("block", String(index));
    return `?${next.toString()}`;
  };
  const segments = read.intervals.flatMap((item) =>
    item.result.segments.map((seg, index) => ({
      key: `${item.id}-${index}`,
      start: seg.start,
      end: seg.end,
      tone: STRIP_TONE[seg.classification] ?? ("not-known" as const),
      label: `${clock(seg.start)} to ${clock(seg.end)} UTC: ${outcome(seg.classification)}`,
      href: href(item.id, index),
      selected: selected?.id === item.id && blockIndex === index,
    })),
  );
  const count = (tone: StripTone) => segments.filter((x) => x.tone === tone).length;
  return (
    <PeriodStrip
      name="dispatch-day-blocks"
      title="The day's assessed 15-minute blocks, by outcome (select one to see its readings)"
      start={read.window.start}
      end={read.window.end}
      startText="00:00 UTC"
      endText="24:00 UTC"
      legend={[
        { tone: "necessary", label: "Needed" },
        { tone: "avoidable", label: "Possibly avoidable" },
        { tone: "undetermined", label: "Cannot determine" },
      ]}
      rows={[
        {
          key: "blocks",
          label: "Generator blocks",
          segments,
          summary: `${segments.length} assessed blocks: ${count("necessary")} needed, ${count("avoidable")} possibly avoidable, ${count("undetermined") + count("not-known")} cannot be determined.`,
        },
      ]}
    />
  );
}

/** The material limits beside the answer; the full list stays in its own panel below. */
function LimitationSummary({ read }: { read: DispatchWindow }) {
  const groups = groupLimitations(read.limitations);
  if (groups.length === 0) return null;
  return (
    <ul data-dispatch-limitation-summary>
      {groups.map((g) => (
        <li key={g.code}>{limitationWords(g.code)}</li>
      ))}
    </ul>
  );
}

function DayTotals({ read }: { read: DispatchWindow }) {
  if (read.intervals.length === 0) {
    return null;
  }
  const cards: [string, string, string, string][] = [
    [
      "Generator operation",
      operationText(read),
      "From reported on/off states; start and stop are bounded, not exact",
      "operation",
    ],
    ["Needed", portionText(portion(read, "necessary")), "A recorded reason required the generator", "needed"],
    [
      "Possibly avoidable",
      portionText(portion(read, "candidate")),
      "Only the blocks that qualify; never the whole period",
      "avoidable",
    ],
    ["Cannot determine", portionText(portion(read, "indeterminate")), "Records missing or conflicting", "unknown"],
  ];
  return (
    <>
      {read.stale ? (
        <p className="dispatch-pinned" data-totals-stale>
          {statusWords(read.status).label}: these totals come from an earlier result and are not current.
        </p>
      ) : null}
      <ul className="dispatch-cards" aria-label="Day totals">
        {cards.map(([label, value, note, key]) => (
          <li key={key} className="dispatch-card" data-total={key} data-stale={read.stale ? "true" : undefined}>
            <span className="dispatch-card__label">{label}</span>
            <span className="dispatch-card__value">{value}</span>
            <span className="dispatch-card__note">{read.stale ? "Not current. " : ""}{note}</span>
          </li>
        ))}
      </ul>
    </>
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

/** The not-current notice for a stored version outside the day's current set (Overview and Analysis). */
function PinnedNotice({ read }: { read: DispatchWindow }) {
  return (
    <p className="dispatch-pinned" data-dispatch-pinned>
      This is a stored result that is not the current one for {read.window.start.slice(0, 10)}. It is shown
      exactly as it was recorded, for reference.
    </p>
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
      {pinned ? <PinnedNotice read={read} /> : null}
      {olderRule !== null ? (
        <div className="dispatch-pinned" data-older-rule>
          <p>This result was made with an earlier version of the assessment rules than the version now in force.</p>
          <ExactReferences
            name="dispatch-older-rule-references"
            references={[
              { label: "Rules this result was made with", value: revision.model_version },
              { label: "Rules now in force", value: read.model_version },
            ]}
          />
        </div>
      ) : null}
      {read.stale && !pinned ? (
        <p className="dispatch-pinned" data-dispatch-stale-selection>
          {statusWords(read.status).label}: this result is kept for reference and is not current.
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
      </FactList>
      {segment !== null ? (
        <div className="dispatch-block-detail" data-selected-block={segment.start}>
          <h3>
            Block {clock(segment.start)} to {clock(segment.end)} UTC: {outcome(segment.classification)}
          </h3>
          <ul>
            {segment.load_kw ? <li>Site demand {segment.load_kw} kW.</li> : null}
            {segment.binding_constraint ? <li>{constraintWords(segment.binding_constraint)}.</li> : null}
            {(segment.missing ?? []).length > 0 ? (
              <li data-block-limited>
                Some readings this block needs are missing or limited; the Analysis view lists them.
              </li>
            ) : null}
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
  const noSeries =
    read.selection !== null && !["SELECTED_UNIQUE", "SELECTED_EXPLICIT"].includes(read.selection.cohort_status);
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
      <p className="chart-note" data-coverage-note>
        {noSeries
          ? `${read.current_basis?.accepted_reading_count ?? "Some"} accepted records exist for this day, but no single series of them was chosen, so none is used for a result. `
          : `${read.evidence_count} accepted records behind this day's result. `}
        A reading counted here is a report the site sent and AssetOps accepted; gaps between reports are not
        filled in.
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
  const shownAbove = new Set(windowNote.map((note) => JSON.stringify(note)));
  const notes = detail.demo_annotations.filter((note) => !shownAbove.has(JSON.stringify(note)));
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
              <td>{item.source_time ? stamp(item.source_time) : `${stamp(item.interval_start)} to ${stamp(item.interval_end)}`}</td>
              <td>{roleWords(item.role)}</td>
              <td>
                {item.value ?? "none"} {item.unit ?? ""}
              </td>
              <td>{qualityWords(item.quality)}</td>
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
        <Fact term="Accepted at (UTC)">{stamp(item.accepted_at)}</Fact>
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
    <Panel heading="Comparison with earlier results" headingId="durable-dispatch-comparison-heading">
      <Disclosure name="dispatch-comparison" summary="Technical details: how this day compares with the earlier results">
      <p data-comparison-outcome={summary.outcome} data-comparison-empty={summary.empty_set}>
        <strong {...REF}>{summary.outcome}</strong> <span {...REF}>{summary.statement}</span>
      </p>
      <FactList>
        {Object.entries(summary.counts).map(([key, value]) => (
          <Fact key={key} term="Count">
            <code {...REF}>{`${key}: ${value}`}</code>
          </Fact>
        ))}
        <Fact term="Rules compared">
          <code {...REF}>{summary.model_version ?? "not recorded"}</code>
        </Fact>
        <Fact term="Compared at">{summary.compared_at}</Fact>
        <Fact term="Report">
          <code {...REF}>{summary.report_id}</code>
        </Fact>
      </FactList>
      {Object.keys(summary.lineage_breaks ?? {}).length > 0 ? (
        <p data-lineage-breaks>
          Records that could not be traced: <code {...REF}>{JSON.stringify(summary.lineage_breaks)}</code>
        </p>
      ) : null}
      {summary.claims.length > 0 ? (
        <ul className="dispatch-comparison-claims">
          {summary.claims.map((claim, index) => (
            <li key={claim.legacy_assessment_id ?? index} data-comparison-class={claim.class}>
              <code {...REF}>{`${claim.class} · ${claim.legacy_assessment_id} (${claim.legacy_claim ?? "?"} to ${claim.postgres_claim ?? "none"}). ${claim.reason ?? ""}`}</code>
              {claim.class === "MISSING_SOURCE" ? (
                <span data-missing-message-ids>
                  {" "}
                  Missing records: <code {...REF}>{(claim.missing_message_ids ?? []).join(", ") || "none cited"}</code>. This needs
                  remediation or a separate migration decision; it is not a match.
                </span>
              ) : null}
              {claim.class === "INTENTIONAL_DELTA" && claim.rule_change ? (
                <span data-delta-rule={claim.rule}>
                  {" "}
                  Rule change: <code {...REF}>{`${claim.rule} (${claim.rule_change.from} to ${claim.rule_change.to}, table rows ${claim.rule_change.table_rows}): ${claim.rule_change.explanation}`}</code>. Limits: <code {...REF}>{(claim.interval_limitations ?? []).join("; ")}</code>. Compared records: <code {...REF}>{(claim.compared_evidence_ids ?? []).join(", ")}</code>.
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      </Disclosure>
    </Panel>
  );
}

const UNAVAILABLE_TERMS: Record<string, string> = {
  alternatives: "Other explanations",
  fuel_and_money: "Fuel and money",
  finding: "Finding comparison",
};

function confidenceWords(level: string): string {
  switch (level) {
    case "HIGH":
      return "High: the readings needed were present and agreed";
    case "MEDIUM":
      return "Medium: some readings needed were limited";
    case "LOW":
      return "Low: readings needed were missing or limited";
    default:
      return "Not stated";
  }
}

/**
 * W1-UX-03 (`analysis`): accepted readings, then the rule, then the bounded
 * conclusion, for the selected period or block. Every step comes from the
 * selected revision; nothing is concluded without one, and the conclusion
 * keeps its limits beside it.
 */
function ReadingsToOutcome({
  read,
  selected,
  selectedIsCurrent,
  segment,
}: {
  read: DispatchWindow;
  selected: AssessmentRevision | null;
  /** True only when `selected` is in `read.intervals`, the day's current set. */
  selectedIsCurrent: boolean;
  segment: DispatchSegment | null;
}) {
  if (selected === null) {
    return (
      <Panel heading="How the readings lead to the outcome" headingId="durable-dispatch-story-analysis-heading">
        <p className="headline-card__question">How do the readings lead to the outcome?</p>
        <p data-dispatch-story="none">
          No period is selected, so nothing is concluded here. Select a period or a 15-minute block on the Overview.
        </p>
      </Panel>
    );
  }
  const result = selected.result;
  const segments = segment === null ? result.segments : [segment];
  const missing = Array.from(new Set(segments.flatMap((s) => s.missing ?? [])));
  const unobserved = segments.filter((s) => s.observed === false).length;
  const demand = segment?.load_kw ? `${segment.load_kw} kW` : null;
  const spare = segment?.margin_kw ? `${segment.margin_kw} kW` : null;
  const constraints = Array.from(
    new Set([...(segment?.binding_constraint ? [segment.binding_constraint] : []), ...(segment === null ? (result.binding_constraints ?? []) : [])]),
  );
  const limits = groupLimitations(result.limitations ?? []);
  const scope = segment === null ? `the period ${clock(result.interval.first_on)} to ${clock(result.interval.last_on)} UTC` : `the block ${clock(segment.start)} to ${clock(segment.end)} UTC`;
  const conclusion = segment === null ? outcome(selected.claim_level) : outcome(segment.classification);
  return (
    <Panel heading="How the readings lead to the outcome" headingId="durable-dispatch-story-analysis-heading">
      <p className="headline-card__question">How do the readings lead to the outcome?</p>
      <ol className="dispatch-story" data-dispatch-story={segment === null ? "period" : "block"}>
        <li className="dispatch-story__step" data-dispatch-story-step="readings">
          <h3>What the accepted readings show</h3>
          <p>
            {`For ${scope}: ${plural(selected.evidence_ids.length, "accepted reading", "accepted readings")} used.`}
            {demand === null ? "" : ` Demand ${demand}.`}
            {spare === null ? "" : ` Spare solar and battery capacity ${spare}.`}
          </p>
          {missing.length === 0 && unobserved === 0 ? null : (
            <p data-dispatch-story-missing>
              {missing.length === 0 ? "" : `Missing: ${Array.from(new Set(missing.map(missingWords))).join(", ")}. `}
              {unobserved === 0 ? "" : `${plural(unobserved, "block was", "blocks were")} not observed directly.`}
            </p>
          )}
        </li>
        <li className="dispatch-story__step" data-dispatch-story-step="rule">
          <h3>The rule applied</h3>
          <p>
            A block is Possibly avoidable only when the reported available solar power and battery output limit were
            above the demand; Needed when a recorded reason required the generator; Cannot determine when readings
            it needs are missing or conflicting.
          </p>
          {constraints.length === 0 ? null : <p>{`What held the generator on: ${constraints.map(constraintWords).join("; ")}.`}</p>}
        </li>
        <li className="dispatch-story__step" data-dispatch-story-step="conclusion">
          <h3>What can be concluded</h3>
          <p data-dispatch-story-conclusion>
            {!selectedIsCurrent
              ? `${conclusion}, for ${scope}, from a stored version that is not the current result.`
              : read.status === "CURRENT" && !read.stale
                ? `${conclusion}, for ${scope}.`
                : `${conclusion}, for ${scope}, from an earlier result that is not current.`}
          </p>
          {limits.length === 0 ? null : (
            <ul data-dispatch-story-limits>
              {limits.map((g) => (
                <li key={g.code}>{limitationWords(g.code)}</li>
              ))}
            </ul>
          )}
          <p>This says nothing about fuel, savings or money.</p>
        </li>
      </ol>
    </Panel>
  );
}

function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

function AnalysisView({
  read,
  selected,
  selectedIsCurrent,
  segment,
  comparison,
  detail,
}: {
  read: DispatchWindow;
  selected: AssessmentRevision | null;
  selectedIsCurrent: boolean;
  segment: DispatchSegment | null;
  comparison: ComparisonSummary | null;
  detail: RevisionDetail | null;
}) {
  const result = selected?.result ?? null;
  return (
    <>
      {selected !== null && !selectedIsCurrent ? <PinnedNotice read={read} /> : null}
      <ReadingsToOutcome read={read} selected={selected} selectedIsCurrent={selectedIsCurrent} segment={segment} />
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
                    <td>
                      {[...(seg.reasons ?? []).map(constraintWords), ...(seg.missing ?? []).map((m) => `missing: ${missingWords(m)}`)].join("; ") ||
                        "none recorded"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          )}
        </Panel>
        <Panel heading="Coverage, confidence and alternatives" headingId="durable-dispatch-confidence-heading">
          <FactList>
            <Fact term="Confidence">
              {result?.confidence ? confidenceWords(result.confidence.level) : "no period selected"}
            </Fact>
            <Fact term="Record series used">
              {read.selection
                ? read.selection.cohort_status === "SELECTED_UNIQUE" || read.selection.cohort_status === "EXPLICIT"
                  ? "One settled series of records for this day"
                  : "No single settled series of records for this day; results are limited"
                : "none"}
            </Fact>
            {Object.entries(read.unavailable).map(([key]) => (
              <Fact key={key} term={UNAVAILABLE_TERMS[key] ?? "Another result"}>
                <span data-unavailable={key}>Not yet available.</span>
              </Fact>
            ))}
            {result?.alternatives && Object.keys(result.alternatives).length > 0 ? (
              <Fact term="Other explanations">
                {`${Object.keys(result.alternatives).length} recorded; their exact wording is in the technical details below.`}
              </Fact>
            ) : null}
            {result?.candidate_bound ? <Fact term="Possibly avoidable bound">Recorded; its exact wording is in the technical details below.</Fact> : null}
          </FactList>
        </Panel>
      </div>
      <Panel heading="Fuel, money and Finding comparison" headingId="durable-dispatch-gated-heading">
        <p data-dispatch-gated>
          Not yet available. This assessment makes no fuel quantity, saving or money claim, and an interval result
          is not itself a Finding; Findings recorded over this day are linked in Overview. Fuel and money need
          later, separately reviewed work.
        </p>
      </Panel>
      {detail !== null && detail.history.length > 0 ? (
        <Panel heading="Versions of this period" headingId="durable-dispatch-history-heading">
          <ol className="dispatch-history">
            {detail.history.map((item) => (
              <li key={item.id} data-history-revision={item.id}>
                <Link to={{ search: `?day=${item.window_start.slice(0, 10)}&revision=${item.id}&view=analysis` }}>
                  Version {item.revision_no}: {outcome(item.claim_level)}
                </Link>
                {item.id === detail.id ? " (shown)" : ""}
              </li>
            ))}
          </ol>
        </Panel>
      ) : null}
      <Panel heading="Stored assessment record" headingId="durable-dispatch-record-heading">
        <Disclosure name="dispatch-stored-record" summary="Technical details: stored record, versions and references">
        <FactList>
          {Object.entries(read.unavailable).map(([key, value]) => (
            <Fact key={`unavailable-${key}`} term="Recorded note on a result still to come">
              <code {...REF}>{`${key}: ${value}`}</code>
            </Fact>
          ))}
          {Object.entries(result?.alternatives ?? {}).map(([key, value]) => (
            <Fact key={`alt-${key}`} term="Other explanation, as recorded">
              <code {...REF}>{`${key}: ${value}`}</code>
            </Fact>
          ))}
          {result?.candidate_bound ? (
            <Fact term="Possibly avoidable bound, as recorded">
              <code {...REF}>{result.candidate_bound}</code>
            </Fact>
          ) : null}
          {result?.confidence ? (
            <Fact term="Confidence basis">
              <code {...REF}>{result.confidence.basis.join("; ")}</code>
            </Fact>
          ) : null}
          {read.selection?.cohort.reason ? (
            <Fact term="Record series state">
              <code {...REF}>{`${read.selection.cohort_status}: ${read.selection.cohort.reason}`}</code>
            </Fact>
          ) : null}
          <Fact term="Status">
            <code {...REF}>{read.status}</code>
          </Fact>
          {read.status_reasons.map((reason) => (
            <Fact key={reason} term="Status reason">
              <code {...REF}>{reason}</code>
            </Fact>
          ))}
          <Fact term="Window">
            {read.window.start} to {read.window.end} ({read.window.calendar})
          </Fact>
          {read.selection ? (
            <>
              <Fact term="Assessment batch and rules">
                <code {...REF}>{read.selection.run_id}</code> · <code {...REF}>{read.selection.model_version}</code>
              </Fact>
              <Fact term="Input reference">
                <code {...REF}>{read.selection.input_sha256}</code>
              </Fact>
              <Fact term="Configuration reference">
                <code {...REF}>{read.selection.configuration_sha256}</code>
              </Fact>
              <Fact term="Foundation revisions">{read.selection.foundation_revision_ids.join(", ")}</Fact>
              <Fact term="Knowledge cutoff">
                {read.selection.knowledge_cutoff} ({read.selection.knowledge_cutoff_label})
              </Fact>
              <Fact term="Prepared at">{read.selection.built_at}</Fact>
            </>
          ) : null}
          {Object.entries(read.watermarks ?? {}).map(([key, value]) => (
            <Fact key={key} term="Latest reading time used">
              <code {...REF}>{`${key}: ${value ?? "none"}`}</code>
            </Fact>
          ))}
          {read.jobs.map((job) => (
            <Fact key={job.id} term="Reassessment task">
              <code {...REF}>{`${job.id} ${job.status} · attempts ${job.attempts}${job.last_error ? ` · ${job.last_error}` : ""}`}</code>
            </Fact>
          ))}
          {selected ? (
            <Fact term="Selected revision">
              <code {...REF}>{`${selected.id} · ${selected.assessment_key} · ${selected.revision_no} · ${selected.model_version}`}</code>
            </Fact>
          ) : null}
          {detail?.model_note ? (
            <Fact term="Rule note">
              <code {...REF}>{detail.model_note}</code>
            </Fact>
          ) : null}
        </FactList>
        </Disclosure>
        {read.limitations.length > 0 ? (
          <Disclosure name="window-limitations" summary={`All ${read.limitations.length} recorded limitations`}>
            <ul className="dispatch-limits dispatch-limits--raw">
              {read.limitations.map((item, index) => (
                <li key={index}>
                  <code {...REF}>{item}</code>
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
