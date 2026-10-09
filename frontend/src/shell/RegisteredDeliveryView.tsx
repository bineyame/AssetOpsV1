/**
 * Lab Commit/status for a registered run (S2-02 phase 3b, answers-2 item 4).
 *
 * Read from GET commit's `registered_release`: the gateway ledger's delivery
 * (batches, receipts, shared batches) combined by the host with the Lab
 * publication schedule. Three rules hold here:
 *
 * - Stage `STAGED` proves only that the reports admitted so far are sealed. It
 *   never reads as "all published" or "all uploaded"; publication completeness
 *   comes from the schedule's `ordinary_publication`.
 * - "Fully released" is shown only when the server says so AND no blocker is
 *   listed AND the schedule (when there is one) is COMPLETE. A terminal gap or
 *   an unknown schedule is never fully released (`registeredReleaseClaim`).
 * - A batch shared with another run is shown blocked, never released under one
 *   run's authority; a gateway the host cannot read is "unavailable", which is
 *   neither a refusal nor progress.
 */

import { DataTable, Disclosure, Fact, FactList } from "../ui";
import { ORDINARY_PUBLICATION_TEXT } from "./GatewayPublicationPanels";
import type { OrdinaryPublicationState, RegisteredBatch, RegisteredRelease } from "./runSetupClient";

export type RegisteredReleaseClaim = "FULLY_RELEASED" | "NOT_FULLY_RELEASED" | "UNAVAILABLE";

/** The only place a registered run may read as fully released. */
export function registeredReleaseClaim(view: RegisteredRelease): RegisteredReleaseClaim {
  if (view.status !== "AVAILABLE" || view.delivery === null) {
    return "UNAVAILABLE";
  }
  const schedule = view.publication_schedule;
  const published = schedule === null ? view.publication_gap === "NOT_APPLICABLE" : schedule.ordinary_publication === "COMPLETE";
  return view.fully_released === true &&
    view.release_blockers.length === 0 &&
    published &&
    view.delivery.shared_batch_ids.length === 0 &&
    view.delivery.gateway_complete === true
    ? "FULLY_RELEASED"
    : "NOT_FULLY_RELEASED";
}

/** Plain words for each release blocker the host lists; an unknown code is shown as-is. */
export const RELEASE_BLOCKER_TEXT: Record<string, string> = {
  EXECUTION_NOT_COMPLETED: "The run has not finished executing.",
  PUBLICATION_REFUSED: "A publication step was refused during this run.",
  PUBLICATION_GAP:
    "Ordinary publication stopped before the world's last boundary; those reports were never published.",
  PUBLICATION_INSTANT_PASSED:
    "Incomplete for good: the publication clock passed a boundary that was never published.",
  PUBLICATION_GAP_UNKNOWN:
    "Whether every boundary was published is unknown: the publication schedule could not be read.",
  STAGE_SEALING_PENDING: "Some admitted reports are not sealed into a batch yet.",
  STAGE_SEALING_REFUSED: "The gateway refused to seal some admitted reports.",
  STAGE_HELD: "Every report of this run is held at the gateway; none is sealed.",
  STAGE_NOT_STAGED: "The gateway holds no report for this run.",
  BATCH_SHARED_WITH_ANOTHER_RUN:
    "A batch also carries another run's reports, so it is not released under this run's authority.",
  NOT_ALL_BATCHES_RELEASED: "Not every sealed batch has been released to the gateway's uploader.",
  BATCH_REFUSED: "The central server refused at least one batch.",
  RECEIPTS_PENDING: "Not every batch has a durable central receipt yet.",
  GATEWAY_UNAVAILABLE: "The gateway's delivery ledger could not be read.",
};

function blockerText(code: string): string {
  return RELEASE_BLOCKER_TEXT[code] ?? code;
}

function ordinaryText(state: string): string {
  return ORDINARY_PUBLICATION_TEXT[state as OrdinaryPublicationState] ?? state;
}

function batchRelease(batch: RegisteredBatch): string {
  if (batch.shared_with_another_run) {
    return "Blocked: shared with another run";
  }
  return batch.released ? "Released" : "Not released";
}

function decisionsText(decisions: Record<string, number>): string {
  const parts = Object.entries(decisions)
    .filter(([, count]) => count > 0)
    .map(([decision, count]) => `${count} ${decision}`);
  return parts.length === 0 ? "none yet" : parts.join(", ");
}

export function RegisteredDeliveryView({
  view,
  statement,
  pending,
  onRelease,
}: {
  view: RegisteredRelease;
  statement: string | undefined;
  pending: boolean;
  onRelease: () => void;
}) {
  const claim = registeredReleaseClaim(view);
  const delivery = view.delivery;
  const schedule = view.publication_schedule;
  const offerRelease =
    claim === "NOT_FULLY_RELEASED" &&
    view.execution_status === "COMPLETED" &&
    delivery !== null &&
    delivery.released_batch_count < delivery.batch_count - delivery.shared_batch_ids.length;

  return (
    <div data-registered-release={claim}>
      <p data-commit-state={claim}>
        {claim === "FULLY_RELEASED"
          ? "Fully released: every report this run published was admitted, sealed, released and has a durable central receipt."
          : claim === "UNAVAILABLE"
            ? `Release status unavailable: ${view.detail ?? "the gateway's delivery ledger could not be read"}. Nothing is known about release progress; this is not a refusal.`
            : "Not fully released. The reasons are listed below."}
      </p>
      {statement === undefined || claim === "UNAVAILABLE" ? null : <p>{statement}</p>}
      {view.release_blockers.length === 0 ? null : (
        <ul className="cell-list" data-commit-blockers>
          {view.release_blockers.map((code) => (
            <li key={code} data-commit-blocker={code}>
              {blockerText(code)}
            </li>
          ))}
        </ul>
      )}
      <FactList>
        <Fact term="Publication">
          <span data-publication-completeness={schedule === null ? "UNKNOWN" : schedule.ordinary_publication}>
            {schedule === null
              ? view.publication_gap === "NOT_APPLICABLE"
                ? "This run's reports carry the gateway's own clock; there is no virtual publication schedule to complete."
                : `Publication completeness is unknown${view.publication_gap_detail === null ? "" : `: ${view.publication_gap_detail}`}.`
              : `${ordinaryText(schedule.ordinary_publication)} Admitted through ${schedule.admitted_through ?? "nothing yet"}; publication clock at ${schedule.clock_instant ?? "not started"}; world reached ${schedule.world_reached_instant ?? "nothing yet"}${schedule.world_complete ? " (world complete)" : ""}.${schedule.ordinary_stopped_at === null ? "" : ` Ordinary publication stopped at ${schedule.ordinary_stopped_at}.`} Delayed reports: ${schedule.delayed_pending_count} of ${schedule.delayed_report_count} still pending.`}
          </span>
        </Fact>
        {delivery === null ? null : (
          <>
            <Fact term="Stage">
              <span data-stage-status={delivery.stage_status}>
                {`${delivery.stage_status}: ${delivery.envelope_count} admitted reports, ${delivery.unbatched_envelope_count} not yet in a batch, ${delivery.held_report_count} held (held reports are not accepted evidence). A sealed Stage covers only the reports admitted so far; it does not show that every expected report was published or uploaded.`}
              </span>
            </Fact>
            <Fact term="Batches">
              <span data-release-counts>
                {`${delivery.released_batch_count} of ${delivery.batch_count} released; ${delivery.batches_by_state.ACKED ?? 0} with a central receipt, ${delivery.batches_by_state.IN_FLIGHT ?? 0} uploading, ${delivery.batches_by_state.READY ?? 0} waiting to upload, ${delivery.batches_by_state.REFUSED ?? 0} refused.`}
                {delivery.shared_batch_ids.length === 0
                  ? ""
                  : ` ${delivery.shared_batch_ids.length} shared with another run and blocked.`}
              </span>
            </Fact>
            <Fact term="Central decisions">{decisionsText(delivery.decisions)}</Fact>
            {delivery.last_upload_error === null ? null : (
              <Fact term="Last upload error">
                <span data-last-upload-error={delivery.last_upload_error.code}>
                  {`${delivery.last_upload_error.code} on ${delivery.last_upload_error.batch_id} at ${delivery.last_upload_error.at}; the batch keeps its exact bytes and is retried.`}
                </span>
              </Fact>
            )}
          </>
        )}
      </FactList>
      {delivery === null || delivery.refusals.length === 0 ? null : (
        <ul className="cell-list" data-upload-refusals>
          {delivery.refusals.map((r) => (
            <li key={`${r.batch_id}/${r.refused_at}`}>
              {`${r.batch_id}: refused by the central server (${r.http_status ?? "no status"} ${r.code ?? ""}) at ${r.refused_at}${r.detail === null ? "" : `: ${r.detail}`}`}
            </li>
          ))}
        </ul>
      )}
      {delivery === null || delivery.batches.length === 0 ? null : (
        <Disclosure name="registered-batches" summary={`Batches and receipts (${delivery.batches.length})`}>
          <DataTable>
              <thead>
                <tr>
                  <th scope="col">Batch</th>
                  <th scope="col">State</th>
                  <th scope="col">Release</th>
                  <th scope="col">Reports</th>
                  <th scope="col">Receipt (server real UTC)</th>
                  <th scope="col">Decisions</th>
                </tr>
              </thead>
              <tbody>
                {delivery.batches.map((b) => (
                  <tr key={b.batch_id} data-registered-batch={b.batch_id} data-batch-state={b.state} data-batch-shared={b.shared_with_another_run ? "true" : "false"}>
                    <th scope="row">{b.batch_id}</th>
                    <td>{b.last_error_code === null ? b.state : `${b.state} (${b.last_error_code})`}</td>
                    <td>{batchRelease(b)}</td>
                    <td>{b.item_count}</td>
                    <td>
                      {b.receipt === null
                        ? "No receipt yet"
                        : `received ${b.receipt.server_received_at}${b.receipt.server_completed_at === null ? ", in progress" : `, completed ${b.receipt.server_completed_at}`}; receipt ${b.receipt.receipt_sha256.slice(0, 12)}…`}
                    </td>
                    <td>{decisionsText(b.decisions)}</td>
                  </tr>
                ))}
              </tbody>
          </DataTable>
        </Disclosure>
      )}
      {offerRelease ? (
        <p>
          <button type="button" disabled={pending} onClick={onRelease}>
            {delivery !== null && delivery.released_batch_count > 0 ? "Release newly sealed batches" : "Commit and release"}
          </button>
        </p>
      ) : null}
    </div>
  );
}
