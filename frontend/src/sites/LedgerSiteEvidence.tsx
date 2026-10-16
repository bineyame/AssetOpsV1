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

import { Badge, DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import { CountBars } from "./assessmentGraphics";
import type { ClaimLimitClient } from "./claimLimitClient";
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

function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

function sourceKind(mode: string): string {
  return mode === "SIMULATED" ? "Demonstration data" : mode === "LIVE" ? "Live data" : "Data of unstated origin";
}

function readingValue(value: { value: string | null; unit: string | null }): string {
  return value.value === null ? "no value" : `${value.value}${value.unit === null ? "" : ` ${value.unit}`}`;
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
}

export function LedgerSiteEvidence({
  siteId,
  evidence,
  ledger,
  gatewayHealth,
  claimLimit,
  assessmentHref,
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
      <WindowChooser evidence={evidence} />
      {view === "overview" ? (
        <OverviewBody evidence={evidence} health={health} params={params} onInspect={(source) => inspect("source", source)} />
      ) : (
        <>
          <StatusBar view="analysis" badge="Evidence · Analysis">
            <span className="evidence-statusbar__facts">Accepted records, timing and how each limit is set</span>
          </StatusBar>
          <Inspector siteId={siteId} ledger={ledger} evidence={evidence} />
          <ClaimLimit evidence={evidence} />
          <EvidenceClaimLimit siteId={siteId} client={claimLimit} assessmentHref={assessmentHref} />
          <Rejected siteId={siteId} ledger={ledger} evidence={evidence} />
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
        </>
      )}
    </div>
  );
}

// --- selected period -------------------------------------------------------------

function WindowChooser({ evidence }: { evidence: LedgerEvidence }) {
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
    <form className="evidence-window evidence-toolbar" onSubmit={apply} data-evidence-window={evidence.window.basis}>
      <div className="evidence-toolbar__controls">
        <label className="evidence-toolbar__field">
          <span>From (UTC)</span>
          <input type="datetime-local" name="from" value={from} onChange={(e) => setFrom(e.target.value)} />
        </label>
        <label className="evidence-toolbar__field">
          <span>To (UTC)</span>
          <input type="datetime-local" name="to" value={to} onChange={(e) => setTo(e.target.value)} />
        </label>
        <button type="submit" className="action action--primary">
          Show this period
        </button>
        <button type="button" className="action" onClick={all}>
          Show all readings
        </button>
      </div>
      <p className="evidence-toolbar__period">
        <strong>Selected period:</strong> {period}. Periods are chosen by the time each reading was taken.
        {evidence.extent.first_source_time === null || evidence.extent.last_source_time === null
          ? " This site has no accepted readings yet."
          : ` Accepted readings for this site span ${readablePeriod(evidence.extent.first_source_time, evidence.extent.last_source_time)}.`}
      </p>
    </form>
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
    <p className="not-available-yet" data-not-available={name}>
      {children}
    </p>
  );
}

/** Technical records on demand: explicitly labelled, keyboard-operable, closed by default. */
function Advanced({ name, summary, children }: { name: string; summary: string; children: ReactNode }) {
  return (
    <div className="evidence-advanced">
      <Disclosure name={name} summary={summary}>
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
    <div className="evidence-statusbar" data-evidence-statusbar={view}>
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

function OutcomeFacts({ evidence }: { evidence: LedgerEvidence }) {
  return (
    <dl className="evidence-outcome-facts" data-evidence-outcome-facts>
      {OUTCOMES.map((o) => (
        <div key={o.key} data-evidence-outcome={o.key}>
          <dt>{o.label}</dt>
          <dd>{evidence.counts[o.key]}</dd>
        </div>
      ))}
    </dl>
  );
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
      >
        <p className="panel-lede" data-evidence-headline={evidence.state}>
          {headlineOf(evidence)}
        </p>
        {notes.length === 0 ? null : (
          <ul data-evidence-notes>
            {notes.map((state) => (
              <li key={state} data-evidence-note={state}>
                {STATE_NOTES[state]}
              </li>
            ))}
          </ul>
        )}
        <OutcomeFacts evidence={evidence} />
        <p data-evidence-rejection-count={refused}>
          {refused === 0
            ? "No reading in this period was refused."
            : `${plural(refused, "reading", "readings")} in this period could not be accepted; the reasons are on the Analysis view.`}
        </p>
        <p className="overview-note" data-evidence-limits>
          This page shows the readings received and what happened to each. It draws no conclusion about how the
          site or its equipment is operating.
        </p>
        <NotAvailableYet name="capability-conclusions">
          Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet.
        </NotAvailableYet>
      </Panel>
      <div className="panel-pair evidence-pair">
        <SourcesOverview evidence={evidence} health={health} onInspect={onInspect} />
        <NextEvidence evidence={evidence} />
      </div>
      <p className="notice notice--info" data-evidence-closing-notice>
        Record-level detail, timing and how each limit is set are on{" "}
        <Link to={{ search: analysis }}>Evidence › Analysis</Link>.
      </p>
      {evidence.migration === null ? null : (
        <Advanced name="evidence-earlier-store" summary="Advanced details — earlier store">
          <MigrationNote evidence={evidence} />
        </Advanced>
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
  return (
    <Panel heading="Data sources · data quality, not equipment condition" headingId="site-evidence-sources-heading">
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
            {evidence.sources.map((s) => (
              <tr key={s.source_id} data-evidence-source={s.source_id}>
                <th scope="row" {...REF}>
                  {s.external_id}
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
      {evidence.sources.length === 0 ? null : (
        <p className="panel__note" data-evidence-source-clocks>
          {`Latest taken: ${Array.from(new Set(evidence.sources.map((s) => clockWords(s.clocks.source_time)))).join(" or ")}; latest received: server clock (UTC).`}
        </p>
      )}
      <div className="evidence-gateway-block">
        <h3>Gateway contact</h3>
        <GatewayContact health={health} detailed={false} />
      </div>
      <NotAvailableYet name="source-judgements">
        Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these.
      </NotAvailableYet>
    </Panel>
  );
}

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
              <li key={s.source_id} {...REF}>
                {s.external_id}
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
}: {
  siteId: string;
  ledger: LedgerEvidenceClient | undefined;
  evidence: LedgerEvidence;
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
    <Panel heading="Readings not accepted" headingId="site-evidence-rejected-heading">
      <p data-evidence-not-accepted-line={refused}>
        {refused === 0
          ? "No reading in this period was refused."
          : `${plural(refused, "reading", "readings")} in this period ${refused === 1 ? "was" : "were"} not accepted (${evidence.counts.rejected} refused, ${evidence.counts.conflicts} arrived again with different contents). They are never counted as accepted.`}
      </p>
      <p data-evidence-untimed={typeof untimed === "number" ? String(untimed) : "unavailable"}>
        {typeof untimed !== "number"
          ? "How many refused readings had no readable time is not available."
          : untimed === 0
            ? "Every refused reading had a readable time."
            : `${plural(untimed, "refused reading has", "refused readings have")} no readable time, so no period can hold ${untimed === 1 ? "it" : "them"}; ${untimed === 1 ? "it is" : "they are"} listed in the advanced details below.`}{" "}
        A whole delivery the server refused is kept as an operational audit record and is not listed as a reading.
      </p>
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
    </Panel>
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
function Inspector({
  siteId,
  ledger,
  evidence,
}: {
  siteId: string;
  ledger: LedgerEvidenceClient | undefined;
  evidence: LedgerEvidence;
}) {
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
            <p>
              {`${list.value.records.length} of ${list.value.total} accepted readings in this period, earliest taken first. Taken and sent times: ${clocks.join(" or ")}; received times: server clock (UTC). The gap between them is not a delivery delay.`}
            </p>
            <DataTable labelledBy="site-evidence-inspector-heading">
              <thead>
                <tr>
                  <th scope="col">Source · reading</th>
                  <th scope="col">Value</th>
                  <th scope="col">Taken</th>
                  <th scope="col">Sent</th>
                  <th scope="col">Received</th>
                  <th scope="col">Record</th>
                </tr>
              </thead>
              <tbody>
                {list.value.records.map((item) => (
                  <tr key={item.evidence_id} data-evidence-record={item.evidence_id} aria-selected={item.evidence_id === record}>
                    <th scope="row" {...REF}>{`${item.source.external_id} · ${item.device_id} / ${item.signal_id}`}</th>
                    <td>
                      {readingValue(item.normalized)}
                      {item.quality === "GOOD" ? null : <span className="evidence-records__quality">{` (quality ${item.quality})`}</span>}
                    </td>
                    <td>{when(item.source_time)}</td>
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
            <p className="evidence-records__paging">
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
      </Panel>
      {record === null ? null : <RecordView detail={detail} onClose={() => change((n) => n.delete("record"))} />}
    </div>
  );
}

/** `evidence-analysis:2`: the S2-supported way a claim is limited, in plain prose. */
function ClaimLimit({ evidence }: { evidence: LedgerEvidence }) {
  const applies = (state: LedgerEvidence["states"][number]) =>
    evidence.states.includes(state) ? " This applies to the selected period." : "";
  const p = evidence.projection;
  const analysisBehind = p.status === "STALE" || p.failed_jobs > 0;
  return (
    <Panel heading="How each limit is set" headingId="site-evidence-claim-limit-heading">
      <div className="prose" data-evidence-claim-limit>
        <p>
          This page states what arrived for the selected period and draws no conclusion about how the site or its
          equipment is operating. What can be said is narrowed in these ways:
        </p>
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
        <p>Data-source status describes reporting, not equipment condition.</p>
      </div>
      <NotAvailableYet name="claim-limit-rule">
        Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment).
      </NotAvailableYet>
    </Panel>
  );
}

function RecordView({ detail, onClose }: { detail: EvidenceRead<LedgerRecordDetail> | null; onClose: () => void }) {
  return (
    <Panel heading="Reading detail" headingId="site-evidence-record-heading">
      <p>
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
    </Panel>
  );
}

function RecordFacts({ item }: { item: LedgerRecordDetail }) {
  const r = item.receipt;
  return (
    <div data-record-detail={item.evidence_id}>
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
        <Fact term="Value as reported by the source">{readingValue(item.original)}</Fact>
        <Fact term="Value in site units">{readingValue(item.normalized)}</Fact>
        <Fact term="Quality">{item.quality}{item.unavailable_reason === null ? "" : ` (${item.unavailable_reason})`}</Fact>
        <Fact term={`Taken (${clockWords(item.clocks.source_time)})`}>{when(item.source_time)}</Fact>
        <Fact term={`Sent (${clockWords(item.clocks.published_at)})`}>{when(item.published_at)}</Fact>
        <Fact term={`Received (${clockWords(item.clocks.received_at)})`}>{when(item.received_at)}</Fact>
        {item.interval === null ? null : (
          <Fact term="Covers">{readablePeriod(item.interval.start, item.interval.end)}</Fact>
        )}
        <Fact term="Origin">{sourceKind(item.source_mode)}</Fact>
      </FactList>
      <h3>Configuration it was accepted under</h3>
      <FactList>
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
        <Fact term="Configuration since updated">{item.accepted_as.configuration_outdated ? "Yes" : "No"}</Fact>
      </FactList>
      <h3>Delivery receipt</h3>
      <FactList>
        <Fact term="Delivery and position">
          <span {...REF}>{`${r.batch_id} / ${r.ordinal}`}</span>
        </Fact>
        <Fact term="Decision">{r.decision}</Fact>
        <Fact term="Delivery first received (server clock, UTC)">{when(r.received_at)}</Fact>
        <Fact term="This reading decided (server clock, UTC)">{when(r.decided_at)}</Fact>
        <Fact term="Delivery progress">
          {`${r.processed} of ${r.total}${r.completed_at === null ? ", still being processed" : `, finished ${when(r.completed_at)}`}`}
        </Fact>
        <Fact term="Delivery fingerprint (SHA-256)">
          <span {...REF}>{r.payload_sha256}</span>
        </Fact>
      </FactList>
      <h3>Exact message as received</h3>
      <FactList>
        <Fact term="Message fingerprint (SHA-256)">
          <span {...REF}>{item.envelope.sha256}</span>
        </Fact>
      </FactList>
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
    </div>
  );
}
