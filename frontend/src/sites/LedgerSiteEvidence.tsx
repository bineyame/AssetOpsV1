/**
 * Site > Evidence for an imported Site read from the central evidence ledger
 * (S2-02 phase 3b; payloads in `ledgerEvidenceClient.ts`).
 *
 * Overview is plain language and one graph: the selected period, how many
 * readings were accepted, repeated, not accepted or in conflict, the gateway's
 * last contact and the limits of what this page shows. Analysis holds the
 * deeper detail: the clocks with their labels, deliveries and their progress,
 * per-input coverage, the rejected readings (unwindowed), the earlier-store
 * comparison and the record inspector, where a reading opens its value as
 * reported and as converted, the configuration it was accepted under, its
 * delivery receipt and the exact message text.
 *
 * Clocks. Reading and publication times on demonstration data are instants on
 * the demonstration timeline; the received time is the server's real clock.
 * Nothing here subtracts one from the other. Analysis status (whether derived
 * results include the newest readings) is shown apart from evidence freshness
 * and never as a conclusion about how the site is operating.
 */

import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";

import { DataTable, Fact, FactList, Panel } from "../ui";
import { LocalViews, localView, readablePeriod, readableTime } from "./findingPresentation";
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
}

export function LedgerSiteEvidence({ siteId, evidence, ledger, gatewayHealth }: LedgerSiteEvidenceProps) {
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
      <StateSummary evidence={evidence} />
      <GatewayContact health={health} detailed={view === "analysis"} />
      {view === "overview" ? (
        <OverviewBody evidence={evidence} onInspect={(source) => inspect("source", source)} />
      ) : (
        <>
          <Clocks evidence={evidence} />
          <Sources evidence={evidence} onInspect={(source) => inspect("source", source)} />
          <Deliveries evidence={evidence} />
          <Coverage evidence={evidence} onInspect={(key) => inspect("signal", key)} />
          <AnalysisStatus evidence={evidence} />
          <Comparison evidence={evidence} />
          <Rejected siteId={siteId} ledger={ledger} evidence={evidence} />
          <Inspector siteId={siteId} ledger={ledger} evidence={evidence} />
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
    <form className="evidence-window" onSubmit={apply} data-evidence-window={evidence.window.basis}>
      <p>
        <strong>Selected period:</strong> {period}. Periods are chosen by the time each reading was taken.
        {evidence.extent.first_source_time === null || evidence.extent.last_source_time === null
          ? " This site has no accepted readings yet."
          : ` Accepted readings for this site span ${readablePeriod(evidence.extent.first_source_time, evidence.extent.last_source_time)}.`}
      </p>
      <label>
        From (UTC){" "}
        <input type="datetime-local" name="from" value={from} onChange={(e) => setFrom(e.target.value)} />
      </label>{" "}
      <label>
        To (UTC){" "}
        <input type="datetime-local" name="to" value={to} onChange={(e) => setTo(e.target.value)} />
      </label>{" "}
      <button type="submit">Show this period</button>{" "}
      <button type="button" onClick={all}>
        Show all readings
      </button>
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

function StateSummary({ evidence }: { evidence: LedgerEvidence }) {
  const { counts } = evidence;
  let headline: string;
  if (evidence.state === "NO_DATA") {
    headline = "No readings were received for this period.";
  } else if (evidence.state === "REJECTED_ONLY") {
    headline = `Readings arrived for this period, but none could be accepted (${plural(counts.rejected + counts.conflicts, "reading", "readings")} not accepted).`;
  } else {
    headline = `${plural(counts.accepted, "reading was", "readings were")} accepted for this period from ${plural(evidence.sources.filter((s) => s.accepted_in_window > 0).length, "source", "sources")}.`;
  }
  const notes = evidence.states.filter((state) => state in STATE_NOTES);
  return (
    <Panel heading="What arrived" headingId="site-evidence-state-heading">
      <p data-evidence-headline={evidence.state}>{headline}</p>
      {notes.length === 0 ? null : (
        <ul data-evidence-notes>
          {notes.map((state) => (
            <li key={state} data-evidence-note={state}>
              {STATE_NOTES[state]}
            </li>
          ))}
        </ul>
      )}
    </Panel>
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
  const total = OUTCOMES.reduce((sum, o) => sum + evidence.counts[o.key], 0);
  return (
    <div className="assessment-graphic value-bars" data-graphic="evidence-outcomes">
      <DataTable>
        <caption className="assessment-graphic__caption">
          Readings that arrived for this period, by what happened to them. Counts of readings.
        </caption>
        <thead>
          <tr>
            <th scope="col">Outcome</th>
            <th scope="col">Readings</th>
            <th scope="col" className="value-bars__bar-heading">
              <span className="visually-hidden">Bar</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {OUTCOMES.map((o) => {
            const count = evidence.counts[o.key];
            const share = total === 0 ? 0 : count / total;
            return (
              <tr key={o.key} data-evidence-outcome={o.key}>
                <th scope="row">{o.label}</th>
                <td>{count}</td>
                <td className="value-bars__bar">
                  <svg viewBox="0 0 1000 12" preserveAspectRatio="none" aria-hidden="true" focusable="false" data-bar-width={share.toFixed(6)}>
                    <rect x="0" y="0" width="1000" height="12" className="graphic-track" />
                    <rect x="0" y="0" width={share * 1000} height="12" className="graphic-fill--value" />
                  </svg>
                </td>
              </tr>
            );
          })}
        </tbody>
      </DataTable>
    </div>
  );
}

function OverviewBody({ evidence, onInspect }: { evidence: LedgerEvidence; onInspect: (source: string) => void }) {
  return (
    <>
      {evidence.state === "NO_DATA" ? null : <OutcomeBars evidence={evidence} />}
      {evidence.sources.length === 0 ? null : (
        <Panel heading="Sources" headingId="site-evidence-sources-heading">
          <ul className="cell-list">
            {evidence.sources.map((s) => (
              <li key={s.source_id} data-evidence-source={s.source_id}>
                <span {...REF}>{s.external_id}</span>
                {`: ${plural(s.accepted_in_window, "reading", "readings")} accepted in this period; latest reading taken ${when(s.last_source_time)} on the ${clockWords(s.clocks.source_time)}, latest received ${when(s.last_received_at)} (${clockWords(s.clocks.received_at)}). ${sourceKind(s.source_mode)}. `}
                <button type="button" onClick={() => onInspect(s.source_id)}>
                  See readings
                </button>
              </li>
            ))}
          </ul>
        </Panel>
      )}
      <p data-evidence-rejection-count={evidence.counts.rejected + evidence.counts.conflicts}>
        {evidence.counts.rejected + evidence.counts.conflicts === 0
          ? "No reading in this period was refused."
          : `${plural(evidence.counts.rejected + evidence.counts.conflicts, "reading", "readings")} in this period could not be accepted; the reasons are on the Analysis view.`}
      </p>
      <MigrationNote evidence={evidence} />
      <p className="overview-note" data-evidence-limits>
        This page shows the readings received and what happened to each. It draws no conclusion about how the
        site or its equipment is operating.
      </p>
    </>
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
  return (
    <Panel heading="Gateway contact" headingId="site-evidence-gateway-heading">
      {body}
    </Panel>
  );
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
  return (
    <Panel heading="Readings not accepted (all periods)" headingId="site-evidence-rejected-heading">
      <p data-evidence-untimed={typeof untimed === "number" ? String(untimed) : "unavailable"}>
        {typeof untimed !== "number"
          ? "How many refused readings had no readable time is not available."
          : untimed === 0
            ? "Every refused reading had a readable time."
            : `${plural(untimed, "refused reading has", "refused readings have")} no readable time, so no period can hold ${untimed === 1 ? "it" : "them"}; ${untimed === 1 ? "it is" : "they are"} listed here.`}{" "}
        A whole delivery the server refused is kept as an operational audit record and is not listed as a reading.
      </p>
      {loaded === null ? (
        <p>Loading the refused readings.</p>
      ) : loaded.status !== "loaded" ? (
        <p data-rejections-unavailable>The list of refused readings could not be read.</p>
      ) : loaded.value.rejections.length === 0 && loaded.value.duplicates.length === 0 ? (
        <p>No reading has been refused or repeated for this site.</p>
      ) : (
        <>
          {loaded.value.rejections.length === 0 ? null : (
            <DataTable labelledBy="site-evidence-rejected-heading">
              <thead>
                <tr>
                  <th scope="col">Message</th>
                  <th scope="col">What happened</th>
                  <th scope="col">Reason</th>
                  <th scope="col">Taken</th>
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
  const open = source !== null || (device !== null && signalId !== null);
  const [list, setList] = useState<EvidenceRead<LedgerRecordPage> | null>(null);
  const [detail, setDetail] = useState<EvidenceRead<LedgerRecordDetail> | null>(null);
  const { start, end } = evidence.window;

  useEffect(() => {
    if (!open || ledger === undefined) {
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
        limit: LEDGER_RECORD_LIMIT,
      })
      .then((value) => {
        if (active) setList(value);
      });
    return () => {
      active = false;
    };
  }, [ledger, siteId, open, source, device, signalId, start, end, cursor]);

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

  if (!open && record === null) {
    return null;
  }
  const change = (edit: (next: URLSearchParams) => void) => {
    const next = new URLSearchParams(params);
    edit(next);
    setParams(next);
  };

  return (
    <div id={LEDGER_INSPECTOR_ID} data-evidence-inspector={source ?? signal ?? "record"}>
      {!open ? null : (
        <Panel heading="Readings" headingId="site-evidence-inspector-heading">
          <p>
            <button type="button" onClick={() => change((n) => ["signal", "source", "record", "cursor"].forEach((k) => n.delete(k)))}>
              Close readings
            </button>
          </p>
          {ledger === undefined ? (
            <p data-inspector-unavailable>The readings could not be read.</p>
          ) : list === null ? (
            <p>Loading the inspected records.</p>
          ) : list.status !== "loaded" ? (
            <p data-inspector-unavailable>
              {list.status === "unavailable" && list.message !== null ? list.message : "The readings could not be read."}
            </p>
          ) : (
            <>
              <p>{`${list.value.records.length} of ${list.value.total} accepted readings in this period, earliest taken first.`}</p>
              <DataTable labelledBy="site-evidence-inspector-heading">
                <thead>
                  <tr>
                    <th scope="col">Taken</th>
                    <th scope="col">Device and signal</th>
                    <th scope="col">Value</th>
                    <th scope="col">Quality</th>
                    <th scope="col">Received (server clock)</th>
                    <th scope="col">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {list.value.records.map((item) => (
                    <tr key={item.evidence_id} data-evidence-record={item.evidence_id} aria-selected={item.evidence_id === record}>
                      <th scope="row">{`${when(item.source_time)} (${clockWords(item.clocks.source_time)})`}</th>
                      <td {...REF}>{`${item.device_id} / ${item.signal_id}`}</td>
                      <td>{readingValue(item.normalized)}</td>
                      <td>{item.quality}</td>
                      <td>{when(item.received_at)}</td>
                      <td>
                        <button
                          type="button"
                          onClick={() => change((n) => n.set("record", item.evidence_id))}
                          data-vocabulary-reference={item.evidence_id}
                          aria-label={`Show reading ${item.evidence_id}`}
                        >
                          Show reading
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </DataTable>
              <p>
                {cursor === null ? null : (
                  <button type="button" onClick={() => change((n) => n.delete("cursor"))}>
                    First page
                  </button>
                )}{" "}
                {list.value.next_cursor === null ? null : (
                  <button type="button" onClick={() => change((n) => n.set("cursor", list.value.next_cursor as string))}>
                    Next page
                  </button>
                )}
              </p>
            </>
          )}
        </Panel>
      )}
      {record === null ? null : <RecordView detail={detail} onClose={() => change((n) => n.delete("record"))} />}
    </div>
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
