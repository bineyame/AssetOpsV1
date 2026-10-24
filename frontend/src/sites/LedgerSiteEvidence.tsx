/**
 * Site > Evidence for an imported Site read from the central evidence ledger
 * (S2-02 phase 3b; payloads in `ledgerEvidenceClient.ts`).
 *
 * V-01b follows the v6.9 mock's hierarchy. Overview: a compact window
 * toolbar, a status bar of window facts with a neutral "No capability
 * conclusion yet" badge, "What we can conclude now", a Data sources / Most
 * useful next evidence pair (with the gateway's central contact inside Data
 * sources) and a closing notice. Analysis: the accepted records behind the
 * conclusions (each opening its configuration, receipt and exact message),
 * how each limit is set, readings not accepted, and the long technical panels
 * (clocks, deliveries, per-input coverage, analysis status, earlier-store
 * comparison, gateway detail) behind labelled Advanced details disclosures.
 * Mock facts with no data source are visible "Not available yet" statements.
 *
 * Clocks. Reading and publication times on demonstration data are instants on
 * the demonstration timeline; the received time is the server's real clock.
 * Nothing here subtracts one from the other. Analysis status (whether derived
 * results include the newest readings) is shown apart from evidence freshness
 * and never as a conclusion about how the site is operating.
 */

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  Badge,
  ChartNote,
  DataTable,
  Disclosure,
  currentnessWords,
  ExactReferences,
  Fact,
  FactList,
  KeyValues,
  Panel,
  plainTime,
  ProductStatus,
  type ProductWords,
  ValueBars,
  asOfText,
  V69Notice,
} from "../ui";
import { PeriodStrip } from "./periodStrip";
import { CountBars } from "./assessmentGraphics";
import type { ClaimLimitClient } from "./claimLimitClient";
import { idWords, qualityWords, roleWords } from "./dispatchWords";
import { EvidenceClaimLimit } from "./EvidenceClaimLimit";
import { LocalViews, localView, localViewSearch, readablePeriod, readableTime } from "./findingPresentation";
import type { EvidenceRead } from "./evidenceRead";
import type { GatewayHealth, GatewayHealthClient } from "./gatewayHealthClient";
import type {
  LedgerEvidence,
  LedgerEvidenceClient,
  LedgerRecordDetail,
  LedgerRecordPage,
  LedgerRejections,
} from "./ledgerEvidenceClient";

export const LEDGER_RECORD_LIMIT = 50;
/** The whole-site list on Analysis opens short; choosing a source or input pages by LEDGER_RECORD_LIMIT. */
export const LEDGER_SITE_RECORD_LIMIT = 10;
export const LEDGER_INSPECTOR_ID = "site-evidence-inspector";
export const LEDGER_EVIDENCE_VIEWS_LABEL = "Evidence views";

const REF = { "data-vocabulary-exempt": "source-reference" } as const;

/** The plain name of a clock label; never shown as its code. */
export function clockWords(label: string): string {
  switch (label) {
    case "RUN_VIRTUAL":
      return "demonstration timeline";
    case "SOURCE_REPORTED":
      return "the source's own clock";
    case "SERVER_RECEIVED_AT":
      return "server clock, UTC";
    default:
      return "clock not stated";
  }
}

function when(value: string | null | undefined): string {
  return value === null || value === undefined ? "none" : readableTime(value);
}

/**
 * post-W6 shell R170 (Q18): the records table's measured time in the selected Site's timezone (the mock's
 * `Measured (EAT)`, `HH:MM:SS`). The stored instant stays UTC and is exposed on the cell's title. Intl names East
 * Africa Time only as `GMT+3`, so the common zones are named here; others use Intl's short name.
 */
const ZONE_ABBREVIATIONS: Record<string, string> = {
  "Africa/Addis_Ababa": "EAT",
  "Africa/Asmara": "EAT",
  "Africa/Dar_es_Salaam": "EAT",
  "Africa/Djibouti": "EAT",
  "Africa/Kampala": "EAT",
  "Africa/Mogadishu": "EAT",
  "Africa/Nairobi": "EAT",
  UTC: "UTC",
  "Etc/UTC": "UTC",
};

/** The usable IANA zone, or null when it is missing or this browser cannot resolve it (the UTC fallback). */
export function usableZone(timezone: string | null | undefined): string | null {
  if (!timezone) return null;
  try {
    new Intl.DateTimeFormat("en-GB", { timeZone: timezone });
    return timezone;
  } catch {
    return null;
  }
}

/**
 * The short zone name at `at` (the selected window's start), so a DST zone is named for the period shown rather
 * than for 1 January 1970. Without an instant it uses the current time.
 */
export function zoneAbbreviation(timezone: string | null | undefined, at?: string | Date | null): string {
  const zone = usableZone(timezone);
  if (zone === null) return "UTC";
  const known = ZONE_ABBREVIATIONS[zone];
  if (known) return known;
  const instant = at instanceof Date ? at : at ? new Date(at) : new Date();
  const when = Number.isNaN(instant.getTime()) ? new Date() : instant;
  const name = new Intl.DateTimeFormat("en-GB", { timeZone: zone, timeZoneName: "short" })
    .formatToParts(when)
    .find((part) => part.type === "timeZoneName")?.value;
  return name ?? zone;
}

function zoneClock(zone: string, date: Date): { day: string; time: string } {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: zone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(date)
      .map((part) => [part.type, part.value]),
  );
  return { day: `${p.year}-${p.month}-${p.day}`, time: `${p.hour}:${p.minute}:${p.second}` };
}

const SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** The selected day (`YYYY-MM-DD`) on the Site's clock, from the read window's start. */
export function selectedLocalDay(windowStart: string | null | undefined, timezone: string | null | undefined): string | null {
  const date = windowStart ? new Date(windowStart) : null;
  if (date === null || Number.isNaN(date.getTime())) return null;
  return zoneClock(usableZone(timezone) ?? "UTC", date).day;
}

/** `HH:MM:SS` on the Site's clock; `D Mon · HH:MM:SS` when that local day differs from the selected day. */
export function measuredTime(
  instant: string | null | undefined,
  timezone: string | null | undefined,
  selectedDay: string | null,
): string {
  if (instant === null || instant === undefined) return "none";
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  const clock = zoneClock(usableZone(timezone) ?? "UTC", date);
  if (selectedDay !== null && clock.day === selectedDay) return clock.time;
  const [, month, day] = clock.day.split("-");
  return `${Number(day)} ${SHORT_MONTHS[Number(month) - 1]} · ${clock.time}`;
}

function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

function sourceKind(mode: string): string {
  return mode === "SIMULATED" ? "Demonstration data" : mode === "LIVE" ? "Live data" : "Data of unstated origin";
}

/** Review fix M5(b): a coded state value ("STOPPED") reads as a plain word ("Stopped"), with no "state" unit. */
function readingValue(value: { value: string | null; unit: string | null }): string {
  if (value.value === null) return "no value";
  if (/^[A-Z][A-Z_]*$/.test(value.value)) {
    const word = value.value.toLowerCase().replace(/_/g, " ");
    return word.charAt(0).toUpperCase() + word.slice(1);
  }
  const unit = value.unit === null || value.unit === "state" ? "" : ` ${value.unit}`;
  return `${value.value}${unit}`;
}

/** The reading's name: its configured role in words, else its channel identifier in words. */
function readingName(item: { role: string | null; signal_id: string }): string {
  if (!item.role) return idWords(item.signal_id);
  const words = roleWords(item.role);
  return words === item.role.replace(/_/g, " ") ? idWords(item.role) : words;
}

/** `datetime-local` text for an instant, or "" (minutes, UTC). */
function localInput(instant: string | null): string {
  return instant === null ? "" : instant.slice(0, 16);
}

function instantFromInput(text: string): string | null {
  return text === "" ? null : `${text.length === 16 ? `${text}:00` : text}Z`;
}

export interface LedgerSiteEvidenceProps {
  siteId: string;
  evidence: LedgerEvidence;
  ledger: LedgerEvidenceClient | undefined;
  gatewayHealth: GatewayHealthClient | undefined;
  claimLimit?: ClaimLimitClient;
  assessmentHref?: (day: string, revisionId: string) => string;
  /** post-W6 shell R170: the selected Site's stored IANA timezone; absent or unknown falls back to UTC. */
  timezone?: string | null;
}

export function LedgerSiteEvidence({
  siteId,
  evidence,
  ledger,
  gatewayHealth,
  claimLimit,
  assessmentHref,
  timezone = null,
}: LedgerSiteEvidenceProps) {
  const [params, setParams] = useSearchParams();
  const view = localView(params);
  const [health, setHealth] = useState<EvidenceRead<GatewayHealth> | null>(null);

  useEffect(() => {
    if (gatewayHealth === undefined) {
      setHealth({ status: "unavailable", message: null });
      return undefined;
    }
    let active = true;
    setHealth(null);
    void gatewayHealth.getGatewayHealth(siteId).then((loaded) => {
      if (active) {
        setHealth(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [gatewayHealth, siteId]);

  // W1-F2 fix round (H2): the chip-row element the claim-limit chooser renders into.
  const [chooserSlot, setChooserSlot] = useState<HTMLDivElement | null>(null);
  // W1-F2 fix round 2 (M1): the slot inside the limits panel's single advanced row.
  const [detailSlot, setDetailSlot] = useState<HTMLDivElement | null>(null);

  const inspect = (key: "signal" | "source", value: string) => {
    const next = new URLSearchParams(params);
    for (const name of ["signal", "source", "record", "cursor"]) next.delete(name);
    next.set(key, value);
    next.set("view", "analysis");
    setParams(next);
  };

  return (
    <div
      className="site-evidence"
      data-evidence-store="POSTGRES"
      data-evidence-state={evidence.state}
      data-evidence-states={evidence.states.join(" ")}
      data-evidence-view={view}
    >
      <LocalViews label={LEDGER_EVIDENCE_VIEWS_LABEL} current={view} params={params} />
      <WindowChooser
        evidence={evidence}
        extra={
          view === "analysis" ? (
            // W1-F2 fix round (H2): the assessment day and period chooser joins the page's chip row.
            <div className="evidence-toolbar__controls evidence-toolbar__assessment" ref={setChooserSlot} />
          ) : null
        }
      />
      {view === "overview" ? (
        <OverviewBody evidence={evidence} health={health} params={params} onInspect={(source) => inspect("source", source)} />
      ) : (
        <>
          <StatusBar view="analysis" badge="Evidence · Analysis">
            <span className="evidence-statusbar__facts" data-evidence-analysis-question>
              Accepted records, timing and how each limit is set
            </span>
          </StatusBar>
          {/* W1-F2: the v69 evidence-analysis panels. Records (and readings not accepted) first, then how a limit is set. */}
          <Inspector siteId={siteId} ledger={ledger} evidence={evidence} timezone={timezone}>
            <Rejected
              siteId={siteId}
              ledger={ledger}
              evidence={evidence}
              technical={
                <>
              <Advanced name="evidence-clocks" summary="Advanced details — which clock each time uses">
                <Clocks evidence={evidence} />
              </Advanced>
              {evidence.sources.length === 0 ? null : (
                <Advanced name="evidence-sources" summary="Advanced details — sources in this period">
                  <Sources evidence={evidence} onInspect={(source) => inspect("source", source)} />
                </Advanced>
              )}
              {evidence.batches.length === 0 ? null : (
                <Advanced name="evidence-deliveries" summary={`Advanced details — deliveries (${evidence.batches.length})`}>
                  <Deliveries evidence={evidence} />
                </Advanced>
              )}
              {evidence.coverage.length === 0 ? null : (
                <Advanced name="evidence-coverage" summary="Advanced details — readings by input">
                  <Coverage evidence={evidence} onInspect={(key) => inspect("signal", key)} />
                </Advanced>
              )}
                </>
              }
            />
          </Inspector>
          <ClaimLimit
            evidence={evidence}
            detailSlotRef={setDetailSlot}
            technical={
            /* W1-F2 compaction: the technical disclosures nest inside the panel's single advanced row; each keeps its own closed disclosure. */
            <Advanced
              name="evidence-analysis-technical"
              summary={
                evidence.migration === null
                  ? "Advanced details — analysis status and gateway contact"
                  : "Advanced details — analysis status, earlier store and gateway contact"
              }
            >
              <Advanced name="evidence-analysis-status" summary="Advanced details — analysis status">
                <AnalysisStatus evidence={evidence} />
              </Advanced>
              {evidence.migration === null ? null : (
                <Advanced name="evidence-comparison" summary="Advanced details — earlier store comparison">
                  <Comparison evidence={evidence} />
                </Advanced>
              )}
              <Advanced name="evidence-gateway" summary="Advanced details — gateway contact">
                <Panel heading="Gateway contact" headingId="site-evidence-gateway-heading">
                  <GatewayContact health={health} detailed />
                </Panel>
              </Advanced>
            </Advanced>
            }
          >
            <EvidenceClaimLimit
              siteId={siteId}
              client={claimLimit}
              assessmentHref={assessmentHref}
              chooserTarget={chooserSlot}
              detailTarget={detailSlot}
            />
          </ClaimLimit>
        </>
      )}
    </div>
  );
}

// --- selected period -------------------------------------------------------------

function WindowChooser({ evidence, extra }: { evidence: LedgerEvidence; extra?: ReactNode }) {
  const [params, setParams] = useSearchParams();
  const { start, end } = evidence.window;
  const [from, setFrom] = useState(localInput(start));
  const [to, setTo] = useState(localInput(end));

  const apply = (event: FormEvent) => {
    event.preventDefault();
    const next = new URLSearchParams(params);
    for (const name of ["record", "cursor"]) next.delete(name);
    const a = instantFromInput(from);
    const b = instantFromInput(to);
    if (a === null) next.delete("from");
    else next.set("from", a);
    if (b === null) next.delete("to");
    else next.set("to", b);
    setParams(next);
  };
  const all = () => {
    const next = new URLSearchParams(params);
    for (const name of ["from", "to", "record", "cursor"]) next.delete(name);
    setParams(next);
  };

  let period: string;
  if (start !== null && end !== null) {
    period = `${readablePeriod(start, end)}, up to but not including the end time`;
  } else if (start !== null) {
    period = `from ${readableTime(start)} onwards`;
  } else if (end !== null) {
    period = `everything before ${readableTime(end)}`;
  } else {
    period = "all readings this site has received";
  }

  return (
    // W1-F2: the window chooser as the v69 chip row (chip-sized controls, `.button`), the app-only control before panel 1.
    <div className="v69-chips evidence-window evidence-toolbar" data-evidence-window={evidence.window.basis}>
      <form className="evidence-toolbar__controls" onSubmit={apply}>
        <label className="evidence-toolbar__field">
          <span>From (UTC)</span>
          <input className="v69-chip-control" type="datetime-local" name="from" value={from} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label className="evidence-toolbar__field">
          <span>To (UTC)</span>
          <input className="v69-chip-control" type="datetime-local" name="to" value={to} onChange={(e) => setTo(e.target.value)} />
        </label>
        <button type="submit" className="button">
          Show this period
        </button>
        <button type="button" className="button" onClick={all}>
          Show all readings
        </button>
      </form>
      {extra}
      <p className="evidence-toolbar__period">
        <strong>Selected period:</strong> {period}. Periods are chosen by the time each reading was taken.
        {evidence.extent.first_source_time === null || evidence.extent.last_source_time === null
          ? " This site has no accepted readings yet."
          : ` Accepted readings for this site span ${readablePeriod(evidence.extent.first_source_time, evidence.extent.last_source_time)}.`}
      </p>
    </div>
  );
}

// --- state ---------------------------------------------------------------------------

const STATE_NOTES: Record<string, string> = {
  PARTIAL_BATCH:
    "Some deliveries are still being processed, so the counts for this period may still grow.",
  CONFLICTING:
    "Some readings arrived again with different contents. The first accepted version is kept and the later one is listed apart.",
  OUTDATED_CONFIGURATION:
    "Some readings were recorded under a site configuration that has since been updated. They stay accepted under the configuration in force when they were taken.",
};

function headlineOf(evidence: LedgerEvidence): string {
  const { counts } = evidence;
  if (evidence.state === "NO_DATA") {
    return "No readings were received for this period.";
  }
  if (evidence.state === "REJECTED_ONLY") {
    return `Readings arrived for this period, but none could be accepted (${plural(counts.rejected + counts.conflicts, "reading", "readings")} not accepted).`;
  }
  return `${plural(counts.accepted, "reading was", "readings were")} accepted for this period from ${plural(reportingSources(evidence).length, "source", "sources")}.`;
}

function reportingSources(evidence: LedgerEvidence) {
  return evidence.sources.filter((s) => s.accepted_in_window > 0);
}

function notAccepted(evidence: LedgerEvidence): number {
  return evidence.counts.rejected + evidence.counts.conflicts;
}

/** A missing fact this slice has no data contract for, stated plainly (V-01a round 3 addendum). */
function NotAvailableYet({ name, children }: { name: string; children: string }) {
  return (
    <p className="not-available-yet v69-chart-note" data-not-available={name}>
      {children}
    </p>
  );
}

/** Technical records on demand: explicitly labelled, keyboard-operable, closed by default. */
function Advanced({ name, summary, children }: { name: string; summary: string; children: ReactNode }) {
  return (
    <div className="evidence-advanced">
      {/* W1-F2 compaction (phase B): the mock's small link-styled `details.tech`; same content, still closed. */}
      <Disclosure name={name} summary={summary} variant="tech">
        {children}
      </Disclosure>
    </div>
  );
}

/** The mock's `.statusbar`: one badge, muted facts, an optional link at the end. */
function StatusBar({
  view,
  badge,
  children,
  link,
}: {
  view: "overview" | "analysis";
  badge: string;
  children: ReactNode;
  link?: ReactNode;
}) {
  return (
    // W1-F2: F1's one-line status strip (inline children only), so the v69 guard reads it as the mock's statusbar.
    <div className="status-strip status-strip--line evidence-statusbar" data-evidence-statusbar={view}>
      <Badge tone="neutral">{badge}</Badge>
      {children}
      {link === undefined ? null : <span className="evidence-statusbar__link">{link}</span>}
    </div>
  );
}

// --- overview ------------------------------------------------------------------------

const OUTCOMES = [
  { key: "accepted", label: "Accepted" },
  { key: "duplicates", label: "Arrived again, identical (kept once)" },
  { key: "rejected", label: "Not accepted" },
  { key: "conflicts", label: "Arrived again with different contents" },
] as const;

function OutcomeBars({ evidence }: { evidence: LedgerEvidence }) {
  return (
    <CountBars
      graphic="evidence-outcomes"
      caption="Readings that arrived for this period, by what happened to them. Counts of readings."
      heading="Outcome"
      rows={OUTCOMES.map((o) => ({ key: o.key, label: o.label, count: evidence.counts[o.key] }))}
    />
  );
}

/**
 * W1-UX-01: the receipt state on the shared state line. These count readings
 * received; none of them is a conclusion about the site, so none is positive.
 */
function receiptWords(evidence: LedgerEvidence): ProductWords {
  const base = { code: evidence.state, unrecognised: false };
  if (evidence.state === "NO_DATA") {
    return {
      ...base,
      label: "No readings received for this period",
      sentence: "No reading arrived for this period, so nothing can be relied on for it.",
      tone: "neutral",
    };
  }
  if (evidence.state === "REJECTED_ONLY") {
    return {
      ...base,
      label: "Readings arrived, but none were accepted",
      sentence: "Nothing from this period can be relied on until readings are accepted.",
      tone: "limited",
    };
  }
  if (evidence.state === "ACCEPTED") {
    return {
      ...base,
      label: "Readings received and accepted",
      sentence: "These counts say what arrived and was accepted. They are not a conclusion about how the site operated.",
      tone: "neutral",
    };
  }
  // A state this screen does not know claims nothing positive; the code stays in the detail only.
  return { ...currentnessWords(null), code: evidence.state };
}

function periodScope(evidence: LedgerEvidence): string {
  if (evidence.window.basis === "ALL") return "Every period on record at this site";
  const start = plainTime(evidence.window.start) ?? "an unrecorded start";
  const end = plainTime(evidence.window.end) ?? "an unrecorded end";
  return `${start} to ${end}, end excluded`;
}

function OverviewBody({
  evidence,
  health,
  params,
  onInspect,
}: {
  evidence: LedgerEvidence;
  health: EvidenceRead<GatewayHealth> | null;
  params: URLSearchParams;
  onInspect: (source: string) => void;
}) {
  const analysis = localViewSearch(params, "analysis");
  const refused = notAccepted(evidence);
  const notes = evidence.states.filter((state) => state in STATE_NOTES);
  return (
    <>
      <StatusBar
        view="overview"
        badge="No capability conclusion yet"
        link={<Link to={{ search: analysis }}>Analysis →</Link>}
      >
        <span className="evidence-statusbar__facts">
          {`${plural(evidence.counts.accepted, "reading", "readings")} accepted · ${reportingSources(evidence).length} of ${plural(evidence.sources.length, "source", "sources")} with accepted readings · ${refused} not accepted`}
        </span>
      </StatusBar>
      <Panel
        heading="What we can conclude now"
        headingId="site-evidence-state-heading"
        description="Evidence readiness is not equipment condition"
        actions={
          <Link to={{ search: analysis }} data-evidence-analysis-link>
            Open Evidence › Analysis for this period
          </Link>
        }
      >
        <div data-evidence-conclusion>
          <p className="v69-prose">
            <strong data-evidence-headline={evidence.state}>{headlineOf(evidence)}</strong>
          </p>
          {/* Review fix M3: the receipt state differs from the statusbar badge, so it is one note-size inline line. */}
          <p className="v69-chart-note evidence-receipt-state">
            <ProductStatus inline words={receiptWords(evidence)} scope={periodScope(evidence)} asOf={evidence.extent.last_received_at} />
          </p>
          <ValueBars
            title="Readings that arrived for this period, by what happened to them"
            items={OUTCOMES.map((o) => ({ key: o.key, label: o.label, value: evidence.counts[o.key], valueText: String(evidence.counts[o.key]) }))}
          />
          {notes.length === 0 ? null : (
            <ul className="v69-chart-note evidence-notes" data-evidence-notes>
              {notes.map((state) => (
                <li key={state} data-evidence-note={state}>
                  {STATE_NOTES[state]}
                </li>
              ))}
            </ul>
          )}
          <ChartNote data={{ "data-evidence-rejection-count": String(refused) }}>
            {refused === 0
              ? "No reading in this period was refused."
              : `${plural(refused, "reading", "readings")} in this period could not be accepted; the reasons are on the Analysis view.`}
            {evidence.state === "NO_DATA" ? " Check that the site's data source is reporting." : ""}
          </ChartNote>
          <ChartNote data={{ "data-evidence-limits": "" }}>
            This page shows the readings received and what happened to each. It draws no conclusion about how the
            site or its equipment is operating.
          </ChartNote>
          <NotAvailableYet name="capability-conclusions">
            Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet.
          </NotAvailableYet>
          <ExactReferences
            name="evidence-conclusion-references"
            references={[
              { label: "Period start", value: evidence.window.start },
              { label: "Period end (excluded)", value: evidence.window.end },
              { label: "Latest delivery received", value: evidence.extent.last_received_at },
              { label: "Evidence state", value: evidence.state },
              ...evidence.states.map((state, i) => ({ label: `Recorded condition ${i + 1}`, value: state })),
            ]}
          />
        </div>
      </Panel>
      <div className="panel-pair evidence-pair">
        <SourcesOverview evidence={evidence} health={health} onInspect={onInspect} />
        <NextEvidence evidence={evidence} />
      </div>
      <V69Notice tone="blue" data={{ "data-evidence-closing-notice": "" }}>
        Record-level detail, timing and how each limit is set are on{" "}
        <Link to={{ search: analysis }}>Evidence › Analysis</Link>.
      </V69Notice>
    </>
  );
}

/**
 * W1-UX-03: three separate facts side by side - readings received, the gateway's
 * own contact, and whether derived analysis includes the newest readings - and a
 * per-source strip of when each source's latest accepted reading was taken.
 * None of the three implies another: a recent gateway report is not recent
 * readings, and neither makes analysis up to date.
 */
type FactTone = "known" | "waiting" | "problem" | "not-known";

function receiptFact(evidence: LedgerEvidence): { tone: FactTone; text: string } {
  if (evidence.counts.accepted === 0) {
    return { tone: "waiting", text: "No reading was accepted for this period." };
  }
  const latest = evidence.extent.last_received_at;
  return {
    tone: "known",
    text: `${plural(evidence.counts.accepted, "reading", "readings")} accepted. Latest delivery received ${latest === null ? "at a time not recorded" : when(latest)}.`,
  };
}

function contactFact(health: EvidenceRead<GatewayHealth> | null): { tone: FactTone; text: string } {
  const fact = contactState(health);
  // W1-F2 compaction (phase B): the gateway block is closed, so the visible fact states a switched-off gateway itself.
  const off = health?.status === "loaded" ? health.value.gateways.filter((g) => g.registration === "DISABLED").length : 0;
  if (off === 0) return fact;
  const total = health?.status === "loaded" ? health.value.gateways.length : 0;
  const offText =
    total === 1 ? "This gateway is currently switched off for this site." : `${plural(off, "gateway is", "gateways are")} currently switched off for this site.`;
  return { ...fact, text: `${fact.text} ${offText}` };
}

function contactState(health: EvidenceRead<GatewayHealth> | null): { tone: FactTone; text: string } {
  if (health === null) return { tone: "not-known", text: "Loading the gateway's contact." };
  if (health.status === "not_found") return { tone: "not-known", text: "No gateway is registered, so there is no contact to report." };
  if (health.status !== "loaded") return { tone: "not-known", text: "The contact record could not be read, so contact is not known." };
  const gateways = health.value.gateways;
  if (gateways.length === 0) return { tone: "not-known", text: "No gateway contact is recorded." };
  const current = gateways.filter((g) => g.status === "CURRENT").length;
  const stale = gateways.filter((g) => g.status === "STALE").length;
  if (current === gateways.length) {
    return { tone: "known", text: gateways.length === 1 ? "The gateway is in contact." : "Every gateway is in contact." };
  }
  if (stale > 0) return { tone: "problem", text: `${plural(stale, "gateway has", "gateways have")} not been heard from recently.` };
  // Fix round 1 (F3): some in contact and the rest in a state that is neither current nor stale.
  if (current > 0) return { tone: "not-known", text: "Some gateways are in contact; the others' contact is not known." };
  return { tone: "not-known", text: "No gateway report has been received yet." };
}

function analysisFact(evidence: LedgerEvidence): { tone: FactTone; text: string } {
  const p = evidence.projection;
  if (p.status === "STALE") return { tone: "waiting", text: "Analysis results do not yet include the newest readings." };
  if (p.failed_jobs > 0) return { tone: "problem", text: `${plural(p.failed_jobs, "analysis update has", "analysis updates have")} failed.` };
  if (p.status === "NO_PENDING_DISPATCH") return { tone: "known", text: "No analysis update is waiting for these readings." };
  return { tone: "not-known", text: "Whether analysis includes the newest readings is not known." };
}

const FACT_WORDS: Record<FactTone, string> = {
  known: "Recorded",
  waiting: "Not yet",
  problem: "Needs a look",
  "not-known": "Not known",
};

function ReportingFacts({ evidence, health }: { evidence: LedgerEvidence; health: EvidenceRead<GatewayHealth> | null }) {
  const facts = [
    { key: "readings", title: "Readings received", ...receiptFact(evidence) },
    { key: "contact", title: "Gateway contact", ...contactFact(health) },
    { key: "analysis", title: "Analysis up to date", ...analysisFact(evidence) },
  ];
  return (
    <div data-evidence-reporting-facts>
      <KeyValues
        label="Which sources reported, and when: three separate facts"
        rows={facts.map((f) => [
          f.title,
          <span key={f.key} data-evidence-reporting-fact={f.key} data-fact-tone={f.tone}>
            <strong>{FACT_WORDS[f.tone]}.</strong> {f.text}
          </span>,
          f.key,
        ])}
      />
      <ChartNote data={{ "data-evidence-reporting-note": "" }}>
        A recent gateway report does not make the readings recent, and recent readings do not make the analysis up
        to date. {asOfText(evidence.extent.last_received_at)}.
      </ChartNote>
    </div>
  );
}

/** W1-F2: the per-source latest-reading strip, below the sources table (the table is the panel's primary content). */
function SourceStrip({ evidence }: { evidence: LedgerEvidence }) {
  const start = evidence.window.basis === "ALL" ? null : evidence.window.start;
  const end = evidence.window.basis === "ALL" ? null : evidence.window.end;
  return (
    <>
      {evidence.sources.length === 0 ? null : (
        <PeriodStrip
          name="evidence-sources"
          title="When each source's latest accepted reading in this period was taken"
          start={start}
          end={end}
          startText={start === null ? undefined : (plainTime(start) ?? undefined)}
          endText={end === null ? undefined : (plainTime(end) ?? undefined)}
          legend={[{ tone: "marker", label: "Latest reading taken" }]}
          rows={evidence.sources.map((s) => {
            const taken = s.accepted_in_window === 0 ? null : s.last_source_time;
            return {
              key: s.source_id,
              label: <span {...REF} title={s.external_id}>{idWords(s.external_id)}</span>,
              segments: taken === null ? [] : [{ key: "latest", start: taken, end: taken, tone: "marker" as const, label: "Latest reading taken" }],
              summary:
                s.accepted_in_window === 0
                  ? "No accepted reading in this period."
                  : `${plural(s.accepted_in_window, "reading", "readings")} accepted; latest taken ${when(s.last_source_time)} (${clockWords(s.clocks.source_time)}).`,
            };
          })}
        />
      )}
    </>
  );
}

function SourcesOverview({
  evidence,
  health,
  onInspect,
}: {
  evidence: LedgerEvidence;
  health: EvidenceRead<GatewayHealth> | null;
  onInspect: (source: string) => void;
}) {
  // W1-F2 compaction: the mock's three source rows first, then "Show all N sources".
  const [showAll, setShowAll] = useState(false);
  return (
    <Panel
      heading="Data sources · data quality, not equipment condition"
      headingId="site-evidence-sources-heading"
      description="Readings received, gateway contact and analysis status are separate facts"
    >
      <ReportingFacts evidence={evidence} health={health} />
      {evidence.sources.length === 0 ? (
        <p data-evidence-sources-empty>No source has reported to this site.</p>
      ) : (
        <DataTable labelledBy="site-evidence-sources-heading">
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Accepted in period</th>
              <th scope="col">Latest taken</th>
              <th scope="col">Latest received</th>
              <th scope="col">Readings</th>
            </tr>
          </thead>
          <tbody>
            {evidence.sources.map((s, index) => (
              <tr key={s.source_id} data-evidence-source={s.source_id} hidden={!showAll && index >= SOURCE_PREVIEW_ROWS}>
                <th scope="row" {...REF} title={s.external_id}>
                  {idWords(s.external_id)}
                </th>
                {s.accepted_in_window === 0 ? (
                  <td colSpan={3}>No accepted reading in this period</td>
                ) : (
                  <>
                    <td>{s.accepted_in_window}</td>
                    <td>{when(s.last_source_time)}</td>
                    <td>{when(s.last_received_at)}</td>
                  </>
                )}
                <td>
                  <button type="button" className="link-button evidence-nowrap" onClick={() => onInspect(s.source_id)}>
                    See readings
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      {evidence.sources.length <= SOURCE_PREVIEW_ROWS ? null : (
        <p className="v69-chart-note">
          <button
            type="button"
            className="link-button"
            aria-expanded={showAll}
            onClick={() => setShowAll((v) => !v)}
            data-evidence-sources-toggle={showAll ? "all" : "preview"}
          >
            {showAll ? `Show the first ${SOURCE_PREVIEW_ROWS} only` : `Show all ${evidence.sources.length} sources`}
          </button>
        </p>
      )}
      <NotAvailableYet name="source-judgements">
        Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these.
      </NotAvailableYet>
      {/* W1-F2 compaction: the clock note, the per-source strip, the gateway's own report and the earlier-store
          comparison sit in one closed disclosure; the three reporting facts above stay visible. */}
      <Advanced
        name="evidence-sources-detail"
        summary={
          evidence.migration === null
            ? "Advanced details — clocks, latest reading per source and gateway contact"
            : "Advanced details — clocks, latest reading per source, gateway contact and earlier store"
        }
      >
        {evidence.sources.length === 0 ? null : (
          <p className="panel__note" data-evidence-source-clocks>
            {`Latest taken: ${Array.from(new Set(evidence.sources.map((s) => clockWords(s.clocks.source_time)))).join(" or ")}; latest received: server clock (UTC).`}
          </p>
        )}
        <SourceStrip evidence={evidence} />
        <div className="evidence-gateway-block" aria-label="Gateway contact">
          <p>
            <strong>Gateway contact</strong>
          </p>
          <GatewayContact health={health} detailed={false} />
        </div>
        {/* W1-F2: the earlier-store comparison is reference material about these sources, so it closes this panel. */}
        {evidence.migration === null ? null : (
          <Advanced name="evidence-earlier-store" summary="Advanced details — earlier store">
            <MigrationNote evidence={evidence} />
          </Advanced>
        )}
      </Advanced>
    </Panel>
  );
}

/** W1-F2 compaction: the sources table shows this many rows until "Show all" (the mock's three). */
const SOURCE_PREVIEW_ROWS = 3;

function NextEvidence({ evidence }: { evidence: LedgerEvidence }) {
  const silent = evidence.sources.filter((s) => s.accepted_in_window === 0);
  return (
    <Panel heading="Most useful next evidence" headingId="site-evidence-next-heading">
      <NotAvailableYet name="next-evidence">
        Not available yet: ranking the next evidence needs a reviewed rule linking missing readings to conclusions.
      </NotAvailableYet>
      {evidence.sources.length === 0 ? null : silent.length === 0 ? (
        <p data-evidence-silent-sources="none">Every source has at least one accepted reading in this period.</p>
      ) : (
        <div data-evidence-silent-sources={silent.length}>
          <p>Sources with no accepted reading in this period (a fact, not a recommendation):</p>
          <ul className="cell-list">
            {silent.map((s) => (
              <li key={s.source_id} {...REF} title={s.external_id}>
                {idWords(s.external_id)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}

function MigrationNote({ evidence }: { evidence: LedgerEvidence }) {
  const m = evidence.migration;
  if (m === null) {
    return null;
  }
  return (
    <p data-evidence-migration={m.empty_set === true ? "empty_set" : (m.outcome ?? "unknown")}>
      {m.empty_set === true
        ? "Before this page switched to the current store, the earlier store held no readings for this site, so none were carried over. Every reading shown here arrived directly."
        : "Before this page switched to the current store, the earlier store's readings for this site were compared with it; the comparison is on the Analysis view."}
    </p>
  );
}

// --- gateway contact -----------------------------------------------------------------

function GatewayContact({ health, detailed }: { health: EvidenceRead<GatewayHealth> | null; detailed: boolean }) {
  let body;
  if (health === null) {
    body = <p>Loading the site&apos;s gateway contact.</p>;
  } else if (health.status === "not_found") {
    body = <p data-gateway-contact="none">No gateway is registered for this site, so there is no contact to report.</p>;
  } else if (health.status === "unavailable") {
    body = (
      <p data-gateway-contact="unavailable">
        The gateway contact record could not be read, so whether the gateway is in touch is not known.
      </p>
    );
  } else {
    body = (
      <>
        {health.value.gateways.map((g) => (
          <div key={g.gateway_id} data-gateway-contact={g.status}>
            <p>
              <span {...REF}>{g.gateway_external_id}</span>
              {": "}
              {g.status === "CURRENT"
                ? `in contact. Last report received ${when(g.last_server_contact)}`
                : g.status === "STALE"
                  ? `not heard from recently. Last report received ${when(g.last_server_contact)}`
                  : "no report has been received yet"}
              {g.declared_cadence_seconds === null
                ? "."
                : `; it is expected to report every ${g.declared_cadence_seconds} seconds.`}
              {g.registration === "DISABLED" ? " This gateway is currently switched off for this site." : ""}
            </p>
            {detailed ? (
              <FactList>
                <Fact term="Last report received (server clock, UTC)">{when(g.last_server_contact)}</Fact>
                <Fact term="Time stated by the gateway (its own clock)">{when(g.gateway_observed_at)}</Fact>
                <Fact term="Gateway clock difference">
                  {g.clock_offset_ms === null ? "Unknown" : `${g.clock_offset_ms} ms`}
                </Fact>
                <Fact term="Readings waiting at the gateway">
                  {g.queue_count === null ? "Unknown" : `${g.queue_count}${g.oldest_queue_age_seconds === null ? "" : `, oldest waiting ${g.oldest_queue_age_seconds} s`}`}
                </Fact>
                <Fact term="Storage pressure reported">
                  {g.disk_pressure === null
                    ? "Unknown"
                    : `${g.disk_pressure}${g.disk_pressure_provenance === "REPORTED_SIMULATED_GATEWAY" ? " (reported by the demonstration gateway, not measured hardware)" : " (as reported by the gateway)"}`}
                </Fact>
                <Fact term="Readings it could not match to an input">
                  {g.mapping_error_count === null ? "Unknown" : g.mapping_error_count}
                </Fact>
                <Fact term="Last report per source">
                  {g.source_contacts.length === 0
                    ? "None registered"
                    : g.source_contacts.map((c) => (
                        <span key={c.source_id} data-gateway-source={c.source_id}>
                          <span {...REF}>{c.source_external_id}</span>
                          {`: ${c.last_contact === null ? "no report" : when(c.last_contact)}${c.registration === "DISABLED" ? " (switched off)" : ""}. `}
                        </span>
                      ))}
                </Fact>
              </FactList>
            ) : null}
          </div>
        ))}
        <p className="overview-note">
          This is the gateway&apos;s own report about itself. It is not a reading, and it says nothing about the
          condition of the equipment.
        </p>
      </>
    );
  }
  return body;
}

// --- analysis ------------------------------------------------------------------------

function Clocks({ evidence }: { evidence: LedgerEvidence }) {
  return (
    <Panel heading="Which clock each time uses" headingId="site-evidence-clocks-heading">
      <ul data-evidence-clocks>
        <li>
          <strong>Taken:</strong> when the reading was taken, on the source&apos;s timeline (the demonstration
          timeline for demonstration data). The selected period uses this time.
        </li>
        <li>
          <strong>Sent:</strong> when the source sent the reading, on the same timeline.
        </li>
        <li>
          <strong>Received:</strong> when the server first received the delivery that carried it, on the
          server clock (UTC).
        </li>
      </ul>
      <p>
        The demonstration timeline and the server clock are different clocks, so the gap between a taken and a
        received time is not a delivery delay.
      </p>
      <p>
        <strong>Period limits:</strong>{" "}
        {evidence.window.start === null ? "no start" : readableTime(evidence.window.start)} up to but not including{" "}
        {evidence.window.end === null ? "no end" : readableTime(evidence.window.end)}. Latest server receipt for
        this site: {when(evidence.extent.last_received_at)}.
      </p>
    </Panel>
  );
}

function Sources({ evidence, onInspect }: { evidence: LedgerEvidence; onInspect: (source: string) => void }) {
  if (evidence.sources.length === 0) {
    return null;
  }
  return (
    <Panel heading="Sources in this period" headingId="site-evidence-source-table-heading" flush>
      <DataTable labelledBy="site-evidence-source-table-heading">
        <thead>
          <tr>
            <th scope="col">Source</th>
            <th scope="col">Gateway</th>
            <th scope="col">Accepted</th>
            <th scope="col">Identical repeats</th>
            <th scope="col">Not accepted</th>
            <th scope="col">Different contents</th>
            <th scope="col">Latest taken</th>
            <th scope="col">Latest sent</th>
            <th scope="col">Latest received</th>
            <th scope="col">Readings</th>
          </tr>
        </thead>
        <tbody>
          {evidence.sources.map((s) => (
            <tr key={s.source_id} data-evidence-source-row={s.source_id}>
              <th scope="row" {...REF}>{s.external_id}</th>
              <td {...REF}>{s.gateway_external_id}</td>
              <td>{s.accepted_in_window}</td>
              <td>{s.duplicates_in_window}</td>
              <td>{s.rejected_in_window}</td>
              <td>{s.conflicts_in_window}</td>
              <td>{`${when(s.last_source_time)} (${clockWords(s.clocks.source_time)})`}</td>
              <td>{`${when(s.last_published_at)} (${clockWords(s.clocks.published_at)})`}</td>
              <td>{`${when(s.last_received_at)} (${clockWords(s.clocks.received_at)})`}</td>
              <td>
                <button type="button" onClick={() => onInspect(s.source_id)}>
                  See readings
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

function Deliveries({ evidence }: { evidence: LedgerEvidence }) {
  if (evidence.batches.length === 0) {
    return null;
  }
  return (
    <Panel heading="Deliveries" headingId="site-evidence-deliveries-heading" flush>
      <DataTable labelledBy="site-evidence-deliveries-heading">
        <thead>
          <tr>
            <th scope="col">Delivery</th>
            <th scope="col">Progress</th>
            <th scope="col">Accepted</th>
            <th scope="col">Identical repeats</th>
            <th scope="col">Not accepted</th>
            <th scope="col">Different contents</th>
            <th scope="col">Received (server clock)</th>
            <th scope="col">Finished (server clock)</th>
          </tr>
        </thead>
        <tbody>
          {evidence.batches.map((b) => (
            <tr key={b.batch_uuid} data-evidence-delivery={b.batch_id} data-delivery-partial={b.partial ? "true" : "false"}>
              <th scope="row" {...REF}>{b.batch_id}</th>
              <td>
                {b.partial
                  ? `Still being processed: ${b.counts.processed} of ${b.counts.total}`
                  : `Finished: ${b.counts.processed} of ${b.counts.total}`}
              </td>
              <td>{b.counts.accepted}</td>
              <td>{b.counts.duplicate}</td>
              <td>{b.counts.rejected}</td>
              <td>{b.counts.conflict}</td>
              <td>{when(b.received_at)}</td>
              <td>{b.completed_at === null ? "Not finished" : when(b.completed_at)}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

function Coverage({ evidence, onInspect }: { evidence: LedgerEvidence; onInspect: (key: string) => void }) {
  if (evidence.coverage.length === 0) {
    return null;
  }
  return (
    <Panel heading="Readings by input" headingId="site-evidence-coverage-heading" flush>
      <DataTable labelledBy="site-evidence-coverage-heading">
        <thead>
          <tr>
            <th scope="col">Device and signal</th>
            <th scope="col">Unit</th>
            <th scope="col">Readings</th>
            <th scope="col">Good quality</th>
            <th scope="col">Earlier configuration</th>
            <th scope="col">First taken</th>
            <th scope="col">Last taken</th>
            <th scope="col">Readings</th>
          </tr>
        </thead>
        <tbody>
          {evidence.coverage.map((c) => (
            <tr key={`${c.device_id}/${c.signal_id}`} data-evidence-coverage={`${c.device_id}/${c.signal_id}`}>
              <th scope="row" {...REF}>{`${c.device_id} / ${c.signal_id}`}</th>
              <td>{c.unit ?? "none"}</td>
              <td>{c.records}</td>
              <td>{c.good}</td>
              <td>{Number(c.configuration_outdated) > 0 ? String(Number(c.configuration_outdated)) : "None"}</td>
              <td>{when(c.first_source_time)}</td>
              <td>{when(c.last_source_time)}</td>
              <td>
                <button type="button" onClick={() => onInspect(`${c.device_id}/${c.signal_id}`)}>
                  See readings
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

function AnalysisStatus({ evidence }: { evidence: LedgerEvidence }) {
  const p = evidence.projection;
  const waiting = p.pending_jobs + p.leased_jobs;
  return (
    <Panel heading="Analysis status" headingId="site-evidence-analysis-status-heading">
      <p data-evidence-analysis-status={p.status}>
        {p.status === "STALE"
          ? `Analysis results do not yet include the newest readings: ${plural(waiting, "update is", "updates are")} waiting${p.failed_jobs > 0 ? ` and ${plural(p.failed_jobs, "update has", "updates have")} failed` : ""}${p.oldest_job_created_at === null ? "" : `, the oldest since ${when(p.oldest_job_created_at)}`}.`
          : p.failed_jobs > 0
            ? `${plural(p.failed_jobs, "analysis update has", "analysis updates have")} failed.`
            : "No analysis update is waiting for readings in this period."}
      </p>
      <p className="overview-note">
        This concerns derived analysis only, not whether readings are arriving: the gateway contact above and the
        received times say that. Analysis results are not produced on this page, and no conclusion about how the
        site is operating is drawn here.
      </p>
    </Panel>
  );
}

function Comparison({ evidence }: { evidence: LedgerEvidence }) {
  const m = evidence.migration;
  if (m === null) {
    return null;
  }
  return (
    <Panel heading="Earlier store comparison" headingId="site-evidence-comparison-heading">
      <MigrationNote evidence={evidence} />
      <FactList>
        <Fact term="Comparison result">{m.outcome ?? "Not stated"}</Fact>
        <Fact term="Readings in the earlier store">{m.empty_set === true ? "None" : m.empty_set === false ? "Some" : "Not stated"}</Fact>
        <Fact term="Compared at (server clock, UTC)">{when(m.compared_at)}</Fact>
        <Fact term="Comparison reference">
          <span {...REF}>{m.report_id ?? "none"}</span>
        </Fact>
      </FactList>
    </Panel>
  );
}

function Rejected({
  siteId,
  ledger,
  evidence,
  technical,
}: {
  siteId: string;
  ledger: LedgerEvidenceClient | undefined;
  evidence: LedgerEvidence;
  /** The record-level technical disclosures; they nest inside the panel's single advanced row. */
  technical?: ReactNode;
}) {
  const [loaded, setLoaded] = useState<EvidenceRead<LedgerRejections> | null>(null);
  useEffect(() => {
    if (ledger === undefined) {
      setLoaded({ status: "unavailable", message: null });
      return undefined;
    }
    let active = true;
    setLoaded(null);
    void ledger.listRejections(siteId).then((value) => {
      if (active) setLoaded(value);
    });
    return () => {
      active = false;
    };
  }, [ledger, siteId]);

  const untimed = evidence.counts.rejected_without_source_time;
  const refused = notAccepted(evidence);
  return (
    <div className="evidence-rejected" aria-labelledby="site-evidence-rejected-heading">
      {/* Review Low 7a: the not-accepted facts fold into one note line, before the one closed disclosure. */}
      <p className="v69-chart-note">
        <strong id="site-evidence-rejected-heading">Readings not accepted:</strong>{" "}
        <span data-evidence-not-accepted-line={refused}>
          {refused === 0
            ? "No reading in this period was refused."
            : `${plural(refused, "reading", "readings")} in this period ${refused === 1 ? "was" : "were"} not accepted (${evidence.counts.rejected} refused, ${evidence.counts.conflicts} arrived again with different contents). They are never counted as accepted.`}
        </span>{" "}
        <span data-evidence-untimed={typeof untimed === "number" ? String(untimed) : "unavailable"}>
          {typeof untimed !== "number"
            ? "How many refused readings had no readable time is not available."
            : untimed === 0
              ? "Every refused reading had a readable time."
              : `${plural(untimed, "refused reading has", "refused readings have")} no readable time, so no period can hold ${untimed === 1 ? "it" : "them"}; ${untimed === 1 ? "it is" : "they are"} listed in the advanced details below.`}{" "}
          A delivery that was rejected as a whole is kept for audit and not listed as a reading.
        </span>
      </p>
      <Advanced name="evidence-records-technical" summary="Advanced details — readings not accepted, clocks, sources, deliveries and readings by input">
      <Advanced name="evidence-not-accepted" summary="Advanced details — readings not accepted">
        {evidence.state === "NO_DATA" ? null : <OutcomeBars evidence={evidence} />}
        <h3 id="site-evidence-rejected-table-heading">Readings not accepted (all periods)</h3>
        {loaded === null ? (
          <p>Loading the refused readings.</p>
        ) : loaded.status !== "loaded" ? (
          <p data-rejections-unavailable>The list of refused readings could not be read.</p>
        ) : loaded.value.rejections.length === 0 && loaded.value.duplicates.length === 0 ? (
          <p>No reading has been refused or repeated for this site.</p>
        ) : (
          <>
            {loaded.value.rejections.length === 0 ? null : (
              <DataTable labelledBy="site-evidence-rejected-table-heading">
                <thead>
                  <tr>
                    <th scope="col">Message</th>
                    <th scope="col">What happened</th>
                    <th scope="col">Reason</th>
                    <th scope="col">Taken</th>
                    <th scope="col">Original reading</th>
                    <th scope="col">Received (server clock)</th>
                    <th scope="col">Decided (server clock)</th>
                  </tr>
                </thead>
                <tbody>
                  {loaded.value.rejections.map((r) => (
                    <tr key={r.rejection_id} data-evidence-rejection={r.rejection_id} data-rejection-kind={r.kind}>
                      <th scope="row" {...REF}>{r.message_id ?? `${r.batch_id} #${r.ordinal ?? "?"}`}</th>
                      <td>{r.kind === "MESSAGE_CONFLICT" ? "Arrived again with different contents" : "Not accepted"}</td>
                      <td {...REF}>{r.detail}</td>
                      <td>{r.source_time === null ? "No readable time" : when(r.source_time)}</td>
                      <td>
                        {r.kind !== "MESSAGE_CONFLICT" ? (
                          "Not applicable"
                        ) : (
                          <span data-conflict-original={r.conflicts_with_evidence_id ?? "unknown"}>
                            {r.conflicts_with_source_time === undefined || r.conflicts_with_source_time === null
                              ? "Original reading's taken time not stated"
                              : `Original reading taken ${when(r.conflicts_with_source_time)}`}
                            {r.conflicts_with_evidence_id === null ? null : (
                              <>
                                {"; kept as "}
                                <RecordLink evidenceId={r.conflicts_with_evidence_id} />
                              </>
                            )}
                          </span>
                        )}
                      </td>
                      <td>{when(r.received_at)}</td>
                      <td>{when(r.decided_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </DataTable>
            )}
            {loaded.value.duplicates.length === 0 ? null : (
              <ul className="cell-list" data-evidence-duplicates>
                {loaded.value.duplicates.map((d) => (
                  <li key={`${d.batch_id}/${d.ordinal}`} data-evidence-duplicate={d.message_id}>
                    {"Identical repeat of "}
                    <span {...REF}>{d.message_id}</span>
                    {`, received ${when(d.received_at)}; kept once as `}
                    <RecordLink evidenceId={d.first_accepted_evidence_id} />
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </Advanced>
      {technical}
      </Advanced>
    </div>
  );
}

function RecordLink({ evidenceId }: { evidenceId: string }) {
  const [params, setParams] = useSearchParams();
  return (
    <button
      type="button"
      data-vocabulary-reference={evidenceId}
      onClick={() => {
        const next = new URLSearchParams(params);
        next.set("record", evidenceId);
        next.set("view", "analysis");
        setParams(next);
      }}
    >
      {`reading ${evidenceId}`}
    </button>
  );
}

// --- inspector -----------------------------------------------------------------------

/**
 * `evidence-analysis:1`: the accepted readings in the selected period, for the
 * whole site or for the source or input a reader chose, each opening its full
 * record (configuration, receipt and the exact message as received).
 */
/** W1-F2 compaction: the accepted-records table shows this many rows until "Show all" (the mock's three). */
const RECORD_PREVIEW_ROWS = 3;

function Inspector({
  siteId,
  ledger,
  evidence,
  timezone,
  children,
}: {
  siteId: string;
  ledger: LedgerEvidenceClient | undefined;
  evidence: LedgerEvidence;
  timezone: string | null;
  children?: ReactNode;
}) {
  const measuredZone = zoneAbbreviation(timezone, evidence.window.start);
  const selectedDay = selectedLocalDay(evidence.window.start, timezone);
  const [params, setParams] = useSearchParams();
  const signal = params.get("signal");
  const source = params.get("source");
  const record = params.get("record");
  const cursor = params.get("cursor");
  const slash = signal === null ? -1 : signal.indexOf("/");
  const device = slash < 0 || signal === null ? null : signal.slice(0, slash);
  const signalId = slash < 0 || signal === null ? null : signal.slice(slash + 1);
  const filtered = source !== null || (device !== null && signalId !== null);
  const [list, setList] = useState<EvidenceRead<LedgerRecordPage> | null>(null);
  const [detail, setDetail] = useState<EvidenceRead<LedgerRecordDetail> | null>(null);
  const { start, end } = evidence.window;

  useEffect(() => {
    if (ledger === undefined) {
      setList(null);
      return undefined;
    }
    let active = true;
    setList(null);
    void ledger
      .listRecords(siteId, {
        source,
        device: source === null ? device : null,
        signal: source === null ? signalId : null,
        from: start,
        to: end,
        cursor,
        limit: filtered ? LEDGER_RECORD_LIMIT : LEDGER_SITE_RECORD_LIMIT,
      })
      .then((value) => {
        if (active) setList(value);
      });
    return () => {
      active = false;
    };
  }, [ledger, siteId, source, device, signalId, start, end, cursor, filtered]);

  useEffect(() => {
    if (record === null || ledger === undefined) {
      setDetail(null);
      return undefined;
    }
    let active = true;
    setDetail(null);
    void ledger.getRecord(siteId, record).then((value) => {
      if (active) setDetail(value);
    });
    return () => {
      active = false;
    };
  }, [ledger, siteId, record]);

  const change = (edit: (next: URLSearchParams) => void) => {
    const next = new URLSearchParams(params);
    edit(next);
    setParams(next);
  };
  const chosen =
    source !== null
      ? (evidence.sources.find((s) => s.source_id === source)?.external_id ?? source)
      : signal;
  const page = list !== null && list.status === "loaded" ? list.value : null;
  const clocks = page === null ? [] : Array.from(new Set(page.records.map((item) => clockWords(item.clocks.source_time))));
  // W1-F2 compaction: the mock's three rows first (the rest stay in the table, hidden), then "Show all" for this page. A chosen record
  // past the third row always shows the full page, so the selected row is never hidden.
  const [showAll, setShowAll] = useState(false);
  const selectedIndex = page === null || record === null ? -1 : page.records.findIndex((item) => item.evidence_id === record);
  const allShown = showAll || selectedIndex >= RECORD_PREVIEW_ROWS;

  return (
    <div id={LEDGER_INSPECTOR_ID} data-evidence-inspector={source ?? signal ?? "site"}>
      <Panel
        heading="Accepted records behind the conclusions"
        headingId="site-evidence-inspector-heading"
        description="Measured time is kept even when a report arrives late"
      >
        {!filtered ? null : (
          <p className="evidence-records__filter" data-evidence-records-filter>
            {"Showing "}
            <span {...REF}>{chosen}</span>
            {" only. "}
            <button
              type="button"
              className="link-button"
              onClick={() => change((n) => ["signal", "source", "cursor"].forEach((k) => n.delete(k)))}
            >
              Show every source
            </button>
          </p>
        )}
        {ledger === undefined ? (
          <p data-inspector-unavailable>The readings could not be read.</p>
        ) : list === null ? (
          <p>Loading the inspected records.</p>
        ) : list.status !== "loaded" ? (
          <p data-inspector-unavailable>
            {list.status === "unavailable" && list.message !== null ? list.message : "The readings could not be read."}
          </p>
        ) : list.value.total === 0 ? (
          <p data-evidence-records-empty>No accepted reading in this period.</p>
        ) : (
          <>
            {/* MOCK DEVIATION D1 (post-W6 shell Q3/Q18, register R381): no "Missing / Inspect the gap" row and no
                external-link marker on Open record; the ledger read has no stored gap row to list. */}
            <ChartNote data={{ "data-evidence-records-count": String(list.value.records.length) }}>
              {`${list.value.records.length} of ${list.value.total} accepted readings in this period, earliest measured first. Measured and sent times: ${clocks.join(" or ")}; received times: server clock (UTC). Measured times are shown in site time (${measuredZone}); sent and received times stay UTC. The gap between them is not a delivery delay.`}
            </ChartNote>
            <DataTable labelledBy="site-evidence-inspector-heading">
              <thead>
                <tr>
                  <th scope="col">Source · reading</th>
                  <th scope="col">Value</th>
                  {/* post-W6 shell R170 (Q18): measured time on the Site's clock, like the mock `Measured (EAT)`. */}
                  <th scope="col" data-evidence-measured-zone={measuredZone}>{`Measured (${measuredZone})`}</th>
                  <th scope="col">Sent</th>
                  <th scope="col">Received</th>
                  <th scope="col">Record</th>
                </tr>
              </thead>
              <tbody>
                {list.value.records.map((item, index) => (
                  <tr
                    key={item.evidence_id}
                    data-evidence-record={item.evidence_id}
                    aria-selected={item.evidence_id === record}
                    hidden={!allShown && index >= RECORD_PREVIEW_ROWS}
                  >
                    <th scope="row" title={`${item.source.external_id} · ${item.device_id} / ${item.signal_id}`}>
                      {readingName(item)}
                      <small {...REF}>{idWords(item.source.external_id)}</small>
                    </th>
                    <td>
                      {readingValue(item.normalized)}
                      {item.quality === "GOOD" ? null : (
                        <span className="evidence-records__quality">{` (quality: ${qualityWords(item.quality).toLowerCase()})`}</span>
                      )}
                    </td>
                    <td
                      data-evidence-measured={item.source_time ?? ""}
                      title={item.source_time ? `Exact time: ${when(item.source_time)} (${item.source_time})` : undefined}
                    >
                      {measuredTime(item.source_time, timezone, selectedDay)}
                    </td>
                    <td>{when(item.published_at)}</td>
                    <td>{when(item.received_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="link-button evidence-nowrap"
                        onClick={() => change((n) => n.set("record", item.evidence_id))}
                        data-vocabulary-reference={item.evidence_id}
                        aria-label={`Open record ${item.evidence_id}`}
                      >
                        Open record
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
            <p className="evidence-records__paging v69-chart-note">
              {list.value.records.length <= RECORD_PREVIEW_ROWS || selectedIndex >= RECORD_PREVIEW_ROWS ? null : (
                <button
                  type="button"
                  className="link-button"
                  aria-expanded={showAll}
                  onClick={() => setShowAll((v) => !v)}
                  data-evidence-records-toggle={showAll ? "all" : "preview"}
                >
                  {showAll
                    ? `Show the first ${RECORD_PREVIEW_ROWS} only`
                    : list.value.records.length === list.value.total
                      ? `Show all ${list.value.total} readings`
                      : `Show all ${list.value.records.length} readings on this page`}
                </button>
              )}{" "}
              {cursor === null ? null : (
                <button type="button" className="action" onClick={() => change((n) => n.delete("cursor"))}>
                  First page
                </button>
              )}{" "}
              {list.value.next_cursor === null ? null : (
                <button
                  type="button"
                  className="action"
                  onClick={() => change((n) => n.set("cursor", list.value.next_cursor as string))}
                >
                  Next page
                </button>
              )}
            </p>
          </>
        )}
        {record === null ? null : <RecordView detail={detail} onClose={() => change((n) => n.delete("record"))} />}
        {children}
      </Panel>
    </div>
  );
}

/** `evidence-analysis:2`: the S2-supported way a claim is limited, in plain prose. */
function ClaimLimit({
  evidence,
  children,
  technical,
  detailSlotRef,
}: {
  evidence: LedgerEvidence;
  children?: ReactNode;
  /** The empty slot inside the panel's single advanced row; the selected assessment's detail renders into it. */
  detailSlotRef?: (el: HTMLDivElement | null) => void;
  /** The closed technical disclosures, after the not-available line and the list of limits. */
  technical?: ReactNode;
}) {
  const applies = (state: LedgerEvidence["states"][number]) =>
    evidence.states.includes(state) ? " This applies to the selected period." : "";
  const p = evidence.projection;
  const analysisBehind = p.status === "STALE" || p.failed_jobs > 0;
  return (
    <Panel heading="How each limit is set" headingId="site-evidence-claim-limit-heading">
      {/* W1-F2: note-size lines in the panel; the full list of limits sits in one closed disclosure, every statement kept. */}
      <div data-evidence-claim-limit>
        {/* W1-F2 fix round (H2): the mock's two paragraphs; the Overview's "This page states what arrived" line is not repeated. */}
        <div className="claim-limit__prose">
          <p>
            Each conclusion lists the readings it needs. When all are present for a period, the full conclusion is
            allowed. When one is missing or unreliable, the conclusion is narrowed to the periods that are covered,
            and the gap is shown rather than filled in.
          </p>
          <p data-evidence-limit-note>
            Data-source status describes reporting, not equipment condition: a source can be online while the
            equipment it watches is faulty. A conclusion describes what the readings show, not the equipment's physical
            capacity; configured ratings are not treated as observed.
          </p>
        </div>
      </div>
      {children}
      <NotAvailableYet name="claim-limit-rule">
        Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment).
      </NotAvailableYet>
      <Advanced
        name="evidence-limit-details"
        summary="Advanced details — what limits it, how what can be said is narrowed, analysis status and earlier store"
      >
        <div ref={detailSlotRef} data-claim-limit-detail-slot />
      <div data-evidence-claim-limit-list>
        <Advanced name="evidence-limit-list" summary="Advanced details — how what can be said is narrowed">
        <p>What can be said is narrowed in these ways:</p>
        <ul>
          <li data-claim-limit="PARTIAL_BATCH">
            {`A partial period: while deliveries are still being processed, the counts may still grow.${applies("PARTIAL_BATCH")}`}
          </li>
          <li data-claim-limit="CONFLICTING">
            {`Conflicting contents: when a reading arrives again with different contents, the first accepted version is kept and the later one is listed apart, beside the original reading's taken time.${applies("CONFLICTING")}`}
          </li>
          <li data-claim-limit="OUTDATED_CONFIGURATION">
            {`Outdated configuration: readings recorded under a site configuration that has since been updated stay accepted under the configuration in force when they were taken.${applies("OUTDATED_CONFIGURATION")}`}
          </li>
          <li data-claim-limit="ANALYSIS_STATUS">
            {`Analysis status: derived results may not yet include the newest readings; this is shown apart from whether readings are arriving.${analysisBehind ? " Derived results are behind for this site now; the analysis status details are below." : ""}`}
          </li>
        </ul>
        </Advanced>
      </div>
      {technical}
      </Advanced>
    </Panel>
  );
}

function RecordView({ detail, onClose }: { detail: EvidenceRead<LedgerRecordDetail> | null; onClose: () => void }) {
  return (
    <div className="evidence-record-view" aria-labelledby="site-evidence-record-heading">
      <p id="site-evidence-record-heading">
        <strong>Reading detail</strong>{" "}
        <button type="button" onClick={onClose}>
          Close reading
        </button>
      </p>
      {detail === null ? (
        <p>Loading the inspected record.</p>
      ) : detail.status === "not_found" ? (
        <p data-record-state="not_found">This reading is not in this site&apos;s accepted readings.</p>
      ) : detail.status === "unavailable" ? (
        <p data-record-state="unavailable">{detail.message ?? "The reading could not be read."}</p>
      ) : (
        <RecordFacts item={detail.value} />
      )}
    </div>
  );
}

/** W1-F5b review M3: a coded word reads as a plain word ("GOOD" as "Good"); an unknown code is not guessed at. */
function plainCode(value: string): string {
  if (!/^[A-Z][A-Z_]*$/.test(value)) return value;
  const word = value.toLowerCase().replace(/_/g, " ");
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function RecordFacts({ item }: { item: LedgerRecordDetail }) {
  const r = item.receipt;
  return (
    <div data-record-detail={item.evidence_id}>
      <FactList>
        <Fact term="Reading">{readingName(item)}</Fact>
        <Fact term="Value as reported by the source">{readingValue(item.original)}</Fact>
        <Fact term="Value in site units">{readingValue(item.normalized)}</Fact>
        <Fact term="Quality">
          {plainCode(item.quality)}
          {item.unavailable_reason === null ? "" : ` (${plainCode(item.unavailable_reason).toLowerCase()})`}
        </Fact>
        <Fact term={`Taken (${clockWords(item.clocks.source_time)})`}>{when(item.source_time)}</Fact>
        <Fact term={`Sent (${clockWords(item.clocks.published_at)})`}>{when(item.published_at)}</Fact>
        <Fact term={`Received (${clockWords(item.clocks.received_at)})`}>{when(item.received_at)}</Fact>
        {item.interval === null ? null : (
          <Fact term="Covers">{readablePeriod(item.interval.start, item.interval.end)}</Fact>
        )}
        <Fact term="Origin">{sourceKind(item.source_mode)}</Fact>
        <Fact term="Decision">{plainCode(r.decision)}</Fact>
        <Fact term="Delivery first received (server clock, UTC)">{when(r.received_at)}</Fact>
        <Fact term="This reading decided (server clock, UTC)">{when(r.decided_at)}</Fact>
        <Fact term="Delivery progress">
          {`${r.processed} of ${r.total}${r.completed_at === null ? ", still being processed" : `, finished ${when(r.completed_at)}`}`}
        </Fact>
        <Fact term="Site configuration since updated">{item.accepted_as.configuration_outdated ? "Yes" : "No"}</Fact>
      </FactList>
      {item.duplicates.length === 0 ? null : (
        <p>{`${plural(item.duplicates.length, "identical repeat", "identical repeats")} arrived and ${item.duplicates.length === 1 ? "was" : "were"} kept once as this reading.`}</p>
      )}
      {item.conflicts.length === 0 ? null : (
        <p>{`${plural(item.conflicts.length, "later message", "later messages")} arrived with different contents. This reading was kept; the later ${item.conflicts.length === 1 ? "message was" : "messages were"} not accepted.`}</p>
      )}
      <Advanced name="evidence-record-references" summary="Exact references">
        <FactList>
          <Fact term="Reading">
            <span {...REF}>{item.evidence_id}</span>
          </Fact>
          <Fact term="Message">
            <span {...REF}>{item.message_id}</span>
          </Fact>
          <Fact term="Source and gateway">
            <span {...REF}>{`${item.source.external_id} / ${item.gateway.external_id}`}</span>
          </Fact>
          <Fact term="Device and signal">
            <span {...REF}>{`${item.device_id} / ${item.signal_id}`}</span>
          </Fact>
          <Fact term="Site configuration version">
            <span {...REF}>{item.accepted_as.foundation_revision_id}</span>
          </Fact>
          <Fact term="Input set version">
            <span {...REF}>{item.accepted_as.binding_set_revision_id}</span>
          </Fact>
          <Fact term="Input version">
            <span {...REF}>{item.accepted_as.binding_revision_id}</span>
          </Fact>
          <Fact term="Equipment">
            <span {...REF}>{item.accepted_as.asset_id ?? "none"}</span>
          </Fact>
          <Fact term="Delivery and position">
            <span {...REF}>{`${r.batch_id} / ${r.ordinal}`}</span>
          </Fact>
          <Fact term="Delivery fingerprint (SHA-256)">
            <span {...REF}>{r.payload_sha256}</span>
          </Fact>
          <Fact term="Message fingerprint (SHA-256)">
            <span {...REF}>{item.envelope.sha256}</span>
          </Fact>
        </FactList>
        <h3>Exact message as received</h3>
        <pre className="evidence-message-text" data-vocabulary-exempt="source-reference" data-record-message>
          {item.envelope.text}
        </pre>
        {item.duplicates.length === 0 ? null : (
          <>
            <h3>Identical repeats</h3>
            <ul className="cell-list">
              {item.duplicates.map((d) => (
                <li key={`${d.batch_id}/${d.ordinal}`} data-record-duplicate={`${d.batch_id}/${d.ordinal}`}>
                  <span {...REF}>{`${d.batch_id} / ${d.ordinal}`}</span>
                  {`: received ${when(d.received_at)}, kept once as this reading.`}
                </li>
              ))}
            </ul>
          </>
        )}
        {item.conflicts.length === 0 ? null : (
          <>
            <h3>Arrived again with different contents</h3>
            {item.conflicts.map((c) => (
              <div key={c.rejection_id} data-record-conflict={c.rejection_id}>
                <p>
                  <span {...REF}>{`${c.batch_id} / ${c.ordinal}`}</span>
                  {`: received ${when(c.received_at)}. This reading was kept; the later message was not accepted.`}
                </p>
                <pre className="evidence-message-text" data-vocabulary-exempt="source-reference">
                  {c.envelope_text ?? "The later message text is not available."}
                </pre>
              </div>
            ))}
          </>
        )}
      </Advanced>
    </div>
  );
}
