import { useState } from "react";

import { DataTable, Fact, FactList, Panel } from "../ui";
import type { GatewayLedgerStage, RunStageFrozenBasis } from "./runSetupClient";

/**
 * S2-01b: a registered run's Stage, as the separate gateway process's durable
 * ledger holds it.
 *
 * Everything shown is read back from the gateway: the snapshot hash it
 * activated, the sequence epoch, every sealed SourceEnvelope V3 and Batch V2
 * with its stored SHA-256 and exact text, the queue state, and the reports it
 * held instead of sequencing. Upload is pending and there is no receipt in
 * this build, so nothing here says a batch was sent, accepted or delivered.
 */
export function GatewayLedgerView({
  stage,
  frozenBasis,
}: {
  stage: GatewayLedgerStage;
  frozenBasis: RunStageFrozenBasis | null | undefined;
}) {
  const [selectedEnvelope, setSelectedEnvelope] = useState<string | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<string | null>(null);
  const depth = Object.entries(stage.queue_depth_by_state);
  const envelope =
    stage.envelopes.find((item) => item.message_id === selectedEnvelope) ??
    stage.envelopes[0];
  const batch =
    stage.batches.find((item) => item.batch_id === selectedBatch) ?? stage.batches[0];

  return (
    <div data-gateway-ledger data-gateway-status={stage.status}>
      <p
        data-stage-statement
        data-stage-status={stage.status}
        data-stage-count={stage.envelopes.length}
        data-stage-execution={stage.execution_status}
      >
        {stage.statement}
      </p>
      {frozenBasis ? (
        <p
          data-stage-basis={frozenBasis.configuration_store}
          data-stage-can-release={String(frozenBasis.can_release)}
        >
          <strong>Registered configuration.</strong> {frozenBasis.statement}
        </p>
      ) : null}
      {stage.unavailable_detail === null ? null : (
        <p data-gateway-unavailable>
          <strong>Gateway not reachable.</strong> {stage.unavailable_detail}
        </p>
      )}
      {stage.publication_notes.length === 0 ? null : (
        <ul className="cell-list" data-gateway-notes>
          {stage.publication_notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      )}
      <FactList>
        <Fact term="Where this Stage is read from">
          Gateway ledger: the local outbox of the separate gateway process
        </Fact>
        <Fact term="Upload">
          <span data-gateway-upload={stage.upload_state}>
            {`${stage.upload_state}. ${stage.upload_statement}`}
          </span>
        </Fact>
        <Fact term="Receipts">
          <span data-gateway-receipts={stage.receipts.length}>None</span>
        </Fact>
        <Fact term="Snapshot SHA-256">
          <code data-gateway-snapshot>{stage.snapshot_sha256}</code>
        </Fact>
        <Fact term="Site and gateway">
          {`${stage.site_id ?? "not provisioned"} / ${stage.gateway_id ?? "not provisioned"}`}
        </Fact>
        <Fact term="Sequence epoch">
          <span data-gateway-epoch>{stage.sequence_epoch ?? "none"}</span>
        </Fact>
        <Fact term="Queue">
          <span data-gateway-queue>
            {depth.length === 0
              ? "empty"
              : depth.map(([state, count]) => `${count} ${state}`).join(", ")}
          </span>
        </Fact>
        <Fact term="Envelopes, batches and holds">
          {`${stage.envelopes.length} envelopes in ${stage.batches.length} batches; ${stage.holds.length} held reports`}
        </Fact>
      </FactList>

      {stage.batches.length === 0 ? null : (
        <Panel heading="Sealed batches" headingId="gateway-batches-heading" flush>
          <DataTable labelledBy="gateway-batches-heading">
            <thead>
              <tr>
                <th scope="col">Batch</th>
                <th scope="col">Source</th>
                <th scope="col">Envelopes</th>
                <th scope="col">State</th>
                <th scope="col">Attempts</th>
                <th scope="col">SHA-256</th>
                <th scope="col">Bytes</th>
              </tr>
            </thead>
            <tbody>
              {stage.batches.map((item, index) => (
                <tr key={item.batch_id} data-gateway-batch={item.batch_id}>
                  <th scope="row">{item.batch_id}</th>
                  <td>{item.source_id}</td>
                  <td>{String(item.message_ids.length)}</td>
                  <td data-gateway-batch-state>{item.state}</td>
                  <td>{String(item.attempt_count)}</td>
                  <td>
                    <code data-gateway-batch-sha256>{item.sha256}</code>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="action"
                      aria-pressed={batch !== undefined && item.batch_id === batch.batch_id}
                      onClick={() => setSelectedBatch(item.batch_id)}
                    >
                      {`Show batch ${index + 1}`}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      )}
      {batch === undefined ? null : (
        <Panel heading="The selected batch, exactly as sealed" headingId="gateway-batch-heading">
          <p>{`${batch.batch_id}, SHA-256 ${batch.sha256}, ${batch.canonical.length} characters.`}</p>
          <pre className="canonical-text" data-gateway-batch-canonical={batch.batch_id}>
            {batch.canonical}
          </pre>
        </Panel>
      )}

      {stage.seal_refusals.length === 0 ? null : (
        <Panel heading="Sealing refused" headingId="gateway-seal-refusals-heading" flush>
          <p className="note">
            The gateway admitted these reports but could not seal them into a
            batch. They stay unbatched in its local outbox; nothing was sent.
          </p>
          <DataTable labelledBy="gateway-seal-refusals-heading">
            <thead>
              <tr>
                <th scope="col">Refusal</th>
                <th scope="col">Source and epoch</th>
                <th scope="col">Outbox group</th>
                <th scope="col">First unsealed envelope</th>
                <th scope="col">Field</th>
                <th scope="col">Reason</th>
                <th scope="col">Seen</th>
              </tr>
            </thead>
            <tbody>
              {stage.seal_refusals.map((refusal) => (
                <tr
                  key={`${refusal.source_id}/${refusal.sequence_epoch}/${refusal.outbox_state ?? ""}/${refusal.message_id}`}
                  data-gateway-seal-refusal={refusal.kind}
                >
                  <th scope="row">{refusal.kind}</th>
                  <td>{`${refusal.source_id}, epoch ${refusal.sequence_epoch}`}</td>
                  <td data-gateway-seal-refusal-state={refusal.outbox_state ?? ""}>
                    {refusal.outbox_state ?? "not reported"}
                  </td>
                  <td>{refusal.message_id}</td>
                  <td>{refusal.field}</td>
                  <td>{refusal.detail}</td>
                  <td>{String(refusal.seen_count)}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      )}

      {stage.holds.length === 0 ? null : (
        <Panel heading="Held reports" headingId="gateway-holds-heading" flush>
          <p className="note">
            The gateway held these reports instead of sequencing them. A held
            report has no envelope and used no sequence number.
          </p>
          <DataTable labelledBy="gateway-holds-heading">
            <thead>
              <tr>
                <th scope="col">Hold</th>
                <th scope="col">Device and signal</th>
                <th scope="col">Source time</th>
                <th scope="col">Field</th>
                <th scope="col">Reason</th>
                <th scope="col">Seen</th>
              </tr>
            </thead>
            <tbody>
              {stage.holds.map((hold) => (
                <tr key={hold.hold_id} data-gateway-hold={hold.kind}>
                  <th scope="row">{hold.kind}</th>
                  <td>{`${hold.device_id ?? "unknown"} / ${hold.signal_id ?? "unknown"}`}</td>
                  <td>{hold.source_time ?? "unknown"}</td>
                  <td data-gateway-hold-field>{hold.field}</td>
                  <td>{hold.detail}</td>
                  <td>{String(hold.seen_count)}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      )}

      {envelope === undefined ? null : (
        <Panel heading="The selected envelope, exactly as stored" headingId="gateway-envelope-heading">
          <FactList>
            <Fact term="Message ID">{envelope.message_id}</Fact>
            <Fact term="Source and sequence">
              {`${envelope.source_id}, epoch ${envelope.sequence_epoch}, sequence ${envelope.sequence}`}
            </Fact>
            <Fact term="Batch and position">
              {envelope.batch_id === null
                ? "not sealed into a batch yet"
                : `${envelope.batch_id}, item ${envelope.ordinal ?? "?"}`}
            </Fact>
            <Fact term="SHA-256">
              <code>{envelope.sha256}</code>
            </Fact>
          </FactList>
          <pre className="canonical-text" data-gateway-envelope-canonical={envelope.message_id}>
            {envelope.canonical}
          </pre>
        </Panel>
      )}
      {stage.envelopes.length === 0 ? null : (
        <Panel heading="Every envelope in the outbox" headingId="gateway-envelopes-heading" flush>
          <DataTable labelledBy="gateway-envelopes-heading">
            <thead>
              <tr>
                <th scope="col">Sequence</th>
                <th scope="col">Source</th>
                <th scope="col">Source time</th>
                <th scope="col">State</th>
                <th scope="col">Batch item</th>
                <th scope="col">SHA-256</th>
                <th scope="col">Exact envelope</th>
              </tr>
            </thead>
            <tbody>
              {stage.envelopes.map((item, index) => (
                <tr key={item.message_id} data-gateway-envelope={item.message_id}>
                  <th scope="row">{String(item.sequence)}</th>
                  <td>{item.source_id}</td>
                  <td>{item.source_time}</td>
                  <td data-gateway-envelope-state>{item.state}</td>
                  <td>{item.ordinal === null ? "none" : String(item.ordinal)}</td>
                  <td>
                    <code>{item.sha256.slice(0, 12)}…</code>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="action"
                      aria-pressed={item.message_id === envelope?.message_id}
                      onClick={() => setSelectedEnvelope(item.message_id)}
                    >
                      {`Show envelope ${index + 1}`}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      )}
    </div>
  );
}
