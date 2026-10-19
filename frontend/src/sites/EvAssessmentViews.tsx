import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  Badge,
  BigClaim,
  Breadcrumbs,
  type Crumb,
  DataTable,
  ExactReferences,
  KeyValues,
  MetricCard,
  MetricCards,
  PageHeader,
  Panel,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
  StatusBar,
} from "../ui";
import { UnavailableInline, UnavailableLinkEntry, UnavailableTab } from "../ui/UnavailableEntry";
import { coldWindowSearch } from "./coldAssessmentClient";
import { classificationWord, lifecycleWord } from "./coldAssessmentWords";
import { dayHm, hm } from "./coldFormat";
import type {
  EvAssessmentClient,
  EvDenominator,
  EvEnvelope,
  EvFindingDetailRead,
  EvRead,
  EvSessionDetailRead,
  EvSessionItem,
  EvSessionsRead,
  EvWindowQuery,
} from "./evAssessmentClient";
import "./w2-ev-assessment.css";

/*
 * W2-06 commit 5: an EV_CHARGING Site's `sessions` and `ev-finding` screens in their exact v69 panel slots
 * (`.agent/W2-06-build-spec.md` "Commit 5: UI route and copy dry-read", as overridden by "Run 5 rulings (r5)"
 * state copy and "Run 7 rulings (r6)" commit-5 dry-read):
 *
 *   sessions    1 Session service records, 2 How to read the denominator, 3 Cause remains bounded
 *   ev-finding  1 Bounded conclusion, 2 Operational context, 3 Recommended next step
 *
 * Every value comes from the selected EV reads. Refusals keep the same panel shells; a missing selection's null
 * counts are never shown as zero; a null link is an in-place labelled gap, never a click.
 */

export const EV_LOADING = "Loading the site's EV session assessment.";
export const EV_SESSIONS_HEADING_ID = "ev-sessions-heading";
export const EV_FINDING_HEADING_ID = "ev-finding-heading";

/* ---------- exact copy (spec Commit 5 ledger, r5 state copy, r6) ---------- */

export const EV_COPY = {
  pending: "New evidence is being assessed. The previous result may change.",
  historical: "This result reflects records known at the selected cutoff.",
  contradictory: "Accepted terminal records conflict, so a completed outcome is not claimed.",
  noSessions: "No charging sessions were observed in this window.",
  orphan: "A terminal record has no qualifying start in this window; it is not counted as an attempt.",
  simulation: "These records came from a registered simulation, not a live charger.",
  analysisGap: "Analysis view not available for this EV record",
  unknownSeparate: "Unknown is separate from failure.",
  causeFault: "A fault record and abort establish an interruption, not its component cause.",
  causeNone: "Cause not established from accepted records.",
  causeDisclosure: "Requested power, allocated limit, site import and charger diagnostics are needed to test competing explanations.",
  conclusion: "A connector fault and session abort were observed; component cause and unmet demand remain unknown.",
  limit: "The records do not establish charger hardware failure, vehicle fault or lost revenue.",
  withdrawn: "This finding is no longer supported by the selected evidence.",
  unsupported: "The selected records do not support an interruption conclusion.",
  nextStep: "Retrieve charger diagnostics and witness a complete session with start, end and meter records.",
  /** r9 M1-a: the whole accepted set is MIXED or UNKNOWN. */
  sourceUnassessable: "EV source provenance is mixed or unverified; session outcomes cannot be assessed.",
  /** r9 M1-c: one accepted record excluded by its exact source/binding. */
  recordUnverified: "Source or binding unverified for this record.",
} as const;

export function evRefusalText(read: Exclude<EvRead<unknown>, { status: "loaded" }>): string {
  if (read.status === "refused") {
    switch (read.httpStatus) {
      case 401:
        return "Sign in to view EV evidence.";
      case 403:
        return "You do not have access to this EV evidence.";
      case 404:
        return "This EV Site or record was not found.";
      case 422:
        return "Choose a valid UTC start and end, up to 31 days.";
      case 409:
        return "Selection changed. Reload this view.";
      default:
        break;
    }
  }
  return "EV evidence is temporarily unavailable. Retry.";
}

/* ---------- reads ---------- */

function useRead<T>(load: (() => Promise<EvRead<T>>) | null, key: string): EvRead<T> | null {
  const [state, setState] = useState<{ key: string; value: EvRead<T> } | null>(null);
  useEffect(() => {
    if (load === null) return undefined;
    let active = true;
    void load().then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // `load` is rebuilt every render; the key names what it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, load === null]);
  return state !== null && state.key === key ? state.value : null;
}

const windowKey = (w: EvWindowQuery) => `${w.from ?? ""}|${w.to ?? ""}|${w.known_at ?? ""}`;
const short = (id: string | null | undefined) => (id ? id.slice(0, 8) : "Unknown");
const count = (n: number | null | undefined) => (n === null || n === undefined ? "Unknown" : String(n));

/** A long stored identifier shown short, with its full value as the accessible name (full value also in the panel's disclosure). */
function ShortId({ value }: { value: string | null }) {
  if (value === null) return <>Unknown</>;
  if (value.length <= 12) return <>{value}</>;
  return (
    <span aria-label={value} title={value} data-ev-short-id>
      {`${value.slice(0, 11)}…`}
    </span>
  );
}

function Gap({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p className="not-available-yet v69-chart-note" data-panel-gap={id}>
      {children}
    </p>
  );
}

/* ---------- shared state lines ---------- */

type Currentness = "CURRENT" | "PENDING_RECOMPUTE" | "HISTORICAL" | "UNKNOWN" | string;

function currentnessLine(env: EvEnvelope): string | null {
  const state: Currentness = env.currentness.state;
  if (state === "PENDING_RECOMPUTE") return EV_COPY.pending;
  if (state === "HISTORICAL") return EV_COPY.historical;
  return null;
}

function historicalStamp(env: EvEnvelope): string | null {
  return env.currentness.state === "HISTORICAL" && env.window.known_at !== null
    ? `Historical assessment · ${dayHm(env.window.known_at)} UTC`
    : null;
}

function ProvenanceBadge({ env }: { env: EvEnvelope }) {
  const simulated = env.source_provenance.classification === "REGISTERED_SIMULATION";
  return (
    <>
      <Badge tone="provenance">{classificationWord(env.source_provenance.classification)}</Badge>
      {simulated ? <span className="ev-strip__note" data-ev-provenance-note>{EV_COPY.simulation}</span> : null}
    </>
  );
}

/** The strip word: pending first, then the stored status (r6 dry-read). */
export function sessionsStripWord(read: EvSessionsRead): string {
  if (read.currentness.state === "PENDING_RECOMPUTE") return "Evidence pending";
  if (read.currentness.state === "UNKNOWN") return "Unknown";
  switch (read.status.state) {
    case "OBSERVED_SESSIONS":
      return "Sessions observed";
    case "NO_SESSIONS_OBSERVED":
      return "No sessions observed";
    case "CONTRADICTORY":
      return "Records disagree";
    default:
      return "Unknown";
  }
}

/* ---------- sessions: one row ---------- */

type Tone = "green" | "amber" | "red" | null;

export function outcomeOf(s: EvSessionItem): { word: string; tone: Tone } {
  switch (s.state) {
    case "COMPLETED":
      return s.energy_complete === true ? { word: "Delivered", tone: "green" } : { word: "Completed · energy partial", tone: "amber" };
    case "OBSERVED_ABORT":
      return s.finding_id !== null ? { word: "Fault-aborted", tone: "amber" } : { word: "Observed abort", tone: "amber" };
    case "INCOMPLETE":
      return { word: "Incomplete", tone: "amber" };
    case "CONTRADICTORY":
      return { word: "Contradictory", tone: "red" };
    default:
      return { word: "Unknown", tone: null };
  }
}

function ToneBadge({ word, tone }: { word: string; tone: Tone }) {
  return (
    <Badge tone="neutral" className={tone === null ? "ev-chip" : `ev-chip ev-tone--${tone}`}>
      {word}
    </Badge>
  );
}

function period(s: EvSessionItem): string {
  const start = s.start_at === null ? "Unknown" : `${hm(s.start_at)} UTC`;
  const end =
    s.state === "CONTRADICTORY" ? "Competing end records" : s.end_at === null ? "End not recorded" : `${hm(s.end_at)} UTC`;
  return `${start} – ${end}`;
}

function energy(s: EvSessionItem): string {
  if (s.supported_kwh === null) return "Unknown";
  return `${s.supported_kwh} kWh · ${s.energy_complete === true ? "complete" : "partial"}`;
}

/**
 * Present facts, then known gaps (r8 M2): the four `completeness` booleans come from the selected revision's
 * SUPPORT uses; a missing chip is explained, never inferred present from an absent reason code.
 */
export function completenessChips(s: EvSessionItem): string[] {
  const c = s.completeness;
  const present = [c.start ? "Start" : null, c.terminal ? "Terminal" : null, c.meter ? "Meter" : null, c.clock ? "Clock" : null];
  const gaps = [
    c.terminal ? null : s.state === "CONTRADICTORY" ? "Competing end records" : "No end record",
    c.meter
      ? null
      : s.state !== "CONTRADICTORY" && s.unknown_meter_seconds !== null && s.unknown_meter_seconds > 0
        ? `Meter gap: ${s.unknown_meter_seconds} s`
        : "Meter coverage unknown",
    c.clock ? null : "Clock not attested",
  ];
  return [...present, ...gaps].filter((x): x is string => x !== null);
}

function NextStep({ s, pending, findingHref }: { s: EvSessionItem; pending: boolean; findingHref: (findingId: string) => string }) {
  // r7 P7: a pending recompute never offers the prior Finding as a current destination.
  if (pending) return <UnavailableInline label="Open Finding" />;
  if (s.links.finding !== null && s.finding_id !== null) {
    return <Link to={findingHref(s.finding_id)}>Open Finding →</Link>;
  }
  return <UnavailableInline />;
}

/* ---------- sessions: panels ---------- */

const COLUMNS = ["Session / connector", "Period", "Energy", "Outcome", "Evidence completeness", "Next step"] as const;
const INITIAL_ROWS = 4;

function SessionRows({ read, findingHref }: { read: EvSessionsRead; findingHref: (findingId: string) => string }) {
  const [all, setAll] = useState(false);
  const rows = all ? read.items : read.items.slice(0, INITIAL_ROWS);
  return (
    <>
      <DataTable labelledBy="ev-records-heading">
        <colgroup>
          {COLUMNS.map((c) => (
            <col key={c} data-ev-col={c} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {COLUMNS.map((c) => (
              <th key={c} scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => {
            const outcome = outcomeOf(s);
            return (
              <tr key={s.session_id} data-ev-session={s.session_id}>
                <td>
                  Session <ShortId value={s.external_session_id} />
                  {` · ${s.connector_display_name ?? "Connector name unknown"}`}
                </td>
                <td>{period(s)}</td>
                <td>{energy(s)}</td>
                <td>
                  <ToneBadge word={outcome.word} tone={outcome.tone} />
                </td>
                <td>
                  <span className="ev-chips">
                    {completenessChips(s).map((chip) => (
                      <Badge key={chip} tone="neutral" className="ev-chip">
                        {chip}
                      </Badge>
                    ))}
                  </span>
                </td>
                <td>
                  <NextStep s={s} pending={read.currentness.state === "PENDING_RECOMPUTE"} findingHref={findingHref} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </DataTable>
      {read.items.length > INITIAL_ROWS ? (
        <button type="button" className="ev-show-all" aria-expanded={all} onClick={() => setAll((x) => !x)}>
          {all ? "Show fewer" : "Show all"}
        </button>
      ) : null}
    </>
  );
}

function sessionReferences(read: EvSessionsRead) {
  return [
    ...read.items.flatMap((s, i) => [
      { label: `Row ${i + 1} · session`, value: s.external_session_id },
      { label: `Row ${i + 1} · session ID`, value: s.session_id },
      { label: `Row ${i + 1} · revision ID`, value: s.revision_id },
      { label: `Row ${i + 1} · connector asset ID`, value: s.connector_asset_id },
    ]),
    { label: "Assessment basis (SHA-256)", value: read.source_provenance.basis_sha256 },
  ];
}

/** r9 M1-c: one closed-disclosure line per excluded accepted record, after the ordinary session references. */
function ExcludedRecords({ read }: { read: EvSessionsRead }) {
  if (read.excluded_records.length === 0) return null;
  return (
    <>
      {read.excluded_records.map((x) => (
        <p key={x.evidence_id} className="ev-excluded" data-ev-excluded={x.evidence_id}>
          <span aria-label={`Record ${x.evidence_id} · ${EV_COPY.recordUnverified}`}>{`Record ${short(x.evidence_id)} · ${EV_COPY.recordUnverified}`}</span>
        </p>
      ))}
    </>
  );
}

/** r9 M1-a: the unassessable set's actual class and exact accepted/source IDs (no stored basis). */
function sourceDetail(read: EvSessionsRead) {
  const p = read.source_provenance;
  return [
    { label: "Source class", value: p.classification },
    ...p.evidence_ids.map((v, i) => ({ label: `Accepted record ${i + 1}`, value: v })),
    ...p.source_ids.map((v, i) => ({ label: `Source ${i + 1}`, value: v })),
  ];
}

function RecordsPanel({ read, gap, findingHref }: { read: EvSessionsRead | null; gap: string | null; findingHref: (findingId: string) => string }) {
  let body: ReactNode;
  const sourceBlocked = read !== null && read.limitations.includes(EV_COPY.sourceUnassessable);
  if (read === null) {
    body = <Gap id="ev-records">{gap}</Gap>;
  } else if (read.currentness.state === "UNKNOWN") {
    body = (
      <>
        <Gap id="ev-records">{read.currentness.limitation ?? "Unknown"}</Gap>
        {sourceBlocked ? <ExactReferences variant="tech" name="ev-source-detail" references={sourceDetail(read)} /> : null}
      </>
    );
  } else if (read.status.state === "UNKNOWN") {
    // r9 M1-b: a stored UNKNOWN result (never "no sessions" or 0); its limitation above the exact references.
    body = (
      <>
        <Gap id="ev-records">{read.status.limitation ?? "Unknown"}</Gap>
        <ExactReferences variant="tech" name="ev-session-references" references={sessionReferences(read)} extra={read.excluded_records.length > 0 ? <ExcludedRecords read={read} /> : null} />
      </>
    );
  } else if (read.items.length === 0) {
    body = (
      <>
        <Gap id="ev-records">{EV_COPY.noSessions}</Gap>
        {(read.denominator.orphan ?? 0) > 0 ? <p className="ev-note">{EV_COPY.orphan}</p> : null}
      </>
    );
  } else {
    body = (
      <>
        {sourceBlocked && read.currentness.state === "PENDING_RECOMPUTE" ? (
          <>
            <p className="ev-note" data-ev-pending-note>{EV_COPY.pending}</p>
            <p className="ev-note" data-ev-source-limitation>{EV_COPY.sourceUnassessable}</p>
          </>
        ) : null}
        <SessionRows read={read} findingHref={findingHref} />
        {(read.denominator.orphan ?? 0) > 0 ? <p className="ev-note">{EV_COPY.orphan}</p> : null}
        <ExactReferences variant="tech" name="ev-session-references" references={sessionReferences(read)} extra={read.excluded_records.length > 0 ? <ExcludedRecords read={read} /> : null} />
      </>
    );
  }
  return (
    <Panel heading="Session service records" headingId="ev-records-heading" description={<UnavailableInline label="Energy summary" />}>
      {body}
    </Panel>
  );
}

function denominatorLine(d: EvDenominator): string {
  return `${count(d.started)} accepted starts · ${count(d.completed)} completed · ${count(d.observed_abort)} observed aborts · ${count(d.incomplete)} incomplete · ${count(d.contradictory)} contradictory`;
}

function DenominatorPanel({ read, gap }: { read: EvSessionsRead | null; gap: string | null }) {
  const known = read !== null && read.currentness.state !== "UNKNOWN";
  return (
    <Panel heading="How to read the denominator" headingId="ev-denominator-heading">
      {!known ? (
        <Gap id="ev-denominator">{read === null ? gap : "Unknown"}</Gap>
      ) : (
        <>
          <p className="prose ev-lines" data-ev-denominator>
            <strong>{denominatorLine(read.denominator)}</strong>
            <br />
            {`Orphan end records: ${count(read.denominator.orphan)}`}
            <br />
            {EV_COPY.unknownSeparate}
          </p>
          <ExactReferences
            variant="tech"
            name="ev-denominator-references"
            references={[
              { label: "Counted as of (UTC)", value: read.denominator.as_of },
              { label: "Count limitation", value: read.denominator.limitation },
            ]}
          />
        </>
      )}
    </Panel>
  );
}

function CausePanel({ read, gap }: { read: EvSessionsRead | null; gap: string | null }) {
  const known = read !== null && read.currentness.state !== "UNKNOWN";
  return (
    <Panel heading="Cause remains bounded" headingId="ev-cause-heading">
      {!known ? (
        <Gap id="ev-cause">{read === null ? gap : "Unknown"}</Gap>
      ) : (
        <>
          <p className="prose">{(read.denominator.fault_aborted ?? 0) > 0 ? EV_COPY.causeFault : EV_COPY.causeNone}</p>
          <details className="disclosure exact-references exact-references--tech" data-disclosure="ev-cause-detail">
            <summary className="disclosure__summary">How this was worked out</summary>
            <p className="disclosure__body">{EV_COPY.causeDisclosure}</p>
          </details>
        </>
      )}
    </Panel>
  );
}

function SessionCards({ read }: { read: EvSessionsRead | null }) {
  const state = read?.currentness.state;
  const value = (n: number | null | undefined) =>
    read === null || state === "UNKNOWN" ? "Unknown" : state === "PENDING_RECOMPUTE" ? "Pending recompute" : count(n);
  const word = read === null || state === "UNKNOWN" || state === "PENDING_RECOMPUTE" || read.status.state === "UNKNOWN";
  const d = read?.denominator;
  return (
    <MetricCards label="Session outcomes">
      <MetricCard label="Attempts" value={value(d?.started)} note="Accepted starts" word={word} data={{ "data-ev-card": "attempts" }} />
      <MetricCard label="Confirmed delivery" value={value(d?.confirmed_delivery)} note="Completed with full meter coverage" word={word} data={{ "data-ev-card": "confirmed" }} />
      <MetricCard label="Fault-aborted" value={value(d?.fault_aborted)} note="Observed abort with fault record" word={word} data={{ "data-ev-card": "fault" }} />
      <MetricCard label="Incomplete" value={value(d?.incomplete)} note="End record missing" word={word} data={{ "data-ev-card": "incomplete" }} />
    </MetricCards>
  );
}

function SessionsStrip({ read, gap }: { read: EvSessionsRead | null; gap: string | null }) {
  if (read === null) {
    return (
      <StatusBar label="Session service state" data={{ "data-ev-strip": "refused" }}>
        <Badge tone="neutral" className="ev-chip">Unknown</Badge> <span data-ev-refusal>{gap}</span>
      </StatusBar>
    );
  }
  const contradictory = read.status.state === "CONTRADICTORY" && read.currentness.state !== "PENDING_RECOMPUTE" && read.currentness.state !== "UNKNOWN";
  const lines = [currentnessLine(read), historicalStamp(read), contradictory ? EV_COPY.contradictory : null].filter(Boolean);
  return (
    <StatusBar label="Session service state" data={{ "data-ev-strip": read.currentness.state }} action={<UnavailableInline label="Inspect session lineage" />}>
      <Badge tone="neutral" className="ev-chip">{sessionsStripWord(read)}</Badge> <ProvenanceBadge env={read} />
      {lines.map((line) => (
        <span key={line} className="ev-strip__note" data-ev-state-line>
          {line}
        </span>
      ))}
    </StatusBar>
  );
}

/* ---------- Performance / Sessions frame ---------- */

export interface EvSessionsFrameProps {
  siteId: string;
  siteName: string;
  mode: string | null;
  window: EvWindowQuery;
  client: EvAssessmentClient;
  tabs: ReactNode;
  parentTrail: Crumb[];
  sessionsHref: string;
  findingHref: (findingId: string) => string;
}

export function EvSessionsFrame(props: EvSessionsFrameProps) {
  const { siteId, window, client } = props;
  const sessions = useRead(() => client.listSessions(siteId, window), `s|${siteId}|${windowKey(window)}`);
  const read = sessions !== null && sessions.status === "loaded" ? sessions.value : null;
  const gap = sessions !== null && sessions.status !== "loaded" ? evRefusalText(sessions) : null;
  return (
    <main aria-labelledby={EV_SESSIONS_HEADING_ID} data-ev-view="sessions">
      <Breadcrumbs trail={[...props.parentTrail, { label: "Performance" }]} />
      <SitePageHeader
        siteName={props.siteName}
        siteId={siteId}
        mode={props.mode}
        description={SITE_SCREEN_DESCRIPTIONS.sessions}
        headingId={EV_SESSIONS_HEADING_ID}
      />
      {props.tabs}
      <nav className="site-tabs site-subtabs" aria-label="Performance sections">
        <ol className="site-tabs__list">
          <li className="site-tabs__item">
            <Link className="site-tabs__link" to={props.sessionsHref} data-performance-subtab="sessions" aria-current="page">
              Sessions
            </Link>
          </li>
          <UnavailableTab label="Availability" />
          <UnavailableTab label="Energy / site power" />
        </ol>
      </nav>
      {sessions === null ? (
        <p>{EV_LOADING}</p>
      ) : (
        <>
          <SessionsStrip read={read} gap={gap} />
          <SessionCards read={read} />
          <RecordsPanel read={read} gap={gap} findingHref={props.findingHref} />
          <div className="panel-pair ev-pair">
            <DenominatorPanel read={read} gap={gap} />
            <CausePanel read={read} gap={gap} />
          </div>
        </>
      )}
    </main>
  );
}

/* ---------- Finding ---------- */

export interface EvFindingFrameProps {
  siteId: string;
  siteName: string;
  findingId: string;
  window: EvWindowQuery;
  client: EvAssessmentClient;
  tabs: ReactNode;
  parentTrail: Crumb[];
}

function exactClaim(f: EvFindingDetailRead): boolean {
  const c = f.claim;
  return (
    f.lifecycle === "SUPPORTED" &&
    c.start_at !== null &&
    c.abort_at !== null &&
    c.fault_evidence_id !== null &&
    c.start_evidence_id !== null &&
    c.abort_evidence_id !== null
  );
}

function deliveredLine(f: EvFindingDetailRead): string {
  const c = f.claim;
  if (c.supported_kwh === null) return "Delivered energy unknown";
  return `${c.supported_kwh} kWh delivered before abort · ${c.energy_complete === true ? "complete" : "partial"} meter coverage`;
}

function FindingStrip({ finding, siteName }: { finding: EvFindingDetailRead; siteName: string }) {
  const pending = finding.currentness.state === "PENDING_RECOMPUTE";
  const word = pending ? "Evidence pending" : finding.lifecycle === "SUPPORTED" ? "Observed interruption" : lifecycleWord(finding.lifecycle);
  const lines = [currentnessLine(finding), historicalStamp(finding)].filter(Boolean);
  return (
    <StatusBar label="Finding state" data={{ "data-ev-strip": finding.currentness.state }}>
      <Badge tone="neutral" className="ev-chip">
        <span aria-label={`Finding ${finding.finding_id}`}>{`Finding ${short(finding.finding_id)}`}</span>
      </Badge>{" "}
      <Badge tone="lifecycle">{word}</Badge> <span className="ev-strip__note">{siteName}</span> <ProvenanceBadge env={finding} />
      {lines.map((line) => (
        <span key={line} className="ev-strip__note" data-ev-state-line>
          {line}
        </span>
      ))}
    </StatusBar>
  );
}

function FindingPanels({ finding, session }: { finding: EvFindingDetailRead; session: EvRead<EvSessionDetailRead> | null }) {
  const c = finding.claim;
  const connector = session !== null && session.status === "loaded" ? session.value.connector_display_name : null;
  // r7 P5: a withdrawn or otherwise unsupported claim never puts a stored limitation in the BigClaim.
  const conclusion = exactClaim(finding)
    ? EV_COPY.conclusion
    : finding.lifecycle === "NO_LONGER_SUPPORTED"
      ? EV_COPY.withdrawn
      : EV_COPY.unsupported;
  // r9 M3: the closed line names the fault only when the verified trio is complete; the disclosure lists the
  // available labelled IDs in semantic order, then the analysis gap once.
  const trio = c.start_evidence_id !== null && c.fault_evidence_id !== null && c.abort_evidence_id !== null;
  const record = trio ? c.fault_evidence_id : null;
  const labelled: [string, string | null][] = [
    ["Start record ID", c.start_evidence_id],
    ["Fault record ID", c.fault_evidence_id],
    ["Abort record ID", c.abort_evidence_id],
  ];
  const recordIds = labelled.filter((x): x is [string, string] => x[1] !== null);
  return (
    <>
      <Panel heading="Bounded conclusion" headingId="ev-conclusion-heading">
        <BigClaim data={{ "data-ev-conclusion": exactClaim(finding) ? "supported" : "limited" }}>{conclusion}</BigClaim>
        <p className="prose" data-ev-delivered>{deliveredLine(finding)}</p>
        <p className="prose">{EV_COPY.limit}</p>
        <p className="ev-record-line" data-ev-record>
          {record === null ? (
            <span>Record Unknown</span>
          ) : (
            <span aria-label={`Record ${record}`}>{`Record ${short(record)}`}</span>
          )}{" "}
          · <span>No analysis link</span>
        </p>
        <details className="disclosure exact-references exact-references--tech" data-disclosure="ev-finding-references" data-exact-references>
          <summary className="disclosure__summary">How this was worked out</summary>
          <ul className="disclosure__body ev-record-ids" data-ev-record-ids>
            {recordIds.map(([label, value]) => (
              <li key={label} data-ev-record-id={label}>
                {`${label}: `}
                <code data-vocabulary-exempt="source-reference">{value}</code>
              </li>
            ))}
          </ul>
          <p className="disclosure__body" data-ev-analysis-gap>{EV_COPY.analysisGap}</p>
          <dl className="disclosure__body exact-references__list">
            {[
              { label: "Finding ID", value: finding.finding_id },
              { label: "Finding revision ID", value: finding.revision_id },
              { label: "Assessment basis (SHA-256)", value: finding.source_provenance.basis_sha256 },
              { label: "Lifecycle", value: finding.lifecycle },
              { label: "Selected cutoff", value: finding.window.known_at },
              ...finding.limitations.map((l, i) => ({ label: `Stored limitation ${i + 1}`, value: l })),
            ].map((reference) => (
              <div className="exact-references__row" key={reference.label}>
                <dt>{reference.label}</dt>
                <dd>{reference.value === null ? "not recorded" : <code data-vocabulary-exempt="source-reference">{reference.value}</code>}</dd>
              </div>
            ))}
          </dl>
        </details>
      </Panel>
      <div className="panel-pair ev-pair">
        <Panel heading="Operational context" headingId="ev-operational-heading">
          <KeyValues
            label="Operational context"
            rows={[
              ["Session", <ShortId value={c.external_session_id} />, "session"],
              ["Connector", connector ?? "Unknown", "connector"],
              ["Energy delta", c.supported_kwh === null ? "Unknown" : `${c.supported_kwh} kWh`, "energy"],
              ["Outcome", c.abort_at === null ? "Unknown" : "Observed abort", "outcome"],
            ]}
          />
          <ExactReferences
            variant="tech"
            name="ev-operational-references"
            references={[
              { label: "Session", value: c.external_session_id },
              { label: "Session ID", value: c.session_id },
              { label: "Connector asset ID", value: c.connector_asset_id },
            ]}
          />
        </Panel>
        <Panel heading="Recommended next step" headingId="ev-next-step-heading">
          <p className="prose">{EV_COPY.nextStep}</p>
          <UnavailableLinkEntry label="Review recommendation" />
        </Panel>
      </div>
    </>
  );
}

function FindingSkeleton({ gap }: { gap: string }) {
  return (
    <>
      <Panel heading="Bounded conclusion" headingId="ev-conclusion-heading">
        <Gap id="ev-conclusion">{gap}</Gap>
      </Panel>
      <div className="panel-pair ev-pair">
        <Panel heading="Operational context" headingId="ev-operational-heading">
          <Gap id="ev-operational">{gap}</Gap>
        </Panel>
        <Panel heading="Recommended next step" headingId="ev-next-step-heading">
          <Gap id="ev-next-step">{gap}</Gap>
          <UnavailableLinkEntry label="Review recommendation" />
        </Panel>
      </div>
    </>
  );
}

export function EvFindingFrame(props: EvFindingFrameProps) {
  const { siteId, findingId, window, client } = props;
  const finding = useRead(() => client.getFinding(siteId, findingId, window), `f|${siteId}|${findingId}|${windowKey(window)}`);
  const detail = finding !== null && finding.status === "loaded" ? finding.value : null;
  // The connector display name: follow the claim's session at the Finding's own selected window (handoff r5 note).
  const own: EvWindowQuery | null = detail === null ? null : { ...detail.window };
  const sessionId = detail?.claim.session_id ?? null;
  const session = useRead(
    own !== null && sessionId !== null ? () => client.getSession(siteId, sessionId, own) : null,
    `s|${siteId}|${sessionId ?? ""}|${own === null ? "" : windowKey(own)}`,
  );
  const sessionReady = detail === null || sessionId === null || session !== null;
  return (
    <main aria-labelledby={EV_FINDING_HEADING_ID} data-ev-view="ev-finding">
      <Breadcrumbs trail={[...props.parentTrail, { label: "Finding" }]} />
      <PageHeader title={detail?.title ?? "Finding"} headingId={EV_FINDING_HEADING_ID} subtitle={`${props.siteName} · EV charging finding`} />
      {props.tabs}
      <nav className="site-tabs site-subtabs" aria-label="Finding sections">
        <ol className="site-tabs__list">
          <li className="site-tabs__item">
            <span className="site-tabs__link" aria-current="page">
              Overview
            </span>
          </li>
          <UnavailableTab label="Recommendation" />
        </ol>
      </nav>
      {finding === null || !sessionReady ? (
        <p>{EV_LOADING}</p>
      ) : finding.status !== "loaded" ? (
        <>
          <StatusBar label="Finding state" data={{ "data-ev-strip": "refused" }}>
            <Badge tone="neutral" className="ev-chip">Unknown</Badge> <span data-ev-refusal>{evRefusalText(finding)}</span>
          </StatusBar>
          <FindingSkeleton gap={evRefusalText(finding)} />
        </>
      ) : (
        <>
          <FindingStrip finding={finding.value} siteName={props.siteName} />
          <FindingPanels finding={finding.value} session={session} />
        </>
      )}
    </main>
  );
}

/** The Finding route address keeping the selected window. */
export function evFindingHref(base: (findingId: string) => string, window: EvWindowQuery) {
  return (findingId: string) => `${base(findingId)}${coldWindowSearch(window)}`;
}
