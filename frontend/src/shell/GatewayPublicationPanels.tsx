import { useCallback, useEffect, useState } from "react";

import { DataTable, Fact, FactList, Panel } from "../ui";
import {
  isPublicationRefusalKind,
  type AdvancePublicationResult,
  type GatewayDiagnosticsCurrent,
  type GatewayEmittedDiagnostic,
  type GatewayDiagnosticsResult,
  type OrdinaryPublicationState,
  type PublicationRefusalKind,
  type PublicationScheduleReport,
  type RunPublicationResult,
  type RunPublicationSchedule,
  type RunSetupClient,
} from "./runSetupClient";

/**
 * S2-01c: a registered run's delayed-publication schedule and the local
 * gateway's diagnostic read, beside the gateway-ledger Stage.
 *
 * Every instant names the clock it is on, because four different clocks meet
 * here: a reading's own source time, the run's virtual publication clock (the
 * scheduled release and the instant the Lab released it), the gateway's own
 * `published_at` stamp on that virtual clock, and the gateway's real UTC clock
 * for its diagnostics. Nothing here is an upload, a central receipt or Site
 * evidence, and a diagnostic is not device or asset health.
 */

/** Plain words for each clock label the backend sends. */
export const CLOCK_LABEL_TEXT: Record<string, string> = {
  SOURCE_TIME: "source time: the reading's own instant",
  RUN_VIRTUAL_SCHEDULED: "scheduled on the run's virtual publication clock",
  RUN_VIRTUAL: "run's virtual publication clock",
  GATEWAY_STAMPED_RUN_VIRTUAL: "stamped by the gateway on the run's virtual publication clock",
  GATEWAY_REAL_UTC: "gateway's real UTC clock",
};

function clockText(label: string | undefined): string {
  if (label === undefined) {
    return "clock not stated";
  }
  return CLOCK_LABEL_TEXT[label] ?? label;
}

/** Plain words for each of the seven publication refusals. */
export const PUBLICATION_REFUSAL_TEXT: Record<PublicationRefusalKind, string> = {
  PUBLICATION_CLOCK_NOT_SUPPORTED:
    "This run's publication profile does not use a virtual publication clock, so there is nothing to advance.",
  PUBLICATION_CLOCK_BACKWARD: "The publication clock never moves backward.",
  PUBLICATION_AHEAD_OF_WORLD:
    "While the world run is still going, the publication clock cannot pass the instant the world has reached.",
  PUBLICATION_SCHEDULE_UNREADABLE:
    "The stored publication schedule could not be read, so nothing was released.",
  PUBLICATION_SCHEDULE_MISSING:
    "This run executed but its stored publication schedule is missing. Nothing was reconstructed or released.",
  PUBLICATION_INSTANT_INVALID:
    "That is not an instant the clock accepts. Use UTC in the form 2026-09-30T15:10:00Z.",
  PUBLICATION_GAP:
    "Ordinary publication stopped before the world's last boundary, and the stored schedule cannot regenerate those readings. Nothing was moved, admitted or sealed.",
};

/** Plain words for where ordinary publication stands against the world. */
const ORDINARY_PUBLICATION_TEXT: Record<OrdinaryPublicationState, string> = {
  NOT_STARTED: "No world boundary reached yet.",
  CONTIGUOUS: "Published without a gap up to where the world has reached.",
  COMPLETE: "Published without a gap through the world's last boundary.",
  INCOMPLETE: "Incomplete: a reached boundary has not been published.",
  TERMINAL_GAP: "Incomplete for good: the gateway clock passed a boundary that was never published.",
};

/** The gap, in words that cannot read as a fully published run. */
function OrdinaryGap({ schedule }: { schedule: RunPublicationSchedule }) {
  const state = schedule.ordinary_publication;
  if (state !== "INCOMPLETE" && state !== "TERMINAL_GAP") {
    return null;
  }
  const through = schedule.admitted_through ?? "no boundary";
  const reached = schedule.world_reached_instant ?? "an unrecorded instant";
  return (
    <p data-publication-gap={state}>
      <strong>This run is not fully published.</strong>{" "}
      {`Ordinary readings are published through ${through}; the world reached ${reached}.`}{" "}
      {state === "TERMINAL_GAP"
        ? `The gateway clock passed ${schedule.ordinary_stopped_at ?? "a missing boundary"} before it was published, so those readings can no longer be published and no later or delayed report is released past the gap. Start a new run to publish this world in full.`
        : "While the live session runs, stepping or advancing retries the missing boundaries. Without it, no delayed report is released past the gap."}
    </p>
  );
}

const PUBLICATION_CLOCK_TEXT: Record<string, string> = {
  RUN_VIRTUAL: "the run's virtual publication clock",
  GATEWAY_UTC: "the gateway's own real UTC clock",
};

export function publicationClockText(clock: string | null | undefined): string {
  if (clock === null || clock === undefined) {
    return "not stated";
  }
  return PUBLICATION_CLOCK_TEXT[clock] ?? clock;
}

function reportState(report: PublicationScheduleReport, clock: string | null): string {
  if (report.state === "RELEASED") {
    // Submitted is not released evidence: a gateway HELD answer has no
    // envelope and no publication instant (answers-4, C1).
    return report.outcome === "HELD" ? "HELD" : "RELEASED";
  }
  // Canonical UTC instants compare as text.
  return clock !== null && report.scheduled_release_at <= clock ? "DUE" : "PENDING";
}

const REPORT_STATE_TEXT: Record<string, string> = {
  RELEASED: "Released to the local gateway",
  HELD: "Submitted, held by the gateway",
  DUE: "Due, not admitted yet",
  PENDING: "Waiting: not due yet",
};

/** The next instant worth advancing to: the earliest release still waiting. */
function suggestedInstant(schedule: RunPublicationSchedule): string {
  const waiting = schedule.reports
    .filter((report) => report.state === "PENDING")
    .map((report) => report.scheduled_release_at)
    .filter((at) => schedule.clock_instant === null || at > schedule.clock_instant)
    .sort();
  return waiting[0] ?? schedule.clock_instant ?? "";
}

export function PublicationSchedulePanel({
  runId,
  runSetup,
  refreshKey,
  onAdvanced,
}: {
  runId: string;
  runSetup: RunSetupClient;
  /** Re-read whenever this changes, such as after a step re-read the Stage. */
  refreshKey: unknown;
  onAdvanced: () => void;
}) {
  const [read, setRead] = useState<RunPublicationResult | null>(null);
  const [instant, setInstant] = useState("");
  const [touched, setTouched] = useState(false);
  const [pending, setPending] = useState(false);
  const [answer, setAnswer] = useState<AdvancePublicationResult | null>(null);

  useEffect(() => {
    let active = true;
    if (runSetup.getPublication === undefined) {
      setRead({ status: "unavailable", message: null });
      return undefined;
    }
    void runSetup.getPublication(runId).then((loaded) => {
      if (active) {
        setRead(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [runSetup, runId, refreshKey]);

  const schedule = read !== null && read.status === "loaded" ? read.publication : null;
  useEffect(() => {
    if (schedule !== null && !touched) {
      setInstant(suggestedInstant(schedule));
    }
  }, [schedule, touched]);

  const advance = useCallback(async () => {
    if (runSetup.advancePublication === undefined) {
      return;
    }
    setPending(true);
    const result = await runSetup.advancePublication(runId, instant.trim());
    setAnswer(result);
    if (result.status === "loaded") {
      setRead({ status: "loaded", publication: result.publication });
      setTouched(false);
    }
    setPending(false);
    onAdvanced();
  }, [runSetup, runId, instant, onAdvanced]);

  return (
    <Panel heading="Delayed publication" headingId="gateway-publication-heading">
      {read === null ? (
        <p data-publication-loading>Loading the publication schedule.</p>
      ) : read.status === "not_found" ? (
        <p data-publication-status="NOT_FOUND">No publication surface answered for this run.</p>
      ) : read.status === "unavailable" ? (
        <p data-publication-status="UNAVAILABLE">
          <strong>Publication schedule not available.</strong>{" "}
          {read.message ?? "It could not be read, so nothing is known about pending reports."}
        </p>
      ) : (
        <ScheduleBody
          schedule={read.publication}
          canAdvance={runSetup.advancePublication !== undefined}
          instant={instant}
          pending={pending}
          onInstant={(value) => {
            setTouched(true);
            setInstant(value);
          }}
          onAdvance={() => void advance()}
          answer={answer}
        />
      )}
    </Panel>
  );
}

function ScheduleBody({
  schedule,
  canAdvance,
  instant,
  pending,
  onInstant,
  onAdvance,
  answer,
}: {
  schedule: RunPublicationSchedule;
  canAdvance: boolean;
  instant: string;
  pending: boolean;
  onInstant: (value: string) => void;
  onAdvance: () => void;
  answer: AdvancePublicationResult | null;
}) {
  const labels = schedule.clock_labels;
  const clock = schedule.clock_instant;
  const heldCount = schedule.reports.filter((report) => reportState(report, clock) === "HELD").length;
  return (
    <div data-publication data-publication-status={schedule.status}>
      <FactList>
        <Fact term="Publication clock this run froze">
          <span data-publication-clock={schedule.publication_clock ?? ""}>
            {publicationClockText(schedule.publication_clock)}
          </span>
        </Fact>
        {schedule.status !== "AVAILABLE" ? null : (
          <>
            <Fact term={`Publication clock now (${clockText(labels.clock_instant)})`}>
              <span data-publication-clock-instant>{clock ?? "not started"}</span>
            </Fact>
            <Fact term="World run">
              <span data-publication-world={schedule.world_complete ? "COMPLETE" : "RUNNING"}>
                {schedule.world_complete
                  ? `Complete at ${schedule.world_reached_instant ?? "an unrecorded instant"}. The clock may move past the end; no world step runs.`
                  : `Reached ${schedule.world_reached_instant ?? "nothing yet"}. The clock cannot pass this until the run completes.`}
              </span>
            </Fact>
            <Fact term={`Ordinary publication (${clockText(labels.admitted_through)})`}>
              <span
                data-ordinary-publication={schedule.ordinary_publication ?? ""}
                data-ordinary-admitted-through={schedule.admitted_through ?? ""}
              >
                {schedule.ordinary_publication === null
                  ? "not stated"
                  : `${ORDINARY_PUBLICATION_TEXT[schedule.ordinary_publication]} Published through ${schedule.admitted_through ?? "no boundary"}.`}
              </span>
            </Fact>
            <Fact term="Delayed reports">
              <span
                data-publication-pending={schedule.pending_count}
                data-publication-released={schedule.released_count}
              >
                {heldCount === 0
                  ? `${schedule.pending_count} waiting, ${schedule.released_count} released`
                  : `${schedule.pending_count} waiting, ${schedule.released_count - heldCount} released, ${heldCount} held by the gateway`}
              </span>
            </Fact>
          </>
        )}
      </FactList>

      {schedule.status === "NOT_SUPPORTED" ? (
        <p className="note">
          This run publishes on {publicationClockText(schedule.publication_clock)}. It has no
          delayed-publication schedule and no publication clock to advance.
        </p>
      ) : schedule.status === "NO_SCHEDULE" ? (
        <p className="note" data-publication-none>
          No publication schedule is recorded for this run. That is not an empty queue: nothing
          is known about delayed reports until the run executes and records one.
        </p>
      ) : schedule.status === "SCHEDULE_MISSING" ? (
        <p data-publication-missing>
          <strong>This run has executed, but its publication schedule is missing.</strong>{" "}
          {schedule.detail ?? ""} That is lost Lab state, not an empty queue: no report is shown as
          pending or released, and none is reconstructed from the scenario.
        </p>
      ) : schedule.status === "UNREADABLE" ? (
        <p data-publication-unreadable>
          <strong>The stored publication schedule could not be read.</strong>{" "}
          {schedule.detail ?? ""} Nothing is shown as pending or released.
        </p>
      ) : null}

      {schedule.status === "AVAILABLE" ? <OrdinaryGap schedule={schedule} /> : null}

      <p className="note">{schedule.statement}</p>

      {schedule.reports.length === 0 ? null : (
        <DataTable labelledBy="gateway-publication-heading">
          <thead>
            <tr>
              <th scope="col">Device and signal</th>
              <th scope="col">
                Source time <span className="note">{`(${clockText(labels.source_time)})`}</span>
              </th>
              <th scope="col">
                Scheduled release{" "}
                <span className="note">{`(${clockText(labels.scheduled_release_at)})`}</span>
              </th>
              <th scope="col">State</th>
              <th scope="col">
                Released at <span className="note">{`(${clockText(labels.released_at_clock)})`}</span>
              </th>
              <th scope="col">
                Published at <span className="note">{`(${clockText(labels.published_at)})`}</span>
              </th>
              <th scope="col">Gateway sequence</th>
            </tr>
          </thead>
          <tbody>
            {schedule.reports.map((report) => {
              const state = reportState(report, clock);
              return (
                <tr
                  key={report.report_key}
                  data-publication-report={report.report_key}
                  data-publication-report-state={state}
                >
                  <th scope="row">{`${report.device_id} / ${report.signal_id}`}</th>
                  <td data-publication-source-time>{report.source_time}</td>
                  <td data-publication-scheduled>{report.scheduled_release_at}</td>
                  <td>{REPORT_STATE_TEXT[state]}</td>
                  <td data-publication-released-at>{report.released_at_clock ?? "not released"}</td>
                  <td data-publication-published-at>
                    {report.published_at ??
                      (state === "HELD"
                        ? `Held by the gateway${report.outcome === null ? "" : ` (${report.outcome})`}: no envelope and no publication instant`
                        : report.state === "RELEASED"
                          ? "not readable from the gateway"
                          : "no envelope yet")}
                  </td>
                  <td>{report.sequence === null ? "none" : String(report.sequence)}</td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
      )}

      {schedule.status !== "AVAILABLE" || !canAdvance ? null : (
        <p className="control-strip">
          <label htmlFor="publication-advance-instant">
            Advance the publication clock to (UTC, the run's virtual clock)
          </label>{" "}
          <input
            id="publication-advance-instant"
            type="text"
            inputMode="text"
            spellCheck={false}
            value={instant}
            onChange={(event) => onInstant(event.target.value)}
          />{" "}
          <button
            type="button"
            className="action"
            disabled={pending || instant.trim() === ""}
            onClick={onAdvance}
          >
            Advance publication clock
          </button>
        </p>
      )}
      <AdvanceAnswer answer={answer} />
    </div>
  );
}

function AdvanceAnswer({ answer }: { answer: AdvancePublicationResult | null }) {
  if (answer === null) {
    return null;
  }
  if (answer.status === "loaded") {
    return (
      <div data-publication-advanced>
        {answer.publicationRefused === null ? null : (
          <p data-publication-refused-by-gateway>
            <strong>The local gateway did not admit the due reports.</strong>{" "}
            {answer.publicationRefused} The clock moved; those reports stay waiting.
          </p>
        )}
        {answer.releaseBasisStatement === null ? null : (
          <p className="note" data-publication-release-basis={answer.releaseBasis ?? ""}>
            {answer.releaseBasisStatement}
          </p>
        )}
      </div>
    );
  }
  if (answer.status === "refused") {
    const kind = answer.refusalKind;
    return (
      <p data-publication-refusal={kind ?? answer.code ?? "REFUSED"}>
        <strong>Not advanced.</strong>{" "}
        {isPublicationRefusalKind(kind) ? `${PUBLICATION_REFUSAL_TEXT[kind]} ` : null}
        {answer.message}
      </p>
    );
  }
  return (
    <p data-publication-refusal="UNAVAILABLE">
      <strong>Whether the clock moved is not known.</strong>{" "}
      {answer.status === "unavailable" && answer.message !== null
        ? answer.message
        : "The request did not complete; the schedule above is re-read."}
    </p>
  );
}

const PROVENANCE_TEXT: Record<string, string> = {
  MEASURED: "measured by the gateway",
  INJECTED_FAULT_FIXTURE: "injected by a labelled fault fixture, not measured",
  UNMEASURABLE: "the probe failed, so the gateway treats it as STOP",
  OBSERVED_SIMULATED_REPORT: "a simulated public report reached the gateway; not proof a device is alive",
  OBSERVED_DEVICE_REPORT: "a device report reached the gateway",
};

function provenanceText(provenance: string | null): string {
  if (provenance === null) {
    return "no provenance recorded";
  }
  return PROVENANCE_TEXT[provenance] ?? provenance;
}

export function GatewayDiagnosticsPanel({
  runSetup,
  refreshKey,
}: {
  runSetup: RunSetupClient;
  refreshKey: unknown;
}) {
  const [read, setRead] = useState<GatewayDiagnosticsResult | null>(null);
  useEffect(() => {
    let active = true;
    if (runSetup.getGatewayDiagnostics === undefined) {
      setRead({ status: "unavailable", message: null });
      return undefined;
    }
    void runSetup.getGatewayDiagnostics().then((loaded) => {
      if (active) {
        setRead(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [runSetup, refreshKey]);

  return (
    <Panel heading="Gateway diagnostics (local)" headingId="gateway-diagnostics-heading">
      {read === null ? (
        <p data-diagnostics-loading>Loading the gateway diagnostics.</p>
      ) : read.status !== "loaded" ? (
        <p data-diagnostics-status="UNREAD">
          <strong>Gateway diagnostics not available.</strong>{" "}
          {read.status === "unavailable" && read.message !== null
            ? read.message
            : "They could not be read, so no queue, contact or pressure is shown."}
        </p>
      ) : read.gateway.status === "GATEWAY_UNAVAILABLE" ? (
        <div data-diagnostics data-diagnostics-status="GATEWAY_UNAVAILABLE">
          <p>
            <strong>Gateway unavailable.</strong> {read.gateway.detail ?? ""} No queue, contact or
            disk pressure is shown, because none could be read. An unreachable gateway is not an
            empty queue.
          </p>
          <p className="note">{read.gateway.statement}</p>
        </div>
      ) : (
        <DiagnosticsBody
          current={read.gateway.current}
          lastEmitted={read.gateway.last_emitted}
          statement={read.gateway.statement}
          clockLabel={read.gateway.observed_at_clock}
        />
      )}
    </Panel>
  );
}

function DiagnosticsBody({
  current,
  lastEmitted,
  statement,
  clockLabel,
}: {
  current: GatewayDiagnosticsCurrent;
  lastEmitted: GatewayEmittedDiagnostic | null;
  statement: string;
  clockLabel: string;
}) {
  const queue = current.queue;
  const clock = clockText(clockLabel);
  const cadence = current.config.emission_cadence_seconds;
  return (
    <div data-diagnostics data-diagnostics-status="AVAILABLE">
      <p className="note">{statement}</p>
      <FactList>
        <Fact term={`Read at (${clock})`}>
          <span data-diagnostics-observed-at>{current.observed_at ?? "not stated"}</span>
        </Fact>
        <Fact term="Gateway and source mode">
          {`${current.gateway_id ?? "not provisioned"}, ${current.source_mode ?? "unknown"} sources`}
        </Fact>
        <Fact term="Queue">
          <span data-diagnostics-queue={queue.queue_count}>
            {`${queue.queue_count} envelopes waiting for upload: ${queue.sealed_pending_envelopes} sealed in ${queue.sealed_pending_batches} batches, ${queue.unbatched_envelopes} not sealed yet`}
          </span>
        </Fact>
        <Fact term={`Oldest waiting since (${clock})`}>
          {queue.oldest_queued_at === null
            ? "nothing waiting"
            : `${queue.oldest_queued_at}, ${queue.oldest_queue_age_seconds ?? "?"} s ago`}
        </Fact>
        <Fact term="Held, refused to seal, dead letters">
          <span data-diagnostics-held={queue.held_reports}>
            {`${queue.held_reports} held reports (${current.mapping_error_count} mapping errors), ${queue.active_seal_refusals} active seal refusals, ${queue.dead_letter_envelopes} dead letters`}
          </span>
        </Fact>
        <Fact term="Clock offset">
          <span
            data-diagnostics-clock-offset={current.clock_offset.value_ms ?? "UNKNOWN"}
            data-diagnostics-clock-provenance={current.clock_offset.provenance ?? ""}
          >
            {current.clock_offset.value_ms === null
              ? "Unknown: not measured"
              : `${current.clock_offset.value_ms} ms, ${provenanceText(current.clock_offset.provenance)}`}
          </span>
        </Fact>
        <Fact term="Disk pressure">
          <span
            data-diagnostics-disk={current.disk_pressure.level}
            data-diagnostics-disk-provenance={current.disk_pressure.provenance ?? ""}
          >
            {`${current.disk_pressure.level}, ${provenanceText(current.disk_pressure.provenance)}`}
          </span>
        </Fact>
        <Fact term="New reports">
          <span data-diagnostics-acquisition={current.acquisition}>
            {current.acquisition === "ACCEPTING"
              ? "Accepted"
              : "Refused at disk pressure STOP, before any sequence number is used. Stored envelopes and batches are kept."}
          </span>
        </Fact>
        <Fact term="Diagnostic reports stored">
          {`${current.diagnostic_count}, ${current.pending_diagnostic_count} waiting for upload${typeof cadence === "number" ? `; one per ${cadence} s slot at most` : ""}`}
        </Fact>
      </FactList>

      <DataTable labelledBy="gateway-diagnostics-heading">
        <thead>
          <tr>
            <th scope="col">Source</th>
            <th scope="col">
              Last report reached the gateway <span className="note">{`(${clock})`}</span>
            </th>
            <th scope="col">What that means</th>
          </tr>
        </thead>
        <tbody>
          {current.source_contacts.map((contact) => (
            <tr key={contact.source_id} data-diagnostics-contact={contact.source_id}>
              <th scope="row">{contact.source_id}</th>
              <td>{contact.last_contact_at ?? "Unknown: no report observed"}</td>
              <td>
                {contact.last_contact_at === null
                  ? "No contact is known. That is not a healthy source."
                  : provenanceText(contact.provenance)}
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>

      {lastEmitted === null ? (
        <p data-diagnostics-last-emitted="NONE">No diagnostic report has been stored yet.</p>
      ) : (
        <p data-diagnostics-last-emitted={lastEmitted.diagnostic_sequence}>
          {`Last stored diagnostic: sequence ${lastEmitted.diagnostic_sequence} in epoch ${lastEmitted.sequence_epoch}, observed ${lastEmitted.observed_at} (${clock}), ${lastEmitted.state}, SHA-256 ${lastEmitted.sha256}. It waits for upload; no central receipt exists.`}
        </p>
      )}
    </div>
  );
}
