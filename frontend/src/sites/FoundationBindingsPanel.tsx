/**
 * Configuration Readiness, the signal binding set in effect and the gateway
 * snapshot for a stored Site (S1-02).
 *
 * Substrate leaf, rendered inside the persisted Foundation panel. Everything
 * here is configuration. "Ready to report" means the configuration names a
 * bound channel for every required role; it never says a device is
 * connected, reporting or healthy. A role with no channel is "Not bound", and
 * no binding set at all is "Unknown".
 */

import { useState, type FormEvent } from "react";

import { Badge, DataTable, Fact, FactList, Panel } from "../ui";
import type {
  BindingPublishOutcome,
  ConfigurationReadiness,
  FoundationReadModel,
  ReadinessRole,
  SignalBinding,
} from "./siteFoundationClient";
import { formatInstant, utcInstantFromLocal } from "./FoundationRevisionPanel";

export const FOUNDATION_READINESS_HEADING_ID = "foundation-readiness-heading";
export const FOUNDATION_BINDINGS_HEADING_ID = "foundation-bindings-heading";

const READINESS_WORD: Record<ConfigurationReadiness["state"], string> = {
  READY_TO_REPORT: "Ready to report",
  INCOMPLETE: "Incomplete",
  UNKNOWN: "Unknown",
};

const ROLE_STATUS_WORD: Record<ReadinessRole["status"], string> = {
  CONFIGURED: "Configured",
  UNBOUND: "Not bound",
  NOT_CONFIGURED: "Not configured",
};

function conversionText(binding: SignalBinding): string {
  const { kind } = binding.conversion;
  if (kind === "IDENTITY") return "Same unit";
  if (kind === "LINEAR") {
    const { scale, offset } = binding.conversion.parameters as { scale?: string; offset?: string };
    return `× ${scale ?? "?"} + ${offset ?? "?"}`;
  }
  return "State labels mapped";
}

function roleCoverage(role: ReadinessRole, mappings: SignalBinding[]): string {
  if (role.covered_by === "FOUNDATION_CONTROL") return role.detail ?? "Foundation control";
  if (role.subjects.length === 0) return "No channel is bound to this role.";
  const byId = new Map(mappings.map((m) => [m.binding_revision_id, m]));
  return role.subjects
    .map((subject) => {
      if (subject.status === "UNBOUND") return `${subject.asset_code ?? "Unknown"}: not bound`;
      const channel = subject.binding_revision_ids
        .map((id) => byId.get(id))
        .filter((m): m is SignalBinding => m !== undefined)
        .map((m) => `${m.device_id} / ${m.signal_id}`)
        .join(", ");
      return `${subject.asset_code ?? "Unknown"}: ${channel}`;
    })
    .join("; ");
}

export interface FoundationBindingsPanelProps {
  foundation: FoundationReadModel;
  /** Where the snapshot for the instant shown downloads from. */
  snapshotHref: string;
  onPublishBindings: (validFrom: string, bindings: SignalBinding[], note: string) => Promise<BindingPublishOutcome>;
}

export function FoundationBindingsPanel({
  foundation,
  snapshotHref,
  onPublishBindings,
}: FoundationBindingsPanelProps) {
  const { readiness, bindings, acquisition_snapshot: snapshot } = foundation;
  const unbound = readiness.channels.filter((channel) => channel.status !== "BOUND");

  return (
    <>
      <Panel heading="Configuration readiness" headingId={FOUNDATION_READINESS_HEADING_ID}>
        <p data-readiness-state={readiness.state}>
          <Badge tone="neutral">{READINESS_WORD[readiness.state]}</Badge>{" "}
          {readiness.state === "READY_TO_REPORT"
            ? "Every required role has a configured channel or control."
            : `Not bound: ${readiness.missing_roles.join(", ")}.`}
        </p>
        <p>{readiness.statement}</p>
        <DataTable labelledBy={FOUNDATION_READINESS_HEADING_ID}>
          <caption>
            Roles the analysis of this Site needs, and what in this configuration covers each one.
            Configuration only; claim readiness is on Evidence.
          </caption>
          <thead>
            <tr>
              <th scope="col">Role</th>
              <th scope="col">Required</th>
              <th scope="col">Configuration</th>
              <th scope="col">Covered by</th>
            </tr>
          </thead>
          <tbody>
            {readiness.roles.map((role) => (
              <tr key={role.role} data-readiness-role={role.role}>
                <th scope="row">{role.label}</th>
                <td>{role.required ? "Required" : "Optional"}</td>
                <td data-readiness-status={role.status}>{ROLE_STATUS_WORD[role.status]}</td>
                <td>{roleCoverage(role, bindings.mappings)}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>

      <Panel heading="Signal bindings" headingId={FOUNDATION_BINDINGS_HEADING_ID}>
        {bindings.binding_set === null ? (
          <p data-bindings-state="NONE">{bindings.statement}</p>
        ) : (
          <>
            <p data-bindings-state="PUBLISHED">
              <Badge tone="neutral">{`Binding v${bindings.binding_set.version}`}</Badge> Effective{" "}
              {formatInstant(bindings.binding_set.valid_from)} to{" "}
              {formatInstant(bindings.binding_set.valid_to)} · {bindings.statement}
            </p>
            <FactList>
              <Fact term="Binding set ID">
                <code>{bindings.binding_set.binding_set_id}</code>
              </Fact>
              <Fact term="Binding version record ID">
                <code>{bindings.binding_set.binding_set_revision_id}</code>
              </Fact>
              <Fact term="Bindings digest (SHA-256)">
                <code>{bindings.binding_set.bindings_sha256}</code>
              </Fact>
              <Fact term="Role set">{bindings.binding_set.role_set}</Fact>
            </FactList>
            <DataTable labelledBy={FOUNDATION_BINDINGS_HEADING_ID}>
              <caption>
                Each bound channel of the registered gateway: its source, the equipment it describes,
                its role and units. Configuration, not readings.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Channel</th>
                  <th scope="col">Source</th>
                  <th scope="col">Equipment</th>
                  <th scope="col">Role</th>
                  <th scope="col">Units</th>
                  <th scope="col">Conversion</th>
                  <th scope="col">Binding ID</th>
                </tr>
              </thead>
              <tbody>
                {bindings.mappings.map((binding) => (
                  <tr key={binding.binding_revision_id} data-binding-channel={`${binding.device_id}/${binding.signal_id}`}>
                    <th scope="row">
                      <code>{`${binding.device_id} / ${binding.signal_id}`}</code>
                    </th>
                    <td>
                      <code>{binding.source_external_id ?? binding.source_id}</code>
                    </td>
                    <td>{binding.asset_code ?? "Unknown"}</td>
                    <td>{binding.role_label}</td>
                    <td>{`${binding.source_unit} → ${binding.canonical_unit}`}</td>
                    <td>{conversionText(binding)}</td>
                    <td>
                      <code>{binding.binding_revision_id}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </>
        )}
        {unbound.length === 0 ? null : (
          <>
            <p>Declared channels with no binding (Unknown until bound):</p>
            <ul aria-label="Unbound channels">
              {unbound.map((channel) => (
                <li key={`${channel.device_id}/${channel.signal_id}`} data-channel-status={channel.status}>
                  <code>{`${channel.device_id} / ${channel.signal_id}`}</code> ({channel.unit}):{" "}
                  {channel.status === "UNREGISTERED" ? "no registered source" : "not bound"}
                </li>
              ))}
            </ul>
          </>
        )}
        {snapshot.available ? (
          <p data-snapshot-available="true">
            Gateway snapshot for this basis: SHA-256 <code>{snapshot.sha256}</code> (Foundation version
            record <code>{snapshot.foundation_revision_id}</code>, binding version record{" "}
            <code>{snapshot.binding_set_revision_id}</code>).{" "}
            <a href={snapshotHref} download>
              Download snapshot
            </a>
          </p>
        ) : (
          <p data-snapshot-available="false">Gateway snapshot: not available. {snapshot.reason}</p>
        )}
        {bindings.binding_set === null || bindings.mappings.length === 0 ? null : (
          <RemoveBindingForm mappings={bindings.mappings} onPublishBindings={onPublishBindings} />
        )}
      </Panel>
    </>
  );
}

function RemoveBindingForm({
  mappings,
  onPublishBindings,
}: {
  mappings: SignalBinding[];
  onPublishBindings: FoundationBindingsPanelProps["onPublishBindings"];
}) {
  const [selected, setSelected] = useState("");
  const [effective, setEffective] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const instant = effective === "" ? null : utcInstantFromLocal(effective);
    if (selected === "" || instant === null) {
      setMessage("Choose a binding and the instant its removal takes effect.");
      return;
    }
    const removed = mappings.find((m) => m.binding_revision_id === selected);
    const remaining = mappings.filter((m) => m.binding_revision_id !== selected);
    setPending(true);
    const outcome = await onPublishBindings(
      instant,
      remaining,
      `Removed ${removed?.device_id ?? ""} / ${removed?.signal_id ?? ""}`,
    );
    setPending(false);
    setMessage(
      outcome.status === "published"
        ? `Published binding v${outcome.binding_set.version}, effective ${formatInstant(
            outcome.binding_set.valid_from,
          )} to ${formatInstant(outcome.binding_set.valid_to)}.`
        : `Not published: ${outcome.message}`,
    );
  }

  return (
    <form aria-label="Remove a binding" onSubmit={submit}>
      <p>
        Remove one binding from a chosen instant. This publishes a new binding version; earlier
        periods keep their stored bindings.
      </p>
      <label>
        Binding{" "}
        <select value={selected} onChange={(event) => setSelected(event.target.value)}>
          <option value="">Choose a binding</option>
          {mappings.map((m) => (
            <option key={m.binding_revision_id} value={m.binding_revision_id}>
              {`${m.role_label} · ${m.device_id} / ${m.signal_id}`}
            </option>
          ))}
        </select>
      </label>{" "}
      <label>
        Effective from (UTC){" "}
        <input type="datetime-local" value={effective} onChange={(event) => setEffective(event.target.value)} />
      </label>{" "}
      <button type="submit" disabled={pending}>
        Publish binding change
      </button>
      {message === null ? null : <p role="status">{message}</p>}
    </form>
  );
}

