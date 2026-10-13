import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, DataTable, Panel } from "../ui";
import { siteEvidenceHref } from "./operatorSiteRoutes";
import type {
  RunCommitResult,
  RunExecution,
  RunExecutionResult,
  RunStageResult,
  RunSummary,
} from "./runSetupClient";
import "./runIngestion.css";

/**
 * V-01b b2: the Lab run page's "Gateway & Ingestion" overview (mock v69 `lab`).
 *
 * Built only from the reads the run page already makes - the persisted run,
 * the execution projection, the Stage and the Commit read - and nothing else.
 * Delivery and central receipt come from the Commit read alone (V-01b Q1: the
 * Stage's own upload line is the gateway's local statement). A read that is
 * loading or absent is said so in its box or panel; a fact these reads do not
 * carry is a visible "Not available yet" statement, never a mock value.
 */
export interface RunIngestionOverviewProps {
  run: RunSummary;
  execution: RunExecutionResult | null;
  stage: RunStageResult | null;
  commit: RunCommitResult | null;
  /** The actionable Commit and release panel, kept right under Release and ingestion. */
  commitPanel: ReactNode;
}

const LOADING_EXECUTION = "Loading the execution of the persisted run.";
const LOADING_STAGE = "Loading the staged source envelopes.";
const LOADING_COMMIT = "Loading the commit status.";
const COMMIT_UNREADABLE = "The commit status could not be read, so what was received centrally is not known.";
const DELIVERY_UNREADABLE = "The gateway delivery could not be read, so what was received centrally is not known.";
const RECEIVED_EXECUTION_UNREADABLE = "Reports were received centrally, but the run's execution could not be read, so no Site Evidence link is offered.";
const NOTHING_RECEIVED = "Nothing from this run has been received centrally.";

interface Delivery {
  batches: number;
  released: number;
  withReceipt: number;
  decisions: Record<string, number>;
}

/** The registered delivery the Commit read carries, or null when it carries none. */
function registeredDelivery(commit: RunCommitResult | null): Delivery | null {
  if (commit === null || commit.status !== "loaded") {
    return null;
  }
  const delivery = commit.commit.registered_release?.delivery ?? null;
  if (delivery === null) {
    return null;
  }
  return {
    batches: delivery.batch_count,
    released: delivery.released_batch_count,
    withReceipt: delivery.batches.filter((b) => b.receipt !== null).length,
    decisions: delivery.decisions,
  };
}

function commitLabel(commit: RunCommitResult | null): string {
  if (commit === null) {
    return "Commit status loading";
  }
  if (commit.status !== "loaded") {
    return "Commit status unavailable";
  }
  const state = commit.commit.commit;
  if (state === "NOT_COMMITTED") {
    return "Not committed";
  }
  if (state === "RELEASED_TO_GATEWAY") {
    return "Released to gateway";
  }
  return "Committed";
}

function plainStatus(status: string): string {
  return status.toLowerCase().replace(/_/g, " ");
}

function count(decisions: Record<string, number>, key: string): number {
  return decisions[key] ?? 0;
}

function decisionLine(d: Record<string, number>): string {
  return `${count(d, "ACCEPTED")} accepted, ${count(d, "DUPLICATE")} duplicate, ${count(d, "CONFLICT")} conflict, ${count(d, "REJECTED")} rejected`;
}

function receiptLine(delivery: Delivery): string {
  return `${delivery.withReceipt} of ${delivery.batches} batches have a central receipt`;
}

function evidenceHref(siteId: string, projection: RunExecution, analysis: boolean): string {
  const params = new URLSearchParams();
  if (analysis) {
    params.set("view", "analysis");
  }
  params.set("from", projection.interval_start_time);
  params.set("to", projection.interval_end_time);
  return `${siteEvidenceHref(siteId)}?${params.toString()}`;
}

export function RunIngestionOverview({
  run,
  execution,
  stage,
  commit,
  commitPanel,
}: RunIngestionOverviewProps) {
  const projection = execution !== null && execution.status === "loaded" ? execution.execution : null;
  const delivery = registeredDelivery(commit);
  // Site Evidence is offered only for a registered Site (the Commit read
  // carries a registered release) with at least one central receipt, and only
  // for the interval the execution names.
  const received = delivery !== null && delivery.withReceipt > 0;
  const evidence = received && projection !== null;

  return (
    <section
      className="run-ingestion"
      aria-labelledby="run-ingestion-heading"
      data-run-ingestion
    >
      <h2 id="run-ingestion-heading" className="run-ingestion__heading">
        Gateway &amp; Ingestion
      </h2>

      <div className="status-strip" data-ingestion-status>
        <div className="status-strip__row">
          <Badge tone="lifecycle">{commitLabel(commit)}</Badge>
          <Badge tone="neutral">
            {projection !== null
              ? `Execution ${plainStatus(projection.status)}`
              : execution === null
                ? "Execution loading"
                : "Execution unavailable"}
          </Badge>
          <DeliveryFact commit={commit} delivery={delivery} />
          <p className="run-ingestion__muted" data-ingestion-frozen>
            {frozenLine(run, projection)}
          </p>
          <p className="status-strip__action">
            {evidence ? (
              <Link to={evidenceHref(run.site_id, projection, false)} data-ingestion-evidence-link>
                Open Site Evidence →
              </Link>
            ) : (
              <span data-ingestion-received="none">{receivedStatement(commit, delivery, execution)}</span>
            )}
          </p>
        </div>
      </div>

      <FlowStrip execution={execution} projection={projection} stage={stage} commit={commit} delivery={delivery} />

      <div className="panel-pair">
        <Panel
          heading="Selected canonical envelope"
          headingId="run-ingestion-envelope-heading"
          description="Exactly the source boundary; no private-truth field"
        >
          <div data-ingestion-panel="envelope">
            <EnvelopeBlock stage={stage} />
            <p className="run-ingestion__note">
              Compact field projection of one stored envelope, the earliest by source time. received_at is
              assigned by ingestion, never the gateway. Every envelope is under Advanced details — Stage and
              staged envelopes, below.
            </p>
          </div>
        </Panel>
        <Panel
          heading="Truth versus observed"
          headingId="run-ingestion-truth-heading"
          description="Latest step on the execution clock; private truth stays in the Lab"
        >
          <div data-ingestion-panel="truth">
            <TruthTable execution={execution} projection={projection} />
            <p className="run-ingestion__note" data-ingestion-missing="product-consequence">
              Not available yet: the product consequence of each report (accepted, latency retained or
              indeterminate). These reads give central decisions per batch, not per device report.
            </p>
          </div>
        </Panel>
      </div>

      <div className="panel-pair">
        <div className="run-ingestion__column">
          <Panel
            heading="Release and ingestion"
            headingId="run-ingestion-release-heading"
            description="From the Commit read: what was released and what ingestion decided"
          >
            <ReleaseFacts commit={commit} delivery={delivery} />
            {evidence ? (
              <p className="run-ingestion__note">
                <Link to={evidenceHref(run.site_id, projection, true)} data-ingestion-inspect>
                  Inspect accepted records
                </Link>
              </p>
            ) : null}
          </Panel>
          {commitPanel}
        </div>
        <Panel heading="What never crosses" headingId="run-ingestion-boundary-heading">
          <div className="prose" data-ingestion-panel="boundary">
            <p>
              Private simulator truth - the world&apos;s true state, the scenario that drove it and each
              simulated device&apos;s error - stays in this workspace and never enters ingestion. Only the
              source envelopes the gateway publishes cross, and only what ingestion accepts reaches a Site.
            </p>
            <p>
              <strong>The gateway observes, maps and publishes.</strong> Normal ingestion and analysis
              decide acceptance and conclusions.
            </p>
            <p className="run-ingestion__note" data-ingestion-missing="dispatch-link">
              Not available yet: a link from this run&apos;s accepted records to the Dispatch analysis that
              used them. No run-to-analysis read exists here.
            </p>
          </div>
        </Panel>
      </div>
    </section>
  );
}

function receivedStatement(
  commit: RunCommitResult | null,
  delivery: Delivery | null,
  execution: RunIngestionOverviewProps["execution"],
): string {
  if (
    delivery === null &&
    commit !== null &&
    commit.status === "loaded" &&
    typeof commit.commit.commit === "object"
  ) {
    return "Not a registered Site: no Site Evidence link. The release is under Release and ingestion.";
  }
  if (commit === null) {
    return LOADING_COMMIT;
  }
  if (commit.status !== "loaded") {
    return COMMIT_UNREADABLE;
  }
  if (delivery !== null) {
    if (delivery.withReceipt === 0) {
      return NOTHING_RECEIVED;
    }
    return execution === null ? LOADING_EXECUTION : RECEIVED_EXECUTION_UNREADABLE;
  }
  if (commit.commit.commit === "NOT_COMMITTED") {
    return NOTHING_RECEIVED;
  }
  return DELIVERY_UNREADABLE;
}

function frozenLine(run: RunSummary, projection: RunExecution | null): string {
  const scenario = `scenario ${run.scenario_id} v${run.scenario_version}`;
  if (projection === null) {
    return `Frozen inputs · ${scenario}`;
  }
  return `Frozen inputs · model ${projection.model_profile_id} v${projection.model_profile_version} · publication ${projection.publication_profile_id} v${projection.publication_profile_version} · ${scenario}`;
}

function DeliveryFact({ commit, delivery }: { commit: RunCommitResult | null; delivery: Delivery | null }) {
  if (delivery !== null) {
    return <p data-ingestion-delivery>{receiptLine(delivery)}</p>;
  }
  if (commit !== null && commit.status === "loaded" && commit.commit.release !== null) {
    const r = commit.commit.release;
    return <p data-ingestion-delivery>{`Ingestion processed ${r.processed} of ${r.total} envelopes`}</p>;
  }
  return null;
}

function FlowBox({
  name,
  title,
  tone,
  children,
}: {
  name: string;
  title: string;
  tone?: "private" | "public";
  children: ReactNode;
}) {
  return (
    <li
      className={`run-ingestion__flow-box${tone === undefined ? "" : ` ${tone}`}`}
      data-flow-box={name}
    >
      <strong>{title}</strong>
      {children}
    </li>
  );
}

function Arrow() {
  return (
    <li className="run-ingestion__flow-arrow" aria-hidden="true">
      →
    </li>
  );
}

function FlowStrip({
  execution,
  projection,
  stage,
  commit,
  delivery,
}: {
  execution: RunExecutionResult | null;
  projection: RunExecution | null;
  stage: RunStageResult | null;
  commit: RunCommitResult | null;
  delivery: Delivery | null;
}) {
  const executionAbsent = execution === null ? LOADING_EXECUTION : "Execution not available.";
  const stageAbsent = stage === null ? LOADING_STAGE : "Stage not available.";
  return (
    <ol className="run-ingestion__flow" aria-label="From private world to accepted evidence">
      <FlowBox name="world" title="1 · Private world (Lab only)" tone="private">
        {projection === null ? (
          <p>{executionAbsent}</p>
        ) : (
          <>
            <p>{`${projection.boundaries_completed} of ${projection.boundaries_total} steps simulated`}</p>
            <p>{`Execution ${plainStatus(projection.status)}`}</p>
          </>
        )}
      </FlowBox>
      <Arrow />
      <FlowBox name="reports" title="2 · Device reports" tone="private">
        {projection === null ? (
          <p>{executionAbsent}</p>
        ) : (
          <p>{`${projection.reported_count} reports published, ${projection.dropped_count} dropped`}</p>
        )}
        {stage !== null && stage.status === "gateway" ? (
          <p>{`${stage.stage.envelopes.length} admitted by the gateway, ${stage.stage.holds.length} held`}</p>
        ) : null}
      </FlowBox>
      <Arrow />
      <FlowBox name="envelopes" title="3 · SourceEnvelope">
        {stage === null || (stage.status !== "gateway" && stage.status !== "loaded") ? (
          <p>{stageAbsent}</p>
        ) : stage.status === "gateway" ? (
          <p>
            {`${stage.stage.envelopes.filter((e) => e.batch_id !== null).length} of ${stage.stage.envelopes.length} envelopes in ${stage.stage.batches.length} sealed ${stage.stage.batches.length === 1 ? "batch" : "batches"}`}
          </p>
        ) : (
          <>
            <p>{`${stage.stage.envelopes.length} envelopes staged`}</p>
            {stage.stage.mapping === null ? null : (
              <p>{`Mapping v${stage.stage.mapping.mapping_version} · schema ${stage.stage.envelope_schema_version}`}</p>
            )}
          </>
        )}
      </FlowBox>
      <Arrow />
      <FlowBox name="accepted" title="4 · Accepted evidence" tone="public">
        <AcceptedFacts commit={commit} delivery={delivery} />
      </FlowBox>
    </ol>
  );
}

function AcceptedFacts({ commit, delivery }: { commit: RunCommitResult | null; delivery: Delivery | null }) {
  if (commit === null) {
    return <p>{LOADING_COMMIT}</p>;
  }
  if (commit.status !== "loaded") {
    return <p>Commit status not available.</p>;
  }
  if (delivery !== null) {
    return (
      <>
        <p>{decisionLine(delivery.decisions)}</p>
        <p>{receiptLine(delivery)}</p>
      </>
    );
  }
  const read = commit.commit;
  if (read.commit === "NOT_COMMITTED") {
    return <p>Not committed: nothing released, nothing accepted centrally.</p>;
  }
  if (read.release !== null) {
    const r = read.release;
    return (
      <p>
        {`${r.accepted} accepted, ${r.duplicates} duplicate, ${r.conflicts} conflict, ${r.rejected} rejected`}
      </p>
    );
  }
  return <p>The Commit read carried no delivery status.</p>;
}

/** One stored envelope's canonical fields, in the mock's compact order. */
function compactLines(canonical: string): string | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(canonical);
  } catch {
    return null;
  }
  if (typeof parsed !== "object" || parsed === null) {
    return null;
  }
  const doc = parsed as Record<string, Record<string, unknown> | undefined>;
  const pick = (section: string, key: string): unknown => doc[section]?.[key];
  const lines: [string, unknown][] = [
    ["device_id", pick("source", "device_id")],
    ["signal_id", pick("source", "signal_id")],
    ["site_id", pick("source", "site_id")],
    ["source_time", pick("timing", "source_time")],
    ["published_at", pick("timing", "published_at")],
    ["family", pick("payload", "family")],
    ["measurement", pick("payload", "measurement")],
    ["value", pick("payload", "value")],
    ["unit", pick("payload", "unit")],
    ["quality", pick("payload", "quality")],
  ];
  const out = lines
    .filter(([, v]) => v !== undefined)
    .map(([k, v]) => `${k}: ${k === "value" || k === "unit" ? JSON.stringify(v) : String(v)}`);
  const mapping = doc.mapping;
  if (mapping !== undefined && mapping.binding_set_id !== undefined) {
    out.push(`mapping: ${String(mapping.binding_set_id)} / v${String(mapping.version)}`);
  }
  return out.length === 0 ? null : out.join("\n");
}

function EnvelopeBlock({ stage }: { stage: RunStageResult | null }) {
  if (stage === null) {
    return <p>{LOADING_STAGE}</p>;
  }
  if (stage.status !== "gateway" && stage.status !== "loaded") {
    return <p>Stage not available, so no stored envelope can be shown.</p>;
  }
  const envelopes: { id: string; time: string; canonical: string; sequence: number }[] =
    stage.status === "gateway"
      ? stage.stage.envelopes.map((e) => ({ id: e.message_id, time: e.source_time, canonical: e.canonical, sequence: e.sequence }))
      : stage.stage.envelopes.map((e) => ({ id: e.message_id, time: e.source_time, canonical: e.canonical, sequence: e.sequence }));
  if (envelopes.length === 0) {
    return <p>No envelope is stored for this run yet.</p>;
  }
  const first = [...envelopes].sort((a, b) =>
    a.time === b.time ? a.sequence - b.sequence : a.time < b.time ? -1 : 1,
  )[0];
  return (
    <pre className="run-ingestion__code" data-ingestion-envelope={first.id}>
      {compactLines(first.canonical) ?? first.canonical}
    </pre>
  );
}

function shown(value: string | null, unit: string): string {
  if (value === null) {
    return "not measured here";
  }
  return unit === "state" ? value : `${value} ${unit}`;
}

function TruthTable({
  execution,
  projection,
}: {
  execution: RunExecutionResult | null;
  projection: RunExecution | null;
}) {
  if (projection === null) {
    return <p>{execution === null ? LOADING_EXECUTION : "Execution not available, so nothing is compared."}</p>;
  }
  // One row per declared signal, reserved before the first step, so the
  // table never grows with the run (T025e AC9: nothing above the cockpit grows).
  return (
    <DataTable labelledBy="run-ingestion-truth-heading">
      <thead>
        <tr>
          <th scope="col">At / signal</th>
          <th scope="col">Private truth</th>
          <th scope="col">Observed</th>
        </tr>
      </thead>
      <tbody>
        {projection.signals.map((signal) => {
          const row = projection.observations.find(
            (o) => o.device_id === signal.device_id && o.signal_id === signal.signal_id,
          );
          const key = `${signal.device_id}:${signal.signal_id}`;
          return (
            <tr key={key} data-truth-row={key}>
              <th scope="row">
                {row === undefined
                  ? `No step yet · ${signal.device_id} / ${signal.signal_id}`
                  : `${row.simulation_time.slice(11, 16)} · ${signal.device_id} / ${signal.signal_id}`}
              </th>
              <td data-truth-private>{row === undefined ? "No step yet" : shown(row.true_value, row.canonical_unit)}</td>
              <td data-truth-observed>
                {row === undefined
                  ? "No step yet"
                  : row.reported_value === null
                    ? `No report (${plainStatus(row.outcome ?? (row.due ? "due" : "not due"))})`
                    : shown(row.reported_value, row.canonical_unit)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </DataTable>
  );
}

function ReleaseFacts({ commit, delivery }: { commit: RunCommitResult | null; delivery: Delivery | null }) {
  if (commit === null) {
    return <p>{LOADING_COMMIT}</p>;
  }
  if (commit.status !== "loaded") {
    return <p>The Commit status could not be read, so nothing is known about release or ingestion.</p>;
  }
  const read = commit.commit;
  const rows: [string, string][] = [["Commit", commitLabel(commit)]];
  if (delivery !== null) {
    rows.push(
      ["Batches", `${delivery.batches} sealed, ${delivery.released} released`],
      ["Central receipts", `${delivery.withReceipt} of ${delivery.batches} batches`],
      ["Accepted", String(count(delivery.decisions, "ACCEPTED"))],
      ["Duplicates", String(count(delivery.decisions, "DUPLICATE"))],
      ["Conflicts", String(count(delivery.decisions, "CONFLICT"))],
      ["Rejected", String(count(delivery.decisions, "REJECTED"))],
    );
  } else if (read.registered_release !== undefined) {
    rows.push([
      "Gateway delivery",
      read.registered_release.detail ?? `Not readable (${plainStatus(read.registered_release.status)})`,
    ]);
  } else if (typeof read.commit === "object") {
    rows.push(["Sealed envelopes", String(read.commit.envelope_count)]);
    if (read.release !== null) {
      const r = read.release;
      rows.push(
        ["Ingestion", `${plainStatus(r.status)}: ${r.processed} of ${r.total} processed`],
        ["Accepted", String(r.accepted)],
        ["Duplicates", String(r.duplicates)],
        ["Conflicts", String(r.conflicts)],
        ["Rejected", String(r.rejected)],
      );
    }
  }
  return (
    <>
      <dl className="run-ingestion__kv" data-ingestion-release>
        {rows.map(([term, value]) => (
          <div key={term}>
            <dt>{term}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {read.commit === "NOT_COMMITTED" ? (
        <p className="run-ingestion__note">Nothing has been sealed for release or received centrally.</p>
      ) : null}
    </>
  );
}
